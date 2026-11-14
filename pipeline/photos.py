#!/usr/bin/env python3
"""Wikimedia Commons'tan serbest lisanslı fotoğraf bulur ve indirir.

Yalnızca CC0 / CC BY / CC BY-SA / kamu malı lisanslı fotoğraflar kullanılır; fotoğrafçı ve lisans
bilgisi ekranda ve YouTube açıklamasında belirtilir (lisansların istediği atıf).

Kullanım (senaryo yazarken aday görmek için):
  python3 pipeline/photos.py search "Tim Cook"
  python3 pipeline/photos.py search "Kapalıçarşı"

Wikimedia kuralları: kendini tanıtan User-Agent, düşük istek hızı, 429'da Retry-After'a uyma,
orijinal dosya yerine standart boyutlu küçük görsel (thumb.wikimedia.org).
"""
import html
import re
import sys
import time
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "GundemShortsBot/1.0 (https://github.com/uo19871996-creator/3dd) python-requests/2"}
OK_LICENSE = re.compile(r"^(CC0|CC BY(-SA)? [0-9.]+|Public domain|PD|No restrictions)", re.I)
GRADE = "eq=contrast=1.05:saturation=0.92:gamma=0.98,colorchannelmixer=rr=1.01:bb=0.98"
_last = [0.0]


def _get(url, params=None, timeout=60, max_wait=90):
    """Wikimedia'ya nazik istek: aralarda bekleme, 429'da Retry-After kadar bekleyip yeniden dene."""
    for _ in range(4):
        wait = 1.6 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        r = requests.get(url, params=params, headers=UA, timeout=timeout)
        if r.status_code != 429:
            return r
        ra = r.headers.get("retry-after", "10")
        delay = int(ra) if ra.isdigit() else 10
        if delay > max_wait:
            return r
        time.sleep(delay + 1)
    return r


def _clean(s, n=70):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def search(query, limit=8, file=None):
    """Aday fotoğrafları (lisans uygun, yeterince büyük) döner."""
    params = {"action": "query", "format": "json", "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280}
    if file:
        params["titles"] = file if file.startswith("File:") else f"File:{file}"
    else:
        params.update({"generator": "search", "gsrnamespace": 6, "gsrlimit": limit,
                       "gsrsearch": f"{query} filetype:bitmap"})
    r = _get(API, params)
    if r.status_code != 200:
        raise RuntimeError(f"Commons araması başarısız ({r.status_code})")
    pages = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        if "imageinfo" not in p:
            continue
        ii = p["imageinfo"][0]
        md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName", {}) or {}).get("value", "")
        if not OK_LICENSE.match(lic or "") or ii.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
            continue
        # Standart boy küçük görsel (1280 px) üretilebilmeli; orijinal dosya istemiyoruz
        # (Wikimedia orijinallerde çok sıkı hız sınırı uyguluyor).
        if ii.get("width", 0) < 1280 or "/thumb/" not in ii.get("thumburl", ""):
            continue
        out.append({
            "title": p["title"],
            "width": ii["width"], "height": ii["height"],
            "thumb": ii["thumburl"],
            "page": ii.get("descriptionurl", ""),
            "artist": _clean((md.get("Artist", {}) or {}).get("value", ""), 60) or "Bilinmiyor",
            "license": lic,
            "license_url": (md.get("LicenseUrl", {}) or {}).get("value", ""),
        })
    return out


def fetch(spec, dest):
    """spec: {"q": "arama"} ya da {"file": "File:..."} -> indirip dest'e JPEG yazar, atıf bilgisini döner.

    Görsel işleme ffmpeg ile yapılır: bazı makinelerde sistemdeki Pillow bozuk geliyor."""
    import subprocess
    import tempfile

    cands = search(spec.get("q", ""), file=spec.get("file"))
    for c in cands[:3]:  # açık dosya adı verildiyse tek aday vardır
        r = _get(c["thumb"], timeout=120)
        if r.status_code == 200:
            break
    else:
        if not cands:
            return None
        raise RuntimeError(f"görsel indirilemedi ({r.status_code})")
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".img") as tmp:
        tmp.write(r.content)
        tmp.flush()
        # En uzun kenar en fazla 1920 px, JPEG. Farklı kaynaklardan gelen fotoğraflar aynı videoda tek
        # bir görünümde buluşsun diye hepsine aynı hafif renk ayarı (cinematic-skill'in "natural"
        # derecelendirmesi): hafif kontrast, %92 doygunluk, çok hafif sıcak denge.
        vf = "scale='if(gt(iw,ih),min(1920,iw),-2)':'if(gt(iw,ih),-2,min(1920,ih))'"
        grade = GRADE if spec.get("grade", True) else ""
        for chain in ([vf + "," + grade] if grade else []) + [vf]:  # renk ayarı olmazsa ayarsız
            ok = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-frames:v", "1", "-vf", chain,
                                 "-q:v", "3", str(dest)], capture_output=True).returncode == 0
            if ok:
                break
        else:
            raise RuntimeError("görsel dönüştürülemedi")
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height", "-of", "csv=p=0", str(dest)],
                        capture_output=True, text=True).stdout.strip()
    c["credit"] = f"Foto: {c['artist']} · {c['license']} · Wikimedia Commons"
    c["size"] = tuple(int(x) for x in wh.split(",")) if "," in wh else None
    return c


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        for c in search(" ".join(sys.argv[2:])):
            print(f"{c['title']}  [{c['width']}x{c['height']}]  {c['license']}  — {c['artist']}")
    else:
        sys.exit(__doc__)
