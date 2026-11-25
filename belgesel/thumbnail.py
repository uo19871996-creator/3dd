#!/usr/bin/env python3
"""Belgesel küçük resmi (1280x720 PNG): filmden bir kare + kocaman 2-4 kelimelik yazı.

Kullanım:  python3 belgesel/thumbnail.py --project PROJE --t 12.5 --text "DÜNYAYI KİLİTLEDİ" \
               [--small "WANNACRY · 2017"] [--out out/thumbnail.png]

Kare render.py ile 1920x1080 alınır, karartılıp sol yarısına Oswald Bold yazı basılır; vurgu
kelimesi (--accent-word) sarı şeritle öne çıkar. Telefonda tek bakışta okunacak büyüklükte.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = Path(__file__).resolve().parent
YELLOW, RED, WHITE = (250, 204, 21), (214, 38, 38), (250, 248, 244)


def tr_upper(t):
    return t.replace("i", "İ").replace("ı", "I").upper()


def wrap(draw, words, font, width):
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and draw.textlength(trial, font=font) > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--t", type=float, required=True, help="filmden alınacak kare (sn)")
    ap.add_argument("--text", required=True, help="2-4 kelime, BÜYÜK harf")
    ap.add_argument("--small", default="", help="üstte küçük satır (ör. WANNACRY · 2017)")
    ap.add_argument("--accent-word", default="", help="sarı şeritle vurgulanacak kelime")
    ap.add_argument("--out", default="out/thumbnail.png")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    r = subprocess.run([sys.executable, str(HERE / "engine" / "render.py"), "--project", str(proj),
                        "--probe", f"{a.t}", "--size", "1920x1080"], capture_output=True, text=True)
    stills = sorted((proj / "out" / "probe").glob(f"t{a.t:07.2f}*.png"))
    if r.returncode != 0 or not stills:
        sys.exit(f"Kare alınamadı: {r.stderr[-400:]}")
    img = Image.open(stills[-1]).convert("RGB").resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.55)
    shade = Image.new("L", (1280, 720))
    for x in range(1280):  # soldan sağa koyulaşan perde: yazı tarafı daha karanlık
        shade.paste(int(200 * max(0.0, 1 - x / 900)), (x, 0, x + 1, 720))
    img.paste(Image.new("RGB", (1280, 720), (5, 7, 14)), (0, 0), shade)
    d = ImageDraw.Draw(img)
    fonts = HERE / "fonts"
    big = ImageFont.truetype(str(fonts / "cond.ttf"), 150)
    lines = wrap(d, tr_upper(a.text).split(), big, 760)
    while len(lines) > 3 and big.size > 90:
        big = ImageFont.truetype(str(fonts / "cond.ttf"), big.size - 10)
        lines = wrap(d, tr_upper(a.text).split(), big, 760)
    y = 360 - len(lines) * big.size * 0.55
    if a.small:
        sf = ImageFont.truetype(str(fonts / "label.ttf"), 40)
        d.rectangle([60, y - 78, 60 + d.textlength(a.small, font=sf) + 36, y - 22], fill=RED)
        d.text((78, y - 74), a.small, font=sf, fill=WHITE)
    for ln in lines:
        x = 60
        for w in ln.split():
            tw = d.textlength(w, font=big)
            if a.accent_word and w.strip(".,!?") == tr_upper(a.accent_word):
                l, t, r, b = d.textbbox((x, y), w, font=big)   # Ç/Ş çengeli ve İ/Ö noktaları şeridin içinde kalsın
                d.rectangle([l - 12, min(t, y + big.size * 0.18) - 8, r + 12, max(b, y + big.size * 1.08) + 8], fill=YELLOW)
                d.text((x, y), w, font=big, fill=(10, 10, 14))
            else:
                d.text((x + 4, y + 5), w, font=big, fill=(0, 0, 0))
                d.text((x, y), w, font=big, fill=WHITE)
            x += tw + d.textlength(" ", font=big)
        y += big.size * 1.05
    out = proj / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    print(f"[ok] {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
