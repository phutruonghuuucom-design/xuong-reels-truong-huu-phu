#!/usr/bin/env bash
# Cài đặt phụ thuộc cho skill edit-video-reels-coban (macOS).
set -u
cd "$(dirname "$0")"
echo "=== Cài đặt edit-video-reels-coban ==="

# 0. macOS?
if [[ "$(uname)" != "Darwin" ]]; then
  echo "❌ Skill này CHỈ chạy trên macOS. Máy hiện tại: $(uname). Dừng."
  exit 1
fi

# 1. Homebrew + ffmpeg
if ! command -v brew >/dev/null 2>&1; then
  echo "❌ Chưa có Homebrew. Cài tại https://brew.sh rồi chạy lại script này."
  exit 1
fi
if command -v ffmpeg >/dev/null 2>&1; then
  echo "✅ ffmpeg đã có: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
else
  echo "➡️  Cài ffmpeg..."; brew install ffmpeg || { echo "❌ Cài ffmpeg lỗi"; exit 1; }
fi

# 2. Python deps
echo "➡️  Cài Pillow + faster-whisper (có thể mất vài phút)..."
python3 -m pip install --user --quiet --upgrade Pillow numpy faster-whisper \
  && echo "✅ Pillow + faster-whisper xong" || { echo "❌ pip install lỗi"; exit 1; }

# 3. Thử tải model "small" (chạy 1 lần cho nhanh ở lần dùng đầu tiên)
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('✅ model small sẵn sàng')" \
  || echo "⚠️  Tải model small lỗi — sẽ tự thử lại ở lần chạy đầu tiên."

# 4. Kiểm font (chỉ cảnh báo, skill có fallback)
for f in "/System/Library/Fonts/SFNSRounded.ttf" "/System/Library/Fonts/Apple Color Emoji.ttc"; do
  [[ -f "$f" ]] && echo "✅ font: $(basename "$f")" || echo "⚠️  thiếu font $(basename "$f") — skill sẽ dùng font thay thế."
done

# 5. Chạy thử import
python3 -c "import sys; sys.path.insert(0,'scripts'); import th_style, th_overlay; print('✅ scripts nạp OK')" \
  || { echo "❌ Lỗi nạp scripts (thiếu Pillow?)"; exit 1; }

echo ""
echo "🎉 XONG. Giờ copy thư mục này vào ~/.claude/skills/  rồi mở Claude Code và nói \"edit video reels\"."
