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

# Cài PyTorch bản CPU-only trước (tránh openai-whisper tự kéo bản CUDA nặng gấp nhiều lần).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir Pillow numpy openai-whisper

COPY . .

# Tải sẵn model Whisper lúc build — tránh lần dùng đầu tiên phải chờ tải ~1.5GB.
# Đổi model qua build-arg nếu máy chủ ít RAM (vd: --build-arg WHISPER_MODEL=small).
ARG WHISPER_MODEL=medium
ENV WHISPER_MODEL=${WHISPER_MODEL}
RUN python3 -c "import whisper; whisper.load_model('${WHISPER_MODEL}')"

EXPOSE 8000
CMD ["python3", "server/xuong-reels-server.py"]
