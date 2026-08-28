#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
th_render.py — dựng video cuối từ 1 plan.json + video gốc, trong MỘT lần encode.

Làm tuần tự trong 1 filtergraph ffmpeg:
  cắt (giữ các đoạn "keep") -> nối -> grade màu (LUT + eq + nét) -> scale ->
  dán overlay (badge chạy suốt, phụ đề/card/cta theo mốc thời gian) ; audio sáng.

plan.json (Claude soạn sau khi đọc transcript). Ví dụ tối thiểu:
{
  "preset": "mau-01-chia-se-cach-quay",
  "keep": [[0.0, 71.3]],                      // đoạn giữ (bỏ vấp). Thiếu = cả video
  "badge": {"title":"HƯNG HUỲNH","subtitle":"Chia sẻ cách quay video","letter":"H"},
  "subtitles": [
     {"start":0.2,"end":2.1,"text":"Vì sao khách VỪA VÔ ĐÃ THOÁT?","keywords":["vừa vô đã thoát"]}
  ],
  "cards": [
     {"start":2.5,"end":6.0,"label":"Mẹo quay video","icon":"💡","accent":"yellow",
      "main":["Vì sao người xem","VỪA VÔ đã THOÁT?"],"keywords":["vừa vô","thoát"]}
  ],
  "cta": {"start":66,"end":71.3,"label":"MUỐN QUAY ĐẸP HƠN?","icon":"🎥",
          "main":"Bình luận:","main_key":"CÁCH QUAY"}
}

Thời gian trong subtitles/cards/cta tính theo TIMELINE GỐC (khớp transcript);
script tự dời mốc qua các lát cắt.

Chạy:
  python3 th_render.py --video in.mp4 --plan plan.json --out final.mp4 --quality standard
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import th_overlay as ov

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
LUT = os.path.join(SKILL, "assets", "lut.cube")

# Kho SFX dùng CHUNG cho mọi skill edit-video (Hill Media – GÓI SFX CƠ BẢN).
SFX_CANDIDATES = [
    os.path.expanduser("~/.claude/skills/_shared/GOI-SFX-CO-BAN"),
    os.path.join(SKILL, "assets", "sfx"),
]
# Pool tiếng cho CARD (thanh khung chữ) — luân phiên để KHÔNG trùng liên tiếp.
SFX_CARD_POOL = ["06-Pop-1", "12-Nut-UI-2", "07-Pop-2", "13-Nut-UI-3", "08-Pop-3", "11-Nut-UI-1"]
SFX_CTA = "16-Chuong-thong-bao-1"


def resolve_sfx_dir(scfg):
    d = scfg.get("dir")
    if d and os.path.isdir(os.path.expanduser(d)):
        return os.path.expanduser(d)
    for c in SFX_CANDIDATES:
        if os.path.isdir(c):
            return c
    return None

QUALITY = {
    # tên: (w, h, crf, x264 preset)
    "draft":    (720, 1280, 23, "veryfast"),
    "standard": (1080, 1920, 19, "slow"),
    "max":      (2160, 3840, 17, "slow"),
}


