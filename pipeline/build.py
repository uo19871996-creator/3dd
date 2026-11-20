#!/usr/bin/env python3
"""Günlük senaryo dosyasından (scripts/TARIH.json) Shorts videoları üretir.

Kullanım:  python3 pipeline/build.py scripts/2026-11-11.json [--only 1,3]

Her video için: Türkçe seslendirme -> altyazı zamanlaması ->
Remotion ile 1080x1920 MP4 (out/TARIH/N-slug.mp4).

Seslendirme motoru config.json içindeki "tts" ile seçilir:
  "elevenlabs" : ElevenLabs API (anahtar ortamda ağ kimliği olarak kayıtlı; ticari kullanım ücretli planda)
  "chatterbox" : Chatterbox Multilingual, kanal sahibinin ses örneğiyle (MIT, işlemcide çalışır)
  "google"     : Google Cloud Text-to-Speech (resmi API, ticari kullanım serbest)
  "piper"      : çevrimdışı, ücretsiz (tr_TR-dfki sesi; lisansı CC BY-NC-SA, ticari değil)
Motor açılamazsa ya da video sırasında kullanılamaz olursa (ör. kredi biter) video, "tts_fallback"
sırasındaki motorla baştan üretilir; tek videoda iki farklı ses karışmaz.
"""
import base64
import glob
import io
import json
import os
import re
import struct
import subprocess
import sys
import time
import wave
import zlib
from pathlib import Path

import numpy as np
import requests

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / "video"
VOICE = ROOT / "voices" / "tr_TR-dfki-medium.onnx"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
FPS = 30
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
          "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
ACCENTS = {
    "EKONOMİ": "#34d399", "SPOR": "#fb923c", "SİYASET": "#f87171",
    "TEKNOLOJİ": "#22d3ee", "MAGAZİN": "#f472b6", "DÜNYA": "#a78bfa",
    "GÜNDEM": "#facc15", "SAĞLIK": "#4ade80", "EĞİTİM": "#60a5fa",
    "YAŞAM": "#fbbf24", "BİLİM": "#38bdf8", "KÜLTÜR": "#e879f9",
}
CATEGORY_ICONS = {  # v2 şablonu: kategori ikonu (Lucide adları)
    "EKONOMİ": "trending-up", "SPOR": "trophy", "SİYASET": "landmark", "TEKNOLOJİ": "cpu",
    "MAGAZİN": "star", "DÜNYA": "globe", "GÜNDEM": "newspaper", "SAĞLIK": "heart-pulse",
    "EĞİTİM": "graduation-cap", "YAŞAM": "sun", "BİLİM": "atom", "KÜLTÜR": "palette",
}


