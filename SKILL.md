---
name: edit-video-reels-coban
description: Edit video talking-head (người ngồi/đứng nói) thành Reels/TikTok dọc 9:16 theo STYLE kênh đào tạo Hưng Huỳnh (giống video mẫu). Nhận 1 video quay mặt nói → cắt đoạn vấp/lặp + nén nghỉ, grade màu (LUT GreenField 50% + đẩy xanh chống ám vàng, contrast/nét), BADGE thương hiệu góc trên-trái chạy suốt (tròn vàng "H" + HƯNG HUỲNH / Chia sẻ cách quay video), phụ đề SF Rounded TRẮNG + TỪ KHOÁ in HOA VÀNG viền đen dưới cằm, thẻ CARD nêu bật (viền trái màu + icon + dòng chính) hiện CÙNG phụ đề, nút CTA vàng cuối, tiếng SÁNG. Tự chứa, chạy trên MÁY NÀY (Apple Silicon, ffmpeg không libass → burn chữ bằng PNG overlay). LUẬT: nghe "Hương/Hùng" ghi "Hưng"; không chữ nào đè MẶT. Dùng khi đưa 1 video quay mặt nói và muốn "edit video reels", "làm reels từ video này", "edit talking-head", "edit theo mẫu Hưng Huỳnh". CHỈ chạy macOS.
---

# Edit Video Reels — style đào tạo Hưng Huỳnh

Biến 1 video quay mặt nói thành Reels/TikTok 9:16 chuẩn gu kênh Hưng Huỳnh.
Style bám **video mẫu1.mp4**. Skill này **tự chứa** trên máy này — không phụ
thuộc kho SFX/whisper-venv của máy anh Hưng.

> **Nguyên tắc chia việc:** script lo phần TẤT ĐỊNH (cắt, màu, render, burn chữ).
> Claude lo phần BIÊN TẬP (đọc transcript → chọn đoạn vấp cần bỏ + soạn phụ đề +
> chọn câu nêu bật thành card + viết CTA). **Luôn trình plan cho anh duyệt trước khi render.**

## Anh chỉ cần đưa ĐÚNG 2 thứ
1. **File video gốc** (đường dẫn `.mp4/.MOV`).
2. **1 câu mô tả**: video nói gì + cuối muốn kêu gọi gì (vd: "dạy quay đỡ rung, cuối kêu bình luận CÁCH QUAY").

Không bắt buộc: tên **preset** (mặc định `mau-01-chia-se-cach-quay`), nơi lưu file xuất.

## ⛔ LUẬT TỐI THƯỢNG (không bao giờ vi phạm)
1. **KHÔNG chữ/nhãn nào đè MẶT người nói.** Talking-head: mặt ở vùng trên-giữa →
   mọi chữ đặt ở **1/3 DƯỚI** (ngang ngực, dưới cằm). Phụ đề mặc định y=0.852,
   card đáy ở 0.755. QC lại từng mốc trước khi chốt.
2. **Chính tả tên:** nghe "Hương/Hùng/Hưn" → viết **"Hưng"**. Tên quán/khoá viết đúng.
3. **KHÔNG bịa lời.** Phụ đề bám transcript; chỉ sửa lỗi nghe nhầm hiển nhiên.

