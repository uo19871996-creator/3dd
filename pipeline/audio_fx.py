"""Arka plan müziği, ses efektleri ve son miks: hepsi burada sentezlenir (telif yok).

mix_to_file(voice, sr, cues, seed, out_path)  -> profesyonel miks (ffmpeg):
  - Ses: alçak frekans temizliği, de-esser, hafif kompresör (cümleler arası seviye eşitlenir).
  - Müzik: 96 BPM yumuşak yatak; seslendirme konuşurken sidechain ile kısılır, 2,4 kHz'de
    sesin "varlık" bandı müzikten açılır.
  - Efektler: görsel olaylara bağlı (cues_for): whoosh, pop, damga, sayaç tıkırtısı, deklanşör,
    riser, impact, ışıltı.
  - İki geçiş: karışım ölçülür, tek kazançla -14 LUFS'ye (YouTube'un referansı) çekilir, tepeler
    limitleyiciyle -2 dBFS'de tutulur.
  - Seviyeler ölçülerek ayarlandı: efektler konuşmanın ~7-11 dB, müzik ~15 dB altında.
mix_simple(...) -> eski numpy karıştırıcı; ffmpeg miksi başarısız olursa yedek.

Efekt sentezi Moh4696/cinematic-skill'in build_sfx.py dosyasından uyarlanmıştır (MIT lisansı).
"""
import hashlib
import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 48000
BLOCK = 4096
HOP = BLOCK // 2

PROGRESSIONS = [  # (kök MIDI notası, minör mü)
    [(57, True), (53, False), (48, False), (55, False)],  # Am F C G
    [(50, True), (46, False), (53, False), (48, False)],  # Dm Bb F C
    [(52, True), (48, False), (55, False), (50, False)],  # Em C G D
]


def _hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _seed_of(seed):
    return int(hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8], 16)


