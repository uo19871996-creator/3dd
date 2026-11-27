#!/usr/bin/env python3
"""İzlenme öğrenme raporu: kanalın kendi verisinden "ne izleniyor, ne izlenmiyor" çıkarır.

Her çalışma konu seçmeden önce bunu çalıştırır; böylece konu türü, başlık ve süre kararları sabit
kurallardan değil kanalın güncel verisinden gelir (kanal sahibinin isteği: amaç üretmek değil,
izletmek).

Kullanım:
  python3 pipeline/ogren.py               # son 21 gün; yazar: out/ogrenim.md (ve ekrana basar)
  python3 pipeline/ogren.py --gun 14

Rapor:
  1. Haber türleri: medyan izlenme, 1.000 izlenmede beğeni ve yorum (turler.json kalıplarıyla)
  2. Viral türleri: aynı ölçüler
  3. Başlık kalıpları: soru, hizmet kalıbı ("ne zaman", "nasıl", "kimler"), rakam; kalıbı olan ve
     olmayanların medyan farkı
  4. Süre: kısa (<45 sn) ve uzun videoların medyanı (haber ve viral ayrı)
  5. İzlenme oranı (YouTube Analytics API açıksa): videoların ortalama izlenme yüzdesi; türlere göre
  6. Son 7 günün en iyi ve en zayıf 5 videosu
Yalnızca en az 24 saatlik videolar sayılır (yeni videolar henüz izlenme topluyor).
"""
import json
import re
import statistics as st
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats import fetch  # noqa: E402
from upload import access_token  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TURLER = json.loads((Path(__file__).resolve().parent / "turler.json").read_text(encoding="utf-8"))
HIZMET = r"ne zaman|nasıl|hangi kanal|kimler|şartlar|nerede|ne kadar|kaç (TL|lira|gün)|İşte|sonuç"


def tur(v):
    for name, pat in TURLER.get(v["kind"], []):
        if re.search(pat, v["title"]):
            return name
    return "Diğer"


def med(xs):
    return st.median(xs) if xs else 0


def table(rows, title):
    out = [f"\n## {title}\n", "| Tür | Video | Medyan izlenme | Beğeni/1k | Yorum/1k | İzlenme oranı | En iyi |",
           "|---|---|---|---|---|---|---|"]
    for name, vs in sorted(rows.items(), key=lambda kv: -med([v["views"] for v in kv[1]])):
        views = sum(v["views"] for v in vs) or 1
        ret = [v["oran"] for v in vs if v.get("oran") is not None]
        best = max(vs, key=lambda v: v["views"])
        out.append(f"| {name} | {len(vs)} | {med([v['views'] for v in vs]):.0f} | "
                   f"{sum(v['likes'] for v in vs) / views * 1000:.1f} | {sum(v['comments'] for v in vs) / views * 1000:.2f} | "
                   f"{'%' + format(med(ret), '.0f') if ret else '-'} | {best['title'][:50]} ({best['views']}) |")
    return out


def retention(token, ids, start):
    """YouTube Analytics: video başına ortalama izlenme yüzdesi. API kapalıysa None."""
    try:
        r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports",
                         headers={"Authorization": f"Bearer {token}"}, timeout=60,
                         params={"ids": "channel==MINE", "startDate": start,
                                 "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                 "metrics": "views,averageViewPercentage,averageViewDuration",
                                 "dimensions": "video", "filters": "video==" + ",".join(ids[:200]),
                                 "maxResults": 200, "sort": "-views"})
    except requests.RequestException:
        return None, "bağlantı kurulamadı"
    if r.status_code != 200:
        msg = r.json().get("error", {}).get("message", r.text[:120]) if r.headers.get("content-type", "").startswith("application/json") else r.text[:120]
        return None, msg.split(".")[0]
    return {row[0]: row[2] for row in r.json().get("rows", [])}, None


def curve(token, vid, start):
    """Tek videonun izleyici tutma eğrisi {süre oranı: izleyen oranı}; Analytics kapalıysa None."""
    try:
        r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports",
                         headers={"Authorization": f"Bearer {token}"}, timeout=60,
                         params={"ids": "channel==MINE", "startDate": start,
                                 "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                 "metrics": "audienceWatchRatio", "dimensions": "elapsedVideoTimeRatio",
                                 "filters": f"video=={vid}"})
    except requests.RequestException:
        return None
    return {round(row[0], 2): row[1] for row in r.json().get("rows", [])} if r.status_code == 200 else None