class ChatterboxTTS:
    """Chatterbox Multilingual (MIT): doğal Türkçe ses, ticari kullanım serbest.
    Ayrı sanal ortamda (.venv-tts, setup.sh kurar) çalışan bir işçi sürece cümle gönderir."""

    def __init__(self):
        py = ROOT / ".venv-tts" / "bin" / "python"
        if not py.exists():
            raise RuntimeError(".venv-tts yok (setup.sh, tts=chatterbox ile çalıştırılmalı)")
        env = dict(os.environ, HF_HUB_DISABLE_XET="1")
        self.label = "Chatterbox, modelin varsayılan sesi"
        # Model önceden indirildiyse (setup.sh) hub'a sorgu atma: açılış dakikalardan saniyelere iner
        hub = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
        if glob.glob(str(hub / "models--ResembleAI--chatterbox" / "snapshots" / "*" / "t3_mtl*.safetensors")):
            env["HF_HUB_OFFLINE"] = "1"
        try:  # kanal sahibinin şifreli ses örneği (assets/ses-ornegi.wav.enc) varsa onun sesiyle konuş
            from voice import decrypt_to
            sample = decrypt_to(ROOT / "out" / ".tts" / "ses-ornegi.wav")
            if sample:
                env["CBX_VOICE_SAMPLE"] = str(sample)
                self.label = "Chatterbox, kanal sahibinin sesi"
                print("[bilgi] Ses: kanal sahibinin ses örneği", flush=True)
        except Exception as e:
            print(f"[bilgi] Ses örneği kullanılamadı ({e}); modelin varsayılan sesi kullanılıyor. "
                  "Bu bir hata değil, işleme devam et.", flush=True)
        self.proc = subprocess.Popen(
            [str(py), str(ROOT / "pipeline" / "tts_chatterbox_worker.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
        self.tmp = ROOT / "out" / ".tts"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.n = 0
        while True:  # modelin yüklenmesini bekle; işçinin diğer çıktısını atla
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("Chatterbox işçisi başlamadı")
            if line.startswith("{"):
                msg = json.loads(line)
                if msg.get("ready"):
                    self.sr = int(msg["sr"])
                    break

    def synth(self, text, prev=None, nxt=None):  # bağlam (prev/nxt) bu motorda kullanılmaz
        self.n += 1
        out = self.tmp / f"{self.n}.wav"
        self.proc.stdin.write(json.dumps({"text": text, "out": str(out)}, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("Chatterbox işçisi kapandı")
            if line.startswith("{"):
                msg = json.loads(line)
                break
        if not msg.get("ok"):
            raise RuntimeError(f"Chatterbox: {msg.get('error')}")
        with wave.open(str(out)) as w:
            return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


class PiperTTS:
    def __init__(self):
        from piper import PiperVoice, SynthesisConfig
        self.voice = PiperVoice.load(str(VOICE))
        self.cfg = SynthesisConfig(length_scale=CONFIG.get("speech_length_scale", 0.95))
        self.sr = self.voice.config.sample_rate
        self.label = "Piper (ücretsiz yedek ses)"

    def synth(self, text, prev=None, nxt=None):
        audio = [c.audio_int16_array for c in self.voice.synthesize(text, syn_config=self.cfg)]
        return np.concatenate(audio) if audio else np.zeros(0, dtype=np.int16)


class GoogleTTS:
    """Google Cloud Text-to-Speech. Anahtar: GOOGLE_TTS_API_KEY ortam değişkeni ya da
    texttospeech.googleapis.com için ortamda kayıtlı ağ kimliği (X-Goog-Api-Key)."""
    URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

    def __init__(self):
        self.sr = 24000
        self.voice = CONFIG.get("google_voice", "tr-TR-Wavenet-E")
        self.rate = CONFIG.get("google_speaking_rate", 1.05)
        self.key = os.environ.get("GOOGLE_TTS_API_KEY", "proxy-tarafindan-eklenir")

    def synth(self, text, prev=None, nxt=None):
        r = requests.post(self.URL, headers={"X-Goog-Api-Key": self.key}, timeout=120, json={
            "input": {"text": text},
            "voice": {"languageCode": "tr-TR", "name": self.voice},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": self.sr,
                            "speakingRate": self.rate},
        })
        if r.status_code != 200:
            raise RuntimeError(f"Google TTS ({r.status_code}): {r.text[:300]}")
        with wave.open(io.BytesIO(base64.b64decode(r.json()["audioContent"]))) as w:
            return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


class TTSUnavailable(RuntimeError):
    """Ses motoru bu çalıştırmada kullanılamıyor (kredi bitti, anahtar geçersiz ya da yetkisiz, servis
    yanıt vermiyor). main() o videoyu sıradaki motorla baştan üretir."""


class ElevenLabsTTS:
    """ElevenLabs (resmi API). Anahtar ortamda ağ kimliği olarak kayıtlıdır: vekil sunucu
    api.elevenlabs.io isteklerine xi-api-key başlığını kendisi ekler, anahtar ne bu betikte ne depoda
    durur (ortam dışında ELEVENLABS_API_KEY ortam değişkeni de olur).

    Her cümle ayrı istenir; önceki ve sonraki cümle bağlam olarak gider (ücretlendirilmez), böylece
    tonlama cümleler arasında kopmaz. Kredi: eleven_v4 ve eleven_multilingual_v2 harf başına 1,
    eleven_v4_turbo ve eleven_flash_v2_5 harf başına 0,5."""
    URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=pcm_24000"
    VOICES = {  # hazır sesler; klonlanmış bir ses için config'e ses kimliğini (voice_id) yaz
        "george": "JBFqnCBsd6RMkjVDRZzb", "brian": "nPczCjzI2devNBz1zQrb", "daniel": "onwK4e9ZLuTAKqWW03F9",
        "sarah": "EXAVITQu4vr4xnSDxMaL", "alice": "Xb7hH8MSUJpSbSDYk0k2",
    }
    OPTIONAL = ("language_code", "previous_text", "next_text")  # kabul etmeyen modelde çıkarılır

    def __init__(self):
        self.sr = 24000
        name = str(CONFIG.get("elevenlabs_voice", "george"))
        self.voice = self.VOICES.get(name.lower(), name)
        self.model = CONFIG.get("elevenlabs_model", "eleven_v4")
        self.settings = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True,
                         **CONFIG.get("elevenlabs_settings", {})}
        if self.model.startswith("eleven_v4"):  # v4 yalnız bu ikisini alır (style ve speed yok)
            self.settings = {k: v for k, v in self.settings.items() if k in ("stability", "similarity_boost")}
        key = os.environ.get("ELEVENLABS_API_KEY")
        self.headers = {"xi-api-key": key} if key else {}
        self.drop = set()
        self.spent = 0  # harcanan kredi (yanıttaki Character-Cost başlığından)
        who = name.lower() if name.lower() in self.VOICES else "klon ses"
        self.label = f"ElevenLabs {who} ({self.model})"
        left = self.credits_left()
        if left is not None:
            per_video = 600 * (0.5 if "turbo" in self.model or "flash" in self.model else 1)
            print(f"[bilgi] ElevenLabs kalan kredi: {left} (yaklaşık {int(left // per_video)} video)", flush=True)
            if left < 3 * per_video:
                print("[uyarı] ElevenLabs kredisi bitmek üzere; bitince videolar yedek sesle üretilir. "
                      "Raporda belirt.", flush=True)

    def credits_left(self):
        """Kalan kredi; anahtarda "User: Read" izni yoksa None (kredi harcamaz)."""
        try:
            r = requests.get("https://api.elevenlabs.io/v1/user/subscription", headers=self.headers, timeout=20)
            if r.status_code == 200:
                s = r.json()
                return int(s["character_limit"]) - int(s["character_count"])
        except Exception:
            pass
        return None

    def synth(self, text, prev=None, nxt=None):
        body = {"text": text, "model_id": self.model, "language_code": "tr", "voice_settings": self.settings,
                "previous_text": prev, "next_text": nxt}
        err = ""
        for attempt in range(5):
            body = {k: v for k, v in body.items() if v is not None and k not in self.drop}
            try:
                r = requests.post(self.URL.format(voice=self.voice), headers=self.headers, json=body, timeout=90)
            except requests.RequestException as e:  # bağlantı/zaman aşımı: bekleyip yeniden dene
                err = f"bağlantı: {str(e)[:160]}"
            else:
                if r.status_code == 200:
                    self.spent += int(r.headers.get("character-cost") or len(text))
                    return np.frombuffer(r.content, dtype=np.int16)  # ham PCM: 16 bit, 24 kHz, mono
                err = f"{r.status_code}: {r.text[:240]}"
                bad = [k for k in self.OPTIONAL if k in body and k in r.text] if r.status_code in (400, 422) else []
                if bad:  # model bu alanı desteklemiyor: çıkarıp hemen yeniden dene
                    self.drop.update(bad)
                    continue
                if r.status_code < 500 and r.status_code not in (408, 409, 429):
                    raise TTSUnavailable(err)  # kredi bitti / anahtar ya da yetki sorunu / ses yok
            time.sleep(2 * 2 ** attempt)
        raise TTSUnavailable(err)


def chrome_path():
    """Önceden kurulu headless Chrome'u bulur (sürüm numarası imaja göre değişebilir)."""
    if CONFIG.get("chrome"):
        return CONFIG["chrome"]
    hits = sorted(glob.glob(
        "/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    return hits[-1] if hits else None


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


_OKUNUS = None


def okunus(text):
    """Yabancı kelime ve kısaltmaları okunus.json'daki Türkçe okunuşlarına çevirir (yalnız seslendirme;
    altyazı değişmez). Büyük/küçük harfe duyarlı, ekler korunur: "CEO'su" -> "Si-İ-O'su"."""
    global _OKUNUS
    if _OKUNUS is None:
        f = ROOT / "okunus.json"
        terms = {}
        if f.exists():
            for k, val in json.loads(f.read_text(encoding="utf-8")).items():
                if not k.startswith("_") and isinstance(val, dict):
                    terms.update(val)
        keys = sorted(terms, key=len, reverse=True)  # uzun eşleşme önce: "Elon Musk" > "Musk"
        pat = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, keys)) + r")(?!\w)") if keys else None
        _OKUNUS = (pat, terms)
    pat, terms = _OKUNUS
    return pat.sub(lambda m: terms[m.group(1)], text) if pat else text


def sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p for p in parts if p]


def chunk_words(sentence, max_words=3, max_chars=20):
    """Cümleyi ekranda aynı anda görünecek kısa altyazı parçalarına böler."""
    chunks, cur = [], []
    for w in sentence.split():
        trial = " ".join(cur + [w])
        if cur and (len(cur) >= max_words or len(trial) > max_chars):
            chunks.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
        if cur and re.search(r"[,;:]$", w) and len(" ".join(cur)) >= 9:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def trim(a, sr, thresh=250, pad=0.04):
    """Baştaki/sondaki sessizliği kırpar ki altyazı sese otursun."""
    loud = np.where(np.abs(a) > thresh)[0]
    if not len(loud):
        return a
    p = int(pad * sr)
    return a[max(0, loud[0] - p): loud[-1] + p]


def ensure_grain(n=4, size=256):
    """Film greni karoları: video/public/fx/grain-*.png (numpy ile üretilir, telifsiz, Pillow gerekmez).

    Gri+saydamlık PNG: benek beyaz ya da siyah, saydamlığı gürültünün mutlak değeri (0,25 ölçekli)."""
    d = VIDEO / "public" / "fx"
    paths = [d / f"grain-{i}.png" for i in range(n)]
    if all(p.exists() for p in paths):
        return
    d.mkdir(parents=True, exist_ok=True)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    rng = np.random.default_rng(1871)
    for p in paths:
        v = rng.standard_normal((size, size))
        la = np.empty((size, size, 2), np.uint8)
        la[..., 0] = np.where(v > 0, 255, 0)
        la[..., 1] = np.clip(np.abs(v) * 0.25 * 255, 0, 255).astype(np.uint8)
        raw = b"".join(b"\x00" + la[y].tobytes() for y in range(size))
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 4, 0, 0, 0))
                      + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def sound_opts(v):
    """Miks ayarları: ElevenLabs müzik/efekt kütüphanesi (config "sounds"), kategoriye göre müzik."""
    from audio_fx import mood_for
    return {"lufs": CONFIG.get("loudness_lufs", -14.0), "mood": mood_for(tr_upper(v.get("category", "GÜNDEM"))),
            "library": CONFIG.get("sounds", "elevenlabs") == "elevenlabs",
            "library_music_db": CONFIG.get("library_music_db", -3.0)}


