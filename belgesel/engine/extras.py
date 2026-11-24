"""Siber belgesel için ek sahne parçaları (engine.Item üstüne).

    from extras import Icon, Screen, DeviceGrid, Timeline, SIBER   # GeoMap(..., look=SIBER)

- Icon(name, x, y, size, t_in): belgesel/icons içindeki Lucide ikonu (lock, shield-check, hospital,
  server, skull, mail-x, smartphone, key-round, refresh-cw, ...), isteğe bağlı renkli halka içinde.
- Screen(x, y, w, t_in, kind, title, lines): monitör içinde hareketli ekran CANLANDIRMASI.
  kind: "ransom" (fidye ekranı + geri sayım), "terminal" (satır satır yazılan kayıt),
  "email" (oltalama e-postası: lines[0] Kimden, lines[1] Konu, gerisi gövde; "http" geçen satır
  bağlantı gibi çizilir), "progress" (dosyalar şifreleniyor: dolan çubuk, akan dosya adları),
  "login" (giriş formu: lines[0] kullanıcı adı; parola noktaları yazılır).
  Köşede her zaman "CANLANDIRMA" yazar (gerçek ekran görüntüsü değil).
- DeviceGrid(x, y, cols, rows, cell, t_in, dur): bilgisayarlar sırayla kırmızıya döner (yayılma).
- Timeline(x, y, w, events, t_in): çizilen zaman çizgisi; events = [(t, "TARİH", "olay"), ...].
"""
import pathlib
import random

import skia

import engine
from engine import Item, draw_text, ease_out_back, ease_out_cubic, paint, ramp, text_width

ICONS = pathlib.Path(__file__).resolve().parent.parent / "icons"
RED, YELLOW, GREEN = (214, 38, 38), (250, 204, 21), (74, 222, 128)
CREAM, INK, NAVY = (246, 240, 228), (24, 26, 32), (14, 20, 36)

# Koyu "siber" harita görünümü: lacivert deniz, gri-mavi kara, ince açık sınırlar
SIBER = dict(sheet=(9, 13, 24), water=(11, 18, 34), land=(36, 48, 70), border=(78, 100, 136), relief=0.0,
             neighbor=(28, 38, 56), neighbor_line=(60, 78, 108), dark=(22, 30, 46), dark_line=(50, 64, 90),
             frame=(40, 56, 84))
engine.MAP_LOOKS["siber"] = SIBER

_SVG = {}


def _icon_dom(name, rgb):
    key = (name, rgb)
    if key not in _SVG:
        p = ICONS / f"{name}.svg"
        if not p.exists():
            raise SystemExit(f"ikon yok: {name} (belgesel/icons içindekiler: "
                             f"{', '.join(sorted(x.stem for x in ICONS.glob('*.svg')))})")
        src = p.read_text().replace("currentColor", "#%02x%02x%02x" % tuple(rgb))
        dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(src.encode(), True))
        dom.setContainerSize(skia.Size(24, 24))
        _SVG[key] = dom
    return _SVG[key]


def draw_icon(c, name, x, y, size, rgb, a=1.0):
    """Ikonu (x, y) merkezli, size genişlikte çizer."""
    c.save()
    c.translate(x - size / 2, y - size / 2)
    c.scale(size / 24, size / 24)
    if a < 0.999:
        c.saveLayerAlpha(skia.Rect.MakeXYWH(-2, -2, 28, 28), int(255 * max(0.0, a)))
        _icon_dom(name, rgb).render(c)
        c.restore()
    else:
        _icon_dom(name, rgb).render(c)
    c.restore()