def main():
    a = sys.argv[1:]
    days = int(a[a.index("--gun") + 1]) if "--gun" in a else 21
    token = access_token()
    now = datetime.now(timezone.utc)
    vids = [v for v in fetch(token) if v["kind"] in ("haber", "viral") and v["duration"] <= 180
            and v["age_h"] >= 24 and v["age_h"] <= days * 24]
    if not vids:
        print("Yeterli veri yok."); return
    for v in vids:
        v["tur"] = tur(v)
    ret, why = retention(token, [v["id"] for v in vids], (now - timedelta(days=days + 1)).strftime("%Y-%m-%d"))
    for v in vids:
        v["oran"] = ret.get(v["id"]) if ret else None
    L = [f"# İzlenme öğrenme raporu ({now.astimezone(timezone(timedelta(hours=3))).strftime('%Y-%m-%d %H:%M')}, son {days} gün, "
         f"{len(vids)} olgun video)",
         "", "Konu, başlık ve süre seçerken bu tabloyu esas al: üst sıradaki türlere öncelik ver, alttakileri yalnızca "
         "çok güçlü bir aday varsa seç. Rakamlar kanalın kendi verisidir; az videolu (n<4) satırlar kesin değildir."]
    for kind, title in (("haber", "Haber türleri"), ("viral", "Viral türleri")):
        rows = {}
        for v in vids:
            if v["kind"] == kind:
                rows.setdefault(v["tur"], []).append(v)
        if rows:
            L += table(rows, title)
    L.append("\n## Başlık kalıpları (haber + viral)\n")
    for name, f in (("Soru işaretli başlık", lambda v: "?" in v["title"]),
                    ("Hizmet kalıbı (ne zaman, nasıl, kimler, hangi kanalda...)", lambda v: re.search(HIZMET, v["title"], re.I)),
                    ("Başlıkta rakam", lambda v: re.search(r"\d", v["title"]))):
        for kind in ("haber", "viral"):
            yes = [v["views"] for v in vids if v["kind"] == kind and f(v)]
            no = [v["views"] for v in vids if v["kind"] == kind and not f(v)]
            if len(yes) >= 3 and len(no) >= 3:
                L.append(f"- {name} ({kind}): var {med(yes):.0f} (n={len(yes)}) / yok {med(no):.0f} (n={len(no)})")
    L.append("\n## Süre\n")
    for kind in ("haber", "viral"):
        for lo, hi, lab in ((0, 45, "45 sn altı"), (45, 999, "45 sn ve üstü")):
            xs = [v["views"] for v in vids if v["kind"] == kind and lo <= v["duration"] < hi]
            if xs:
                L.append(f"- {kind}, {lab}: medyan {med(xs):.0f} (n={len(xs)})")
    L.append("\n## İzlenme oranı\n")
    if ret:
        withr = [v for v in vids if v["oran"] is not None]
        L.append(f"- Ortalama izlenme yüzdesi medyanı: %{med([v['oran'] for v in withr]):.0f} (n={len(withr)}). "
                 "Shorts'ta %70 altı zayıf, %90 üstü güçlü sayılır; düşük oranlı türlerde açılışı ve uzunluğu değiştir.")
        for v in sorted(withr, key=lambda v: -v["oran"])[:3]:
            L.append(f"  - en iyi: %{v['oran']:.0f} · {v['title'][:60]}")
        for v in sorted(withr, key=lambda v: v["oran"])[:3]:
            L.append(f"  - en zayıf: %{v['oran']:.0f} · {v['title'][:60]}")
        start = (now - timedelta(days=days + 1)).strftime("%Y-%m-%d")
        L.append("\n**Tutma eğrisi** (son videolar; saniyede hâlâ izleyenlerin oranı; %100 üstü = tekrar izleme):")
        for kind in ("haber", "viral"):
            sel = sorted([v for v in withr if v["kind"] == kind], key=lambda v: v["published"])[-12:]
            cs = [c for c in (curve(token, v["id"], start) for v in sel) if c]
            if not cs:
                continue
            d = med([v["duration"] for v in sel])
            pts = (0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.7, 0.9)
            row = []
            for p in pts:
                xs = [c[p] for c in cs if p in c]
                if xs:
                    row.append(f"{p * d:.0f}. sn %{med(xs) * 100:.0f}")
            L.append(f"- {kind} (n={len(cs)}, medyan {d:.0f} sn): " + " · ".join(row))
        L.append("  En büyük düşüş hangi saniyedeyse o andaki sahneyi (genelde açılıştan 2. sahneye geçiş) güçlendir.")
    else:
        L.append(f"- YouTube Analytics verisi alınamadı ({why}). Kanal sahibi Google Cloud'da \"YouTube Analytics API\"yi "
                 "açınca izlenme oranı da burada görünür.")
    week = [v for v in vids if v["age_h"] <= 7 * 24]
    if week:
        L.append("\n## Son 7 gün: en iyi ve en zayıf 5\n")
        for v in sorted(week, key=lambda v: -v["views"])[:5]:
            L.append(f"- ↑ {v['views']} · {v['kind']} · {v['tur']} · {v['title'][:70]}")
        for v in sorted(week, key=lambda v: v["views"])[:5]:
            L.append(f"- ↓ {v['views']} · {v['kind']} · {v['tur']} · {v['title'][:70]}")
    text = "\n".join(L) + "\n"
    out = ROOT / "out" / "ogrenim.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
