"""Pilot: WannaCry (45 sn). Gece görünümü, kırmızı vurgu; dört küme yan yana, kamera soldan sağa."""
from engine import BigText, Card, Counter, Film, PenMark, Stamp

RED = (214, 38, 38)
YELLOW = (250, 204, 21)
CREAM = (246, 240, 228)
X1, X2, X3, X4 = 0, 7600, 15200, 22800


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    film = Film(doc.duration, fps=30, look="night")

    # 1-2  tarih, sonra fidye ekranı (canlandırma: üstteki cümle gerçek ekrandaki İngilizce metin)
    film.add(BigText("12 MAYIS 2017", X1, -1150, 560, L(1) + 0.05, rgb=CREAM, type_on=0.8))
    film.add(PenMark("underline", X1, -1000, 4200, 60, t_in=W(1, "kırmızıya") - 0.1, dur=0.5, width=30, rgb=RED))
    film.add(Card(X1, 700, 4200, 2100, L(2) + 0.05, title="Ooops, your files have been encrypted!",
                  lines=["Ödeme: 300 dolar değerinde Bitcoin", "CANLANDIRMA"], rgb=(150, 18, 18),
                  text_rgb=(255, 244, 240), accent=YELLOW, title_size=190, body_size=140))
    film.add(Stamp("KİLİTLİ", X1 + 1200, 1250, size=380, rot=-9, t_in=W(2, "kilitlenmişti") + 0.2, rgb=YELLOW))

    # 3  ad ve yayılma: iki sayaç
    film.add(BigText("WANNACRY", X2, -1500, 640, W(3, "vana") - 0.05, rgb=CREAM, bar=RED, bar_h=0.42))
    film.add(Counter(X2 - 1700, 300, 620, 150, W(3, "yüz elli") - 0.1, dur=1.0, caption="ÜLKE", rgb=YELLOW))
    film.add(Counter(X2 + 1700, 300, 620, 200000, W(3, "iki yüz") - 0.1, dur=1.4, suffix="+", caption="BİLGİSAYAR",
                     rgb=YELLOW))

    # 4-5  NHS ve fatura
    film.add(Card(X3, -500, 4600, 1700, L(4) + 0.05, title="NHS · İngiltere sağlık sistemi",
                  lines=["En ağır darbeyi aldı", "Hastaneler hastaları başka yerlere yönlendirdi"],
                  rgb=(246, 242, 236), text_rgb=(30, 30, 34), accent=RED, title_size=210, body_size=150))
    film.add(Counter(X3, 1500, 600, 92, W(5, "doksan") - 0.1, dur=0.9, prefix="£", suffix=" MİLYON",
                     caption="NHS'İN ZARARI", rgb=YELLOW))

    # 6  acil durdurma anahtarı
    film.add(Card(X4, -1300, 4200, 1000, W(6, "araştırmacı") - 0.1, title="13 Mayıs 2017 · Marcus Hutchins",
                  lines=["Genç bir güvenlik araştırmacısı"], rgb=(246, 242, 236), text_rgb=(30, 30, 34),
                  accent=YELLOW, title_size=170, body_size=130))
    film.add(BigText("KILL SWITCH", X4, 650, 720, W(6, "acil") - 0.05, rgb=CREAM, bar=YELLOW, bar_h=0.42,
                     hit=0.25))
    film.add(PenMark("underline", X4, 840, 4800, 60, t_in=W(6, "anahtarı"), dur=0.5, width=34, rgb=YELLOW))

    # kamera: her kümede kahramana it, kümeler arasında hızlı geçiş, sonda tüm duvar
    film.shot(0.0, X1, -1100, 0.5)
    film.shot(L(1) + 1.2, X1, -1000, 0.62, rot=-0.5)
    film.shot(L(2) + 0.4, X1, 650, 0.7, rot=0.4)
    film.shot(E(2) - 0.2, X1 + 200, 700, 0.74)
    film.shot(L(3) + 0.3, X2, -900, 0.52, rot=-0.4)
    film.shot(W(3, "yüz elli") + 0.3, X2, 0, 0.6)
    film.shot(E(3) - 0.1, X2 + 300, 100, 0.62, rot=0.5)
    film.shot(L(4) + 0.4, X3, -500, 0.66, rot=-0.4)
    film.shot(W(5, "doksan") + 0.3, X3, 600, 0.5, rot=0.4)
    film.shot(E(5) - 0.1, X3 + 200, 650, 0.52)
    film.shot(L(6) + 0.4, X4, -1100, 0.7, rot=-0.4)
    film.shot(W(6, "acil") + 0.3, X4, 500, 0.62, rot=0.3)
    film.shot(E(6) + 0.2, X4 + 200, 400, 0.6)
    film.shot(film.duration, (X1 + X4) / 2, 0, 0.16, radius=24000, strength=0.1)
    return film
