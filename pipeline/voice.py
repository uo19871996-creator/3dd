#!/usr/bin/env python3
"""Kanal sahibinin ses örneğini şifreli saklar ve üretim sırasında çözer.

Depo herkese açık olduğu için ses örneği yalnızca şifreli halde (assets/ses-ornegi.wav.enc) tutulur.
Anahtar, ortamda zaten kayıtlı olan YT_REFRESH_TOKEN değişkeninden türetilir (OpenSSL, AES-256, PBKDF2);
ek bir gizli bilgi gerekmez. Refresh token değişirse örnek yeniden şifrelenmelidir (aşağıdaki komut).

Kullanım:
  YT_REFRESH_TOKEN=... python3 pipeline/voice.py encrypt <kayıt.m4a|mp3|wav>
  YT_REFRESH_TOKEN=... python3 pipeline/voice.py check
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENC = ROOT / "assets" / "ses-ornegi.wav.enc"
OPENSSL = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-pass", "env:YT_REFRESH_TOKEN"]


def _need_key():
    if not os.environ.get("YT_REFRESH_TOKEN"):
        raise RuntimeError("YT_REFRESH_TOKEN tanımlı değil; ses örneği çözülemez")


def encrypt(src):
    """Kaydı temizleyip (mono, 24 kHz, baş/son sessizlik kırpılmış, ses düzeyi dengelenmiş) şifreler."""
    _need_key()
    ENC.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "ses.wav"
        af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,"
              "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,areverse,"
              "highpass=f=70,loudnorm=I=-18:TP=-2")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "24000",
                        "-af", af, "-t", "30", str(wav)], check=True)
        subprocess.run(OPENSSL + ["-salt", "-in", str(wav), "-out", str(ENC)], check=True)
    print(f"[ok] şifreli ses örneği: {ENC.relative_to(ROOT)}")


def decrypt_to(dest):
    """Şifreli örneği dest yoluna çözer; örnek yoksa None döner."""
    if not ENC.exists():
        return None
    _need_key()
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(OPENSSL + ["-d", "-in", str(ENC), "-out", str(dest)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ses örneği çözülemedi (refresh token değişmiş olabilir)")
    return dest


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "encrypt":
        encrypt(sys.argv[2])
    elif len(sys.argv) >= 2 and sys.argv[1] == "check":
        with tempfile.TemporaryDirectory() as td:
            p = decrypt_to(Path(td) / "kontrol.wav")
            if p is None:
                print("[bilgi] ses örneği yok")
                return
            dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
            print(f"[ok] ses örneği çözüldü: {float(dur):.1f} sn")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
