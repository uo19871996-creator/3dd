# Günlük çalışma talimatı

Bu dosya, her gün otomatik açılan oturumun izleyeceği adımlardır. Amaç: Türkiye'de son 3 günde
en çok konuşulan 5 konuyu seçmek, her biri için bir YouTube Shorts videosu üretmek ve kanala yüklemek.
Tarih olarak İstanbul saatine göre bugünü kullan (`TZ=Europe/Istanbul date +%F`).

## 1. Kurulum

```bash
bash setup.sh
```

## 2. Adayları topla

```bash
mkdir -p out && python3 pipeline/trends.py --days 3 > out/gundem.md
```

`out/gundem.md` dosyasını oku. Bu yalnızca aday listesidir; "en çok konuşulan" kararını verirken
birden çok kaynakta/manşette tekrar eden ve arama hacmi yüksek konulara öncelik ver. Gerekirse web
aramasıyla listeyi genişlet.

## 3. Daha önce işlenenleri kontrol et

```bash
python3 pipeline/upload.py --recent
ls scripts/ | tail -5
```

Son günlerde işlenmiş bir konuyu, yalnızca önemli yeni bir gelişme varsa (ve yeni gelişmeyi anlatarak) tekrar seç.

## 4. 5 konu seç

- Çeşitlilik: aynı kategoriden en fazla 2 video (GÜNDEM, EKONOMİ, SPOR, SİYASET, DÜNYA, TEKNOLOJİ,
  MAGAZİN, SAĞLIK, EĞİTİM, YAŞAM, BİLİM, KÜLTÜR).
- Her konu için web aramasıyla **en az 2 bağımsız, güvenilir kaynaktan** doğrula. Kaynaklar
  çelişiyorsa temkinli yaz ("en az", "ilk belirlemelere göre") ya da o ayrıntıyı hiç yazma.
- Videolar kontrolsüz olarak herkese açık yayınlanıyor; bu yüzden şunlardan **kaçın**:
  doğrulanamayan iddialar; kişilere kesinleşmemiş suç isnadı (resmi açıklama/yargı kararı
  varsa kaynağını belirterek ve "iddia" diliyle aktar); mağdurların ve çocukların kimlikleri;
  ölüm/şiddet olaylarında grafik ayrıntı; sağlık ve yatırım tavsiyesi; bahis/kumar; nefret söylemi.
- Siyasi konularda tarafsız, yorumsuz dil kullan.
- Metni kendi cümlelerinle yaz; haber sitelerinden cümle kopyalama.

## 5. Senaryoyu yaz: `scripts/TARIH.json`

Örnek için `scripts/` klasöründeki önceki dosyalara bak. Kurallar:

- `slug`: küçük harf, ASCII, tireli. `category`: yukarıdaki listeden.
- `title` (ekrandaki başlık): en fazla 55 karakter. `yt_title`: en fazla 90 karakter, sonu `#shorts`.
- `description`: 1-2 cümle. `sources`: 2 kaynak URL'si. `tags`: 4-6 etiket.
- `scenes`: 5-6 sahne, toplam 90-130 kelime (35-55 saniye).
  - İlk sahne giriş cümlesidir (`heading` yok), merak uyandırmalı ve konuyu söylemeli.
  - Diğer sahnelerde `heading` (en fazla 20 karakter) ve 1-2 kısa cümlelik `text`.
  - `stat` isteğe bağlı büyük rakam kartı: `value` en fazla 10 karakter, `label` kısa.
  - Son sahne kapanış: izleyiciye soru ya da "takipte kal".
- `say` (isteğe bağlı): seslendirme motorunun doğru okuması için `text`'in okunuş hali.
  Rakamları yazıyla ("on yedi"), kısaltmaları harf harf ("Be De De Ka"), yabancı sözcükleri
  okunduğu gibi ("Pleysteyşın") yaz. **Cümle sayısı `text` ile aynı olmalı.**

## 6. Videoları üret ve kontrol et

```bash
python3 pipeline/build.py scripts/TARIH.json
```

Her videodan birkaç kare çıkarıp bak (taşan/bozuk yazı var mı) ve süreleri kontrol et (60 sn altı):

```bash
for f in out/TARIH/*.mp4; do ffmpeg -v error -y -ss 8 -i "$f" -frames:v 1 -vf scale=540:-1 "${f%.mp4}.png"; done
```

Sorun varsa senaryoyu düzeltip yalnızca o videoyu yeniden üret (`--only 3`).

## 7. Yükle

```bash
python3 pipeline/upload.py scripts/TARIH.json
```

Betik aynı videoyu iki kez yüklemez (`state/uploaded.json`). Kimlik hatası alırsan videoları
üretilmiş bırak, yeniden deneme döngüsüne girme ve hatayı raporla.

## 8. Kaydet ve raporla

`scripts/TARIH.json` ve `state/uploaded.json` dosyalarını commit edip `gundem-shorts` dalına push etmeyi dene
(`git push -u origin gundem-shorts`; deponun `main` dalına dokunma)
(olmuyorsa atla, raporda belirt). Son mesajında yüklenen videoların başlık + bağlantı listesini,
atlanan/başarısız adımları ve nedenlerini yaz.
