#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xuong-reels-server.py — Server chạy trên MÁY MAC.
Điện thoại (cùng wifi) mở http://<ip-mac>:<port> -> chọn video + badge -> bấm Làm.
Server TỰ: chép lời (whisper) -> tự soạn plan -> render -> trả reel về điện thoại.
Không phụ thuộc gì ngoài Python chuẩn + skill sẵn có.
"""
import os, sys, json, uuid, threading, subprocess, re, socket, tempfile, shutil, argparse, cgi
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPTS = os.path.join(SKILL, "scripts")
sys.path.insert(0, HERE)
import auto_plan

WORKROOT = os.path.join(tempfile.gettempdir(), "xuong-reels-jobs")
os.makedirs(WORKROOT, exist_ok=True)
JOBS = {}            # id -> dict(state,pct,msg,out,error,name)
MODEL = "medium"     # đặt qua --model


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
        # 2) TRANSCRIBE (đọc % của whisper trên stderr)
        set_job(jid, state="transcribing", pct=2, msg="Đang nghe chép lời…")
        p = subprocess.Popen([sys.executable, os.path.join(SCRIPTS, "th_transcribe.py"),
                              "--video", video, "--out", os.path.join(wd, "tx"),
                              "--model", MODEL], stderr=subprocess.PIPE, text=True)
        for line in p.stderr:
            m = re.findall(r"(\d+)%\|", line)
            if m:
                set_job(jid, pct=2 + int(m[-1]) * 0.48, msg="Đang nghe chép lời…")
        p.wait()
        segf = os.path.join(wd, "tx.segments.json")
        if p.returncode != 0 or not os.path.exists(segf):
            raise RuntimeError("Chép lời lỗi (đã cài whisper chưa?)")
        segments = json.load(open(segf, encoding="utf-8"))
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
        for line in p.stdout:
            m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line.replace("\r", "\n"))
            if m:
                t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                set_job(jid, pct=min(99, 55 + 44 * t / max(dur, 1)))
        p.wait()
        if p.returncode != 0 or not os.path.exists(out):
            raise RuntimeError("Render lỗi")
        set_job(jid, state="done", pct=100, msg="Xong!", out=out)
    except Exception as e:
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

    def do_POST(self):
        if self.path.split("?")[0] != "/render":
            return self._send(404, json.dumps({"error": "not found"}))
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                environ={"REQUEST_METHOD": "POST",
                                         "CONTENT_TYPE": self.headers["Content-Type"]})
        if "video" not in form:
            return self._send(400, json.dumps({"error": "thiếu video"}))
        item = form["video"]
        ext = os.path.splitext(item.filename or "v.mp4")[1] or ".mp4"
        jid = uuid.uuid4().hex[:12]
        vpath = os.path.join(WORKROOT, jid + ext)
        with open(vpath, "wb") as f:
            shutil.copyfileobj(item.file, f)
        opts = {k: form.getvalue(k, "") for k in
                ("badge_title", "badge_sub", "cta", "cta_label", "cta_icon", "quality")}
        opts["quality"] = opts.get("quality") or "standard"
        set_job(jid, state="queued", pct=0, msg="Đã nhận video…",
                name=item.filename or "video")
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--model", default="medium")
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