# ------------------------------------------------------------------ müzik yatağı
def _music(dur, sr, rng, prog):
    n = int(dur * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    beat = 60 / 96
    bar = beat * 4
    nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        root, minor = prog[b % len(prog)]
        tones = [0, 3 if minor else 4, 7]
        b0 = b * bar
        # Pad (akor, dedüne sinüsler, yumuşak giriş/çıkış)
        s0, s1 = int(b0 * sr), min(n, int((b0 + bar + 0.6) * sr))
        if s0 >= n:
            break
        tt = t[s0:s1] - b0
        env = np.clip(tt / 0.5, 0, 1) * np.clip((bar + 0.6 - tt) / 0.6, 0, 1)
        for k in tones:
            f = _hz(root + 12 + k)
            for det, amp in ((1.0, 0.5), (1.004, 0.25), (0.996, 0.25)):
                out[s0:s1] += 0.05 * amp * env * np.sin(2 * np.pi * f * det * tt)
            out[s0:s1] += 0.012 * env * np.sin(2 * np.pi * 2 * f * tt)
        # Arpej (8'lik pluck notaları)
        seq = [0, 1, 2, 1, 2, 0, 1, 2]
        for j, idx in enumerate(seq):
            st = b0 + j * beat / 2
            a, z = int(st * sr), min(n, int((st + 0.45) * sr))
            if a >= n:
                break
            u = t[a:z] - st
            f = _hz(root + 24 + tones[idx])
            out[a:z] += 0.06 * np.exp(-u / 0.12) * (np.sin(2 * np.pi * f * u) + 0.2 * np.sin(4 * np.pi * f * u))
        # Bas + kick (1. ve 3. vuruş) ve hi-hat (ara 8'likler)
        for j in (0, 2):
            st = b0 + j * beat
            a, z = int(st * sr), min(n, int((st + 0.5) * sr))
            if a >= n:
                continue
            u = t[a:z] - st
            out[a:z] += 0.10 * np.exp(-u / 0.35) * np.sin(2 * np.pi * _hz(root - 12) * u)
            fk = 45 + 65 * np.exp(-u / 0.03)
            out[a:z] += 0.12 * np.exp(-u / 0.16) * np.sin(2 * np.pi * np.cumsum(fk) / sr)
        for j in range(4):
            st = b0 + j * beat + beat / 2
            a, z = int(st * sr), min(n, int((st + 0.06) * sr))
            if a >= n:
                continue
            u = t[a:z] - st
            noise = rng.standard_normal(z - a)
            out[a:z] += 0.018 * np.exp(-u / 0.02) * (noise - np.convolve(noise, np.ones(4) / 4, "same"))
    fade = np.clip(t / 0.6, 0, 1) * np.clip((dur - t) / 1.2, 0, 1)
    return out * fade


# ------------------------------------------------------------------ efekt sentezi (cinematic-skill, MIT)
def _n(sec):
    return int(sec * SR)


def _envelope(points, n):
    return np.interp(np.linspace(0.0, 1.0, n), [p[0] for p in points], [p[1] for p in points])


def _sweep(a, b, n, curve=1.0):
    return a + (b - a) * np.linspace(0.0, 1.0, n) ** curve


def _band_mask(freqs, lo, hi, tilt):
    mask = np.zeros_like(freqs)
    mask[(freqs >= lo) & (freqs <= hi)] = 1.0
    lower = (freqs < lo) & (freqs > lo / 2)
    if lower.any():
        mask[lower] = 0.5 - 0.5 * np.cos(np.pi * (freqs[lower] - lo / 2) / (lo / 2))
    upper = (freqs > hi) & (freqs < hi * 2)
    if upper.any():
        mask[upper] = 0.5 + 0.5 * np.cos(np.pi * (freqs[upper] - hi) / hi)
    if tilt:
        with np.errstate(divide="ignore"):
            mask *= np.where(freqs > 0, (np.maximum(freqs, 1.0) / 1000.0) ** tilt, 0.0)
    return mask


def _band_noise(n, lo, hi, amp, seed, tilt=0.0):
    """Zamanla kayabilen bir banda sıkıştırılmış gürültü (örtüşmeli spektral maskeleme)."""
    rng = np.random.default_rng(seed)
    source = rng.standard_normal(n + BLOCK)
    out = np.zeros(n + BLOCK)
    window = np.hanning(BLOCK)
    freqs = np.fft.rfftfreq(BLOCK, 1.0 / SR)
    lo_arr = np.full(n, lo, np.float64) if np.isscalar(lo) else np.asarray(lo, np.float64)
    hi_arr = np.full(n, hi, np.float64) if np.isscalar(hi) else np.asarray(hi, np.float64)
    for start in range(0, n, HOP):
        c = min(start + HOP, n - 1)
        spec = np.fft.rfft(source[start:start + BLOCK] * window)
        spec *= _band_mask(freqs, max(lo_arr[c], 1.0), max(hi_arr[c], 2.0), tilt)
        out[start:start + BLOCK] += np.fft.irfft(spec, BLOCK)
    out = out[:n]
    peak = np.max(np.abs(out))
    return (out / peak if peak > 0 else out) * amp


def _tone(n, freq, decay, partials=(1.0, 2.01, 3.03)):
    t = np.arange(n) / SR
    return sum((0.6 ** i) * np.sin(2 * np.pi * freq * r * t) for i, r in enumerate(partials)) * np.exp(-t / decay)


def _hit(n, lo, hi, decay, seed):
    # Kısa vuruşlar (deklanşör gibi) için gürültü uzun üretilip ortasından kesilir; yoksa pencere
    # kenarına denk gelip neredeyse sessiz kalıyorlar.
    m = max(n, 2 * BLOCK)
    seg = _band_noise(m, lo, hi, 1.0, seed=seed)[(m - n) // 2:(m - n) // 2 + n]
    return seg / (np.max(np.abs(seg)) or 1.0) * np.exp(-(np.arange(n) / SR) / decay)


def sfx_whoosh(seed):
    n = _n(.55)
    return _band_noise(n, _sweep(300, 1400, n), _sweep(1800, 6000, n),
                       _envelope([(0, 0), (.45, 1), (1, 0)], n) ** 1.5, seed=seed, tilt=-.4)


def sfx_pop(seed):
    n = _n(.18)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * _sweep(260, 150, n) * t) * np.exp(-t / .035) * .8 + _hit(n, 1200, 5000, .01, seed) * .25


def sfx_stamp(seed):
    n = _n(.4)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * _sweep(120, 55, n) * t) * np.exp(-t / .07) + _hit(n, 400, 3500, .025, seed) * .8


def sfx_impact(seed):
    n = _n(1.2)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * _sweep(90, 42, n, .6) * t) * np.exp(-t / .35)
            + _band_noise(n, 200, 2500, np.exp(-t / .12), seed=seed) * .35)


