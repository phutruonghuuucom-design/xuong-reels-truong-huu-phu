#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_plan.py — TỰ soạn plan.json từ transcript (không cần người biên tập).
Dùng cho chế độ "bỏ video vào là xong": tách câu dài, tự chọn 1-2 từ khoá/câu
để renderer tô VÀNG. Badge lấy từ người dùng. Không tự đặt card (cần biên tập).
"""
import re

# Từ chức năng tiếng Việt — KHÔNG chọn làm từ khoá nổi bật.
STOP = set("""
thì là mà và của các bạn này cái nó cho để một như thế đang rất hơn được có không ở
khi đó nè nha nhé vào ra lại nữa mình ta người những cũng với về trong ngoài trên dưới
đi đến từ nếu đây kia ấy rồi sẽ đã bị phải nên hay hoặc thôi chỉ vẫn còn quá lắm nào
sao vì bởi do tại khiến làm gì ai đâu mọi hay thường luôn ngay cứ tôi anh chị em chúng
""".split())

WORD = re.compile(r"[0-9A-Za-zÀ-ỹ]+")


def _core(w):
    m = WORD.findall(w)
    return "".join(m).lower()


def pick_keywords(text, k=2):
    """Chọn tối đa k từ 'mạnh' nhất (dài, không phải từ chức năng) để tô vàng."""
    words = text.split()
    scored = []
    for i, w in enumerate(words):
        c = _core(w)
        if len(c) < 4 or c in STOP:
            continue
        scored.append((len(c), i, w))
    scored.sort(key=lambda t: (-t[0], -t[1]))          # dài nhất, ưu tiên về cuối
    picked = sorted(scored[:k], key=lambda t: t[1])     # trả về theo thứ tự trong câu
    out = []
    for _, _, w in picked:
        kw = re.sub(r"^[^0-9A-Za-zÀ-ỹ]+|[^0-9A-Za-zÀ-ỹ/]+$", "", w)  # bỏ dấu câu 2 đầu
        if kw:
            out.append(kw)
    return out


def _split_long(seg, max_words=9):
    words = seg["text"].split()
    if len(words) <= max_words:
        return [seg]
    mid = len(words) // 2
    span = seg["end"] - seg["start"]
    cut = seg["start"] + span * mid / len(words)
    return [
        {"start": seg["start"], "end": round(cut, 2), "text": " ".join(words[:mid])},
        {"start": round(cut, 2), "end": seg["end"], "text": " ".join(words[mid:])},
    ]


def build_plan(segments, opts, dur):
    """segments: [{start,end,text}]; opts: badge_title/badge_sub/cta...; dur: giây."""
    subs = []
    for seg in segments:
        for s in _split_long(seg):
            txt = (s.get("text") or "").strip()
            if not txt:
                continue
            subs.append({
                "start": round(float(s["start"]), 2),
                "end": round(float(s["end"]), 2),
                "text": txt,
                "keywords": pick_keywords(txt),
            })
    title = (opts.get("badge_title") or "TRƯƠNG HỮU PHÚ").strip()
    plan = {
        "preset": "mau-01-chia-se-cach-quay",
        "keep": [[0, round(float(dur), 2)]],
        "badge": {
            "title": title,
            "subtitle": (opts.get("badge_sub") or "Chia sẻ cách quay video").strip(),
            "letter": (title[:1] or "T").upper(),
        },
        "subtitles": subs,
        "cards": [],
    }
    cta = (opts.get("cta") or "").strip()
    if cta:
        if ":" in cta:
            m, mk = cta.split(":", 1)
            main, main_key = m.strip() + ":", mk.strip()
        else:
            main, main_key = cta, ""
        plan["cta"] = {
            "start": max(0.0, round(float(dur), 2) - 6),
            "end": round(float(dur), 2),
            "label": (opts.get("cta_label") or "MUỐN QUAY ĐẸP HƠN?").strip(),
            "icon": opts.get("cta_icon") or "🎥",
            "main": main, "main_key": main_key,
        }
    return plan


if __name__ == "__main__":
    import json, sys
    segs = json.load(open(sys.argv[1], encoding="utf-8"))
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else segs[-1]["end"]
    print(json.dumps(build_plan(segs, {}, dur), ensure_ascii=False, indent=2))
