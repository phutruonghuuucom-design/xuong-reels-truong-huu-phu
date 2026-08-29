# Xưởng Reels Trương Hữu Phú — chạy trên server thuê ngoài (Railway/Render/VPS...).
# Build: docker build -t xuong-reels .
# Run:   docker run -p 8000:8000 xuong-reels
FROM python:3.11-slim

# ffmpeg để cắt/ghép/render video; không cần cài font hệ thống vì đã bundle
# Be Vietnam Pro + Noto Color Emoji trong assets/fonts/ (xem scripts/th_style.py).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# faster-whisper (CTranslate2) — không cần PyTorch, nhẹ hơn nhiều và nhanh hơn hẳn
# openai-whisper CLI trên CPU. Model được server giữ cache trong RAM (xem
# scripts/th_transcribe.py) nên chỉ tải 1 lần cho suốt vòng đời container.
RUN pip install --no-cache-dir Pillow numpy faster-whisper

COPY . .

# Tải sẵn model lúc build — tránh lần dùng đầu tiên phải chờ tải.
# Mặc định "small": điểm cân bằng tốt nhất tốc độ/độ chính xác, chỉ cần ~1GB RAM.
# Máy chủ nhiều RAM hơn thì đổi qua build-arg, vd: --build-arg WHISPER_MODEL=medium
# để nghe chép lời chính xác hơn (chậm hơn đáng kể).
ARG WHISPER_MODEL=small
ENV WHISPER_MODEL=${WHISPER_MODEL}
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', device='cpu', compute_type='int8')"

EXPOSE 8000
CMD ["python3", "server/xuong-reels-server.py"]
