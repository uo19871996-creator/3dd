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


def levels_db(src):
    """(gürültü tabanı, konuşma seviyesi) dBFS: en sessiz %5'lik ve en gür yarının medyanı (50 ms)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "24000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    win = 1200
    db = np.array([20 * np.log10(np.sqrt(np.mean(a[i:i + win] ** 2)) + 1e-9) for i in range(0, len(a) - win, win)])
    if not len(db):
        return -60.0, -20.0
    return float(np.percentile(db, 5)), float(np.median(db[db >= np.percentile(db, 50)]))


def clean(src, dst):
    """Kaydı temizler: mono 24 kHz, uğultu filtresi, baş/son sessizlik kırpma, ses düzeyi.

    Model sesin rengini ve tonunu en çok kaydın ilk 10 saniyesinden alır; baştaki sessizlik ya da
    kayda basarken oluşan gürültü mutlaka kırpılmalı. Eşik hem gürültünün 8 dB üstünde hem de
    konuşmanın 14 dB altında olacak şekilde kaydın kendisine göre seçilir."""
    nf, sp = levels_db(src)
    thr = min(-25.0, max(-45.0, nf + 8, sp - 14))
    trim = f"silenceremove=start_periods=1:start_threshold={thr:.0f}dB:start_silence=0.1"
    af = f"highpass=f=80,{trim},areverse,{trim},areverse,loudnorm=I=-18:TP=-2"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "24000",
                    "-af", af, "-t", "30", str(dst)], check=True)
    return nf


def encrypt(src):
    """Kaydı temizleyip (clean) şifreler."""
    _need_key()
    ENC.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "ses.wav"
        nf = clean(src, wav)
        subprocess.run(OPENSSL + ["-salt", "-in", str(wav), "-out", str(ENC)], check=True)
    print(f"[ok] şifreli ses örneği: {ENC.relative_to(ROOT)} (gürültü tabanı {nf:.0f} dB)")


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
