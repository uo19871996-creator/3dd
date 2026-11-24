"""Pilot: WannaCry (45 sn). Gece görünümü; her satırda gerçek fotoğraf/harita ya da hareketli canlandırma."""
from engine import BigText, Counter, Film, PenMark, Print, Stamp
from extras import GREEN, RED, YELLOW, DeviceGrid, Icon, Screen

CREAM = (246, 240, 228)
XA, XB, XC, XD = 0, 9800, 19600, 29400


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    film = Film(doc.duration, fps=30, look="night")

    # 1  tarih; veri merkezinde ekranlar birer birer kırmızıya döner
    film.add(Print("P03", XA, 250, 8600, rot=-0.8, t_in=0.0, pin=False, label="VERİ MERKEZİ · TEMSİLÎ", label_t=1.2))
    film.add(BigText("12 MAYIS 2017", XA, -2350, 560, L(1) + 0.05, rgb=CREAM, type_on=0.8, bar=(10, 12, 22), bar_h=0.92))
    film.add(DeviceGrid(XA, 350, 14, 7, 470, W(1, "ekranlar") - 0.3, dur=E(1) - W(1, "ekranlar") + 0.2))
    film.add(PenMark("underline", XA, -2200, 4300, 60, t_in=W(1, "kırmızıya") - 0.1, dur=0.5, width=30, rgb=RED))

    # 2  fidye ekranı (canlandırma; üst cümle gerçek ekrandaki İngilizce metin)
    film.add(Screen(XA, 300, 5600, L(2) + 0.05, kind="ransom", title="Ooops, your files have been encrypted!",
                    lines=["Dosyalarınız kilitlendi.", "Ödeme: 300 dolar değerinde Bitcoin"], step=0.7))
    film.add(Stamp("KİLİTLİ", XA + 3300, 2150, size=380, rot=-9, t_in=W(2, "kilitlenmişti") + 0.3, rgb=YELLOW))

    # 3  ad, ilk etkilenen ülkeler haritası (gerçek), iki sayaç
    film.add(BigText("WANNACRY", XB, -2500, 640, W(3, "vana") - 0.05, rgb=CREAM, bar=RED, bar_h=0.42))
    film.add(Print("P01", XB, -350, 6800, rot=0.6, t_in=W(3, "vana") + 0.2, pin=False,
                   label="İLK ETKİLENEN ÜLKELER", label_t=W(3, "yayıldı") - 0.2))
    film.add(Counter(XB - 1900, 2500, 600, 150, W(3, "yüz elli") - 0.1, dur=1.0, caption="ÜLKE", rgb=YELLOW))
    film.add(Counter(XB + 1900, 2500, 600, 200000, W(3, "iki yüz") - 0.1, dur=1.4, suffix="+", caption="BİLGİSAYAR",
                     rgb=YELLOW))

    # 4-5  NHS: hastane fotoğrafı, ikonlar, fatura
    film.add(Print("P02", XC - 1300, -400, 5000, rot=1.4, t_in=L(4) + 0.05, pin=False, label="NHS HASTANESİ · LONDRA",
                   label_t=W(4, "sağlık") + 0.1))
    film.add(Icon("hospital", XC + 3500, -1500, 760, W(4, "sağlık") - 0.1, rgb=CREAM, ring=RED, label="EN AĞIR DARBE"))
    film.add(Icon("siren", XC + 3500, 600, 760, W(4, "yönlendirdi") - 0.6, rgb=CREAM, ring=RED,
                  label="HASTALAR YÖNLENDİRİLDİ"))
    film.add(Icon("banknote", XC - 2300, 2450, 640, W(5, "faturası") - 0.1, rgb=YELLOW))
    film.add(Counter(XC + 600, 2650, 620, 92, W(5, "doksan") - 0.1, dur=0.9, prefix="£", suffix=" MİLYON",
                     caption="NHS'İN ZARARI", rgb=YELLOW))

    # 6  acil durdurma anahtarı: terminal canlandırması, kalkan
    film.add(BigText("13 MAYIS 2017", XD - 1200, -2600, 480, L(6) + 0.05, rgb=CREAM, type_on=0.6))
    film.add(Screen(XD - 1200, -400, 5400, L(6) + 0.3, kind="terminal", title="analiz.log",
                    lines=["> örnek incelemeye alındı", "> şüpheli bir alan adı sorgusu bulundu",
                           "> alan adı kaydedildi", "[!] yayılma durdu"], step=0.95))
    film.add(Icon("shield-check", XD + 3300, -900, 950, W(6, "durduran") - 0.1, rgb=CREAM, ring=GREEN))
    film.add(BigText("KILL SWITCH", XD, 2350, 700, W(6, "acil") - 0.05, rgb=CREAM, bar=YELLOW, bar_h=0.42, hit=0.25))
    film.add(PenMark("underline", XD, 2540, 4800, 60, t_in=W(6, "anahtarı"), dur=0.5, width=34, rgb=YELLOW))

    # kamera
    film.shot(0.0, XA, -800, 0.36)
    film.shot(L(1) + 1.0, XA, -1400, 0.46, rot=-0.5)
    film.shot(W(1, "ekranlar") + 0.2, XA, 0, 0.42, rot=0.3)
    film.shot(L(2) + 0.45, XA, 300, 0.62, rot=0.4)
    film.shot(E(2) - 0.2, XA + 300, 500, 0.6)
    film.shot(L(3) + 0.3, XB, -1500, 0.5, rot=-0.4)
    film.shot(W(3, "yüz elli") - 0.2, XB, 400, 0.36)
    film.shot(E(3) - 0.1, XB + 200, 900, 0.42, rot=0.5)
    film.shot(L(4) + 0.4, XC - 800, -500, 0.52, rot=-0.4)
    film.shot(W(4, "yönlendirdi") - 0.3, XC + 900, -300, 0.44)
    film.shot(W(5, "doksan") + 0.2, XC, 1500, 0.5, rot=0.4)
    film.shot(E(5) - 0.1, XC + 200, 1600, 0.52)
    film.shot(L(6) + 0.5, XD - 1200, -900, 0.48, rot=-0.4)
    film.shot(W(6, "durduran") + 0.3, XD + 700, -500, 0.4, rot=0.3)
    film.shot(W(6, "acil") + 0.4, XD, 1500, 0.5)
    film.shot(film.duration, (XA + XD) / 2, 0, 0.115, radius=30000, strength=0.1)
    return film