## Style khoá cứng (đo từ video mẫu — đừng đổi trừ khi anh yêu cầu)
- **Khung:** dọc 9:16. draft 720p / standard 1080p / max 4K (2160×3840).
- **Màu (palette):** vàng thương hiệu `#F7C92E` · nền tối card `rgb(18,18,22)`~85% · xanh nhấn `#2ECC40` · đỏ cảnh báo `#EB4A4A` · chữ trắng.
- **Font:** phụ đề & card & CTA = **SF Rounded** (weight Black/Bold, có tiếng Việt); badge = Arial Bold/Regular; icon = Apple Color Emoji.
- **Badge:** góc trên-trái, chạy SUỐT video. Tròn vàng chữ "H" + "HƯNG HUỲNH" (trắng đậm) / "Chia sẻ cách quay video" (xám).
- **Phụ đề:** trắng, **từ khoá in HOA VÀNG**, viền đen dày ~7, căn giữa ngang, dưới cằm. Mỗi dòng 4–8 chữ, tô vàng 1–2 cụm đắt nhất.
- **Card:** thẻ tối bo góc, **thanh viền trái màu** (vàng=mẹo, xanh=giải pháp, đỏ=lỗi/nỗi đau), dòng nhãn (icon + LABEL in hoa), 1–2 dòng chính (trắng + từ khoá màu accent), dòng phụ mờ tuỳ chọn. Hiện đúng lúc đang nói ý đó (2–5s).
- **CTA:** 4–6s cuối. Hộp tối chứa dòng nhãn ("MUỐN QUAY ĐẸP HƠN? 🎥") + nút VÀNG chữ tối ("Bình luận: CÁCH QUAY").
- **Tiếng:** highpass + đẩy treble + nén nhẹ + loudnorm ‑14 LUFS ("tiếng sáng").
- **SFX + Zoom (mặc định BẬT):** mỗi khi **CARD (thanh khung chữ) hiện** → 1 tiếng *Pop/Nút UI* (luân phiên, không trùng) **+ ZOOM punch-in ~1.09×** vào mặt rồi trả về khi card tắt; **CTA** → *Chuông thông báo*. SFX trộn DƯỚI giọng (volume 0.7, có `alimiter` chống vỡ), zoom chỉ đẩy HÌNH — chữ/badge đứng yên (dán sau zoom). Kho SFX dùng CHUNG: `~/.claude/skills/_shared/GOI-SFX-CO-BAN` (30 tiếng, -16 LUFS). Tắt: thêm `"zoom":{"enable":false}` / `"sfx":{"enable":false}` vào plan. Chỉnh: `zoom.amp`, `zoom.y_center`, `sfx.volume`, `sfx.card_pool`, `sfx.cta_sfx`.

## Môi trường máy này (đã kiểm tra)
- ffmpeg (Homebrew, Apple Silicon) — **KHÔNG có libass** → chữ burn bằng **PNG overlay** (Pillow) rồi `overlay` + `enable`.
- Pillow (đã cài), numpy.
- Transcribe: **whisper CLI** `~/Library/Python/3.9/bin/whisper` (openai-whisper).
- Fonts: `/System/Library/Fonts/SFNSRounded.ttf`, `.../Supplemental/Arial*.ttf`, `.../Apple Color Emoji.ttc`.
- LUT: `assets/lut.cube` (HBK_GreenField, kèm trong skill).

## QUY TRÌNH (chạy từng bước, có checkpoint anh duyệt)

**B1 — Transcribe.** Bóc lời có mốc thời gian:
```
python3 scripts/th_transcribe.py --video "<video>" --out /tmp/evr/tx --model medium
```
→ `tx.words.json` (từng từ) + `tx.segments.json` (câu). Model `small` cho nhanh, `medium`/`large-v3` cho chính xác (chậm hơn trên CPU).

**B2 — Claude soạn PLAN + trình anh duyệt.** Đọc transcript rồi TỰ đề xuất:
- `keep`: các đoạn giữ (bỏ đoạn vấp/lặp/im lặng dài). Thiếu = giữ cả video.
- `subtitles`: từng dòng bám lời (mốc theo timeline GỐC), chọn `keywords` tô vàng.
- `cards`: mỗi ý lớn 1 card (label + icon + accent + main + keywords).
- `cta`: nút cuối.
Trình bảng cho anh xem → anh "ok" hoặc sửa. **Không render khi chưa duyệt.**

**B3 — Vòng NHÁP (nhanh).** Render draft 720p để anh xem bố cục/chữ/nhịp:
```
python3 scripts/th_render.py --video "<video>" --plan plan.json --out nhap.mp4 --quality draft
```
Sửa plan tới khi ưng (transcribe KHÔNG chạy lại — chỉ sửa plan + render lại).

**B4 — Vòng CHỐT (đẹp).** Đổi `--quality max` (hoặc `standard`) ra bản nạp platform:
```
python3 scripts/th_render.py --video "<video>" --plan plan.json --out final.mp4 --quality max
```

**B5 — QC + giao.** Trích vài khung tại mỗi card/CTA, chắc chắn không đè mặt, chính tả đúng. Báo anh đường dẫn file.

