#!/usr/bin/env python3
"""Kanal performansı: her video kanalın kendi medyanının kaç katı izlendi (yt-viral yöntemi).

Ham izlenme sayısı kanal büyüklüğünü ve videonun yaşını ölçer, fikrin tutup tutmadığını değil.
Burada her video, kanalın olgun videolarının medyan izlenmesine bölünür ("kat"). Yeni yüklenen
videolar henüz izlenme toplarken haksız karşılaştırılmasın diye sıralamaya yalnızca en az
--min-age saatlik (varsayılan 24) videolar girer; daha yeniler ayrıca gösterilir.

Kullanım:
  python3 pipeline/stats.py                   # tüm olgun videolar, kata göre
  python3 pipeline/stats.py --top 8           # en iyi 8 ve en zayıf 8
  python3 pipeline/stats.py --json veri.json  # ham veriyi de yaz (analiz için)
"""
import json
import re
import statistics
import sys
from datetime import datetime, timezone

import requests

from upload import API, access_token, die


def _dur(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def fetch(token):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API}/channels", params={"part": "contentDetails", "mine": "true"}, headers=h, timeout=60)
    if r.status_code != 200 or not r.json().get("items"):
        die(f"Kanal okunamadı ({r.status_code}): {r.text[:200]}")
    uploads = r.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    while True:
        p = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
        if page:
            p["pageToken"] = page
        r = requests.get(f"{API}/playlistItems", params=p, headers=h, timeout=60)
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            die(f"Video listesi okunamadı ({r.status_code}): {r.text[:200]}")
        js = r.json()
        ids += [it["contentDetails"]["videoId"] for it in js.get("items", [])]
        page = js.get("nextPageToken")
        if not page:
            break
    now = datetime.now(timezone.utc)
    out = []
    for i in range(0, len(ids), 50):
        r = requests.get(f"{API}/videos", headers=h, timeout=60,
                         params={"part": "snippet,statistics,contentDetails", "id": ",".join(ids[i:i + 50])})
        if r.status_code != 200:
            die(f"Video istatistikleri okunamadı ({r.status_code}): {r.text[:200]}")
        for it in r.json().get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            pub = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
            out.append({
                "id": it["id"], "url": f"https://youtube.com/shorts/{it['id']}", "title": sn["title"],
                "published": sn["publishedAt"], "age_h": round((now - pub).total_seconds() / 3600, 1),
                "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)), "duration": _dur(it["contentDetails"]["duration"]),
                "kind": ("belgesel" if "#belgesel" in sn.get("description", "").lower() else "viral" if "#viral" in sn.get("description", "").lower() else "haber"),
            })
    return out


def rank(vids, min_age=24.0):
    mature = [v for v in vids if v["age_h"] >= min_age]
    med = statistics.median([v["views"] for v in mature]) if mature else 0
    for v in vids:
        v["multiple"] = round(v["views"] / med, 2) if med else None
    return sorted(mature, key=lambda v: -v["views"]), [v for v in vids if v["age_h"] < min_age], med


def _row(v):
    k = f"{v['multiple']:.1f}x" if v["multiple"] is not None else "  -"
    return (f"  {k:>6}  {v['views']:>7} izl  {v['likes']:>4} beğ  {v['age_h']:>5.0f} sa  "
            f"{'[viral] ' if v.get('kind') == 'viral' else ''}{v['title']}")


def main():
    a = sys.argv[1:]
    min_age = float(a[a.index("--min-age") + 1]) if "--min-age" in a else 24.0
    top = int(a[a.index("--top") + 1]) if "--top" in a else 0
    vids = fetch(access_token())
    if "--json" in a:
        with open(a[a.index("--json") + 1], "w", encoding="utf-8") as fh:
            json.dump(vids, fh, ensure_ascii=False, indent=1)
    mature, young, med = rank(vids, min_age)
    print(f"{len(vids)} video · {len(mature)} tanesi en az {min_age:.0f} saatlik · olgun videoların medyanı "
          f"{med:.0f} izlenme (1,0x = medyan)")
    rows = mature if not top or len(mature) <= 2 * top else mature[:top] + [None] + mature[-top:]
    for v in rows:
        print("  ..." if v is None else _row(v))
    viral = [v for v in mature if v.get("kind") == "viral"]
    if viral and med:  # 5 haber + 5 viral denemesi: türlerin medyana göre karşılaştırması
        for kind in ("haber", "viral"):
            m = statistics.median([v["views"] for v in mature if v.get("kind") == kind])
            n = sum(1 for v in mature if v.get("kind") == kind)
            print(f"\n{kind:>5}: {n} olgun video, medyan {m:.0f} izlenme ({m / med:.2f}x)", end="")
        print()
    if young:
        print(f"\nHenüz {min_age:.0f} saati doldurmayan {len(young)} video (sıralamaya girmedi):")
        for v in sorted(young, key=lambda v: v["age_h"]):
            print(_row(v))


if __name__ == "__main__":
    main()
