#!/usr/bin/env bash
# Bật server Xưởng Reels trên máy Mac. Điện thoại cùng wifi mở link hiện ra.
# Dùng: bash chay-server.sh [port] [model]
cd "$(dirname "$0")"
PORT="${1:-8000}"; MODEL="${2:-small}"
command -v python3 >/dev/null || { echo "❌ Chưa có python3"; exit 1; }
python3 -c "import PIL" 2>/dev/null || { echo "⚠️  Thiếu thư viện — chạy: bash cai-dat.sh"; }
python3 -c "import faster_whisper" 2>/dev/null || { echo "⚠️  Thiếu faster-whisper — chạy: python3 -m pip install --user faster-whisper"; }
exec python3 server/xuong-reels-server.py --port "$PORT" --model "$MODEL"
