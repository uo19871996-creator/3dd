#!/usr/bin/env python3
"""Günlük senaryo dosyasından (scripts/TARIH.json) Shorts videoları üretir.

Kullanım:  python3 pipeline/build.py scripts/2026-11-11.json [--only 1,3]

Her video için: Türkçe seslendirme -> altyazı zamanlaması ->
Remotion ile 1080x1920 MP4 (out/TARIH/N-slug.mp4).

Seslendirme motoru config.json içindeki "tts" ile seçilir:
  "piper"  : çevrimdışı, ücretsiz (tr_TR-dfki sesi; lisansı CC BY-NC-SA, ticari değil)
  "google" : Google Cloud Text-to-Speech (resmi API, ticari kullanım serbest)
"""
import base64
import glob
import io
import json
import os
import re
import subprocess
import sys
import wave
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
        # Model önceden indirildiyse (setup.sh) hub'a sorgu atma: açılış dakikalardan saniyelere iner
        hub = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
        if glob.glob(str(hub / "models--ResembleAI--chatterbox" / "snapshots" / "*" / "t3_mtl*.safetensors")):
            env["HF_HUB_OFFLINE"] = "1"
        try:  # kanal sahibinin şifreli ses örneği (assets/ses-ornegi.wav.enc) varsa onun sesiyle konuş
            from voice import decrypt_to
            sample = decrypt_to(ROOT / "out" / ".tts" / "ses-ornegi.wav")
            if sample:
                env["CBX_VOICE_SAMPLE"] = str(sample)
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

    def synth(self, text):
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

    def synth(self, text):
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

    def synth(self, text):
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


def chrome_path():
    """Önceden kurulu headless Chrome'u bulur (sürüm numarası imaja göre değişebilir)."""
    if CONFIG.get("chrome"):
        return CONFIG["chrome"]
    hits = sorted(glob.glob(
        "/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    return hits[-1] if hits else None


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


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


def build_video(tts, day, n, total, v, out_dir):
    sr = tts.sr
    gap_sentence = np.zeros(int(0.16 * sr), dtype=np.int16)
    gap_scene = np.zeros(int(0.42 * sr), dtype=np.int16)
    track = [np.zeros(int(0.25 * sr), dtype=np.int16)]
    pos = track[0].size
    scenes = []
    for sc in v["scenes"]:
        shown = sentences(sc["text"])
        spoken = sentences(sc.get("say") or sc["text"])
        if len(spoken) != len(shown):  # hizalanamıyorsa tek blok olarak ele al
            shown, spoken = [sc["text"]], [sc.get("say") or sc["text"]]
        start = pos / sr
        chunks = []
        for shown_s, spoken_s in zip(shown, spoken):
            a = trim(tts.synth(spoken_s), sr)
            parts = chunk_words(shown_s)
            weights = [len(p) + 2 for p in parts]
            t0, dur = pos / sr, a.size / sr
            acc = 0
            for p, w in zip(parts, weights):
                c0 = t0 + dur * acc / sum(weights)
                acc += w
                c1 = t0 + dur * acc / sum(weights)
                chunks.append({"text": p, "start": round(c0, 3), "end": round(c1, 3)})
            track += [a, gap_sentence]
            pos += a.size + gap_sentence.size
        track.append(gap_scene)
        pos += gap_scene.size
        # Altyazı, bir sonraki parça başlayana (son parçada sahne bitene) kadar ekranda kalır
        for c, nxt in zip(chunks, chunks[1:]):
            c["until"] = nxt["start"]
        chunks[-1]["until"] = round(pos / sr, 3)
        scene = {"heading": sc.get("heading", ""), "start": round(start, 3),
                 "end": round(pos / sr, 3), "chunks": chunks}
        for key in ("stat", "icon", "map", "chart", "points"):  # v2 görsel alanları
            if sc.get(key):
                scene[key] = sc[key]
        scenes.append(scene)
    track.append(np.zeros(int(0.5 * sr), dtype=np.int16))
    audio = np.concatenate(track)
    duration = audio.size / sr

    slug = v["slug"]
    pub = VIDEO / "public" / day
    pub.mkdir(parents=True, exist_ok=True)
    template = os.environ.get("GUNDEM_TEMPLATE") or CONFIG.get("template", "v1")
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
    final = audio
    if template == "v2" and CONFIG.get("music", True):
        from audio_fx import mix
        last = len(scenes) - 1
        stat_times = [s["start"] + 0.25 for i, s in enumerate(scenes)
                      if 0 < i < last and s.get("stat") and not s.get("map") and not s.get("chart")]
        final = mix(audio, sr, [s["start"] for s in scenes], stat_times, seed=slug)
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
        props.pop("levels")
    props_file = pub / f"{slug}.json"
    props_file.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    out = out_dir / f"{n}-{slug}.mp4"
    comp = "ShortV2" if template == "v2" else "Short"
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out),
           f"--props={props_file}", "--codec=h264", "--crf=22", "--log=error",
           f"--concurrency={CONFIG.get('concurrency', 4)}"]
    chrome = chrome_path()
    if chrome:
        cmd.append(f"--browser-executable={chrome}")
    subprocess.run(cmd, cwd=VIDEO, check=True)
    cred_file = out.with_suffix(".credits.json")
    if credits:
        cred_file.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    elif cred_file.exists():
        cred_file.unlink()
    print(f"[ok] {out.relative_to(ROOT)}  {duration:.1f} sn", flush=True)
    if duration > 175:
        print(f"[uyarı] {slug}: {duration:.0f} sn — Shorts sınırı 180 sn", flush=True)
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
    tts = None
    if engine == "chatterbox":
        try:
            tts = ChatterboxTTS()
        except Exception as e:
            print(f"[bilgi] Chatterbox sesi kullanılamadı ({str(e)[:120]}); ücretsiz Piper sesine geçildi. "
                  "Bu bir hata değil, işleme devam et.", flush=True)
            tts = None
    if engine == "google":
        try:
            tts = GoogleTTS()
            tts.synth("Merhaba.")  # anahtar/faturalandırma çalışıyor mu?
        except Exception as e:
            print(f"[bilgi] Google sesi kullanılamadı ({str(e)[:80]}...); ücretsiz sese geçildi. "
                  "Bu bir hata değil, işleme devam et.", flush=True)
            tts = None
    if tts is None:
        tts = PiperTTS()
    print(f"[bilgi] Seslendirme motoru: {type(tts).__name__}", flush=True)
    vids = data["videos"]
    for n, v in enumerate(vids, 1):
        if only and n not in only:
            continue
        build_video(tts, day, n, len(vids), v, out_dir)


if __name__ == "__main__":
    main()