def sfx_ticks(seed, dur=1.1):
    """Yavaşlayarak duran sayaç tıkırtısı (sayı kartı sayarken)."""
    n = _n(dur + .1)
    out = np.zeros(n)
    rng = np.random.default_rng(seed)
    gaps = np.linspace(.035, .1, 22)
    gaps *= dur / max(np.sum(gaps), 1e-6)
    for at in np.cumsum(gaps):
        s = _n(at)
        if s >= n:
            break
        c = _tone(_n(.03), 2400 + rng.uniform(-150, 150), .004, (1.0, 2.3))
        out[s:s + len(c)] += c[: n - s]
    return out * .8


def sfx_click(seed):
    """Deklanşör: fotoğraf açılırken."""
    n = _n(.11)
    out = np.zeros(n)
    a = _hit(_n(.012), 2500, 9000, .0018, seed) + _tone(_n(.012), 3400, .0015, (1.0,)) * .4
    out[:len(a)] += a
    b = _hit(_n(.01), 2000, 7000, .0015, seed + 1) * .6
    out[_n(.075):_n(.075) + len(b)] += b
    return out


def sfx_riser(seed, dur=1.0):
    """Gürültü ve tonla yükselen geçiş; t + dur anında tepe yapar."""
    n = _n(dur)
    t = np.arange(n) / SR
    env = (t / dur) ** 2.4
    out = (_band_noise(n, _sweep(250, 1800, n), _sweep(1200, 9000, n), env, seed=seed) * .7
           + np.sin(2 * np.pi * np.cumsum(_sweep(70, 260, n, 1.4)) / SR) * env * .5)
    out[-_n(.02):] *= np.linspace(1, 0, _n(.02))
    return out


def sfx_shimmer(seed):
    n = _n(1.0)
    out = np.zeros(n)
    rng = np.random.default_rng(seed)
    for i in range(14):
        s = _n(i * .05 + rng.uniform(0, .02))
        c = _tone(_n(.12), rng.uniform(1600, 3400), .03, (1.0, 2.0))
        out[s:s + len(c)] += c[: n - s] * .5
    return out


SOUNDS = dict(whoosh=sfx_whoosh, pop=sfx_pop, stamp=sfx_stamp, impact=sfx_impact, ticks=sfx_ticks,
              click=sfx_click, riser=sfx_riser, shimmer=sfx_shimmer)


