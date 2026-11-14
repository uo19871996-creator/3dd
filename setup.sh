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

# Chatterbox Multilingual sesi ("tts": "chatterbox"): ayrı sanal ortam, işlemci (CPU) sürümü PyTorch
TTS=$(python3 -c "import json; print(json.load(open('config.json')).get('tts', 'piper'))")
if [ "$TTS" = "chatterbox" ]; then
  if [ ! -x .venv-tts/bin/python ] || ! .venv-tts/bin/python -c "import chatterbox" 2>/dev/null; then
    python3 -m venv .venv-tts
    .venv-tts/bin/pip install -q --upgrade pip
    .venv-tts/bin/pip install -q torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
    .venv-tts/bin/pip install -q chatterbox-tts
  fi
  # Modeli önceden indir (büyük dosyalar izinli HTTP CDN üzerinden)
  # yalnızca çok dilli modelin kullandığı dosyalar (~3,5 GB; deponun tamamı ~13 GB)
  HF_HUB_DISABLE_XET=1 .venv-tts/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('ResembleAI/chatterbox', allow_patterns=['ve.pt', 't3_mtl23ls_v2.safetensors', 's3gen.pt', 'grapheme_mtl_merged_expanded_v1.json', 'conds.pt', 'Cangjie5_TC.json'])" >/dev/null
fi

# Altyazı kelime hizalaması (pipeline/align.py): faster-whisper ve "small" modeli (~480 MB).
# Kurulamazsa betik durmaz; altyazılar eski yöntemle (cümle içinde orantılı) zamanlanır.
ALIGN=$(python3 -c "import json; print(json.load(open('config.json')).get('word_align', True))")
if [ "$ALIGN" = "True" ]; then
  if ! python3 -m pip install -q --root-user-action=ignore faster-whisper \
     || ! HF_HUB_DISABLE_XET=1 python3 -c "from faster_whisper import download_model; download_model('small')" >/dev/null; then
    echo "[bilgi] Kelime hizalama kurulamadı; altyazılar oransal zamanlanacak (hata değil)."
  fi
fi

# Remotion ve yazı tipleri (zaten kuruluysa atla)
if [ ! -d video/node_modules/remotion ]; then
  (cd video && npm ci --silent --no-audit --no-fund)
fi
echo "[ok] kurulum tamam"
