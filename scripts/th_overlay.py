#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
th_overlay.py — render các thành phần overlay thành PNG (RGBA) + trả vị trí.

Mỗi hàm render_* nhận:
  W, H : kích thước khung xuất (px)
  S    : hệ số scale = W / 720  (kích thước style khai báo trong không gian 720)
  spec : dict mô tả nội dung (lấy từ plan.json, hợp nhất preset)
và trả (PIL.Image RGBA đã crop, x, y)  — toạ độ dán trong khung xuất.

Bốn thành phần: badge (góc trên-trái, chạy suốt) · subtitle (phụ đề dưới cằm)
· card (thẻ nêu bật) · cta (nút kêu gọi cuối).
"""
from PIL import Image, ImageDraw
import th_style as st


def _canvas(W, H):
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _accent(name):
    return {"yellow": st.YELLOW, "green": st.GREEN, "red": st.RED,
            "white": st.WHITE}.get((name or "yellow").lower(), st.YELLOW)


# ------------------------------------------------------------------ BADGE
def render_badge(W, H, S, spec):
    """spec: {title, subtitle, letter}  -> pill tối + tròn vàng chữ + 2 dòng."""
    title = spec.get("title", "HƯNG HUỲNH")
    sub = spec.get("subtitle", "Chia sẻ cách quay video")
    letter = spec.get("letter", "H")

    pad = int(13 * S)
    circle_d = int(58 * S)
    gap = int(12 * S)
    f_title = st.arial(26 * S, bold=True)
    f_sub = st.arial(16 * S, bold=False)
    f_letter = st.sf(34 * S, "Black")

    tw = int(max(f_title.getlength(title), f_sub.getlength(sub)))
    text_h = int(30 * S + 6 * S + 20 * S)
    inner_h = max(circle_d, text_h)
    pill_w = pad + circle_d + gap + tw + int(18 * S)
    pill_h = inner_h + 2 * pad

    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    x0, y0 = int(22 * S), int(26 * S)
    st.rounded_rect(d, [x0, y0, x0 + pill_w, y0 + pill_h],
                    radius=int(pill_h / 2), fill=st.DARK_BG + (225,))
    # tròn vàng + chữ
    cx = x0 + pad
    cy = y0 + (pill_h - circle_d) // 2
    d.ellipse([cx, cy, cx + circle_d, cy + circle_d], fill=st.YELLOW)
    d.text((cx + circle_d / 2, cy + circle_d / 2 - int(2 * S)), letter,
           font=f_letter, fill=st.BLACK, anchor="mm")
    # 2 dòng chữ
    tx = cx + circle_d + gap
    ty = y0 + pad + int(2 * S)
    d.text((tx, ty), title, font=f_title, fill=st.WHITE, anchor="la")
    d.text((tx, ty + int(30 * S) + int(5 * S)), sub, font=f_sub,
           fill=st.SUB_GRAY, anchor="la")

    im, ox, oy = st.crop_to_content(im, pad=0)
    return im, ox, oy


# ------------------------------------------------------------------ SUBTITLE
def _word_runs(text, kws):
    """Tách 'text' thành list (từ, is_key) — từ khoá đã IN HOA."""
    out = []
    for s, k in st.split_runs(text, kws):
        for w in s.split(" "):
            if w:
                out.append((w, k))
    return out


def _wrap(words, font, max_w, max_lines=2):
    """Gói các từ thành dòng vừa max_w. None nếu cần >max_lines hoặc 1 từ quá rộng."""
    sp = font.getlength(" ")
    lines, cur, cur_w = [], [], 0.0
    for w, k in words:
        ww = font.getlength(w)
        if ww > max_w:
            return None
        add = ww if not cur else cur_w + sp + ww
        if cur and add > max_w:
            lines.append(cur); cur, cur_w = [(w, k)], ww
        else:
            cur.append((w, k)); cur_w = add
    if cur:
        lines.append(cur)
    return lines if len(lines) <= max_lines else None


def render_subtitle(W, H, S, spec):
    """spec: {text, keywords, y}  -> phụ đề trắng + từ khoá VÀNG, viền đen dày,
       căn giữa ngang, đặt ở vùng dưới cằm (mặc định y≈0.85H).
       Tự CO CHỮ rồi XUỐNG 2 DÒNG nếu quá rộng — không bao giờ tràn mép."""
    text = spec["text"]
    kws = spec.get("keywords", [])
    base = spec.get("size", 40)
    yc = spec.get("y", 0.852)
    weight = spec.get("weight", "Bold")
    stroke = int(spec.get("stroke", 7) * S)
    max_w = spec.get("max_w", 0.93) * W

    words = _word_runs(text, kws)
    chosen = None
    for factor in (1.0, 0.93, 0.86, 0.80, 0.74):
        f = st.sf(base * factor * S, weight)
        lines = _wrap(words, f, max_w, max_lines=2)
        if lines is not None:
            chosen = (f, lines); break
    if chosen is None:                       # ép ở cỡ nhỏ nhất, cho phép 3 dòng
        f = st.sf(base * 0.74 * S, weight)
        chosen = (f, _wrap(words, f, max_w, max_lines=3) or [words])
    f, lines = chosen

    line_h = int(f.getbbox("Ẫyộ")[3] - f.getbbox("Ẫyộ")[1])
    gap = int(6 * S)
    block_h = len(lines) * line_h + (len(lines) - 1) * gap
    y0 = int(yc * H - block_h / 2) - int(6 * S)

    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        lw = sum(f.getlength(w) for w, _ in line) + f.getlength(" ") * (len(line) - 1)
        x = int((W - lw) / 2)
        y = y0 + i * (line_h + gap)
        for w, k in line:
            d.text((x, y), w, font=f, fill=(st.YELLOW if k else st.WHITE),
                   stroke_width=stroke, stroke_fill=st.BLACK, anchor="la")
            x += f.getlength(w) + f.getlength(" ")
    im, ox, oy = st.crop_to_content(im, pad=int(2 * S))
    return im, ox, oy


# ------------------------------------------------------------------ CARD
def render_card(W, H, S, spec):
    """spec: {label, icon, accent, main:[..], keywords:[..], sub, bottom}
       Thẻ tối, thanh viền màu bên trái, dòng nhãn (icon + LABEL), 1-2 dòng chính
       (trắng + từ khoá màu accent), dòng phụ mờ tuỳ chọn.
       'bottom' = tỉ lệ H cho ĐÁY thẻ (mặc định 0.755, ngay trên phụ đề)."""
    label = spec.get("label", "")
    icon = spec.get("icon", "")
    accent = _accent(spec.get("accent", "yellow"))
    mains = spec.get("main", [])
    if isinstance(mains, str):
        mains = [mains]
    kws = spec.get("keywords", [])
    sub = spec.get("sub", "")
    bottom = spec.get("bottom", 0.755)

    pad = int(18 * S)
    bar_w = int(6 * S)
    f_label = st.sf(19 * S, "Bold")
    f_main = st.sf(30 * S, "Bold")
    f_sub = st.sf(19 * S, "Medium")
    icon_px = int(23 * S)
    line_gap = int(9 * S)

    # đo chiều rộng
    ic = st.emoji_img(icon, icon_px) if icon else None
    label_w = (ic.width + int(8 * S) if ic else 0) + int(f_label.getlength(label.upper()))
    main_ws = [sum(f_main.getlength(s) for s, _ in st.split_runs(m, kws)) for m in mains]
    sub_w = int(f_sub.getlength(sub)) if sub else 0
    content_w = int(max([label_w] + main_ws + [sub_w]))

    inner_x = pad + bar_w + int(12 * S)
    card_w = inner_x + content_w + pad
    card_w = int(min(max(card_w, 300 * S), 0.82 * W))

    lab_h = int(22 * S)
    main_h = int(f_main.getbbox("Ẫy")[3] - f_main.getbbox("Ẫy")[1])
    n_main = len(mains)
    sub_h = int(24 * S) if sub else 0
    content_h = lab_h + line_gap + n_main * main_h + (n_main - 1) * int(4 * S)
    if sub:
        content_h += line_gap + sub_h
    card_h = content_h + 2 * pad

    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    x0 = int(0.285 * W)                      # lệch trái, ngang ngực
    y1 = int(bottom * H)
    y0 = y1 - card_h
    st.rounded_rect(d, [x0, y0, x0 + card_w, y1], radius=int(16 * S),
                    fill=st.DARK_BG + (222,))
    # thanh viền trái
    st.rounded_rect(d, [x0 + pad, y0 + pad, x0 + pad + bar_w, y1 - pad],
                    radius=int(bar_w / 2), fill=accent)

    cy = y0 + pad
    # dòng nhãn
    lx = x0 + inner_x
    if ic:
        im.alpha_composite(ic, (lx, cy + (lab_h - ic.height) // 2))
        lx += ic.width + int(8 * S)
    d.text((lx, cy + lab_h / 2), label.upper(), font=f_label,
           fill=(215, 215, 220), anchor="lm")
    cy += lab_h + line_gap
    # dòng chính
    for i, m in enumerate(mains):
        runs = st.split_runs(m, kws)
        st.draw_runs(d, x0 + inner_x, cy, runs, f_main,
                     key_color=accent, base_color=st.WHITE, stroke=0)
        cy += main_h + int(4 * S)
    # dòng phụ
    if sub:
        cy += line_gap - int(4 * S)
        d.text((x0 + inner_x, cy), sub, font=f_sub, fill=st.SUB_GRAY, anchor="la")

    im, ox, oy = st.crop_to_content(im, pad=0)
    return im, ox, oy


# ------------------------------------------------------------------ CTA
def render_cta(W, H, S, spec):
    """spec: {label, icon, main, main_key, y}
       Hộp tối chứa: dòng nhãn (LABEL + icon) + nút VÀNG chữ tối.
       'main' vd 'Bình luận:', 'main_key' vd 'CÁCH QUAY' (đậm)."""
    label = spec.get("label", "MUỐN QUAY ĐẸP HƠN?")
    icon = spec.get("icon", "🎥")
    main = spec.get("main", "Bình luận:")
    main_key = spec.get("main_key", "")
    yc = spec.get("y", 0.66)

    pad = int(16 * S)
    f_label = st.sf(18 * S, "Bold")
    f_main = st.sf(26 * S, "Bold")
    f_key = st.sf(26 * S, "Black")
    icon_px = int(20 * S)

    ic = st.emoji_img(icon, icon_px) if icon else None
    label_w = int(f_label.getlength(label.upper())) + (ic.width + int(8 * S) if ic else 0)
    key_txt = " " + main_key if main_key else ""
    btn_text_w = int(f_main.getlength(main) + f_key.getlength(key_txt))
    btn_pad_x = int(22 * S)
    btn_w = btn_text_w + 2 * btn_pad_x
    btn_h = int(56 * S)

    content_w = max(label_w, btn_w)
    box_w = content_w + 2 * pad
    lab_h = int(22 * S)
    box_h = pad + lab_h + int(12 * S) + btn_h + pad

    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    x0 = (W - box_w) // 2
    y0 = int(yc * H)
    st.rounded_rect(d, [x0, y0, x0 + box_w, y0 + box_h], radius=int(16 * S),
                    fill=st.DARK_BG + (220,))
    # dòng nhãn (căn giữa)
    lx = x0 + (box_w - label_w) // 2
    cy = y0 + pad
    d.text((lx, cy + lab_h / 2), label.upper(), font=f_label, fill=st.WHITE, anchor="lm")
    if ic:
        im.alpha_composite(ic, (lx + int(f_label.getlength(label.upper())) + int(8 * S),
                                cy + (lab_h - ic.height) // 2))
    # nút vàng
    by0 = cy + lab_h + int(12 * S)
    bx0 = x0 + (box_w - btn_w) // 2
    st.rounded_rect(d, [bx0, by0, bx0 + btn_w, by0 + btn_h], radius=int(btn_h / 2),
                    fill=st.YELLOW)
    tx = bx0 + btn_pad_x
    tym = by0 + btn_h / 2
    d.text((tx, tym), main, font=f_main, fill=(20, 20, 20), anchor="lm")
    if main_key:
        d.text((tx + f_main.getlength(main), tym), key_txt, font=f_key,
               fill=(20, 20, 20), anchor="lm")

    im, ox, oy = st.crop_to_content(im, pad=0)
    return im, ox, oy


RENDERERS = {
    "badge": render_badge,
    "subtitle": render_subtitle,
    "card": render_card,
    "cta": render_cta,
}
