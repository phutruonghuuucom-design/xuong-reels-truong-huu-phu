#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_plan.py — TỰ soạn plan.json từ transcript (không cần người biên tập).
Dùng cho chế độ "bỏ video vào là xong": tách câu dài, tự chọn 1-2 từ khoá/câu
để renderer tô VÀNG. Badge lấy từ người dùng. Không tự đặt card (cần biên tập).
"""
import re

# Từ đệm/tiếng đưa hơi — khi đứng RIÊNG một mình ở đầu/cuối câu (hoặc chiếm
# trọn nguyên 1 segment do VAD tách vì có khoảng lặng quanh nó) thì bị CẮT bỏ
# luôn, không giữ trong video lẫn phụ đề.
FILLER = set("""
à ạ á ằ ầy ừ ừm ừa ờ ợ ê ề ế ơ ơi dạ hử hửm ối ưm um
""".split())

# Khoảng lặng giữa 2 đoạn nói dài hơn ngưỡng này (giây) -> cắt bỏ hẳn.
CUT_GAP = 0.35
# Đệm quanh mỗi đoạn giữ, tránh cắt cụt đầu/cuối tiếng nói.
KEEP_PAD = 0.12

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


def _strip_filler_edges(words):
    """Bỏ các từ đệm đứng LIÊN TỤC ở đầu và cuối câu. Trả None nếu cả câu chỉ
    toàn từ đệm (segment bị bỏ hẳn)."""
    i, j = 0, len(words) - 1
    while i <= j and _core(words[i]["word"]) in FILLER:
        i += 1
    while j >= i and _core(words[j]["word"]) in FILLER:
        j -= 1
    if i > j:
        return None
    return words[i:j + 1]


def _adjust_segments(segments):
    """Cắt từ đệm đầu/cuối mỗi segment bằng mốc thời gian từng-từ (nếu có);
    segment nào toàn từ đệm thì bỏ hẳn. Segment không có mốc từng-từ (nguồn
    cũ/test) thì giữ nguyên — không lọc được, nhưng vẫn dùng để tính khoảng lặng."""
    out = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        words = seg.get("words") or []
        if not words:
            out.append(dict(seg))
            continue
        kept = _strip_filler_edges(words)
        if not kept:
            continue
        out.append({
            "start": kept[0]["start"], "end": kept[-1]["end"],
            "text": " ".join(w["word"].strip() for w in kept if w["word"].strip()),
        })
    return out


def _build_keep(segments, dur):
    """Ghép các đoạn có tiếng nói (đã đệm) thành danh sách [start,end] cần
    GIỮ; khoảng lặng > CUT_GAP giữa 2 đoạn thì cắt bỏ hẳn (jump-cut)."""
    spans = sorted((float(s["start"]), float(s["end"])) for s in segments)
    if not spans:
        return [[0.0, round(float(dur), 2)]]
    keep = []
    for s, e in spans:
        s = max(0.0, s - KEEP_PAD)
        e = min(float(dur), e + KEEP_PAD)
        if keep and s - keep[-1][1] <= CUT_GAP:
            keep[-1][1] = max(keep[-1][1], e)
        else:
            keep.append([s, e])
    return [[round(a, 2), round(b, 2)] for a, b in keep]


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
    """segments: [{start,end,text,words?}]; opts: badge_title/badge_sub/cta...; dur: giây."""
    segments = _adjust_segments(segments)
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
        "keep": _build_keep(segments, dur),
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