def map3d_ok(video, scenes):
    """3D harita gerçekten çizildi mi? İğne indikten sonraki karenin orta bandına bakar: 3D sahnede
    ~120 parlaklık, en koyu normal sahnede ~30; çizim başarısızsa koyu zemin (~10) kalır."""
    for s in scenes:
        if not s.get("map"):
            continue
        a, b = round(s["start"] * FPS), round(s["end"] * FPS)
        flight = int(min(90, max(45, (b - a) * 0.45)) + 0.5)  # Map3D.tsx map3dTiming ile aynı
        f = min(b - 3, a + flight - 14 + 6 + 15)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                              f"select=eq(n\\,{f}),scale=108:192,format=gray", "-frames:v", "1",
                              "-f", "rawvideo", "-"], capture_output=True).stdout
        if len(raw) != 108 * 192:
            return False
        if np.frombuffer(raw, np.uint8).reshape(192, 108)[57:119].mean() < 45:
            return False
    return True


def build_video(tts, day, n, total, v, out_dir):
    sr = tts.sr
    gap_sentence = np.zeros(int(0.16 * sr), dtype=np.int16)
    gap_scene = np.zeros(int(0.42 * sr), dtype=np.int16)
    track = [np.zeros(int(0.08 * sr), dtype=np.int16)]  # ilk karede söz başlasın (kaydırılmayı önler)
    pos = track[0].size
    scenes = []
    template = os.environ.get("GUNDEM_TEMPLATE") or CONFIG.get("template", "v1")
    script_scenes = list(v["scenes"])
    if template == "v2" and CONFIG.get("outro_text"):  # her videonun sonunda "abone ol" kapanışı
        script_scenes.append({"heading": "", "text": CONFIG["outro_text"],
                              "say": CONFIG.get("outro_say") or CONFIG["outro_text"], "subscribe": True})
    spent0 = getattr(tts, "spent", None)  # ElevenLabs: bu videonun kredisi [ok] satırında yazılır
    plan = []  # sahne başına (ekranda görünen cümleler, okunacak cümleler)
    for sc in script_scenes:
        shown = sentences(sc["text"])
        spoken = sentences(sc.get("say") or sc["text"])
        if len(spoken) != len(shown):  # hizalanamıyorsa tek blok olarak ele al
            shown, spoken = [sc["text"]], [sc.get("say") or sc["text"]]
        plan.append((shown, [okunus(s) for s in spoken]))
    said = [s for _, spoken in plan for s in spoken]  # bağlam: önceki/sonraki cümle (ElevenLabs)
    k = 0
    sents = []  # her cümle: sahnesi, sesteki başı/sonu, ekranda görünen metni
    for si, (sc, (shown, spoken)) in enumerate(zip(script_scenes, plan)):
        start = pos / sr
        for shown_s, spoken_s in zip(shown, spoken):
            a = trim(tts.synth(spoken_s, said[k - 1] if k else None, said[k + 1] if k + 1 < len(said) else None), sr)
            k += 1
            sents.append({"scene": si, "t0": pos / sr, "t1": (pos + a.size) / sr, "text": shown_s})
            track += [a, gap_sentence]
            pos += a.size + gap_sentence.size
        track.append(gap_scene)
        pos += gap_scene.size
        scene = {"heading": sc.get("heading", ""), "start": round(start, 3),
                 "end": round(pos / sr, 3), "chunks": []}
        for key in ("stat", "icon", "map", "chart", "points", "subscribe"):  # v2 görsel alanları
            if sc.get(key):
                scene[key] = sc[key]
        scenes.append(scene)
    track.append(np.zeros(int(0.5 * sr), dtype=np.int16))
    audio = np.concatenate(track)
    duration = audio.size / sr

    # Altyazı: her kelime sesteki gerçek anında vurgulanır (align.py, faster-whisper). Hizalama
    # yapılamazsa ya da bir cümlede zayıf kalırsa o cümle eski yöntemle (harf sayısına göre) zamanlanır.
    aligned, cap_label = [None] * len(sents), "oransal"
    if CONFIG.get("word_align", True):
        try:
            from align import align_words
            aligned = align_words(audio, sr, sents)
            cap_label = f"kelime hizalı {sum(1 for x in aligned if x)}/{len(sents)} cümle"
        except Exception as e:
            print(f"[bilgi] Kelime hizalama yapılamadı ({str(e)[-160:]}); altyazılar oransal zamanlanıyor. "
                  "Bu bir hata değil.", flush=True)
    for s, times in zip(sents, aligned):
        words = s["text"].split()
        if not times or len(times) != len(words):
            w8 = [len(w) + 1 for w in words]
            times = [round(s["t0"] + (s["t1"] - s["t0"]) * sum(w8[:i]) / sum(w8), 3) for i in range(len(words))]
        new, i = [], 0
        for part in chunk_words(s["text"]):
            cnt = len(part.split())  # (n değil: n bu fonksiyonda videonun sıra numarası)
            new.append({"text": part, "start": times[i], "words": times[i:i + cnt]})
            i += cnt
        if not new:  # ekranda metni olmayan cümle
            continue
        for c, nxt in zip(new, new[1:]):
            c["end"] = nxt["start"]
        new[-1]["end"] = round(s["t1"], 3)
        scenes[s["scene"]]["chunks"] += new
    for scene in scenes:  # altyazı bir sonraki parça başlayana (son parçada sahne bitene) kadar kalır
        ch = scene["chunks"]
        for c, nxt in zip(ch, ch[1:]):
            c["until"] = nxt["start"]
        if ch:
            ch[-1]["until"] = scene["end"]

    slug = v["slug"]
    pub = VIDEO / "public" / day
    pub.mkdir(parents=True, exist_ok=True)
    credits = []
    if template == "v2":  # Wikimedia Commons fotoğrafları (lisanslı, atıflı)
        for i, (sc, scene) in enumerate(zip(v["scenes"], scenes)):
            spec = sc.get("photo")
            if not spec:
                continue
            try:
                from photos import fetch
                c = fetch(spec, pub / f"{slug}-p{i}.jpg")
            except Exception as e:
                print(f"[bilgi] Fotoğraf alınamadı ({str(e)[:100]}); sahne diğer görselle devam ediyor.",
                      flush=True)
                c = None
            if c:
                scene["photo"] = {"src": f"{day}/{slug}-p{i}.jpg", "credit": c["credit"]}
                credits.append({k: c[k] for k in ("title", "artist", "license", "license_url", "page")})
                print(f"[bilgi] Fotoğraf: {c['title']} ({c['license']})", flush=True)
    # Ses: seslendirme + görsel olaylara bağlı efektler + müzik, -14 LUFS'ye ayarlı miks (audio_fx.py)
    final, mix_label = audio, "yalnız ses"
    if template == "v2" and CONFIG.get("music", True):
        try:
            from audio_fx import cues_for, mix_to_file
            cues = cues_for(scenes, FPS, map3d=bool(CONFIG.get("map3d", True)))
            minfo = {}
            lufs, tp = mix_to_file(audio, sr, cues, slug, pub / f"{slug}.wav", info=minfo, **sound_opts(v))
            final = None
            mix_label = (f"{len(cues)} efekt ({minfo.get('sfx')}) + müzik ({minfo.get('music')})"
                         + (f", {lufs:.1f} LUFS / tepe {tp:.1f} dBTP" if lufs else ""))
        except Exception as e:
            print(f"[bilgi] Gelişmiş ses miksi yapılamadı ({str(e)[-200:]}); basit miksle devam ediliyor. "
                  "Bu bir hata değil.", flush=True)
            from audio_fx import mix_simple
            final, mix_label = mix_simple(audio, sr, [s["start"] for s in scenes], seed=slug), "basit miks (yedek)"
    if final is not None:
        with wave.open(str(pub / f"{slug}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(final.tobytes())

    # Kare başına ses seviyesi (görsel ses çubukları için)
    hop = sr / FPS
    nframes = int(np.ceil(duration * FPS))
    f = audio.astype(np.float32) / 32768
    rms = np.array([np.sqrt(np.mean(f[int(i * hop): int((i + 1) * hop)] ** 2) + 1e-9)
                    for i in range(nframes)])
    levels = np.clip(rms / (np.percentile(rms, 97) + 1e-6), 0, 1)

    y, m, d = day.split("-")
    cat = tr_upper(v.get("category", "GÜNDEM"))
    props = {
        "brand": CONFIG["brand"], "date": f"{int(d)} {MONTHS[int(m) - 1]} {y}",
        "index": n, "total": total, "category": cat,
        "accent": v.get("accent") or ACCENTS.get(cat, "#facc15"),
        "title": v["title"], "audio": f"{day}/{slug}.wav",
        "duration": round(duration, 3),
        "levels": [round(float(x), 3) for x in levels], "scenes": scenes,
    }
    if template == "v2":
        props["categoryIcon"] = v.get("category_icon") or CATEGORY_ICONS.get(cat, "newspaper")
        props["channelName"] = CONFIG.get("channel_name", "")
        props["channelTagline"] = CONFIG.get("channel_tagline", "")
        props["grain"] = float(CONFIG.get("grain", 0.025) or 0)
        props["map3d"] = bool(CONFIG.get("map3d", True))  # false: eski 2D harita kartı
        if props["grain"]:
            ensure_grain()
        props.pop("levels")
    props_file = pub / f"{slug}.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    out = out_dir / f"{n}-{slug}.mp4"
    comp = "ShortV2" if template == "v2" else "Short"
    if template == "v2" and not (VIDEO / "node_modules" / "@remotion" / "three").exists():
        # şablon 3D harita paketlerini içe aktarıyor; eski kurulumda yoksa paketleme başarısız olur
        print("[bilgi] 3D paketleri eksik; npm ci ile kuruluyor.", flush=True)
        subprocess.run(["npm", "ci", "--silent", "--no-audit", "--no-fund"], cwd=VIDEO, check=False)
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out),
           f"--props={props_file}", "--codec=h264", "--crf=22", "--log=error",
           f"--concurrency={CONFIG.get('concurrency', 4)}"]
    chrome = chrome_path()
    if chrome:
        cmd.append(f"--browser-executable={chrome}")
    subprocess.run(cmd, cwd=VIDEO, check=True)
    map_label = ""
    if template == "v2" and any(s.get("map") for s in scenes):
        map_label = " · harita: 3D" if props.get("map3d") else " · harita: 2D"
        if props.get("map3d") and not map3d_ok(out, scenes):
            # 3D çizilemediyse (ör. bu makinede WebGL yok) kara kare yayınlanmasın: 2D haritayla yeniden üret
            print("[bilgi] 3D harita bu makinede çizilemedi; video 2D haritayla yeniden üretiliyor. "
                  "Bu bir hata değil.", flush=True)
            props["map3d"] = False
            if final is None:  # gelişmiş miks yapıldıysa iğne sesini 2D zamanlamasına göre yeniden miksle
                try:
                    from audio_fx import cues_for, mix_to_file
                    mix_to_file(audio, sr, cues_for(scenes, FPS, map3d=False), slug, pub / f"{slug}.wav",
                                **sound_opts(v))
                except Exception as e:
                    print(f"[bilgi] Ses 2D haritaya göre yeniden mikslenemedi ({str(e)[-120:]}); "
                          "ilk miks kullanılıyor.", flush=True)
            props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
            subprocess.run(cmd, cwd=VIDEO, check=True)
            map_label = " · harita: 2D (yedek)"
    cred_file = out.with_suffix(".credits.json")
    if credits:
        cred_file.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    elif cred_file.exists():
        cred_file.unlink()
    voice_label = getattr(tts, "label", type(tts).__name__)
    if spent0 is not None:
        voice_label += f", {tts.spent - spent0} kredi"
    print(f"[ok] {out.relative_to(ROOT)}  {duration:.1f} sn · ses: {voice_label} · "
          f"fotoğraf: {len(credits)} · miks: {mix_label} · altyazı: {cap_label}{map_label}", flush=True)
    if duration > 175:
        print(f"[uyarı] {slug}: {duration:.0f} sn — Shorts sınırı 180 sn", flush=True)
    yt = " ".join(re.sub(r"#shorts\b", "", v.get("yt_title", ""), flags=re.I).split())
    if len(yt) > 60:  # mobilde ~40, masaüstü aramada 60 karakter görünür
        print(f"[uyarı] {slug}: yt_title {len(yt)} karakter; en fazla 60 olsun, konu ilk 40 karakterde. "
              "Yalnızca senaryodaki yt_title'ı kısalt, video yeniden üretilmez.", flush=True)
    return out


