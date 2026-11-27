#!/usr/bin/env python3
"""Belgeselden dikey tanıtım Shorts'u (fragman): filmin en çarpıcı 30-50 saniyesi + "TAMAMI KANALDA" kartı.

Kullanım (proje klasöründe, film ve miks hazırken):
  python3 ../../tanitim.py --project . --lines 1-4 --hook "ÇOCUKLARI TETİKÇİ YAPAN TUZAK" \
      --series "YENİ NESİL SUÇ · BÖLÜM 2"

Okur:   out/film.mp4 (altyazısız render), audio/mix.m4a, audio/timing.json
Yazar:  out/tanitim.mp4 (1080x1920, 30 fps)

Düzen: arka planda filmin bulanık ve koyulaştırılmış hâli; ortada film (16:9); üstte seri etiketi ve
2-5 kelimelik kanca; altta kelime kelime vurgulanan büyük altyazı (Shorts arayüzünün kapattığı alt
kısmın üstünde); sonda 3 saniyelik "TAMAMI KANALDA" kartı. Satırlar (`--lines A-B`, script.json
id'leri) cümle sınırında başlar ve biter: yarım cümle kalmaz.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia

ENGINE = Path(__file__).resolve().parent / "engine"
sys.path.insert(0, str(ENGINE))
from engine import Res, draw_text, ease_out_cubic, paint, ramp, text_width  # noqa: E402
from captions import words_with_times  # noqa: E402

W, H, FPS = 1080, 1920, 30
VID_Y = 660                 # filmin üst kenarı (1080 genişlikte 608 px yükseklik)
CAP_Y = 1400                # altyazı ilk satırının taban çizgisi
END = 3.0                   # kapanış kartı (sn)
WHITE, YELLOW, RED = (245, 245, 245), (255, 205, 0), (200, 30, 40)


def chunks(segs, t0, t1, max_words=4, max_chars=24):
    """Altyazı parçaları [(kelimeler [(w, t)], başlangıç, bitiş)], zaman t0'a göre."""
    out = []
    for s in segs:
        cur = []
        for w, t in words_with_times(s):
            cur.append((w, t - t0))
            if len(cur) >= max_words or len(" ".join(x for x, _ in cur)) >= max_chars or re.search(r"[.,!?;:…]$", w):
                out.append(cur); cur = []
        if cur:
            out.append(cur)
    res = []
    for i, c in enumerate(out):
        end = out[i + 1][0][1] if i + 1 < len(out) else (t1 - t0)
        res.append((c, c[0][1], end))
    return res


