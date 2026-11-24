---
name: video-izle
description: Bir videoyu "izle" ve anla - Instagram/TikTok/YouTube reel'i, kısa video, rakip videosu ya da sohbete yüklenen mp4/mov. Sahne kesmeleri ve tempo, zaman damgalı anahtar kare temas sayfaları (Read ile bakılır), ekrandaki yazılar (OCR, Türkçe) ve konuşma dökümü çıkarır. "Bu videoyu izle", "şu reel'e bak", "bu tarzı incele", "videoda ne var", "nasıl kurgulanmış" gibi isteklerde ya da kullanıcı bir video dosyası/linki paylaştığında kullan.
---

# Video izle

Claude videoyu doğrudan izleyemez; bu araç onu kareye, yazıya ve sese çevirir.

```bash
python3 araclar/izle.py "KAYNAK" --out <scratchpad>/izle/AD     # KAYNAK: dosya yolu ya da URL
```

Sohbete yüklenen dosyalar `/root/.claude/uploads/<oturum>/` altında durur.

Kurulum (yoksa): `python3 -m pip install yt-dlp faster-whisper` ve
`apt-get install -y tesseract-ocr tesseract-ocr-tur` (OCR yoksa araç yazı okumayı atlar).

## Sonra gerçekten izle

1. `rapor.md`'yi oku: süre, kesme sayısı ve ortalama çekim süresi (tempo), ekrandaki yazılar,
   konuşma dökümü.
2. **Her temas sayfasına Read ile bak** (`temas-1.png`, `temas-2.png`, ...). Her karede zaman damgası
   var. Görsel dili tarif et: çizim/3D/gerçek görüntü, renkler, altyazı yeri ve stili, grafikler,
   oklar, etiketler, logo yeri, geçişler.
3. OCR gürültülü olabilir; büyük yazıları karelerden kendin oku, OCR'a körü körüne güvenme.
4. Soruyu cevapla; zaman damgası ver ("00:45'te kesit diyagramı").

## Linkler

- YouTube ve birçok site yt-dlp ile iner.
- **Instagram ve TikTok çoğu zaman girişsiz indirmeye izin vermez** (429 / login required). O zaman
  kullanıcıdan videoyu telefondan kaydedip **dosya olarak göndermesini** iste. Erişim kısıtlarını
  aşmaya çalışma (sahte tarayıcı kimliği, gömülü sayfa kazıma, başkasının girişi).
- İndirilen videoyu yalnızca incelemek için kullan; yeniden yayınlama, kendi videolarımızda kullanma.