def _sfx_bed(cues, duration):
    n = int(duration * SR)
    buf = np.zeros((2, n))
    for i, c in enumerate(cues):
        fn = SOUNDS[c["type"]]
        sig = fn(100 + i, c["dur"]) if "dur" in c and c["type"] in ("ticks", "riser") else fn(100 + i)
        s = int(max(c["t"], 0) * SR)
        if s >= n or len(sig) == 0:
            continue
        sig = sig[: n - s].copy()
        a, b = min(_n(.002), len(sig) // 2), min(_n(.02), len(sig) // 2)
        if a > 0:  # tıkırtısız giriş/çıkış; giriş kısa tutulur, yoksa vuruşların atağı kaybolur
            sig[:a] *= np.linspace(0, 1, a)
        if b > 0:
            sig[-b:] *= np.linspace(1, 0, b)
        pan = ((i * 37) % 11 - 5) / 20
        g = c.get("gain", 1.0)
        buf[0, s:s + len(sig)] += sig * g * np.sqrt((1.0 - pan) / 2.0) * np.sqrt(2.0)
        buf[1, s:s + len(sig)] += sig * g * np.sqrt((1.0 + pan) / 2.0) * np.sqrt(2.0)
    peak = np.max(np.abs(buf))
    if peak > 0.89:  # seviyeler cue kazançlarıyla sabit kalsın; yalnızca taşarsa kıs
        buf = buf / peak * 0.89
    return buf


# ------------------------------------------------------------------ görsel olaylardan efekt listesi
_COUNTABLE = re.compile(r"^([%$€₺]?)(\d+(?:,\d+)?)(\+| milyon| milyar| bin)?$")


def cues_for(scenes, fps=30):
    """Şablondaki (video/src/v2/ShortV2.tsx) zamanlamalarla eşleşen efekt listesi."""
    cues = []
    last = len(scenes) - 1 - (1 if scenes and scenes[-1].get("subscribe") else 0)
    for i, s in enumerate(scenes):
        st = round(s["start"] * fps) / fps  # şablon da sahneleri kareye yuvarlıyor
        dur_f = round(s["end"] * fps) - round(s["start"] * fps)
        if i == 0:
            cues += [dict(type="impact", t=0.0, gain=.2), dict(type="whoosh", t=0.0, gain=.15)]
            if s.get("photo"):
                cues.append(dict(type="click", t=.05, gain=.2))
            continue
        if s.get("subscribe"):
            # riser konuşmadan 0,12 sn önce biter: tepe noktası ilk heceyi maskelemesin
            cues += [dict(type="riser", t=max(0.0, st - 1.12), gain=.25, dur=1.0),
                     dict(type="pop", t=st + 6 / fps, gain=.42),  # düğme belirirken
                     dict(type="click", t=st + 30 / fps, gain=.35),
                     dict(type="shimmer", t=st + 31 / fps, gain=.18)]
            continue
        cues.append(dict(type="whoosh", t=st - .3, gain=.28))
        if i == last:  # soru kartı
            cues.append(dict(type="pop", t=st + 14 / fps, gain=.47))
            continue
        if s.get("photo"):
            cues.append(dict(type="click", t=st + .05, gain=.3))
            if s.get("stat"):
                cues.append(dict(type="stamp", t=st + 10 / fps, gain=.32))
        elif s.get("map"):
            zoom = min(75, max(30, dur_f * 0.4))
            cues.append(dict(type="pop", t=st + round(zoom * 0.6) / fps, gain=.5))
        elif s.get("chart"):
            n_items = min(5, len(s["chart"].get("items", [])))
            cues.append(dict(type="ticks", t=st + 8 / fps, gain=.16, dur=(30 + 6 * max(n_items - 1, 0)) / fps))
        elif s.get("stat"):
            cues.append(dict(type="stamp", t=st + 6 / fps, gain=.3))
            if _COUNTABLE.match(str(s["stat"].get("value", ""))):
                cues.append(dict(type="ticks", t=st + 6 / fps, gain=.16, dur=34 / fps))
        elif s.get("points"):
            pts = s["points"][:4]
            for k in range(len(pts)):
                cues.append(dict(type="pop", t=st + (6 + k * dur_f * 0.7 / max(1, len(s["points"]))) / fps, gain=.42))
        else:
            cues.append(dict(type="pop", t=st + .05, gain=.34))
    return cues


# ------------------------------------------------------------------ miks
def _write_wav(path, data, sr, channels):
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.T.reshape(-1).tobytes() if channels == 2 else pcm.tobytes())


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg miks hatası: {r.stderr.strip()[-300:]}")
    return r


def _measure(inputs, graph):
    """EBU R128 ölçümü: (integrated LUFS, true peak dBTP)."""
    r = _run(["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-y", *inputs, "-filter_complex",
              graph + ",loudnorm=print_format=json", "-f", "null", "-"])
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    return float(m["input_i"]), float(m["input_tp"])


# Ses cilası: 70 Hz altı uğultu kesilir, "s" sesleri yumuşatılır, cümleler arası seviye eşitlenir.
VOICE_CHAIN = ("aformat=sample_rates=48000:channel_layouts=mono,highpass=f=70,deesser=i=0.35,"
               "acompressor=threshold=0.1:ratio=2.5:attack=6:release=150:makeup=1.5,"
               "aformat=sample_rates=48000:channel_layouts=stereo")


