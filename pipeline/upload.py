#!/usr/bin/env python3
"""Üretilen Shorts videolarını YouTube'a yükler.

Kullanım:
  python3 pipeline/upload.py --check                    # sadece kimlik doğrulamayı dener
  python3 pipeline/upload.py --recent                   # kanaldaki son 50 videonun başlığı
  python3 pipeline/upload.py --today                    # bugün kaç video yüklendi (sınır: config)
  python3 pipeline/upload.py --belgesel PROJE/yukleme.json   # haftalık yatay belgesel (BELGESEL.md)
  python3 pipeline/upload.py scripts/2026-11-11.json    # o günün videolarını yükler
  python3 pipeline/upload.py scripts/2026-11-11.json --only 1,3 --privacy private

Kimlik bilgileri (hiçbiri depoya yazılmaz):
  YT_REFRESH_TOKEN  ortam değişkeni (zorunlu)
  YT_CLIENT_ID / YT_CLIENT_SECRET  ortam değişkenleri; yoksa oauth2.googleapis.com
  için ortamda kayıtlı ağ kimliği (Basic) kullanılır — proxy başlığı kendisi ekler.

Yüklenen videolar state/uploaded.json içine kaydedilir; aynı video ikinci kez yüklenmez.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
STATE = ROOT / "state" / "uploaded.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
API = "https://www.googleapis.com/youtube/v3"
IST = timezone(timedelta(hours=3))  # Türkiye: sabit UTC+3 (yaz saati yok)


def die(msg):
    print(f"[hata] {msg}", file=sys.stderr)
    sys.exit(1)


def access_token():
    refresh = os.environ.get("YT_REFRESH_TOKEN")
    if not refresh:
        die("YT_REFRESH_TOKEN ortam değişkeni yok. Kurulum için README.md > YouTube bağlantısı.")
    data = {"grant_type": "refresh_token", "refresh_token": refresh}
    cid, secret = os.environ.get("YT_CLIENT_ID"), os.environ.get("YT_CLIENT_SECRET")
    if cid and secret:
        auth = (cid, secret)
    else:
        # Yer tutucu; ortamın ağ kimliği gerçek client_id:client_secret ile değiştirir.
        auth = ("client-id-proxy-tarafindan-eklenir", "x")
    r = requests.post(TOKEN_URL, data=data, auth=auth, timeout=60)
    if r.status_code != 200:
        die(f"Erişim anahtarı alınamadı ({r.status_code}): {r.text[:300]}")
    return r.json()["access_token"]


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save_state(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def recent_items(token, limit=50):
    """Kanalın son `limit` yüklemesi (playlistItems snippet'leri, en yeni önce)."""
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API}/channels", params={"part": "contentDetails", "mine": "true"},
                     headers=h, timeout=60)
    if r.status_code != 200 or not r.json().get("items"):
        die(f"Kanal okunamadı ({r.status_code}): {r.text[:300]}")
    uploads = r.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    out, page = [], None
    while len(out) < limit:
        p = {"part": "snippet", "playlistId": uploads, "maxResults": min(50, limit - len(out))}
        if page:
            p["pageToken"] = page
        r = requests.get(f"{API}/playlistItems", headers=h, timeout=60, params=p)
        if r.status_code == 404:  # henüz hiç video yok
            return out
        if r.status_code != 200:
            die(f"Son videolar okunamadı ({r.status_code}): {r.text[:300]}")
        out += [it["snippet"] for it in r.json().get("items", [])]
        page = r.json().get("nextPageToken")
        if not page:
            break
    return out


def today_count(items):
    """İstanbul saatine göre bugün yüklenen Shorts sayısı (haftalık belgesel sayılmaz)."""
    today = datetime.now(IST).date()
    return sum(1 for s in items if kind_of(s) != "belgesel"
               and datetime.fromisoformat(s["publishedAt"].replace("Z", "+00:00")).astimezone(IST).date() == today)