def wrap(res, text, size, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if cur and text_width(res, trial, size, font) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    return lines + ([cur] if cur else [])


class Icon(Item):
    z = 30

    def __init__(self, name, x, y, size, t_in, rgb=CREAM, ring=None, t_out=None, label=None, label_rgb=CREAM, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.name, self.x, self.y, self.size, self.rgb, self.ring = name, x, y, size, rgb, ring
        self.label, self.label_rgb = label, label_rgb

    def bounds(self, res):
        r = self.size * 2.5
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def cues(self):
        return [("pop", self.t_in, 0.5, {})]

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.2) * self.fade(t)
        if a <= 0:
            return
        s = 0.6 + 0.4 * ease_out_back(ramp(t, self.t_in, 0.45), 1.6)
        c.save()
        c.translate(self.x, self.y)
        c.scale(s, s)
        if self.ring:
            c.drawCircle(0, 0, self.size * 0.82, paint(self.ring, 0.22 * a))
            c.drawCircle(0, 0, self.size * 0.82, paint(self.ring, 0.9 * a, stroke=self.size * 0.05))
        draw_icon(c, self.name, 0, 0, self.size, self.rgb, a)
        c.restore()
        if self.label:
            la = a * ramp(t, self.t_in + 0.25, 0.3)
            draw_text(c, res, self.label, self.x, self.y + self.size * 1.35, self.size * 0.3, "label", self.label_rgb,
                      la, 0.02, "center")


class Screen(Item):
    z = 20

    def __init__(self, x, y, w, t_in, kind="terminal", title="", lines=(), t_out=None, step=0.35, dur=4.0,
                 accent=RED, countdown=72 * 3600, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.w, self.h = x, y, w, w * 0.6
        self.kind, self.title, self.lines, self.step, self.dur = kind, title, list(lines), step, dur
        self.accent, self.countdown = accent, countdown

    def bounds(self, res):
        r = self.w * 0.9
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def cues(self):
        return [("whoosh", self.t_in - 0.1, 0.5, {}), ("click", self.t_in + 0.35, 0.5, {})]

    def draw(self, c, res, t):
        u = ease_out_back(ramp(t, self.t_in, 0.5), 1.1)
        a = ramp(t, self.t_in, 0.2) * self.fade(t)
        if a <= 0:
            return
        W, H = self.w, self.h
        c.save()
        c.translate(self.x, self.y + (1 - u) * 160)
        c.scale(0.9 + 0.1 * u, 0.9 + 0.1 * u)
        bez = W * 0.025
        body = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-W / 2 - bez, -H / 2 - bez, W + 2 * bez, H + 2 * bez), bez, bez)
        c.save(); c.translate(0, 40); c.drawRRect(body, paint((0, 0, 0), 0.45 * a, blur=60)); c.restore()
        c.drawRect(skia.Rect.MakeXYWH(-W * 0.06, H / 2 + bez, W * 0.12, H * 0.12), paint((30, 32, 40), a))   # ayak
        c.drawRect(skia.Rect.MakeXYWH(-W * 0.2, H / 2 + bez + H * 0.12, W * 0.4, H * 0.03), paint((40, 42, 52), a))
        c.drawRRect(body, paint((22, 24, 30), a))
        scr = skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H)
        c.save()
        c.clipRect(scr)
        on = ramp(t, self.t_in + 0.15, 0.25)   # ekran açılırken parlama
        getattr(self, "_" + self.kind)(c, res, t, W, H, a * on)
        c.drawRect(scr, paint((255, 255, 255), 0.25 * (1 - on) * a))
        for k in range(0, int(H), 9):   # hafif tarama çizgileri
            c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2 + k, W, 2), paint((0, 0, 0), 0.06 * a))
        tag = "CANLANDIRMA"
        ts = H * 0.045
        tw = text_width(res, tag, ts, "label", 0.08)
        c.drawRect(skia.Rect.MakeXYWH(W / 2 - tw - ts * 1.4, H / 2 - ts * 1.9, tw + ts, ts * 1.4), paint((0, 0, 0), 0.55 * a))
        draw_text(c, res, tag, W / 2 - tw - ts * 0.9, H / 2 - ts * 0.85, ts, "label", (235, 235, 235), 0.9 * a, 0.08)
        c.restore()
        c.restore()

    def _typed(self, t, i):
        return ramp(t, self.t_in + 0.5 + i * self.step, 0.25)

    def _ransom(self, c, res, t, W, H, a):
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H), paint((128, 14, 16), a))
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H * 0.12), paint((90, 8, 10), a))
        draw_icon(c, "lock", -W * 0.32, -H * 0.06, H * 0.36, (255, 236, 200), a)
        tx, maxw = -W * 0.1, W * 0.56
        y = -H * 0.26
        for ln in wrap(res, self.title, H * 0.085, "label", maxw):
            draw_text(c, res, ln, tx, y, H * 0.085, "label", (255, 255, 255), a)
            y += H * 0.1
        for i, ln in enumerate(self.lines):
            for k, part in enumerate(wrap(res, ln, H * 0.055, "labelm", maxw)):
                y += H * (0.08 if k == 0 else 0.065)
                draw_text(c, res, part, tx, y, H * 0.055, "labelm", (255, 225, 220), a * self._typed(t, i))
        left = max(0, self.countdown - int(max(0.0, t - self.t_in)))
        clock = f"{left // 3600:02d}:{left % 3600 // 60:02d}:{left % 60:02d}"
        draw_text(c, res, "KALAN SÜRE", -W * 0.32, H * 0.25, H * 0.045, "label", (255, 210, 200), a, 0.1, "center")
        draw_text(c, res, clock, -W * 0.32, H * 0.37, H * 0.1, "mono", YELLOW, a, 0.02, "center")

    def _terminal(self, c, res, t, W, H, a):
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H), paint((6, 10, 9), a))
        size = H * 0.05
        x, y = -W / 2 + W * 0.05, -H / 2 + H * 0.12
        if self.title:
            draw_text(c, res, self.title, x, y, size, "mono", (140, 160, 150), a)
            y += size * 1.7
        last = -1
        for i, ln in enumerate(self.lines):
            r = self._typed(t, i)
            if r <= 0:
                break
            col = RED if ln.startswith("[!]") else GREEN
            draw_text(c, res, ln, x, y, size, "mono", col, a, reveal=len(ln) * r + 0.999)
            y += size * 1.55
            last = i
        if int((t - self.t_in) * 2.2) % 2 == 0:   # yanıp sönen imleç
            c.drawRect(skia.Rect.MakeXYWH(x, y - size * 0.85, size * 0.55, size), paint(GREEN, a))
        del last

    def _email(self, c, res, t, W, H, a):
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H), paint((248, 249, 251), a))
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H * 0.11), paint((42, 92, 190), a))
        draw_text(c, res, self.title or "Gelen kutusu", -W / 2 + W * 0.04, -H / 2 + H * 0.075, H * 0.05, "label",
                  (255, 255, 255), a)
        x, y, size = -W / 2 + W * 0.05, -H / 2 + H * 0.22, H * 0.048
        for i, ln in enumerate(self.lines):
            r = self._typed(t, i)
            if r <= 0:
                break
            if i == 0:
                ln = "Kimden: " + ln
            elif i == 1:
                ln = "Konu: " + ln
            link = "http" in ln
            col = (36, 90, 210) if link else ((90, 94, 104) if i < 2 else INK)
            draw_text(c, res, ln, x, y, size * (1.08 if i == 1 else 1.0), "label" if i < 2 else "labelm", col, a * r)
            if link:
                lw = text_width(res, ln, size, "labelm")
                c.drawRect(skia.Rect.MakeXYWH(x, y + size * 0.2, lw * r, size * 0.07), paint(col, a))
            y += size * (2.0 if i == 1 else 1.6)
            if i == 1:
                c.drawRect(skia.Rect.MakeXYWH(x, y - size * 1.1, W * 0.9, 3), paint((210, 214, 222), a))

    def _progress(self, c, res, t, W, H, a):
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H), paint((12, 16, 28), a))
        p = ease_out_cubic(ramp(t, self.t_in + 0.4, self.dur))
        draw_text(c, res, self.title or "Dosyalar şifreleniyor", 0, -H * 0.2, H * 0.075, "label", (255, 255, 255), a,
                  0.0, "center")
        bw, bh = W * 0.7, H * 0.07
        c.drawRect(skia.Rect.MakeXYWH(-bw / 2, -H * 0.06, bw, bh), paint((40, 48, 70), a))
        c.drawRect(skia.Rect.MakeXYWH(-bw / 2, -H * 0.06, bw * p, bh), paint(self.accent, a))
        draw_text(c, res, f"%{int(p * 100)}", 0, H * 0.12, H * 0.07, "mono", YELLOW, a, 0.0, "center")
        if self.lines:
            k = int(p * 40) % len(self.lines)
            draw_text(c, res, self.lines[k], 0, H * 0.27, H * 0.045, "mono", (150, 160, 180), a, 0.0, "center")

    def _login(self, c, res, t, W, H, a):
        c.drawRect(skia.Rect.MakeXYWH(-W / 2, -H / 2, W, H), paint((236, 239, 244), a))
        fw, fh = W * 0.5, H * 0.1
        draw_text(c, res, self.title or "Oturum aç", 0, -H * 0.24, H * 0.07, "label", INK, a, 0.0, "center")
        user = self.lines[0] if self.lines else "kullanici@ornek.com"
        for k, (y, txt) in enumerate(((-H * 0.12, user), (H * 0.03, "•" * 10))):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-fw / 2, y, fw, fh), 14, 14), paint((255, 255, 255), a))
            r = self._typed(t, k)
            draw_text(c, res, txt, -fw / 2 + fh * 0.4, y + fh * 0.68, H * 0.045, "mono", INK, a,
                      reveal=len(txt) * r + 0.999)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-fw / 2, H * 0.19, fw, fh), 14, 14),
                    paint((42, 92, 190), a))
        draw_text(c, res, "Giriş", 0, H * 0.19 + fh * 0.68, H * 0.045, "label", (255, 255, 255), a, 0.0, "center")


