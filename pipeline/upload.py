#!/usr/bin/env python3
"""Üretilen Shorts videolarını YouTube'a yükler.

Kullanım:
  python3 pipeline/upload.py --check                    # sadece kimlik doğrulamayı dener
  python3 pipeline/upload.py --recent                   # kanaldaki son 30 videonun başlığı
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
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
STATE = ROOT / "state" / "uploaded.json"
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
API = "https://www.googleapis.com/youtube/v3"


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


def upload(token, path, v, privacy):
    desc = v["description"].strip()
    if v.get("sources"):
        desc += "\n\nKaynaklar:\n" + "\n".join(v["sources"])
    cred = path.with_suffix(".credits.json")
    if cred.exists():  # Wikimedia Commons lisanslarının istediği atıf
        lines = [f"- {c['title'].removeprefix('File:')} — {c['artist']}, {c['license']} ({c['page']})"
                 for c in json.loads(cred.read_text(encoding="utf-8"))]
        desc += "\n\nGörseller (Wikimedia Commons):\n" + "\n".join(lines)
    desc += "\n\n" + CONFIG.get("description_footer", "#shorts #gündem #haber")
    tags = list(dict.fromkeys(v.get("tags", []) + CONFIG.get("default_tags", [])))
    body = {
        "snippet": {
            "title": v["yt_title"][:100],
            "description": desc[:4900],
            "tags": tags,
            "categoryId": v.get("youtube_category_id", CONFIG.get("youtube_category_id", "25")),
            "defaultLanguage": "tr",
            "defaultAudioLanguage": "tr",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        },
    }
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
    if "--recent" in args:
        # Kanala son yüklenen videoların başlıkları (aynı konuyu tekrar işlememek için)
        h = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{API}/channels", params={"part": "contentDetails", "mine": "true"},
                         headers=h, timeout=60)
        if r.status_code != 200 or not r.json().get("items"):
            die(f"Kanal okunamadı ({r.status_code}): {r.text[:300]}")
        uploads = r.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        r = requests.get(f"{API}/playlistItems", headers=h, timeout=60,
                         params={"part": "snippet", "playlistId": uploads, "maxResults": 30})
        if r.status_code == 404:  # henüz hiç video yok
            return
        if r.status_code != 200:
            die(f"Son videolar okunamadı ({r.status_code}): {r.text[:300]}")
        for it in r.json().get("items", []):
            s = it["snippet"]
            print(f"{s['publishedAt'][:10]} | {s['title']}")
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
        res = upload(token, path, v, privacy)
        got = res.get("status", {}).get("privacyStatus")
        state[key] = {"id": res["id"], "url": f"https://youtube.com/shorts/{res['id']}",
                      "title": v["yt_title"], "privacy": got}
        save_state(state)
        print(f"[ok] {state[key]['url']}  ({got})  {v['yt_title']}")
        if got != privacy:
            print(f"[uyarı] İstenen görünürlük '{privacy}' ama YouTube '{got}' olarak kaydetti "
                  "(kanal/hesap ayarları yüklemeleri gizliye çekebilir; YouTube Studio'dan kontrol et).")


if __name__ == "__main__":
    main()
