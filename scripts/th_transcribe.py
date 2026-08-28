#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
th_transcribe.py — bóc lời video ra transcript có mốc thời gian TỪNG TỪ.

Dùng whisper CLI (openai-whisper) đã cài sẵn trên máy. Xuất 2 thứ:
  <out>.words.json  : [{"start","end","word"}...] toàn bộ từ
  <out>.segments.json: [{"start","end","text"}...] theo câu whisper cắt

Chạy:
  python3 th_transcribe.py --video in.mp4 --out /tmp/job/tx [--model medium]

LƯU Ý CHÍNH TẢ (kênh Hưng Huỳnh): whisper hay nghe "Hưng" thành "Hương/Hùng".
Sau khi có transcript, Claude tự sửa lại đúng tên khi soạn phụ đề — KHÔNG sửa ở đây.
"""
import argparse
import json
import os
import subprocess
import sys

WHISPER = os.path.expanduser("~/Library/Python/3.9/bin/whisper")


def run(video, out, model="medium", lang="Vietnamese"):
    out_dir = os.path.dirname(os.path.abspath(out)) or "."
    os.makedirs(out_dir, exist_ok=True)
    wav = out + ".16k.wav"
    # -map 0:a:0: ép lấy luồng tiếng chính (iPhone .MOV có thêm luồng spatial 4ch)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video,
                    "-map", "0:a:0", "-ar", "16000", "-ac", "1", wav], check=True)

    whisper = WHISPER if os.path.exists(WHISPER) else "whisper"
    subprocess.run([whisper, wav, "--model", model, "--language", lang,
                    "--word_timestamps", "True", "--output_format", "json",
                    "--output_dir", out_dir, "--verbose", "False"], check=True)

    base = os.path.splitext(os.path.basename(wav))[0]
    wj = os.path.join(out_dir, base + ".json")
    with open(wj, encoding="utf-8") as f:
        data = json.load(f)

    words, segs = [], []
    for seg in data.get("segments", []):
        segs.append({"start": round(seg["start"], 2),
                     "end": round(seg["end"], 2),
                     "text": seg["text"].strip()})
        for w in seg.get("words", []):
            words.append({"start": round(w["start"], 2),
                          "end": round(w["end"], 2),
                          "word": w["word"].strip()})

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
    ap.add_argument("--model", default="medium")
    ap.add_argument("--lang", default="Vietnamese")
    a = ap.parse_args()
    if not os.path.exists(a.video):
        sys.exit("Không thấy video: " + a.video)
    run(a.video, a.out, a.model, a.lang)
