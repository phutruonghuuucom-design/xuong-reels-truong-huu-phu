#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
th_transcribe.py — bóc lời video ra transcript có mốc thời gian TỪNG TỪ.

Dùng faster-whisper (CTranslate2) — nhanh hơn nhiều lần so với openai-whisper CLI
gốc trên CPU, cùng chất lượng model, không cần cài PyTorch. Xuất 2 thứ:
  <out>.words.json  : [{"start","end","word"}...] toàn bộ từ
  <out>.segments.json: [{"start","end","text"}...] theo câu whisper cắt

Chạy CLI (dùng khi Claude thao tác thủ công trên máy Mac):
  python3 th_transcribe.py --video in.mp4 --out /tmp/job/tx [--model small]

Dùng như module (server web) — gọi run() trực tiếp để TÁI SỬ DỤNG model đã tải
trong bộ nhớ (get_model() cache theo kích thước), tránh phải tải lại model
(~10-30s) mỗi lần có video mới.

LƯU Ý CHÍNH TẢ (kênh Hưng Huỳnh): whisper hay nghe "Hưng" thành "Hương/Hùng".
Sau khi có transcript, Claude tự sửa lại đúng tên khi soạn phụ đề — KHÔNG sửa ở đây.
"""
import argparse
import json
import os
import subprocess
import sys
import threading

_model_cache = {}
_model_lock = threading.Lock()


def get_model(model_name):
    """Tải model 1 lần rồi cache lại — gọi lại lần sau (cùng process) không tải lại."""
    with _model_lock:
        if model_name not in _model_cache:
            from faster_whisper import WhisperModel
            _model_cache[model_name] = WhisperModel(
                model_name, device="cpu", compute_type="int8")
        return _model_cache[model_name]


def run(video, out, model="small", lang="vi", progress_cb=None):
    out_dir = os.path.dirname(os.path.abspath(out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    wav = out + ".16k.wav"
    # -map 0:a:0: ép lấy luồng tiếng chính (iPhone .MOV có thêm luồng spatial 4ch)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video,
                    "-map", "0:a:0", "-ar", "16000", "-ac", "1", wav], check=True)

    wmodel = get_model(model)
    # vad_filter=True: tự bỏ đoạn im lặng, vừa nhanh hơn vừa đỡ "ảo giác" ra chữ.
    segments_iter, info = wmodel.transcribe(
        wav, language=lang, word_timestamps=True, vad_filter=True)

    words, segs = [], []
    for seg in segments_iter:
        segs.append({"start": round(seg.start, 2),
                     "end": round(seg.end, 2),
                     "text": seg.text.strip()})
        for w in (seg.words or []):
            words.append({"start": round(w.start, 2),
                          "end": round(w.end, 2),
                          "word": w.word.strip()})
        if progress_cb:
            progress_cb(seg.end, info.duration)

    with open(out + ".words.json", "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=1)
    with open(out + ".segments.json", "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    try:
        os.remove(wav)
    except OSError:
        pass
    print("WORDS", out + ".words.json", len(words))
    print("SEGMENTS", out + ".segments.json", len(segs))
    return segs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="vi")
    a = ap.parse_args()
    if not os.path.exists(a.video):
        sys.exit("Không thấy video: " + a.video)
    run(a.video, a.out, a.model, a.lang)