def ffprobe_dur(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", path]).decode().strip()
    return float(out)


def load_preset(name):
    if not name:
        return {}
    p = os.path.join(SKILL, "presets", name + ".json")
    if not os.path.exists(p):
        print("! Không thấy preset:", p, file=sys.stderr)
        return {}
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    return {k: v for k, v in d.items() if not k.startswith("_")}


def merge(preset, plan):
    """Hợp nhất: preset làm nền, plan ghi đè (nông theo từng khối)."""
    out = dict(preset)
    for k, v in plan.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            m = dict(out[k]); m.update(v); out[k] = m
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------- time remap
def build_keep(plan, dur):
    keep = plan.get("keep")
    if not keep:
        return [[0.0, dur]]
    return [[max(0.0, float(a)), min(dur, float(b))] for a, b in keep if b > a]


def remapper(keep):
    """Trả hàm map t(gốc)->t(cuối), và None nếu t nằm trong đoạn bị bỏ."""
    segs = []
    off = 0.0
    for s, e in keep:
        segs.append((s, e, off))
        off += (e - s)
    total = off

    def f(t, clamp=False):
        for s, e, o in segs:
            if s <= t <= e:
                return o + (t - s)
        if clamp:
            # về mốc đoạn keep gần nhất
            best = None
            for s, e, o in segs:
                for edge, val in ((s, o), (e, o + (e - s))):
                    d = abs(t - edge)
                    if best is None or d < best[0]:
                        best = (d, val)
            return best[1] if best else 0.0
        return None
    return f, total


# ---------------------------------------------------------------- overlays
def prepare_overlays(cfg, keep, W, H, S, workdir):
    """Render mọi PNG overlay + tính mốc thời gian đã dời. Trả list dict."""
    fmap, total = remapper(keep)
    items = []
    idx = 0
    sub_def = cfg.get("subtitle_defaults", {})
    card_def = cfg.get("card_defaults", {})
    cta_def = cfg.get("cta_defaults", {})

    def withdef(defaults, spec):
        m = dict(defaults); m.update(spec); return m

    def add(kind, spec, t0, t1):
        nonlocal idx
        s = fmap(t0, clamp=True)
        e = fmap(t1, clamp=True)
        if e <= s:
            return
        img, x, y = ov.RENDERERS[kind](W, H, S, spec)
        if img.width == 0:
            return
        path = os.path.join(workdir, f"ov_{idx:03d}_{kind}.png")
        img.save(path)
        items.append({"path": path, "x": int(x), "y": int(y),
                      "start": round(s, 3), "end": round(e, 3)})
        idx += 1

    # BADGE — chạy suốt (nếu preset/ plan không tắt)
    badge = cfg.get("badge")
    if badge not in (False, None):
        bspec = badge if isinstance(badge, dict) else {}
        img, x, y = ov.render_badge(W, H, S, bspec)
        path = os.path.join(workdir, "ov_000_badge.png")
        img.save(path)
        items.append({"path": path, "x": int(x), "y": int(y),
                      "start": 0.0, "end": round(total, 3)})
        idx = 1

    for sub in cfg.get("subtitles", []):
        add("subtitle", withdef(sub_def, sub), float(sub["start"]), float(sub["end"]))
    for card in cfg.get("cards", []):
        add("card", withdef(card_def, card), float(card["start"]), float(card["end"]))
    cta = cfg.get("cta")
    if cta:
        add("cta", withdef(cta_def, cta), float(cta["start"]), float(cta["end"]))
    return items, total


# ---------------------------------------------------------------- filtergraph
def grade_chain(cfg, W, H):
    """Chuỗi filter grade màu áp lên [vc] -> [vg]. LUT trộn theo lut_strength."""
    g = cfg.get("grade", {})
    strength = float(g.get("lut_strength", 0.5))
    lut_esc = LUT.replace(":", r"\:")
    parts = [
        "[vc]split=2[graw][glut]",
        f"[glut]lut3d=file='{lut_esc}'[gl]",
        f"[graw][gl]blend=all_mode=normal:all_opacity={strength}[gb]",
        (f"[gb]eq=contrast={g.get('contrast',1.06)}:"
         f"saturation={g.get('saturation',1.12)}:"
         f"brightness={g.get('brightness',0.01)}:"
         f"gamma_b={g.get('gamma_b',1.03)}[ge]"),        # gamma_b>1: đẩy xanh chống ám vàng
        f"[ge]unsharp=5:5:{g.get('sharpen',0.6)}:5:5:0.0[us]",
        f"[us]scale={W}:{H}:flags=lanczos,setsar=1[vg]",
    ]
    return parts


def zoom_and_sfx_plan(cfg, keep):
    """Từ cards + cta, tính cửa sổ ZOOM (mốc đã dời) và danh sách SFX cần chèn.
    Trả (zoom_windows, sfx_items, zcfg). SFX_items = [(path, delay_s, volume)]."""
    fmap, _ = remapper(keep)
    zcfg = cfg.get("zoom", {}) or {}
    scfg = cfg.get("sfx", {}) or {}
    cards = cfg.get("cards", [])
    cta = cfg.get("cta")

    # --- ZOOM: punch-in đúng cửa sổ card (+ cta) ---
    zoom_windows = []
    if zcfg.get("enable", True):
        for c in cards:
            s = fmap(float(c["start"]), clamp=True); e = fmap(float(c["end"]), clamp=True)
            if e > s:
                zoom_windows.append((s, e))
        if zcfg.get("cta_zoom", True) and cta:
            s = fmap(float(cta["start"]), clamp=True); e = fmap(float(cta["end"]), clamp=True)
            if e > s:
                zoom_windows.append((s, e))

    # --- SFX: card = pool luân phiên; cta = chuông thông báo ---
    sfx_items = []
    if scfg.get("enable", True):
        sdir = resolve_sfx_dir(scfg)
        if sdir:
            vol = float(scfg.get("volume", 0.7))
            pool = scfg.get("card_pool", SFX_CARD_POOL)
            for ci, c in enumerate(cards):
                name = pool[ci % len(pool)]
                p = os.path.join(sdir, name + ".mp3")
                if os.path.exists(p):
                    sfx_items.append((p, fmap(float(c["start"]), clamp=True), vol))
            cta_name = scfg.get("cta_sfx", SFX_CTA)
            if cta and cta_name:
                p = os.path.join(sdir, cta_name + ".mp3")
                if os.path.exists(p):
                    sfx_items.append((p, fmap(float(cta["start"]), clamp=True), vol))
    return zoom_windows, sfx_items, zcfg


def zoom_filter(zoom_windows, zcfg, W, H, src="[vg]", dst="[vz]", fps=30):
    """zoompan: z = 1 trong lúc thường, nhảy lên (1+amp) trong mỗi cửa sổ card.
    Giữ MẶT trong khung (tâm dọc y_center ~0.40). Chữ overlay dán SAU nên đứng yên."""
    amp = float(zcfg.get("amp", 0.09))
    yc = float(zcfg.get("y_center", 0.40))
    zin = 1.0 + amp
    expr = "1"
    for (s, e) in reversed(zoom_windows):
        expr = f"if(between(on/{fps}\\,{s:.3f}\\,{e:.3f})\\,{zin:.3f}\\,{expr})"
    x = "max(0\\,min(iw-iw/zoom\\,iw/2-(iw/zoom)/2))"
    y = f"max(0\\,min(ih-ih/zoom\\,ih*{yc}-(ih/zoom)/2))"
    # fps=<fps> trước zoompan: chuẩn hoá nguồn (có thể 25fps) về đúng {fps}
    # trước khi zoompan tiêu thụ d=1 khung/khung — nếu không, nguồn không phải
    # {fps} sẽ bị gán sai nhịp thời gian, làm video ngắn/dài lệch so với tiếng.
    return (f"{src}fps={fps},zoompan=z='{expr}':x='{x}':y='{y}':"
            f"d=1:s={W}x{H}:fps={fps}{dst}")


def audio_chain(cfg):
    a = cfg.get("audio", {})
    hp = a.get("highpass", 85)
    treble_g = a.get("treble", 2.0)
    loud_I = a.get("loudness", -14)
    return (f"highpass=f={hp},"
            f"treble=g={treble_g}:f=3500:t=q:w=1,"
            f"acompressor=threshold=-18dB:ratio=3:attack=6:release=180,"
            f"loudnorm=I={loud_I}:TP=-1.3:LRA=11")


def render(video, cfg, keep, out, quality, workdir):
    W, H, crf, x264 = QUALITY[quality]
    S = W / 720.0
    FPS = 30
    items, total = prepare_overlays(cfg, keep, W, H, S, workdir)
    zoom_windows, sfx_items, zcfg = zoom_and_sfx_plan(cfg, keep)

    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", video]
    for it in items:
        cmd += ["-i", it["path"]]
    for p, _d, _v in sfx_items:               # SFX là các input audio nối sau PNG overlay
        cmd += ["-i", p]
    sfx_base = 1 + len(items)                 # input index của SFX đầu tiên

    fc = []
    # cắt + nối
    vlabels, alabels = [], []
    for i, (s, e) in enumerate(keep):
        # 0:a:0 = luồng tiếng chính (iPhone .MOV có thể có nhiều luồng audio)
        fc.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        fc.append(f"[0:a:0]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}]")
        vlabels.append(f"[v{i}]"); alabels.append(f"[a{i}]")
    n = len(keep)
    if n == 1:
        fc.append(f"{vlabels[0]}null[vc]")
        fc.append(f"{alabels[0]}anull[ac]")
    else:
        fc.append("".join(vlabels) + f"concat=n={n}:v=1:a=0[vc]")
        fc.append("".join(alabels) + f"concat=n={n}:v=0:a=1[ac]")
    # grade màu ([vc] -> [vg])
    fc += grade_chain(cfg, W, H)
    # ZOOM punch-in ([vg] -> [vz]) — chỉ khi có cửa sổ zoom
    if zoom_windows:
        fc.append(zoom_filter(zoom_windows, zcfg, W, H, src="[vg]", dst="[vz]", fps=FPS))
        cur = "[vz]"
    else:
        cur = "[vg]"
    # overlays (dán SAU zoom -> badge/phụ đề/card đứng yên)
    for i, it in enumerate(items):
        inp = f"[{i+1}:v]"
        outl = f"[o{i}]"
        en = f":enable='between(t,{it['start']},{it['end']})'"
        fc.append(f"{cur}{inp}overlay={it['x']}:{it['y']}{en}{outl}")
        cur = outl
    vfinal = cur
    # audio: giọng chính -> chuẩn hoá "tiếng sáng"; rồi TRỘN SFX lên trên
    fc.append(f"[ac]{audio_chain(cfg)},aformat=channel_layouts=stereo[av]")
    if sfx_items:
        slabels = []
        for k, (_p, delay_s, vol) in enumerate(sfx_items):
            d = max(0, int(round(delay_s * 1000)))
            fc.append(f"[{sfx_base+k}:a]adelay={d}:all=1,volume={vol},"
                      f"aformat=channel_layouts=stereo[sfx{k}]")
            slabels.append(f"[sfx{k}]")
        fc.append(f"[av]{''.join(slabels)}amix=inputs={1+len(sfx_items)}:"
                  f"normalize=0:dropout_transition=0,alimiter=limit=0.95[aout]")
    else:
        fc.append("[av]anull[aout]")

    cmd += ["-filter_complex", ";".join(fc),
            "-map", vfinal, "-map", "[aout]",
            "-c:v", "libx264", "-preset", x264, "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            "-r", str(FPS), out]
    print("RENDER", W, "x", H, "quality=", quality, "overlays=", len(items),
          "zoom=", len(zoom_windows), "sfx=", len(sfx_items),
          "duration≈", round(total, 1), "s")
    subprocess.run(cmd, check=True)
    print("OK ->", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quality", default="standard", choices=list(QUALITY))
    ap.add_argument("--workdir", default=None)
    a = ap.parse_args()

    with open(a.plan, encoding="utf-8") as f:
        plan = json.load(f)
    cfg = merge(load_preset(plan.get("preset")), plan)
    dur = ffprobe_dur(a.video)
    keep = build_keep(plan, dur)
    wd = a.workdir or tempfile.mkdtemp(prefix="evr_")
    os.makedirs(wd, exist_ok=True)
    render(a.video, cfg, keep, a.out, a.quality, wd)


if __name__ == "__main__":
    main()
