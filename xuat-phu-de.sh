#!/usr/bin/env bash
# Nghe chép phụ đề 1 video rồi xuất file .json để NHẬP vào app điện thoại Xưởng Reels.
# Dùng: bash xuat-phu-de.sh <video.mov> [model]   (model mặc định: medium)
set -u
cd "$(dirname "$0")"
V="${1:-}"; MODEL="${2:-medium}"
[ -z "$V" ] && { echo "Dùng: bash xuat-phu-de.sh <đường-dẫn-video> [tiny|base|small|medium]"; exit 1; }
[ -f "$V" ] || { echo "❌ Không thấy file: $V"; exit 1; }

NAME="$(basename "${V%.*}")"
OUT="$HOME/Desktop/phu-de-$NAME.json"
TMP="$(mktemp -d)"

echo "➡️  Đang nghe chép \"$NAME\" bằng whisper ($MODEL)… vài phút, chờ chút."
python3 scripts/th_transcribe.py --video "$V" --out "$TMP/tx" --model "$MODEL" \
  || { echo "❌ Lỗi transcribe (đã cài whisper chưa? chạy bash cai-dat.sh)"; rm -rf "$TMP"; exit 1; }

cp "$TMP/tx.segments.json" "$OUT"; rm -rf "$TMP"
N=$(python3 -c "import json;print(len(json.load(open('$OUT'))))" 2>/dev/null || echo "?")
echo ""
echo "✅ Xong! $N dòng phụ đề → $OUT"
echo "👉 AirDrop / gửi Zalo file này sang điện thoại, mở app Xưởng Reels, bấm \"Nhập phụ đề\"."
