#!/usr/bin/env python3
"""Chatterbox Multilingual (MIT lisanslı) Türkçe seslendirme işçisi.

build.py tarafından ayrı sanal ortamın (.venv-tts) Python'u ile başlatılır; modeli bir kez yükler,
sonra stdin'den satır satır JSON alır:  {"text": "...", "out": "/yol/dosya.wav"}
Her istek için WAV (24 kHz, 16 bit, mono) yazar ve stdout'a {"ok": true} ya da {"ok": false, "error": ...} döner.
İlk satırda {"ready": true, "sr": 24000} gönderir.

Ortam değişkenleri:
  CBX_VOICE_SAMPLE  isteğe bağlı referans ses dosyası (konuşmacının sesi; yalnızca hakkı olan bir kayıt)
"""
import json
import os
import sys
import wave

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # büyük dosyalar izinli HTTP CDN üzerinden insin

import numpy as np  # noqa: E402
import torch  # noqa: E402
from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: E402


def main():
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    sample = os.environ.get("CBX_VOICE_SAMPLE") or None
    if sample and not os.path.exists(sample):
        sample = None
    print(json.dumps({"ready": True, "sr": model.sr}), flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            kw = {"language_id": "tr"}
            if sample:
                kw["audio_prompt_path"] = sample
            wav = model.generate(req["text"], **kw)
            a = wav.squeeze().detach().cpu().numpy()
            a = np.clip(a, -1.0, 1.0)
            pcm = (a * 32767).astype(np.int16)
            with wave.open(req["out"], "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(model.sr)
                w.writeframes(pcm.tobytes())
            print(json.dumps({"ok": True}), flush=True)
        except Exception as e:  # tek cümle hatası tüm işi düşürmesin
            print(json.dumps({"ok": False, "error": str(e)[:300]}), flush=True)


if __name__ == "__main__":
    main()
