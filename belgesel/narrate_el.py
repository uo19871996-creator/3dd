#!/usr/bin/env python3
"""Belgesel seslendirmesi: ElevenLabs ile her satır ayrı okunur, motorun anlatı biçimine yazılır.

Kullanım:  python3 belgesel/narrate_el.py --project PROJE [--model eleven_v4]
Sonra:     python3 belgesel/engine/build_narration.py --project PROJE

Okur:   PROJE/script.json   (takes -> lines: id, text, spoken, isteğe bağlı gap_after)
Yazar:  PROJE/audio/lines/segNN.wav, PROJE/audio/segments.json (split_takes.py ile aynı biçim)

Anlatım varsayılanda heyecanlı: her satıra "[excited]" duygu etiketi (satırda "tone" ile değişir:
"[dramatic]", "[tense]", "[whispers]"...; etiket okunmaz, tonu belirler) ve düşük kararlılık (0.3).
Kısa videolarla aynı ses (config.json: elevenlabs_voice) ve aynı okunuş sözlüğü (okunus.json,
"_elevenlabs" bölümü) kullanılır. Uzun videoda kalite daha çok fark edildiği için varsayılan model
config.json "belgesel_model" (yoksa eleven_v4). Önceki/sonraki satır bağlam olarak gider.
"""
import argparse
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import build  # noqa: E402  (ElevenLabsTTS, okunus, CONFIG)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--model", default=build.CONFIG.get("belgesel_model", "eleven_v4"))
    ap.add_argument("--gap", type=float, default=0.3, help="satırdan sonra sessizlik (sn); kısa = daha tempolu")
    ap.add_argument("--take-gap", type=float, default=0.7, help="bölümün son satırından sonra sessizlik (sn)")
    ap.add_argument("--tone", default=build.CONFIG.get("belgesel_tone", "[excited]"),
                    help="her satırın başına eklenen duygu etiketi (eleven_v4); satırda \"tone\" varsa o kullanılır")
    ap.add_argument("--stability", type=float, default=build.CONFIG.get("belgesel_stability", 0.3),
                    help="düşük = daha canlı, değişken anlatım (0.3); yüksek = düz, sakin (0.5+)")
    a = ap.parse_args()
    proj = Path(a.project)
    script = json.loads((proj / "script.json").read_text(encoding="utf-8"))
    build.CONFIG["elevenlabs_model"] = a.model
    build.CONFIG["elevenlabs_settings"] = {**build.CONFIG.get("elevenlabs_settings", {}), "stability": a.stability}
    tts = build.ElevenLabsTTS()
    lines = [(take, ln, li == len(take["lines"]) - 1) for take in script["takes"]
             for li, ln in enumerate(take["lines"])]
    said = [build.okunus(ln["spoken"], tts.dictionary) for _, ln, _ in lines]
    out = proj / "audio" / "lines"
    out.mkdir(parents=True, exist_ok=True)
    segments = []
    for k, (take, ln, last) in enumerate(lines):
        tone = ln.get("tone", a.tone) if a.model.startswith("eleven_v") else ""   # etiket yalnız v3/v4'te
        pcm = tts.synth((tone + " " if tone else "") + said[k], said[k - 1] if k else None,
                        said[k + 1] if k + 1 < len(said) else None)
        with wave.open(str(out / f"seg{ln['id']:02d}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(tts.sr)
            w.writeframes(pcm.tobytes())
        segments.append({"id": ln["id"], "scene": take["take"], "caption": ln["text"], "vo": ln["spoken"],
                         "gap_after": ln.get("gap_after", a.take_gap if last else a.gap)})
        print(f"  {ln['id']:2d}  {len(pcm) / tts.sr:5.1f} sn  {ln['text'][:70]}", flush=True)
    (proj / "audio" / "segments.json").write_text(json.dumps({"segments": segments}, ensure_ascii=False, indent=1))
    print(f"[ok] {len(segments)} satır · {tts.label}, {tts.spent} kredi -> {proj / 'audio' / 'segments.json'}")


if __name__ == "__main__":
    main()
