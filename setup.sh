#!/usr/bin/env bash
# Bağımlılıkları kurar. Depo kökünden çalıştır:  bash setup.sh
# Tekrar çalıştırmak güvenlidir (kurulu olanları atlar).
set -euo pipefail
cd "$(dirname "$0")"

pip install -q --root-user-action=ignore numpy requests

# Çevrimdışı Piper sesi yalnızca config.json içinde "tts": "piper" ise gerekir.
TTS=$(python3 -c "import json; print(json.load(open('config.json')).get('tts', 'google'))")
if [ "$TTS" = "piper" ]; then
  pip install -q --root-user-action=ignore piper-tts
  VOICE=tr_TR-dfki-medium
  BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium
  mkdir -p voices
  for f in "$VOICE.onnx" "$VOICE.onnx.json"; do
    if [ ! -s "voices/$f" ]; then
      curl -fsSL --retry 4 --retry-delay 3 -o "voices/$f" "$BASE/$f"
    fi
  done
fi

# Remotion ve yazı tipleri (zaten kuruluysa atla)
if [ ! -d video/node_modules/remotion ]; then
  (cd video && npm ci --silent --no-audit --no-fund)
fi
echo "[ok] kurulum tamam"
