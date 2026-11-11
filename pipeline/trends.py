#!/usr/bin/env python3
"""Türkiye'de son günlerde en çok konuşulan konular için ham aday listesi çıkarır.

Kullanım:  python3 pipeline/trends.py [--days 3] > out/gundem.md

Kaynaklar: Google Trends (TR, anlık trend aramalar + arama hacmi) ve Google Haberler
(TR manşetler ve bölüm başlıkları). Çıktı yalnızca ADAY listesidir; konu seçimi ve
bilgilerin doğrulanması ayrıca yapılır (bkz. GUNLUK.md).
"""
import html
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = {"User-Agent": "Mozilla/5.0 (compatible; rss-reader)"}
NEWS = "https://news.google.com/rss{path}?hl=tr&gl=TR&ceid=TR:tr"
SECTIONS = [
    ("Manşetler", ""),
    ("Türkiye", "/headlines/section/topic/NATION"),
    ("Dünya", "/headlines/section/topic/WORLD"),
    ("Ekonomi", "/headlines/section/topic/BUSINESS"),
    ("Spor", "/headlines/section/topic/SPORTS"),
    ("Teknoloji", "/headlines/section/topic/TECHNOLOGY"),
    ("Magazin", "/headlines/section/topic/ENTERTAINMENT"),
    ("Bilim", "/headlines/section/topic/SCIENCE"),
    ("Sağlık", "/headlines/section/topic/HEALTH"),
]


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")


def items(xml):
    return re.findall(r"<item>(.*?)</item>", xml, re.S)


def tag(block, name):
    m = re.search(rf"<{name}>(.*?)</{name}>", block, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 3
    since = datetime.now(timezone.utc) - timedelta(days=days)
    print(f"# Gündem adayları (son {days} gün) — {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC\n")

    print("## Google Trends TR — trend aramalar\n")
    try:
        for it in items(fetch("https://trends.google.com/trending/rss?geo=TR")):
            news = re.findall(r"<ht:news_item_title>(.*?)</ht:news_item_title>", it, re.S)
            first = html.unescape(news[0]).strip() if news else ""
            print(f"- **{tag(it, 'title')}** ({tag(it, 'ht:approx_traffic')} arama) — {first[:140]}")
    except Exception as e:  # kaynak düşerse diğerleriyle devam et
        print(f"- (alınamadı: {e})")

    seen = set()
    for name, path in SECTIONS:
        print(f"\n## Google Haberler — {name}\n")
        try:
            rows = []
            for it in items(fetch(NEWS.format(path=path))):
                title = tag(it, "title")
                try:
                    when = parsedate_to_datetime(tag(it, "pubDate"))
                except Exception:
                    continue
                key = title[:60]
                if when < since or key in seen:
                    continue
                seen.add(key)
                rows.append((when, title))
            for when, title in rows[: 30 if not path else 15]:
                print(f"- {when:%d.%m %H:%M} | {title[:170]}")
        except Exception as e:
            print(f"- (alınamadı: {e})")


if __name__ == "__main__":
    main()