def kind_of(snippet):
    """Videonun türü açıklamasındaki etiketten: #belgesel (haftalık yatay), #viral ya da haber."""
    desc = snippet.get("description", "").lower()
    return "belgesel" if "#belgesel" in desc else ("viral" if "#viral" in desc else "haber")


def today_mix(items):
    """Bugün (İstanbul) yüklenenlerin türlere göre sayısı ve en son yüklenenin türü (items en yeni önce)."""
    today = datetime.now(IST).date()
    todays = [s for s in items
              if datetime.fromisoformat(s["publishedAt"].replace("Z", "+00:00")).astimezone(IST).date() == today]
    counts = {"haber": 0, "viral": 0}
    for s in todays:
        k = kind_of(s)
        if k in counts:
            counts[k] += 1
    shorts = [x for x in todays if kind_of(x) != "belgesel"]
    return counts, (kind_of(shorts[0]) if shorts else None)


def next_kind(counts, last):
    """Günlük karışıma (config daily_mix, ör. 5 haber + 5 viral) göre bu çalışmanın türü; ikisi de
    dolduysa None. Kalanı çok olan seçilir; eşitlikte son yüklenenin tersi (gün boyu sırayla)."""
    mix = CONFIG.get("daily_mix", {"haber": 5, "viral": 5})
    left = {k: mix[k] - counts.get(k, 0) for k in mix}
    best = max(left.values(), default=0)
    if best <= 0:
        return None
    tied = [k for k, n in left.items() if n == best]
    if len(tied) > 1 and last in tied:
        tied.remove(last)
    return "haber" if "haber" in tied else tied[0]


def clean_title(t):
    """Başlıktan #shorts'u çıkarır (açıklamada zaten var; başlıkta görünen 40-60 karakteri harcar)."""
    return " ".join(re.sub(r"#shorts\b", "", t, flags=re.I).split())[:100] or t.strip()[:100]


def upload(token, path, v, privacy):
    desc = v["description"].strip()
    if v.get("sources"):
        desc += "\n\nKaynaklar:\n" + "\n".join(v["sources"])
    tags_line = " ".join(h if h.startswith("#") else f"#{h}" for h in v.get("hashtags", [])[:3])
    if tags_line:  # açıklamadaki ilk hashtag'ler başlığın üstünde görünür
        desc += "\n\n" + tags_line
    cred = path.with_suffix(".credits.json")
    if cred.exists():  # Wikimedia Commons lisanslarının istediği atıf
        lines = [f"- {c['title'].removeprefix('File:')} — {c['artist']}, {c['license']} ({c['page']})"
                 for c in json.loads(cred.read_text(encoding="utf-8"))]
        desc += "\n\nGörseller (Wikimedia Commons):\n" + "\n".join(lines)
    viral = v.get("type") == "viral"
    footer = (CONFIG.get("description_footer_viral") if viral else None) or \
        CONFIG.get("description_footer", "#shorts #gündem #haber")
    if viral and "#viral" not in footer.lower():  # --today tür sayımı bu etikete bakar
        footer += " #viral"
    desc = desc[:4900 - len(footer) - 2] + "\n\n" + footer  # kesilirse dipnot (tür etiketi) korunur
    tags = list(dict.fromkeys(v.get("tags", []) + CONFIG.get("default_tags_viral" if viral else "default_tags", [])))
    category = CONFIG.get("youtube_category_id_viral", "27") if viral else CONFIG.get("youtube_category_id", "25")
    body = {
        "snippet": {
            "title": clean_title(v["yt_title"]),
            "description": desc,
            "tags": tags,
            "categoryId": v.get("youtube_category_id", category),
            "defaultLanguage": "tr",
            "defaultAudioLanguage": "tr",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        },
    }
    return send_video(token, path, body)