def main():
    script = Path(sys.argv[1])
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    data = json.loads(script.read_text(encoding="utf-8"))
    day = data["date"]
    out_dir = ROOT / "out" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = os.environ.get("GUNDEM_TTS") or CONFIG.get("tts", "google")  # GUNDEM_TTS=piper ile test
    chain = [engine] + [e for e in CONFIG.get("tts_fallback", ["chatterbox", "piper"]) if e != engine]
    if "piper" not in chain:
        chain.append("piper")  # son çare: çevrimdışı ses her makinede açılır

    def next_tts():
        while chain:
            t = open_tts(chain.pop(0))
            if t:
                print(f"[bilgi] Seslendirme motoru: {getattr(t, 'label', type(t).__name__)}", flush=True)
                return t
        raise RuntimeError("Hiçbir ses motoru açılamadı (önce: bash setup.sh)")

    tts = next_tts()
    vids = data["videos"]
    for n, v in enumerate(vids, 1):
        if only and n not in only:
            continue
        while True:
            try:
                build_video(tts, day, n, len(vids), v, out_dir)
                break
            except TTSUnavailable as e:
                print(f"[bilgi] {getattr(tts, 'label', type(tts).__name__)} bu videoda kullanılamadı "
                      f"({str(e)[:200]}); video yedek sesle baştan üretiliyor. Bu bir hata değil, işleme "
                      "devam et; raporda belirt.", flush=True)
                tts = next_tts()


def open_tts(engine):
    """Ses motorunu açar; açılamazsa None döner ve main() sıradaki motora geçer."""
    try:
        if engine == "elevenlabs":
            return ElevenLabsTTS()
        if engine == "chatterbox":
            return ChatterboxTTS()
        if engine == "google":
            t = GoogleTTS()
            t.synth("Merhaba.")  # anahtar/faturalandırma çalışıyor mu?
            return t
        if engine == "piper":
            return PiperTTS()
        print(f"[bilgi] Bilinmeyen ses motoru: {engine}", flush=True)
    except Exception as e:
        print(f"[bilgi] {engine} sesi kullanılamadı ({str(e)[:160]}); sıradaki sese geçiliyor. "
              "Bu bir hata değil, işleme devam et.", flush=True)
    return None


if __name__ == "__main__":
    main()