def _graph(has_music, tap="mix", music_db=-7.0, sfx_db=-7.0):
    """Ses (0), efekt (1) ve müzik (2) girişlerinden filtre grafiği. tap: mix | voice | sfx | music."""
    g = (f"[0:a]{VOICE_CHAIN},asplit=2[v][vk];"
         f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=28,volume={sfx_db}dB[s];")
    buses = {"voice": "[v]", "sfx": "[s]"}
    if has_music:
        # Müzik: sesin varlık bandı (2,4 kHz) açılır, seslendirme konuşurken sidechain ile kısılır.
        g += (f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,equalizer=f=2400:t=q:w=1.1:g=-4,"
              f"volume={music_db}dB[m];"
              "[m][vk]sidechaincompress=threshold=0.025:ratio=4:attack=35:release=550:makeup=1:knee=4[md];")
        buses["music"] = "[md]"
    else:
        g += "[vk]anullsink;"
    keep = list(buses.values()) if tap == "mix" else [buses[tap]]
    g += "".join(f"{lab}anullsink;" for lab in buses.values() if lab not in keep)
    if len(keep) == 1:
        return g + keep[0] + "anull"
    n = len(keep)  # amix yerine amerge+pan: her ffmpeg sürümünde normalizasyonsuz düz toplama
    return (g + "".join(keep) + f"amerge=inputs={n},pan=stereo|c0=" + "+".join(f"c{2 * i}" for i in range(n))
            + "|c1=" + "+".join(f"c{2 * i + 1}" for i in range(n)))


def mix_to_file(voice, sr, cues, seed, out_path, lufs=-14.0, music=True, stems_dir=None):
    """Seslendirme + efekt + (isteğe bağlı) müzik -> out_path (48 kHz stereo WAV).

    Önce karışımın ses yüksekliği ölçülür, sonra tek bir kazançla hedefe (-14 LUFS) çekilip tepe
    noktaları limitleyiciyle -2 dBFS'de tutulur. Döner: (LUFS, true peak dBTP) ya da ölçülemezse None'lar."""
    dur = len(voice) / sr
    h = _seed_of(seed)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _write_wav(td / "voice.wav", voice.astype(np.float64) / 32768.0, sr, 1)
        _write_wav(td / "sfx.wav", _sfx_bed(cues, dur), SR, 2)
        inputs = ["-i", str(td / "voice.wav"), "-i", str(td / "sfx.wav")]
        if music:
            m = _music(dur, SR, np.random.default_rng(h), PROGRESSIONS[h % len(PROGRESSIONS)])
            rms = float(np.sqrt(np.mean(m ** 2))) or 1.0
            _write_wav(td / "music.wav", m * 0.1 / rms, SR, 1)  # -20 dBFS RMS
            inputs += ["-i", str(td / "music.wav")]
        pre, _ = _measure(inputs, _graph(music))
        gain = f",volume={max(-20.0, min(20.0, lufs - pre)):.2f}dB"
        _run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *inputs, "-filter_complex",
              _graph(music) + gain + ",alimiter=limit=0.8:level=disabled,aresample=48000",
              "-c:a", "pcm_s16le", str(out_path)])
        if stems_dir:  # ayar için: her kanal, son miksle aynı kazançla ayrı dosyaya
            Path(stems_dir).mkdir(parents=True, exist_ok=True)
            for tap in ("voice", "sfx") + (("music",) if music else ()):
                _run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *inputs, "-filter_complex",
                      _graph(music, tap) + gain, "-c:a", "pcm_s16le", str(Path(stems_dir) / f"{tap}.wav")])
    try:
        return _measure(["-i", str(out_path)], "[0:a]anull")
    except Exception:
        return None, None


# ------------------------------------------------------------------ yedek: eski basit numpy miksi
def _place(dst, clip, at, sr, gain):
    a = int(at * sr)
    if a < 0:
        clip, a = clip[-a:], 0
    z = min(len(dst), a + len(clip))
    if z > a:
        dst[a:z] += gain * clip[: z - a]


def mix_simple(voice, sr, scene_starts, seed="", music_db=-16.0):
    """ffmpeg miksi başarısız olursa: müzik + whoosh, tepe -1 dBFS (mono, sr)."""
    v = voice.astype(np.float64) / 32768.0
    dur = len(v) / sr
    h = _seed_of(seed)
    rng = np.random.default_rng(h)
    m = _music(dur, sr, rng, PROGRESSIONS[h % len(PROGRESSIONS)])
    speech = v[np.abs(v) > 0.01]
    v_rms = float(np.sqrt(np.mean(speech ** 2))) if len(speech) else 0.1
    m *= (v_rms * 10 ** (music_db / 20)) / (float(np.sqrt(np.mean(m ** 2))) or 1.0)
    fx = np.zeros_like(v)
    peak = float(np.max(np.abs(v))) or 0.5
    for st in scene_starts[1:]:
        w = sfx_whoosh(int(rng.integers(1 << 30)))
        idx = np.linspace(0, len(w) - 1, int(len(w) * sr / SR)).astype(int)  # 48 kHz -> sr
        _place(fx, w[idx], st - 0.3, sr, 0.28 * peak)
    out = np.tanh((v + m + fx) * 1.1) / np.tanh(1.1)
    out *= 0.89 / max(float(np.max(np.abs(out))), 1e-9)
    return (np.clip(out, -1, 1) * 32767).astype(np.int16)
