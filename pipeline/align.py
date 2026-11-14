#!/usr/bin/env python3
"""Altyazılar için kelime düzeyinde zamanlama.

Seslendirmenin tamamı bir kez faster-whisper ile kelime zamanlarıyla yazıya dökülür; tanınan harfler
ekranda görünen metnin harfleriyle hizalanır (difflib). Böylece her kelime sesteki gerçek anında
vurgulanır. Rakam, kısaltma gibi tanınanla birebir eşleşmeyen yerler komşu kelimelerden doğrusal
olarak tamamlanır; harflerinin yeterince eşleşmediği cümle None döner (çağıran oransal zamanlar).

  align_words(audio, sr, sents) -> [cümle başına kelime başlangıçları (sn) ya da None, ...]
  sents: [{"t0": cümle sesinin başı, "t1": sonu, "text": ekranda görünen cümle}, ...]

Deneme:  python3 pipeline/align.py ses.wav "Birinci cümle." "İkinci cümle."
"""
import difflib
import os
import subprocess
import sys

import numpy as np

MODEL = os.environ.get("GUNDEM_ALIGN_MODEL", "small")
MIN_MATCH = 0.45  # cümle harflerinin en az bu oranı eşleşmeli
SLACK = 0.25  # tanınan kelimeyi cümleye atarken pay (sn)


def _chars(word):
    w = word.replace("I", "ı").replace("İ", "i").lower()
    return [c for c in w if c.isalnum()]


def _to16k(audio, sr):
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                        "-f", "s16le", "-ar", "16000", "-ac", "1", "-"],
                       input=np.asarray(audio, np.int16).tobytes(), capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def _model():
    from faster_whisper import WhisperModel  # yoksa ImportError: çağıran oransal zamanlamaya düşer
    kw = dict(device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    try:
        return WhisperModel(MODEL, local_files_only=True, **kw)  # önbellekteyse ağa hiç çıkma
    except Exception:
        return WhisperModel(MODEL, **kw)


def transcribe(audio, sr):
    """[(kelime, başlangıç, bitiş), ...]"""
    segs, _ = _model().transcribe(_to16k(audio, sr), language="tr", beam_size=5, word_timestamps=True,
                                  condition_on_previous_text=False, vad_filter=False)
    return [(w.word, float(w.start), float(w.end)) for s in segs for w in (s.words or [])]


def _align_sentence(rec, s):
    S, starts = [], []
    for w in s["text"].split():
        starts.append(len(S))
        S += _chars(w)
    R, Rt = [], []
    for text, a, b in rec:
        cs = _chars(text)
        for j, c in enumerate(cs):
            R.append(c)
            Rt.append(a + (b - a) * j / len(cs))
    if not S or not R:
        return None
    t = [None] * len(S)
    matched = 0
    for a, b, n in difflib.SequenceMatcher(None, S, R, autojunk=False).get_matching_blocks():
        for k in range(n):
            t[a + k] = Rt[b + k]
        matched += n
    if matched < MIN_MATCH * len(S):
        return None
    # eşleşmeyen harfler: komşu eşleşmeler ve cümle sınırları arasında doğrusal
    idx = [-1] + [i for i, v in enumerate(t) if v is not None] + [len(S)]
    val = [s["t0"]] + [v for v in t if v is not None] + [s["t1"]]
    full = np.interp(np.arange(len(S)), idx, val)
    out, last = [], s["t0"]
    for st in starts:
        last = min(max(float(full[st]), last), s["t1"])  # sıralı ve cümle içinde
        out.append(round(last, 3))
    return out


def align_words(audio, sr, sents):
    rec = transcribe(audio, sr)
    out = []
    for s in sents:
        mine = [w for w in rec if s["t0"] - SLACK <= (w[1] + w[2]) / 2 <= s["t1"] + SLACK]
        out.append(_align_sentence(mine, s))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16)
    texts = sys.argv[2:]
    dur = len(a) / 16000
    sents = [{"t0": dur * i / len(texts), "t1": dur * (i + 1) / len(texts), "text": t} for i, t in enumerate(texts)]
    for s, w in zip(sents, align_words(a, 16000, sents)):
        print(s["text"], "->", w)