def send_video(token, path, body):
    """Sürdürülebilir (resumable) yükleme; döner: YouTube video kaynağı."""
    size = path.stat().st_size
    start = requests.post(
        UPLOAD_URL,
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={
            "Authorization": f"Bearer {token}",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        json=body,
        timeout=60,
    )
    if start.status_code != 200:
        die(f"Yükleme başlatılamadı ({start.status_code}): {start.text[:400]}")
    with path.open("rb") as f:
        r = requests.put(
            start.headers["Location"],
            data=f,
            headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
            timeout=1800,
        )
    if r.status_code not in (200, 201):
        die(f"Video yüklenemedi ({r.status_code}): {r.text[:400]}")
    return r.json()


def upload_long(token, meta_path):
    """Haftalık yatay belgesel (BELGESEL.md). meta: video, thumbnail, yt_title, description, chapters
    [[sn, başlık]], sources, credits, tags, publish_at (ISO, İstanbul saati; gizli yüklenip o anda
    kendiliğinden yayına girer). Açıklamaya #belgesel eklenir: Shorts sayımına girmez."""
    meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    base = Path(meta_path).parent
    path = (base / meta["video"]).resolve()
    if not path.exists():
        die(f"Video dosyası yok: {path}")
    if any(s["title"] == meta["yt_title"] for s in recent_items(token, 100)):
        print(f"[atla] Aynı başlıkta video zaten var: {meta['yt_title']}")
        return
    desc = meta["description"].strip()
    if meta.get("chapters"):  # YouTube bölümleri: ilki 00:00, en az 3 bölüm, her biri en az 10 sn
        desc += "\n\nBölümler:\n" + "\n".join(f"{int(t) // 60:02d}:{int(t) % 60:02d} {title}"
                                                 for t, title in meta["chapters"])
    if meta.get("sources"):
        desc += "\n\nKaynaklar:\n" + "\n".join(meta["sources"])
    if meta.get("credits"):
        desc += "\n\nGörseller:\n" + "\n".join(f"- {c}" for c in meta["credits"])
    footer = CONFIG.get("description_footer_belgesel",
                        "#belgesel #siberguvenlik\n\nBu video güvenilir kaynaklardan derlenen bilgilerle hazırlanmıştır.")
    if "#belgesel" not in footer.lower():
        footer += " #belgesel"
    desc = desc[:4900 - len(footer) - 2] + "\n\n" + footer
    status = {"privacyStatus": CONFIG.get("privacy", "public"), "selfDeclaredMadeForKids": False, "embeddable": True}
    if meta.get("publish_at"):
        when = datetime.fromisoformat(meta["publish_at"])
        if when.tzinfo is None:
            when = when.replace(tzinfo=IST)
        status.update(privacyStatus="private", publishAt=when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    body = {"snippet": {"title": meta["yt_title"][:100], "description": desc,
                        "tags": list(dict.fromkeys(meta.get("tags", []) + CONFIG.get("default_tags_belgesel", []))),
                        "categoryId": CONFIG.get("youtube_category_id_belgesel", "28"),
                        "defaultLanguage": "tr", "defaultAudioLanguage": "tr"},
            "status": status}
    res = send_video(token, path, body)
    vid = res["id"]
    print(f"[ok] https://youtube.com/watch?v={vid}  ({res.get('status', {}).get('privacyStatus')}"
          f"{', yayın ' + meta['publish_at'] if meta.get('publish_at') else ''})  {meta['yt_title']}")
    thumb = (base / meta["thumbnail"]).resolve() if meta.get("thumbnail") else None
    if thumb and thumb.exists():
        r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                          headers={"Authorization": f"Bearer {token}", "Content-Type": "image/png"},
                          data=thumb.read_bytes(), timeout=120)
        if r.status_code == 200:
            print("[ok] Küçük resim yüklendi")
        else:  # kanal doğrulanmamışsa YouTube özel küçük resme izin vermez; video yine yayına girer
            print(f"[uyarı] Küçük resim yüklenemedi ({r.status_code}): {r.text[:200]}. Video yine de yüklendi; "
                  "kanal doğrulaması (YouTube Studio > Ayarlar > Kanal > Özellik uygunluğu) gerekebilir.")
    state = load_state()
    state[f"belgesel/{meta.get('slug', vid)}"] = {"id": vid, "url": f"https://youtube.com/watch?v={vid}",
                                                   "title": meta["yt_title"], "publish_at": meta.get("publish_at")}
    save_state(state)


def main():
    args = sys.argv[1:]
    token = access_token()
    if "--check" in args:
        r = requests.get(f"{API}/channels", params={"part": "snippet", "mine": "true"},
                         headers={"Authorization": f"Bearer {token}"}, timeout=60)
        if r.status_code != 200:
            die(f"Kanal okunamadı ({r.status_code}): {r.text[:300]}")
        items = r.json().get("items", [])
        if not items:
            die("Bu Google hesabına bağlı bir YouTube kanalı bulunamadı.")
        print(f"[ok] Bağlı kanal: {items[0]['snippet']['title']}")
        return
    if "--belgesel" in args:
        upload_long(token, args[args.index("--belgesel") + 1])
        return
    cap = int(CONFIG.get("daily_upload_cap", 10) or 0)
    if "--today" in args:
        items = recent_items(token)
        counts, last = today_mix(items)
        mix = CONFIG.get("daily_mix", {"haber": 5, "viral": 5})
        print(f"Bugün (İstanbul) kanala yüklenen video: {today_count(items)} / {cap or '-'} "
              f"(haber {counts['haber']}, viral {counts['viral']})")
        kind = next_kind(counts, last)
        if cap and today_count(items) >= cap:
            kind = None
        left = ", ".join(f"{k} {max(0, mix[k] - counts.get(k, 0))}" for k in mix)
        print(f"Sıradaki video türü: {kind or 'yok (bugünkü videolar tamam)'}  (kalan: {left})")
        return
    if "--recent" in args:
        # Kanala son yüklenen videoların başlıkları (aynı konuyu tekrar işlememek için); --recent 300
        i = args.index("--recent")
        limit = int(args[i + 1]) if i + 1 < len(args) and args[i + 1].isdigit() else 50
        try:
            for s in recent_items(token, limit):
                tag = {"viral": "[viral] ", "belgesel": "[belgesel] "}.get(kind_of(s), "")
                print(f"{s['publishedAt'][:10]} | {tag}{s['title']}", flush=True)
        except BrokenPipeError:  # `| head -5` okumayı erken kesti: hata değil, sessizce çık
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return

    data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    day = data["date"]
    only = None
    if "--only" in args:
        only = {int(x) for x in args[args.index("--only") + 1].split(",")}
    privacy = CONFIG.get("privacy", "public")
    if "--privacy" in args:
        privacy = args[args.index("--privacy") + 1]

    state = load_state()
    for n, v in enumerate(data["videos"], 1):
        key = f"{day}/{v['slug']}"
        if only and n not in only:
            continue
        if key in state:
            print(f"[atla] {key} zaten yüklü: {state[key]['url']}")
            continue
        path = ROOT / "out" / day / f"{n}-{v['slug']}.mp4"
        if not path.exists():
            die(f"Video dosyası yok: {path}")
        if cap and today_count(recent_items(token)) >= cap:
            # 13-14 Kasım verisi: günün 10. videosundan sonrakiler neredeyse hiç dağıtılmadı
            print(f"[bilgi] Bugün kanala zaten {cap} video yüklendi; YouTube günün {cap}. videosundan "
                  "sonrakileri neredeyse hiç göstermiyor. Yükleme yapılmadı (hata değil).")
            return
        res = upload(token, path, v, privacy)
        got = res.get("status", {}).get("privacyStatus")
        state[key] = {"id": res["id"], "url": f"https://youtube.com/shorts/{res['id']}",
                      "title": clean_title(v["yt_title"]), "privacy": got}
        save_state(state)
        print(f"[ok] {state[key]['url']}  ({got})  {clean_title(v['yt_title'])}")
        if got != privacy:
            print(f"[uyarı] İstenen görünürlük '{privacy}' ama YouTube '{got}' olarak kaydetti "
                  "(kanal/hesap ayarları yüklemeleri gizliye çekebilir; YouTube Studio'dan kontrol et).")


if __name__ == "__main__":
    main()