def wrap(res, words, size, font, maxw):
    lines, cur = [], []
    for k, (w, _) in enumerate(words):
        if cur and text_width(res, " ".join(words[j][0] for j in cur + [k]), size, font) > maxw:
            lines.append(cur); cur = []
        cur.append(k)
    return lines + ([cur] if cur else [])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--lines", required=True, help="script.json satır id aralığı, ör. 1-4")
    ap.add_argument("--hook", required=True, help="üstteki 2-5 kelimelik kanca (büyük harfe çevrilir)")
    ap.add_argument("--series", default="", help="üstteki küçük kırmızı etiket, ör. 'YENİ NESİL SUÇ · BÖLÜM 2'")
    ap.add_argument("--end-text", default="TAMAMI KANALDA", help="kapanış kartının büyük yazısı")
    ap.add_argument("--video", default="out/film.mp4")
    ap.add_argument("--audio", default="audio/mix.m4a")
    ap.add_argument("--out", default="out/tanitim.mp4")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
    from build import tr_upper  # Türkçe büyük harf (i → İ)

    timing = json.loads((proj / "audio" / "timing.json").read_text(encoding="utf-8"))
    lo, hi = (int(x) for x in a.lines.split("-"))
    segs = [s for s in timing["segments"] if lo <= s["id"] <= hi]
    if not segs:
        sys.exit(f"--lines {a.lines}: timing.json'da bu id'lerde satır yok")
    t0 = max(0.0, segs[0]["start"] - 0.15)
    t1 = segs[-1]["end"] + 0.45
    clip = t1 - t0
    total = clip + END
    if not 20 <= clip <= 55:
        print(f"[uyarı] seçilen bölüm {clip:.1f} sn; tanıtım için 30-50 sn önerilir", flush=True)
    caps = chunks(segs, t0, t1)
    res = Res(1.0, None, proj / "fonts" if (proj / "fonts").exists() else Path(__file__).parent / "fonts")

    # Üst blok (sabit): seri etiketi + kanca
    hook = tr_upper(a.hook)
    hsize = 118
    hwords = [(w, 0) for w in hook.split()]
    hl = wrap(res, hwords, hsize, "cond", 960)
    while len(hl) > 2 and hsize > 80:
        hsize -= 8; hl = wrap(res, hwords, hsize, "cond", 960)

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{clip:.3f}", "-i", str(proj / a.video),
         "-filter_complex",
         f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration={END},split[a][b];"
         f"[a]scale=-2:{H},crop={W}:{H},gblur=sigma=38,eq=brightness=-0.22:saturation=0.8[bg];"
         f"[b]scale={W}:-2[fg];[bg][fg]overlay=0:{VID_Y},format=rgba[v]",
         "-map", "[v]", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
    out = proj / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-ss", f"{t0:.3f}", "-t", f"{clip:.3f}", "-i", str(proj / a.audio),
         "-filter_complex", f"[1:a]afade=t=in:d=0.15,afade=t=out:st={clip - 0.7:.3f}:d=0.7,apad=pad_dur={END}[au]",
         "-map", "0:v", "-map", "[au]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)

    n = 0
    fsize = W * H * 4
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        arr = np.frombuffer(buf, np.uint8).reshape(H, W, 4).copy()
        t = n / FPS
        surf = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        c = surf.getCanvas()
        # üst blok
        y = 250
        if a.series:
            ss = 40
            sw = text_width(res, a.series, ss, "label", 0.06)
            c.drawRect(skia.Rect.MakeXYWH(60, y - ss - 14, sw + 36, ss + 30), paint(RED))
            draw_text(c, res, a.series, 78, y, ss, "label", WHITE, 1.0, 0.06)
            y += 40
        for ln in hl:
            y += hsize * 1.08
            txt = " ".join(hwords[k][0] for k in ln)
            draw_text(c, res, txt, 64, y + 5, hsize, "cond", (0, 0, 0), 0.7)
            draw_text(c, res, txt, 60, y, hsize, "cond", WHITE)
        # altyazı: parça parça, o an söylenen kelime sarı
        if t < clip:
            for words, a0, a1 in caps:
                if a0 - 0.05 <= t < a1:
                    al = ramp(t, a0 - 0.05, 0.12)
                    size = 74
                    lines = wrap(res, words, size, "label", 940)
                    now = max((k for k, (_, wt) in enumerate(words) if wt <= t + 0.02), default=-1)
                    for li, ln in enumerate(lines):
                        txt = " ".join(words[k][0] for k in ln)
                        x = (W - text_width(res, txt, size, "label")) / 2
                        yy = CAP_Y + li * size * 1.25
                        for k in ln:
                            w = words[k][0]
                            draw_text(c, res, w, x + 4, yy + 5, size, "label", (0, 0, 0), 0.75 * al)
                            draw_text(c, res, w, x, yy, size, "label", YELLOW if k == now else WHITE, al)
                            x += text_width(res, w + " ", size, "label")
                    break
        else:   # kapanış kartı
            u = ease_out_cubic(ramp(t, clip, 0.35))
            c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint((8, 8, 12), 0.82 * u))
            es = 132
            ew = text_width(res, tr_upper(a.end_text), es, "cond")
            draw_text(c, res, tr_upper(a.end_text), (W - ew) / 2, 900 + (1 - u) * 60, es, "cond", YELLOW, u)
            if a.series:
                ss = 54
                sw = text_width(res, a.series, ss, "label", 0.05)
                draw_text(c, res, a.series, (W - sw) / 2, 1010, ss, "label", WHITE, u, 0.05)
            sub = "Belgeselin tamamı kanalımızda"
            sw = text_width(res, sub, 44, "labelm")
            draw_text(c, res, sub, (W - sw) / 2, 1100, 44, "labelm", (210, 210, 215), u)
        enc.stdin.write(arr.tobytes())
        n += 1
    enc.stdin.close()
    if enc.wait() or dec.wait():
        sys.exit("[hata] ffmpeg tanıtımı oluşturamadı")
    print(f"[ok] {out}  ({n / FPS:.1f} sn: film {t0:.1f}-{t1:.1f} sn + {END:.0f} sn kapanış)")


if __name__ == "__main__":
    main()
