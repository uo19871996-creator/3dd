#!/usr/bin/env bash
# Haftalık belgesel için ek kurulum (önce depo kökünde: bash setup.sh). Tekrar çalıştırmak güvenli.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q --root-user-action=ignore skia-python pillow numpy scipy
# Sistemdeki Pillow başka bir Python sürümü için derlenmiş olabilir: açılmıyorsa bu sürüme kur
python3 -c "from PIL import _imaging" 2>/dev/null || \
  python3 -m pip install -q --root-user-action=ignore --ignore-installed --no-deps pillow
if ! python3 -c "import skia" 2>/dev/null; then  # skia-python sistemde libEGL ister
  (apt-get install -y -q libegl1 >/dev/null 2>&1 || (apt-get update -q >/dev/null 2>&1 && apt-get install -y -q libegl1 >/dev/null))
fi
python3 -c "import skia" && echo "[ok] belgesel kurulumu tamam"
