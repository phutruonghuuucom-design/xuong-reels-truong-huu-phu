#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuong-reels-server.py — Server chạy trên MÁY MAC.
Điện thoại (cùng wifi) mở http://<ip-mac>:<port> -> chọn video + badge -> bấm Làm.
Server TỰ: chép lời (whisper) -> tự soạn plan -> render -> trả reel về điện thoại.
Không phụ thuộc gì ngoài Python chuẩn + skill sẵn có.
"""
import os, sys, json, uuid, threading, subprocess, re, socket, tempfile, shutil, argparse, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, HERE)
sys.path.insert(0, SCRIPTS)
import auto_plan
import th_transcribe

WORKROOT = os.path.join(tempfile.gettempdir(), "xuong-reels-jobs")
os.makedirs(WORKROOT, exist_ok=True)
JOBS = {}            # id -> dict(state,pct,msg,out,error,name)
UPLOADS = {}         # id -> dict(opts,cdir,filename) — upload đang nhận theo từng mảnh
MODEL = "small"      # đặt qua --model


def set_job(jid, **kw):
    JOBS.setdefault(jid, {}).update(kw)


def run_pipeline(jid, video, opts):
    wd = os.path.join(WORKROOT, jid)
    os.makedirs(wd, exist_ok=True)
    try:
        # 1) DURATION
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nokey=1:noprint_wrappers=1", video]).decode().strip())
        # 2) TRANSCRIBE — gọi trực tiếp trong process (model đã cache sẵn trong RAM
        # từ lần chạy trước, không tải lại mất 10-30s mỗi lần như trước).
        set_job(jid, state="transcribing", pct=2, msg="Đang nghe chép lời…")

        def _prog(cur_t, total_t):
            total_t = total_t or dur or 1
            set_job(jid, pct=2 + min(48, 48 * cur_t / total_t))

        try:
            segments = th_transcribe.run(video, os.path.join(wd, "tx"),
                                          model=MODEL, progress_cb=_prog)
        except Exception as e:
            raise RuntimeError("Chép lời lỗi: " + str(e))
        # 3) AUTO PLAN
        set_job(jid, state="planning", pct=52, msg="Đang soạn phụ đề + tô từ khoá…")
        plan = auto_plan.build_plan(segments, opts, dur)
        planf = os.path.join(wd, "plan.json")
        json.dump(plan, open(planf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        # 4) RENDER (đọc time= của ffmpeg -> % 55..99)
        set_job(jid, state="rendering", pct=55, msg="Đang dựng video…")
        out = os.path.join(wd, "reels.mp4")
        p = subprocess.Popen([sys.executable, os.path.join(SCRIPTS, "th_render.py"),
                              "--video", video, "--plan", planf, "--out", out,
                              "--quality", opts.get("quality", "standard"),
                              "--workdir", os.path.join(wd, "rd")],
                             stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
        render_log = []
        for line in p.stdout:
            render_log.append(line)
            m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line.replace("\r", "\n"))
            if m:
                t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                set_job(jid, pct=min(99, 55 + 44 * t / max(dur, 1)))
        p.wait()
        if p.returncode != 0 or not os.path.exists(out):
            tail = "".join(render_log[-40:]).strip()
            print("RENDER FAIL rc=%s\n%s" % (p.returncode, tail), flush=True)
            raise RuntimeError("Render lỗi (rc=%s): %s" % (p.returncode, tail[-600:] or "không có output"))
        set_job(jid, state="done", pct=100, msg="Xong!", out=out)
    except Exception as e:
        print("PIPELINE FAIL:", traceback.format_exc(), flush=True)
        set_job(jid, state="error", error=str(e), msg="Lỗi: " + str(e))
    finally:
        try:
            if os.path.exists(video):
                os.remove(video)
        except Exception:
            pass


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_header("Content-Length", str(len(body) if body is not None else 0))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            html = open(os.path.join(HERE, "app.html"), encoding="utf-8").read()
            return self._send(200, html, "text/html; charset=utf-8")
        if path == "/health":
            return self._send(200, json.dumps({"ok": True}))
        if path == "/status":
            q = dict(x.split("=") for x in self.path.split("?")[-1].split("&") if "=" in x)
            j = JOBS.get(q.get("id"), {"state": "unknown"})
            return self._send(200, json.dumps({k: j.get(k) for k in
                              ("state", "pct", "msg", "error")}))
        if path == "/result":
            q = dict(x.split("=") for x in self.path.split("?")[-1].split("&") if "=" in x)
            j = JOBS.get(q.get("id"))
            if not j or j.get("state") != "done" or not os.path.exists(j.get("out", "")):
                return self._send(404, json.dumps({"error": "chưa có kết quả"}))
            data = open(j["out"], "rb").read()
            return self._send(200, data, "video/mp4",
                              {"Content-Disposition": 'attachment; filename="reels.mp4"'})
        return self._send(404, json.dumps({"error": "not found"}))

    def _qs(self):
        return dict(x.split("=") for x in self.path.split("?")[-1].split("&") if "=" in x)

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/upload-init":
            return self._upload_init()
        if path == "/upload-chunk":
            return self._upload_chunk()
        if path == "/upload-complete":
            return self._upload_complete()
        return self._send(404, json.dumps({"error": "not found"}))

    def _upload_init(self):
        # Client gửi JSON {badge_title, badge_sub, cta, cta_label, cta_icon, quality, filename}
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            opts = json.loads(body.decode("utf-8"))
        except Exception:
            opts = {}
        jid = uuid.uuid4().hex[:12]
        cdir = os.path.join(WORKROOT, jid + ".chunks")
        os.makedirs(cdir, exist_ok=True)
        UPLOADS[jid] = {"opts": opts, "cdir": cdir,
                         "filename": opts.get("filename") or "video.mp4"}
        return self._send(200, json.dumps({"id": jid}))

    def _upload_chunk(self):
        # Nhận 1 mảnh video (raw bytes) — video lớn được cắt nhỏ ở client để không
        # vượt giới hạn upload 100MB/lần của Cloudflare khi dùng qua link public.
        q = self._qs()
        u = UPLOADS.get(q.get("id"))
        if not u or "index" not in q:
            return self._send(400, json.dumps({"error": "upload không hợp lệ"}))
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length) if length else b""
        with open(os.path.join(u["cdir"], "%08d" % int(q["index"])), "wb") as f:
            f.write(data)
        return self._send(200, json.dumps({"ok": True}))

    def _upload_complete(self):
        u = UPLOADS.pop(self._qs().get("id"), None)
        if not u:
            return self._send(400, json.dumps({"error": "upload không hợp lệ"}))
        jid = os.path.basename(u["cdir"])[:-len(".chunks")]
        ext = os.path.splitext(u["filename"])[1] or ".mp4"
        vpath = os.path.join(WORKROOT, jid + ext)
        with open(vpath, "wb") as out:
            for name in sorted(os.listdir(u["cdir"])):
                with open(os.path.join(u["cdir"], name), "rb") as f:
                    shutil.copyfileobj(f, out)
        shutil.rmtree(u["cdir"], ignore_errors=True)
        opts = u["opts"]
        opts["quality"] = opts.get("quality") or "standard"
        set_job(jid, state="queued", pct=0, msg="Đã nhận video…", name=u["filename"])
        threading.Thread(target=run_pipeline, args=(jid, vpath, opts), daemon=True).start()
        return self._send(200, json.dumps({"id": jid}))


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    global MODEL
    # PaaS (Railway/Render...) gán cổng qua biến môi trường PORT — ưu tiên nó nếu có,
    # còn không thì dùng mặc định 8000 như khi chạy trên máy Mac.
    default_port = int(os.environ.get("PORT", 8000))
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=default_port)
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"))
    a = ap.parse_args()
    MODEL = a.model
    ip = lan_ip()
    print("=" * 52)
    print("  XƯỞNG REELS — SERVER ĐÃ CHẠY")
    print("  Mở trên điện thoại (cùng wifi với Mac):")
    print(f"      http://{ip}:{a.port}")
    print(f"  (whisper: {MODEL})   Nhấn Ctrl+C để tắt.")
    print("=" * 52)
    ThreadingHTTPServer(("0.0.0.0", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
