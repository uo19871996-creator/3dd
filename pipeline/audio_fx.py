"""Arka plan müziği ve geçiş efektleri: tamamen burada sentezlenir (telif yok).

mix(voice, sr, scene_starts, stat_times, seed) -> int16 ses
- Müzik: 96 BPM, yumuşak pad + pluck arpej + bas + hafif davul; konuşma sırasında kısılır (ducking).
- Efektler: sahne geçişlerinde "whoosh", açılışta alçak "boom", rakam kartlarında hafif "ding".
"""
import hashlib

import numpy as np

PROGRESSIONS = [  # (kök MIDI notası, minör mü)
    [(57, True), (53, False), (48, False), (55, False)],  # Am F C G
    [(50, True), (46, False), (53, False), (48, False)],  # Dm Bb F C
    [(52, True), (48, False), (55, False), (50, False)],  # Em C G D
]


def _hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _onepole_lp(x, a):
    """Basit tek kutuplu alçak geçiren (a: 0..1, küçük = daha yumuşak)."""
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


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


def _whoosh(sr, rng, length=0.5):
    n = int(length * sr)
    u = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    # süpürülen alçak geçiren: önce açılır sonra kapanır
    cut = 0.02 + 0.5 * np.sin(np.pi * u) ** 2
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += cut[i] * (noise[i] - acc)
        y[i] = acc
    return y * np.sin(np.pi * u) ** 1.5


def _boom(sr, length=0.9):
    u = np.arange(int(length * sr)) / sr
    f = 38 + 50 * np.exp(-u / 0.08)
    return np.exp(-u / 0.35) * np.sin(2 * np.pi * np.cumsum(f) / sr)


def _ding(sr, length=0.35):
    u = np.arange(int(length * sr)) / sr
    return np.exp(-u / 0.09) * (np.sin(2 * np.pi * 1320 * u) + 0.4 * np.sin(2 * np.pi * 1980 * u))


def _place(dst, clip, at, sr, gain):
    a = int(at * sr)
    if a < 0:
        clip, a = clip[-a:], 0
    z = min(len(dst), a + len(clip))
    if z > a:
        dst[a:z] += gain * clip[: z - a]


def mix(voice, sr, scene_starts, stat_times=(), seed="", music_db=-16.0, duck=0.45):
    v = voice.astype(np.float64) / 32768.0
    dur = len(v) / sr
    h = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16)
    rng = np.random.default_rng(h)
    prog = PROGRESSIONS[h % len(PROGRESSIONS)]

    m = _music(dur, sr, rng, prog)
    speech = v[np.abs(v) > 0.01]
    v_rms = float(np.sqrt(np.mean(speech ** 2))) if len(speech) else 0.1
    m_rms = float(np.sqrt(np.mean(m ** 2))) or 1.0
    m *= (v_rms * 10 ** (music_db / 20)) / m_rms

    # Ducking: konuşma zarfına göre müziği kıs
    win = max(1, int(0.03 * sr))
    env = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, "same"))
    env = np.clip(env / (v_rms + 1e-9), 0, 1)
    env = _onepole_lp(env, 1 - np.exp(-1 / (0.25 * sr)))  # yumuşak bırakış
    m *= 1 - (1 - duck) * np.clip(env * 1.5, 0, 1)

    fx = np.zeros_like(v)
    peak = float(np.max(np.abs(v))) or 0.5
    _place(fx, _boom(sr), 0.0, sr, 0.32 * peak)
    _place(fx, _whoosh(sr, rng), 0.0, sr, 0.22 * peak)
    for st in scene_starts[1:]:
        _place(fx, _whoosh(sr, rng), st - 0.3, sr, 0.28 * peak)
    for st in stat_times:
        _place(fx, _ding(sr), st, sr, 0.10 * peak)

    out = v + m + fx
    out = np.tanh(out * 1.1) / np.tanh(1.1)  # yumuşak sınırlayıcı
    out *= 0.89 / max(float(np.max(np.abs(out))), 1e-9)  # tepe -1 dBFS (kodlamada patlama olmasın)
    return (np.clip(out, -1, 1) * 32767).astype(np.int16)