## plan.json — cấu trúc
```json
{
  "preset": "mau-01-chia-se-cach-quay",
  "keep": [[0.0, 71.3]],
  "subtitles": [
    {"start": 0.2, "end": 2.1, "text": "Vì sao khách VỪA VÔ ĐÃ THOÁT?", "keywords": ["vừa vô đã thoát"]}
  ],
  "cards": [
    {"start": 2.5, "end": 6.0, "label": "Mẹo quay video", "icon": "💡", "accent": "yellow",
     "main": ["Vì sao người xem", "VỪA VÔ đã THOÁT?"], "keywords": ["vừa vô", "thoát"], "sub": ""}
  ],
  "cta": {"start": 66, "end": 71.3, "label": "MUỐN QUAY ĐẸP HƠN?", "icon": "🎥",
          "main": "Bình luận:", "main_key": "CÁCH QUAY"}
}
```
- Mốc `start/end` trong subtitles/cards/cta theo **timeline GỐC** — script tự dời qua các lát `keep`.
- `keywords` = cụm cần tô màu (không phân biệt hoa/thường); khớp thì tự IN HOA.
- `accent`: `yellow` | `green` | `red` | `white`.
- Muốn TẮT badge: `"badge": false`. Muốn đổi chữ badge: `"badge": {...}`.
- Ghi đè style 1 video: thêm nhánh `grade`/`audio`/`subtitle_defaults`/`card_defaults` vào plan (đè lên preset).

## Hệ thống PRESET (thêm mẫu mới không đụng code)
Mỗi mẫu = 1 file `presets/<tên>.json` mô tả badge + màu grade + audio + default cỡ chữ/vị trí + ghi chú recipe. Config/plan ghi đè lên preset. **Thêm mẫu:** đưa 1 video mẫu mới → phân tích style → copy 1 preset có sẵn, chỉnh số + recipe.
- `mau-01-chia-se-cach-quay` — HIỆN ĐẠI: badge + card/cta, phụ đề trắng + từ khoá vàng. (nguồn: video mẫu1.mp4)

## Scripts
- `scripts/th_transcribe.py` — whisper CLI → words/segments JSON.
- `scripts/th_style.py` — palette + font + tiện ích vẽ (PIL).
- `scripts/th_overlay.py` — render badge/subtitle/card/cta thành PNG + vị trí.
- `scripts/th_render.py` — cắt + grade + ghép overlay + audio + export (1 lần encode).

## Bẫy đã gặp (đừng dính lại)
- **ffprobe 8.x**: dùng `-of default=nokey=1:noprint_wrappers=1` (không phải `nk=1:np=0`).
- **Emoji màu**: PIL phải render ở strike 160 rồi thu nhỏ, `embedded_color=True`.
- **SF Rounded**: chọn weight bằng `set_variation_by_name("Black")` (font biến thiên).
- **Grade double**: nếu test trên video ĐÃ edit sẽ thấy màu gắt/đỏ — trên video RAW mới đúng. Đừng chỉnh preset dựa trên test video đã grade.
- **Không cắt** thì `keep` để trống hoặc bỏ hẳn — script tự lấy cả video.
- **zoompan làm video ngắn lại khi nguồn không phải 30fps** (đã fix): `zoom_filter()` trong
  `scripts/th_render.py` hardcode `fps=30` cho `zoompan`. Nếu video gốc là 25fps (phổ biến với
  máy quay VN/điện thoại) mà không quy đổi trước, `zoompan` với `d=1` sẽ gán mỗi khung nguồn = 1
  khung ở nhịp 30fps, làm cả video ngắn lại còn `n_khung/30` giây thay vì đúng thời lượng — tiếng
  vẫn đủ nhưng hình dừng sớm (mất hẳn đoạn cuối, kể cả CTA). Fix: chèn `fps={fps}` NGAY TRƯỚC
  `zoompan` trong filter chain để quy đổi khung về đúng nhịp trước khi zoompan tiêu thụ (`d=1`).
  Luôn QC bằng cách trích khung ở cuối video (`ffprobe format=duration` cũng phải khớp
  `ffprobe` gốc) sau khi bật zoom, nhất là với nguồn không phải 30fps.
- **Muốn da sáng hơn / màu trong trẻo hơn**: ghi đè nhánh `grade` trong plan.json, đẩy
  `brightness` lên (vd `0.01`→`0.03-0.06`), `contrast` lên nhẹ (`1.06`→`1.09-1.11`), giảm
  `saturation` một chút (`1.12`→`1.05-1.08`, màu bớt gắt = "trong" hơn), tăng `gamma_b`
  (`1.03`→`1.05-1.07`, cắt ám vàng thêm), tăng `sharpen` nhẹ (`0.6`→`0.75-0.85`), và có thể
  giảm `lut_strength` (`0.5`→`0.4-0.45`) để LUT bớt lấn màu tự nhiên. Đẩy tăng dần qua vài
  vòng nháp, đừng nhảy quá tay kẻo cháy sáng.
