#!/usr/bin/env python3
"""Seslendirmeyi konuşma tanıma ile yazıya döker (telaffuz kontrolü için).

Kullanım: python3 pipeline/check_audio.py video/public/TARIH/*.wav
Gerekir:  pip install faster-whisper
"""
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel


def load(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2)
for path in sys.argv[1:]:
    print(f"== {path}")
    segs, _ = model.transcribe(load(path), language="tr", beam_size=5)
    for s in segs:
        print(f"{s.start:5.1f}-{s.end:5.1f} {s.text.strip()}")
