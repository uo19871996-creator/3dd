#!/usr/bin/env python3
"""Viral / bilgilendirici video adayları: YouTube'da şu an Türkiye'de en çok izlenen ve etkileşim alan
kısa videolar. Yalnızca KONU FİKRİ içindir; bu videoların görüntüsü, sesi ya da metni kullanılmaz.

Kullanım:  python3 pipeline/viral.py > out/viral.md
           python3 pipeline/viral.py --queries 3     # daha fazla arama (her biri ~100 kota birimi)

Her çalışmada:
  1. YouTube Türkiye trend listesi (1 kota birimi)
  2. Sıradaki 2 konu aramasında son 14 günün en çok izlenen Türkçe kısa videoları (~200 birim);
     sorgular saate göre döner, gün içinde hepsi taranır
  3. Günlük izlenme, etkileşim ((beğeni + yorum) / izlenme) ve yorum oranıyla sıralı tablolar
  4. Kanalda son 3 günde yüklenen başlıklar (aynı konuyu tekrar seçmemek için)
Kota: video yüklemesi aynı kotayı kullanır; günde 5 viral çalışma ~1.000 birim harcar.
"""
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

from upload import API, IST, access_token, recent_items

# 2026-11-20 incelemesi: Türkçe bilgilendirici Shorts'ta kendi kanal medyanının en çok katlandığı türler
# (tuhaf hayvan davranışları 30-177x, vizesiz ülke/seyahat 43-155x, "neden?" günlük merak 41-84x,
# "dünyanın en ..." 45-76x). Sorgular bu türleri sırayla tarar.
QUERIES = [  # 24 Kasım: kanalda zayıf kalan "neden?" sorguları rekor/hayvan sorgularıyla değişti
    "dünyanın en tuhaf hayvanı", "vizesiz ülkeler", "dünyanın en derin", "dünyanın en küçük ülkesi",
    "ilginç bilgiler", "hayvanlar belgesel ilginç", "biliyor muydunuz", "dünyanın en",
    "rekor kırdı ilginç", "bilinmeyen gerçekler", "en uzun yaşayan hayvan", "dünyanın en büyük",
]
_TR = re.compile(r"[çğıöşüÇĞİÖŞÜ]|\b(ve|bir|bu|en|ile|için|neden|nasıl|ne|gerçek|dünya)\b", re.I)


def _dur(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def _rows(items, now):
    out = []
    for v in items:
        st, sn = v.get("statistics", {}), v["snippet"]
        views = int(st.get("viewCount", 0))
        if not views:
            continue
        likes, com = int(st.get("likeCount", 0)), int(st.get("commentCount", 0))
        age = max(0.5, (now - datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))).total_seconds() / 86400)
        out.append({"title": sn["title"], "channel": sn["channelTitle"], "views": views, "per_day": views / age,
                    "eng": (likes + com) / views, "com": com, "dur": _dur(v["contentDetails"].get("duration")),
                    "lang": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or ""})
    return out


def _table(rows, n):
    lines = ["| günlük izl. | toplam | etkileşim | yorum | süre | kanal | başlık |", "|---|---|---|---|---|---|---|"]
    for r in rows[:n]:
        title = r["title"].replace("|", "/")[:95]
        lines.append(f"| {r['per_day']:,.0f} | {r['views']:,} | %{100 * r['eng']:.1f} | {r['com']} "
                     f"| {r['dur']} sn | {r['channel'][:22]} | {title} |")
    return "\n".join(lines)


def main():
    n_q = int(sys.argv[sys.argv.index("--queries") + 1]) if "--queries" in sys.argv else 2
    token = access_token()
    h = {"Authorization": f"Bearer {token}"}
    now = datetime.now(timezone.utc)
    local = now.astimezone(IST)
    print(f"# Viral aday araştırması ({local:%Y-%m-%d %H:%M} İstanbul)\n")
    print("Bu liste yalnızca konu fikri içindir: başkasının videosu, görüntüsü, sesi ya da metni KULLANILMAZ. "
          "Konuyu güvenilir kaynaklardan doğrula, kendi şablonumuzla (kart, harita, serbest lisanslı "
          "fotoğraf, rakam) anlat.\n")

    r = requests.get(f"{API}/videos", headers=h, timeout=60, params={
        "part": "snippet,statistics,contentDetails", "chart": "mostPopular", "regionCode": "TR", "maxResults": 50})
    if r.status_code == 200:
        rows = sorted(_rows(r.json().get("items", []), now), key=lambda x: -x["per_day"])
        print("## YouTube Türkiye trendleri (o an en çok izlenenler; uzun videolar dahil, gündemi gösterir)\n")
        print(_table(rows, 15) + "\n")
    else:
        print(f"[bilgi] Trend listesi alınamadı ({r.status_code}); aramalarla devam.\n")

    slot = local.timetuple().tm_yday * 10 + local.hour  # her çalışmada sıradaki sorgular
    after = (now - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for k in range(n_q):
        q = QUERIES[(slot * n_q + k) % len(QUERIES)]
        s = requests.get(f"{API}/search", headers=h, timeout=60, params={
            "part": "id", "q": q, "type": "video", "videoDuration": "short", "regionCode": "TR",
            "relevanceLanguage": "tr", "order": "viewCount", "publishedAfter": after, "maxResults": 50})
        if s.status_code != 200:
            print(f"[bilgi] \"{q}\" araması yapılamadı ({s.status_code}): {s.text[:160]}\n")
            continue
        ids = [x["id"]["videoId"] for x in s.json().get("items", []) if x["id"].get("videoId")]
        if not ids:
            continue
        d = requests.get(f"{API}/videos", headers=h, timeout=60, params={
            "part": "snippet,statistics,contentDetails", "id": ",".join(ids)})
        rows = [x for x in _rows(d.json().get("items", []), now)
                if x["dur"] <= 180 and x["views"] >= 10000 and (x["lang"].startswith("tr") or _TR.search(x["title"]))]
        if not rows:
            print(f"## Arama: \"{q}\": 10 binin üstünde izlenen Türkçe kısa video yok\n")
            continue
        print(f"## Arama: \"{q}\" (son 14 gün, Türkçe kısa videolar)\n")
        print("Günlük izlenmeye göre:\n")
        print(_table(sorted(rows, key=lambda x: -x["per_day"]), 12) + "\n")
        eng = sorted([x for x in rows if x["views"] >= 50000], key=lambda x: -x["eng"])
        if eng:
            print("Etkileşime göre (en az 50 bin izlenme):\n")
            print(_table(eng, 6) + "\n")

    cutoff = now - timedelta(days=3)
    recent = [s for s in recent_items(token)
              if datetime.fromisoformat(s["publishedAt"].replace("Z", "+00:00")) >= cutoff]
    print("## Kanalda son 3 günde yüklenenler (tekrar etme)\n")
    for s in recent:
        kind = "viral" if "#viral" in s.get("description", "").lower() else "haber"
        print(f"- [{kind}] {s['title']}")


if __name__ == "__main__":
    main()
