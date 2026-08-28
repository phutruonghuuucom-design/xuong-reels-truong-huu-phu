# Cài đặt skill `edit-video-reels-coban`

Skill biến 1 video quay mặt nói (talking-head) thành Reels/TikTok dọc 9:16 theo style kênh **Hưng Huỳnh** (badge, phụ đề vàng, thẻ card, CTA, grade màu, **SFX + zoom punch-in tự động**).

> ✅ Gói này **tự chứa**: 30 hiệu ứng âm thanh (SFX) đã nhúng sẵn trong `assets/sfx/` — cài xong là chạy, khỏi tải thêm. Mỗi khi hiện thẻ card sẽ có tiếng "pop" + zoom nhẹ vào mặt cho hút mắt; CTA có tiếng chuông.

> ⚠️ **Chỉ chạy trên macOS** (dùng font hệ thống của Mac + ffmpeg). Windows/Linux không chạy được.

---

## 1. Cần có sẵn
- **macOS** (máy Mac bất kỳ)
- **Homebrew** — nếu chưa có, cài tại https://brew.sh
- **Claude Code** (skill này chạy trong Claude Code)

## 2. Cài nhanh (1 lệnh)
Mở **Terminal**, `cd` vào thư mục skill này rồi chạy:

```bash
bash cai-dat.sh
```

Script sẽ tự: cài **ffmpeg**, **openai-whisper**, **Pillow**, kiểm tra font, và chạy thử.

## 3. Đặt skill vào đúng chỗ
Copy nguyên thư mục `edit-video-reels-coban/` vào 1 trong 2 nơi:
- **Dùng chung mọi dự án:** `~/.claude/skills/edit-video-reels-coban/`
- **Chỉ 1 vault/dự án:** `<thư-mục-dự-án>/.claude/skills/edit-video-reels-coban/`

Mở lại Claude Code là skill xuất hiện.

## 4. Cách dùng
Trong Claude Code, nói:
> "edit video reels" + kéo/đưa đường dẫn 1 video quay mặt nói + 1 câu mô tả (video nói gì, cuối kêu gọi gì).

Ví dụ: *"Edit video reels giúp mình file ~/Downloads/quay.mov, video dạy cách quay đỡ rung, cuối kêu bình luận CÁCH QUAY."*

AI sẽ: transcribe → đề xuất plan (phụ đề/card/CTA) cho bạn duyệt → render nháp 720p → chốt 1080p/4K.

---

## 📱 Chế độ "Điện thoại bấm — Mac làm hết" (khỏi đụng tay)
Muốn chỉ **bỏ video vào điện thoại là xong**, Mac tự chép phụ đề + render:

1. Trên Mac (đã cài xong ở bước 2), chạy:
   ```bash
   bash chay-server.sh
   ```
   Màn hình hiện 1 link kiểu `http://192.168.x.x:8000`.
2. Điện thoại **cùng wifi** với Mac → mở link đó bằng trình duyệt.
3. Trong app: **Chọn video** → sửa **Badge** (nếu muốn) → bấm **Làm reel**.
4. Máy Mac tự nghe chép + dựng, xong thì bấm **Tải video** về điện thoại.

> Mac phải **đang bật + chạy server** và **cùng wifi**. Lần đầu macOS hỏi "cho phép python nhận kết nối" → bấm **Allow**. Video dài xử lý lâu, cứ giữ trang mở.
> Chép lời nhanh/chậm tùy model: `bash chay-server.sh 8000 small` (nhanh, kém chính xác hơn) hoặc `medium` (mặc định).

## Tự cài tay (nếu không dùng cai-dat.sh)
```bash
brew install ffmpeg
python3 -m pip install --user Pillow openai-whisper
```

## Trục trặc thường gặp
- **"command not found: whisper"** → chạy lại `python3 -m pip install --user openai-whisper`. Script tự dò whisper ở `~/Library/Python/*/bin` và trong PATH.
- **Render chậm** → bình thường, decode 4K trên CPU nặng. Xem bản nháp 720p trước, chốt 1080p (đủ đẹp cho Reels/TikTok).
- **Chữ phụ đề khác kiểu** → máy thiếu font *SF Rounded*, skill tự fallback sang SF Pro/Helvetica (vẫn chạy, chỉ khác nét chữ chút).
