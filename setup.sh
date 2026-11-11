#!/usr/bin/env bash
# Bağımlılıkları kurar. Depo kökünden çalıştır:  bash setup.sh
# Tekrar çalıştırmak güvenlidir (kurulu olanları atlar).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install -q --root-user-action=ignore numpy requests

# Çevrimdışı Piper sesi: "tts": "piper" ise ana ses, "google" ise anahtar yokken yedek ses.
python3 -m pip install -q --root-user-action=ignore piper-tts
VOICE=tr_TR-dfki-medium
BASE=https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium
mkdir -p voices
for f in "$VOICE.onnx" "$VOICE.onnx.json"; do
  if [ ! -s "voices/$f" ]; then
    curl -fsSL --retry 4 --retry-delay 3 -o "voices/$f.part" "$BASE/$f" && mv "voices/$f.part" "voices/$f"
  fi
done

# Remotion ve yazı tipleri (zaten kuruluysa atla)
if [ ! -d video/node_modules/remotion ]; then
  (cd video && npm ci --silent --no-audit --no-fund)
fi
echo "[ok] kurulum tamam"
