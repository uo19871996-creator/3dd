#!/usr/bin/env python3
"""ElevenLabs ile ses efekti ve müzik kütüphanesi üretir (bir kez; dosyalar depoya girer).

Kullanım:  python3 pipeline/el_sounds.py               # eksik dosyaları üretir
           python3 pipeline/el_sounds.py --only music  # yalnız müzik (ya da: sfx)
           python3 pipeline/el_sounds.py --force       # hepsini yeniden üretir

Videolar bu dosyaları audio_fx.py üzerinden kullanır: video üretilirken ElevenLabs'e istek atılmaz,
video başına ek kredi harcanmaz. Kütüphane yoksa audio_fx.py eski sentez seslere döner.

Anahtar: ElevenLabs SDK'sı ELEVENLABS_API_KEY'i ortamdan okur. Bu bulut ortamında anahtar ağ kimliği
olarak kayıtlıdır ve vekil sunucu her isteğe kendisi ekler; değişken yoksa yer tutucu konur (gerçek
anahtar ne kodda ne depoda durur).

Maliyet (ElevenLabs fiyat sayfası, Kasım 2026): müzik dakikası 900 kredi, efekt üretimi en çok 200
kredi. Varsayılan kütüphane: 8 parça x 60 sn müzik (~7.200 kredi) + 16 efekt.
Lisans: ücretli planda (Creator) üretilen müzik ve efektler ticari kullanıma açıktır.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "assets" / "sounds"
SFX_MODEL = "eleven_text_to_sound_v3"
MUSIC_MODEL = "music_v2_5"

# Efektler: audio_fx.SOUNDS ile aynı adlar (görsel olaylara bağlı ipuçları bu adları kullanır).
SFX = {
    "whoosh": ("Fast clean whoosh transition for a modern news video, airy swoosh passing from left to "
               "right, dry, no reverb tail", 0.8),
    "pop": ("Short soft pop for a graphic element appearing on screen, clean modern interface bubble pop, "
            "dry", 0.5),
    "stamp": ("Heavy rubber stamp slammed onto paper on a wooden desk, punchy dry thud, close mic", 0.6),
    "impact": ("Deep cinematic impact boom for a news intro, short low-end hit with a quick decay, "
               "no music", 1.5),
    "ticks": ("Fast mechanical number counter ticking that gradually slows down and stops, small dry "
              "clicks", 1.2),
    "click": ("Single camera shutter click, modern digital camera, dry, close", 0.5),
    "riser": ("Short whoosh riser building tension, rising noise sweep that ends abruptly at its peak", 1.2),
    "shimmer": ("Bright subtle sparkle shimmer, light glittering chimes, short and clean", 1.2),
}
SFX_VARIANTS = 2

# Müzik: haber kategorisine göre ruh hali (audio_fx.MOODS). Hepsi sözsüz, konuşmanın altında kalacak
# sabit enerjide; sanatçı ya da şarkı adı geçmez.
_UNDER = ("Consistent energy from start to end, no big build-ups or drops, no vocals. "
          "Mixed to sit under a voice-over.")
MUSIC = {
    "haber": [
        "Modern news background music for a short vertical news video. Steady mid-tempo pulse around "
        "100 BPM, soft analog synth bass, light electronic percussion, subtle piano motif. Neutral, "
        "informative and confident. " + _UNDER,
        "Contemporary newsroom underscore at 96 BPM, plucked synth arpeggio, warm pads, tight minimal "
        "drums. Neutral and focused. " + _UNDER,
    ],
    "gergin": [
        "Serious investigative news underscore with restrained tension, low staccato strings and a soft "
        "pulsing synth, 90 BPM, minor key, dark but not horror. " + _UNDER,
        "Tense political news background, deep sub pulse, ticking hi-hats, low piano notes in a minor key, "
        "92 BPM, serious and suspenseful. " + _UNDER,
    ],
    "enerjik": [
        "Energetic sports highlight background music, driving drums and palm-muted electric guitar, "
        "120 BPM, upbeat and motivating, no crowd noise. " + _UNDER,
        "Upbeat sports news music, punchy electronic drums, energetic synth bass, bright stabs, 124 BPM, "
        "exciting and positive. " + _UNDER,
    ],
    "modern": [
        "Light modern tech background music, bright plucks and a soft electronic beat, 105 BPM, "
        "optimistic, clean and minimal. " + _UNDER,
        "Warm lifestyle and culture background music, soft acoustic guitar with a light electronic beat "
        "and gentle claps, 100 BPM, positive and friendly. " + _UNDER,
    ],
}
MUSIC_MS = 60000


def client():
    from elevenlabs import ElevenLabs
    # Bu ortamda gerçek anahtarı vekil sunucu ekler; SDK değişken ister, yer tutucu yeterli.
    os.environ.setdefault("ELEVENLABS_API_KEY", "proxy-injected")
    return ElevenLabs()


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True).stdout.strip()
    return round(float(out), 2) if out else None


def save(stream, path):
    tmp = path.with_suffix(path.suffix + ".part")
    with open(tmp, "wb") as f:
        for chunk in stream:
            f.write(chunk)
    tmp.replace(path)


def with_retry(fn, what):
    for attempt in range(4):
        try:
            return fn()
        except Exception as e:  # 429 / ağ hatası: bekle, tekrar dene; içerik hatası: bildir
            msg = str(e)
            if attempt == 3 or not any(s in msg for s in ("429", "500", "502", "503", "timed out", "Connection")):
                raise RuntimeError(f"{what}: {msg[:300]}") from e
            time.sleep(5 * 2 ** attempt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=["sfx", "music"])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    el = client()
    man_path = LIB / "manifest.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {"files": {}}
    manifest["note"] = ("ElevenLabs ile üretildi (Creator planı, ticari kullanım serbest). "
                        "Yeniden üretmek için: python3 pipeline/el_sounds.py --force")
    jobs = []
    if args.only in (None, "sfx"):
        for name, (prompt, dur) in SFX.items():
            for k in range(1, SFX_VARIANTS + 1):
                jobs.append(("sfx", f"sfx/{name}-{k}.wav", prompt, dur))
    if args.only in (None, "music"):
        for mood, prompts in MUSIC.items():
            for k, prompt in enumerate(prompts, 1):
                jobs.append(("music", f"music/{mood}-{k}.mp3", prompt, MUSIC_MS / 1000))
    made = 0
    for kind, rel, prompt, dur in jobs:
        path = LIB / rel
        if path.exists() and not args.force:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        if kind == "sfx":
            with_retry(lambda: save(el.text_to_sound_effects.convert(
                text=prompt, model_id=SFX_MODEL, duration_seconds=dur, prompt_influence=0.7,
                output_format="wav_48000"), path), rel)
            model = SFX_MODEL
        else:
            with_retry(lambda: save(el.music.compose(
                prompt=prompt, music_length_ms=int(dur * 1000), model_id=MUSIC_MODEL,
                force_instrumental=True, output_format="mp3_48000_192"), path), rel)
            model = MUSIC_MODEL
        manifest["files"][rel] = {"kind": kind, "model": model, "prompt": prompt,
                                  "seconds": duration(path), "created": time.strftime("%Y-%m-%d")}
        made += 1
        print(f"[ok] {rel}  {manifest['files'][rel]['seconds']} sn  ({time.time() - t0:.0f} sn sürdü)", flush=True)
        man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[ok] {made} dosya üretildi; kütüphane: {LIB.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