class DeviceGrid(Item):
    """cols x rows küçük bilgisayar; t_in'den t_in+dur'a hızlanarak kırmızıya döner (frac kadarı)."""
    z = 18

    def __init__(self, x, y, cols, rows, cell, t_in, dur=3.0, frac=1.0, seed=7, t_out=None, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.cols, self.rows, self.cell, self.dur = x, y, cols, rows, cell, dur
        n = cols * rows
        order = list(range(n))
        random.Random(seed).shuffle(order)
        hit = order[:int(n * frac)]
        self.when = {k: t_in + 0.4 + dur * (i / max(1, len(hit))) ** 1.7 for i, k in enumerate(hit)}

    def bounds(self, res):
        r = max(self.cols, self.rows) * self.cell
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def cues(self):
        return [("ticks", self.t_in + 0.4, 0.5, {})]

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.35) * self.fade(t)
        if a <= 0:
            return
        cw = self.cell
        x0 = self.x - (self.cols - 1) * cw / 2
        y0 = self.y - (self.rows - 1) * cw / 2
        for k in range(self.cols * self.rows):
            cx, cy = x0 + (k % self.cols) * cw, y0 + (k // self.cols) * cw
            hit = ramp(t, self.when.get(k, 1e9), 0.25)
            m = cw * 0.38
            scr = skia.Rect.MakeXYWH(cx - m, cy - m * 0.75, 2 * m, 1.3 * m)
            if hit > 0:
                c.drawRect(scr.makeOutset(m * 0.25, m * 0.25), paint(RED, 0.35 * hit * a, blur=m * 0.6))
            col = tuple(int(c0 + (c1 - c0) * hit) for c0, c1 in zip((52, 66, 92), RED))
            c.drawRect(scr, paint(col, a))
            c.drawRect(scr, paint((120, 140, 170), 0.6 * a * (1 - hit), stroke=m * 0.08))
            c.drawRect(skia.Rect.MakeXYWH(cx - m * 0.12, cy + m * 0.57, m * 0.24, m * 0.22), paint((90, 104, 130), a))


class Timeline(Item):
    z = 22

    def __init__(self, x, y, w, events, t_in, rgb=CREAM, accent=YELLOW, t_out=None, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.w, self.events, self.rgb, self.accent = x, y, w, list(events), rgb, accent

    def bounds(self, res):
        return skia.Rect.MakeLTRB(self.x - self.w, self.y - self.w * 0.5, self.x + self.w, self.y + self.w * 0.5)

    def cues(self):
        return [("whoosh", self.t_in, 0.4, {})] + [("pop", e[0], 0.4, {}) for e in self.events]

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.2) * self.fade(t)
        if a <= 0:
            return
        L = self.w * ease_out_cubic(ramp(t, self.t_in, 0.9))
        x0 = self.x - self.w / 2
        c.drawRect(skia.Rect.MakeXYWH(x0, self.y - 6, L, 12), paint(self.rgb, 0.85 * a))
        n = len(self.events)
        for i, (te, date, label) in enumerate(self.events):
            ex = x0 + self.w * (i + 0.5) / n
            ea = ramp(t, te, 0.3) * a
            if ea <= 0:
                continue
            c.drawCircle(ex, self.y, 34 + 20 * ease_out_back(ramp(t, te, 0.4)), paint(self.accent, ea))
            up = -1 if i % 2 == 0 else 1
            draw_text(c, res, date, ex, self.y + up * 150 + (40 if up > 0 else 0), 120, "cond", self.accent, ea, 0.04,
                      "center")
            draw_text(c, res, label, ex, self.y + up * 260 + (40 if up > 0 else 0), 78, "labelm", self.rgb, ea, 0.0,
                      "center")
