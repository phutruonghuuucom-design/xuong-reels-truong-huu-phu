#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
th_style.py — Bảng màu + tiện ích vẽ overlay bằng Pillow cho skill edit-video-reels-coban.

Mọi kích thước khai báo trong "không gian 720" (chiều rộng khung = 720px, giống
video mẫu gốc). Khi render ở độ phân giải khác, nhân với hệ số S = out_w / 720
để giữ nét ở mọi độ phân giải (1080 → S=1.5, 4K 2160 → S=3).

Không phụ thuộc gì ngoài Pillow + font hệ thống macOS.
"""
import os
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
# Đo trực tiếp từ video mẫu1.mp4 (xem SKILL.md).
YELLOW      = (247, 201, 46)     # vàng thương hiệu: badge H, từ khoá, nút CTA
WHITE       = (255, 255, 255)
GREEN       = (46, 204, 64)      # xanh nhấn (card "cách sửa")
RED         = (235, 74, 74)      # đỏ cảnh báo (card lỗi/nỗi đau)
DARK_BG     = (18, 18, 22)       # nền tối pill / card
SUB_GRAY    = (176, 176, 184)    # chữ phụ mờ trong card / dòng phụ badge
BLACK       = (0, 0, 0)

# alpha mặc định cho nền tối (0-255)
BG_ALPHA = 214

# ---------------------------------------------------------------- fonts
def _first_existing(cands, label):
    for p in cands:
        if os.path.exists(p):
            return p
    # không thấy -> trả cái đầu, để ImageFont báo lỗi rõ ràng nếu thật sự thiếu
    import sys
    print(f"[th_style] CẢNH BÁO: thiếu font {label}, thử: {cands[0]}", file=sys.stderr)
    return cands[0]

# SF Rounded là font phụ đề/card. Fallback: SF Pro -> Helvetica (mọi máy Mac đều có).
SF_ROUNDED = _first_existing([
    "/System/Library/Fonts/SFNSRounded.ttf",
    "/System/Library/Fonts/SFNSRounded-Regular.otf",
    "/System/Library/Fonts/SFNS.ttf",              # SF Pro (không bo tròn, vẫn đẹp)
    "/System/Library/Fonts/Helvetica.ttc",
], "SF Rounded")
ARIAL_BOLD = _first_existing([
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
], "Arial Bold")
ARIAL_REG  = _first_existing([
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
], "Arial")
EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"
EMOJI_STRIKE = 160  # Apple Color Emoji chỉ có bitmap ở size 160 -> render rồi thu nhỏ

_font_cache = {}


def sf(size, weight="Black"):
    """SF Rounded ở weight yêu cầu (Black/Heavy/Bold/Semibold/Medium/Regular)."""
    key = ("sf", int(size), weight)
    if key in _font_cache:
        return _font_cache[key]
    f = ImageFont.truetype(SF_ROUNDED, int(size))
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    _font_cache[key] = f
    return f


def arial(size, bold=True):
    key = ("ar", int(size), bold)
    if key in _font_cache:
        return _font_cache[key]
    f = ImageFont.truetype(ARIAL_BOLD if bold else ARIAL_REG, int(size))
    _font_cache[key] = f
    return f


def emoji_img(ch, px):
    """Trả về ảnh RGBA của 1 emoji, cao/rộng ~px. None nếu lỗi."""
    try:
        ef = ImageFont.truetype(EMOJI_FONT, EMOJI_STRIKE)
        im = Image.new("RGBA", (EMOJI_STRIKE + 20, EMOJI_STRIKE + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((10, 6), ch, font=ef, embedded_color=True)
        im = im.crop(im.getbbox())
        if im.width == 0:
            return None
        scale = px / im.height
        return im.resize((max(1, int(im.width * scale)), int(px)), Image.LANCZOS)
    except Exception:
        return None


# ---------------------------------------------------------------- primitives
def rounded_rect(draw, box, radius, fill):
    """fill có thể là (r,g,b) hoặc (r,g,b,a)."""
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def text_size(font, text):
    bb = font.getbbox(text)
    return bb[2] - bb[0], bb[3] - bb[1]


def draw_text(draw, xy, text, font, fill, anchor="la", stroke=0, stroke_fill=BLACK):
    draw.text(xy, text, font=font, fill=fill, anchor=anchor,
              stroke_width=int(stroke), stroke_fill=stroke_fill)


# ---------------------------------------------------------------- mixed-color line
# Một dòng gồm nhiều "run": mỗi run có màu riêng (trắng thường, vàng cho từ khoá).
def split_runs(text, keywords):
    """
    Chia 'text' thành list run [(chuỗi, is_key)]. Một cụm keyword khớp
    (không phân biệt hoa/thường, có dấu) -> is_key=True và cụm đó IN HOA.
    keywords: list các cụm từ cần tô vàng (giữ nguyên chuỗi con, tách theo dấu cách).
    """
    if not keywords:
        return [(text, False)]
    lo = text.lower()
    marks = [False] * len(text)
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        klo = kw.lower()
        start = 0
        while True:
            i = lo.find(klo, start)
            if i < 0:
                break
            for j in range(i, i + len(klo)):
                marks[j] = True
            start = i + len(klo)
    runs = []
    cur, cur_key = "", marks[0] if text else False
    for idx, ch in enumerate(text):
        if marks[idx] == cur_key:
            cur += ch
        else:
            runs.append((cur, cur_key))
            cur, cur_key = ch, marks[idx]
    if cur:
        runs.append((cur, cur_key))
    # IN HOA các run từ khoá
    return [(s.upper() if k else s, k) for (s, k) in runs]


def measure_runs(font, runs):
    w = 0
    h = 0
    for s, _ in runs:
        bw, bh = text_size(font, s)
        # dùng advance thật để không dính chữ
        aw = font.getlength(s)
        w += aw
        h = max(h, bh)
    return int(w), int(h)


def draw_runs(draw, x, y, runs, font, key_color=YELLOW, base_color=WHITE,
              stroke=0, anchor_y="top"):
    """Vẽ chuỗi run bắt đầu tại (x,y). anchor_y='top' hoặc 'baseline'.
       Trả về x cuối."""
    cx = x
    for s, is_key in runs:
        color = key_color if is_key else base_color
        draw.text((cx, y), s, font=font, fill=color,
                  stroke_width=int(stroke), stroke_fill=BLACK, anchor="la")
        cx += font.getlength(s)
    return cx


def crop_to_content(img, pad=0):
    """Cắt ảnh RGBA về bbox nội dung + pad. Trả (img_cropped, offx, offy)."""
    bb = img.getbbox()
    if not bb:
        return img, 0, 0
    l, t, r, b = bb
    l = max(0, l - pad); t = max(0, t - pad)
    r = min(img.width, r + pad); b = min(img.height, b + pad)
    return img.crop((l, t, r, b)), l, t
