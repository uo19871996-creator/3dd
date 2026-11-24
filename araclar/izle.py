#!/usr/bin/env python3
"""Bir videoyu "izler": sahne kesmeleri, anahtar kareler (temas sayfası), ekrandaki yazılar (OCR),
konuşma dökümü ve tempo. Claude karelere Read ile bakar, raporu okur.

Kullanım:  python3 araclar/izle.py VIDEO_DOSYASI_YA_DA_URL [--out KLASÖR] [--max-kare 24] [--dil tur+eng]

- URL verilirse yt-dlp ile indirilir (Instagram çoğu zaman girişsiz indirmeye izin vermez; o zaman
  videoyu dosya olarak gönder). Dosya her yerden olabilir: sohbete yüklenen mp4/mov/webm.
- Çıktı (--out, varsayılan out/izle/AD): rapor.md, kareler/ (720p), temas-1.png ... (12'şer kare,
  zaman damgalı), dokum.txt
Gerekenler: ffmpeg, faster-whisper ("small"), tesseract (+ tur dili; yoksa OCR atlanır).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "belgesel" / "fonts" / "label.ttf"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", str(path)])
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0
    return float(d.get("format", {}).get("duration", 0)), v.get("width"), v.get("height"), fps, has_audio


def download(url, out):
    out.mkdir(parents=True, exist_ok=True)
    r = run(["yt-dlp", "-q", "--no-warnings", "-f", "mp4/best", "-o", str(out / "video.%(ext)s"), url], timeout=600)
    files = sorted(out.glob("video.*"))
    if r.returncode != 0 or not files:
        msg = (r.stderr or "").strip().splitlines()[-1:] or ["bilinmeyen hata"]
        sys.exit(f"İndirilemedi: {msg[0][:300]}\nInstagram/TikTok çoğu zaman girişsiz indirmeye izin vermez: videoyu "
                 "telefondan kaydedip dosya olarak gönder, bu araç dosyayla aynı analizi yapar.")
    return files[0]


def cuts_from(frames, fps, thr=28.0):
    """Ardışık kareler arası ortalama mutlak fark eşikten büyükse kesme (sn)."""
    if len(frames) < 2:
        return []
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    out, last = [], -1.0
    for i, d in enumerate(diff):
        t = (i + 1) / fps
        if d > thr and t - last > 0.4:
            out.append(round(t, 2))
            last = t
    return out


def grab(path, t, dst, w=720):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1", "-vf", f"scale={w}:-2",
         str(dst)])
    return dst.exists()


def ocr(img, lang):
    if not shutil.which("tesseract"):
        return ""
    r = run(["tesseract", str(img), "-", "-l", lang, "--psm", "11"], timeout=60)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in r.stdout.splitlines()]
    return " / ".join(ln for ln in lines if len(re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", ln)) >= 3)


def contact_sheets(frames, out, per=12, cols=4, tw=360):
    sheets = []
    font = ImageFont.truetype(str(FONT), 22) if FONT.exists() else ImageFont.load_default()
    for k in range(0, len(frames), per):
        chunk = frames[k:k + per]
        thumbs = []
        for t, p in chunk:
            im = Image.open(p).convert("RGB")
            im.thumbnail((tw, tw * 2))
            d = ImageDraw.Draw(im)
            label = f"{int(t) // 60:02d}:{t % 60:04.1f}"
            d.rectangle([0, 0, 110, 32], fill=(0, 0, 0))
            d.text((6, 4), label, font=font, fill=(255, 220, 60))
            thumbs.append(im)
        th = max(i.height for i in thumbs)
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), (16, 16, 20))
        for i, im in enumerate(thumbs):
            sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
        p = out / f"temas-{k // per + 1}.png"
        sheet.save(p, optimize=True)
        sheets.append(p)
    return sheets


def transcribe(path, has_audio):
    if not has_audio:
        return [], None
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return [], "faster-whisper yok"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, info = model.transcribe(audio, beam_size=5, vad_filter=True)
    out = [(s.start, s.end, s.text.strip()) for s in segs]
    return out, f"{info.language} (p={info.language_probability:.2f})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kaynak")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-kare", type=int, default=24)
    ap.add_argument("--dil", default="tur+eng")
    a = ap.parse_args()
    src = a.kaynak
    name = re.sub(r"[^\w-]+", "-", Path(src.split("?")[0].rstrip("/")).name or "video")[:40]
    out = Path(a.out or ROOT / "out" / "izle" / name)
    (out / "kareler").mkdir(parents=True, exist_ok=True)
    path = download(src, out) if re.match(r"https?://", src) else Path(src)
    if not path.exists():
        sys.exit(f"Dosya yok: {path}")
    dur, w, h, fps, has_audio = probe(path)

    # kesmeler: küçük gri karelerden (bytes olarak oku)
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "fps=4,scale=160:284,format=gray", "-f",
                        "rawvideo", "-"], capture_output=True)
    arr = np.frombuffer(p.stdout, np.uint8)
    n = arr.size // (160 * 284)
    frames = arr[: n * 160 * 284].reshape(n, 284, 160).astype(np.float32)
    cuts = cuts_from(frames, 4.0)
    shots = [0.0] + cuts
    # anahtar kareler: her çekimin ortası; çok fazlaysa eşit seç, çok azsa aradan doldur
    mids = [(s + e) / 2 for s, e in zip(shots, shots[1:] + [dur])]
    if len(mids) > a.max_kare:
        idx = np.linspace(0, len(mids) - 1, a.max_kare).round().astype(int)
        mids = [mids[i] for i in sorted(set(idx))]
    while len(mids) < min(a.max_kare, max(6, int(dur / 3))):
        gaps = sorted(zip([0.0] + mids, mids + [dur]), key=lambda g: g[0] - g[1])
        g = gaps[0]
        mids = sorted(mids + [(g[0] + g[1]) / 2])
    keys = []
    for i, t in enumerate(mids):
        dst = out / "kareler" / f"k{i + 1:02d}_{t:06.2f}.png"
        if grab(path, min(t, max(0.0, dur - 0.05)), dst):
            keys.append((t, dst))
    sheets = contact_sheets(keys, out)
    texts = [(t, ocr(p_, a.dil)) for t, p_ in keys]
    segs, lang = transcribe(path, has_audio)

    lines = [f"# İzleme raporu: {Path(src).name if not src.startswith('http') else src}", "",
             f"- Süre {dur:.1f} sn · {w}x{h} · {fps:.0f} fps · ses {'var' if has_audio else 'yok'}"
             + (f" · konuşma dili {lang}" if lang else ""),
             f"- Kesme sayısı {len(cuts)} · ortalama çekim süresi {dur / max(1, len(cuts) + 1):.1f} sn"
             + (" (çok hızlı kurgu)" if dur / max(1, len(cuts) + 1) < 1.5 else ""),
             f"- Kesmeler (sn): {', '.join(f'{c:.1f}' for c in cuts[:60])}{' ...' if len(cuts) > 60 else ''}",
             "- Temas sayfaları (Read ile bak): " + ", ".join(str(s) for s in sheets), "",
             "## Ekrandaki yazılar (OCR, kare zamanına göre)", ""]
    seen = set()
    for t, txt in texts:
        if txt and txt not in seen:
            seen.add(txt)
            lines.append(f"- {int(t) // 60:02d}:{t % 60:04.1f}  {txt[:220]}")
    if not seen:
        lines.append("- (okunabilir yazı yok ya da tesseract kurulu değil)")
    lines += ["", "## Konuşma dökümü", ""]
    lines += [f"- [{s // 60:02.0f}:{s % 60:04.1f}-{e // 60:02.0f}:{e % 60:04.1f}] {txt}" for s, e, txt in segs] or \
             ["- (konuşma yok ya da yalnızca müzik)"]
    (out / "dokum.txt").write_text("\n".join(f"{s:.1f}-{e:.1f} {txt}" for s, e, txt in segs), encoding="utf-8")
    (out / "rapor.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n(dosyalar: {out})")


if __name__ == "__main__":
    main()
