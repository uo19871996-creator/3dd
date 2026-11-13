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
- **Yayın yasağı kontrolü (zorunlu):** kaza, patlama, saldırı, cinayet, soruşturma gibi olay
  haberlerinde web aramasıyla ("<olay> yayın yasağı") mahkeme/RTÜK yayın yasağı olup olmadığına bak.
  Yasak varsa ya da emin olamıyorsan o konuyu **seçme** (yasaklar sosyal medyayı da kapsar).
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
    Sayıyla başlayan değerler (`17+`, `%42`, `7,7 milyon`, `$79,99`) ekranda sayarak açılır.
  - Son sahne kapanış: izleyiciye soru ya da "takipte kal" (ekranda yorum/beğen/takip kartı çıkar).
- **Görseller (v2 şablonu)** — her sahneye konuya uygun EN AZ BİR görsel alanı ekle, sahneler
  arasında çeşitlilik olsun (her videoda en az bir `map` ya da `chart` ya da `points`):
  - `icon`: her sahnede (giriş dahil) konuya uygun bir Lucide ikon adı, ör. `landmark` (kurum/banka),
    `trending-up`, `trophy`, `cloud-lightning`, `plane`, `gavel`, `factory`, `shirt`, `cpu`,
    `gamepad-2`, `users`, `briefcase`, `heart-pulse`, `map-pin`, `chart-column`, `flame`, `zap`.
    Listeyi görmek için: `cd video && node -e "console.log(Object.keys(require('lucide-react').icons).join(' '))"`
    (PascalCase adı tireli yaz: `CloudLightning` → `cloud-lightning`).
  - `map`: olayın geçtiği yer `{"place": "İzmir", "lat": 38.42, "lon": 27.14, "label": "9 Kasım · Aliağa"}`.
    Türkiye içindeki yerler Türkiye haritasında, yurt dışı yerler dönen dünya küresinde gösterilir.
    Koordinatları doğrula; emin değilsen `map` kullanma.
  - `chart`: karşılaştırmalı rakamlar `{"unit": "%", "items": [{"label": "Eylül", "value": 33.3}, ...]}`
    (en fazla 5 madde, en önemlisi sonda). Yalnızca kaynakta geçen rakamlar.
  - `points`: 2-4 kısa madde (her biri en fazla 35 karakter).
  - `photo`: Wikimedia Commons'tan serbest lisanslı fotoğraf `{"file": "File:Tim Cook (2017, cropped).jpg"}`.
    Adayları gör: `python3 pipeline/photos.py search "Tim Cook"` (yalnızca uygun lisanslılar listelenir;
    atıf ekrana ve YouTube açıklamasına otomatik yazılır). Arama sonuçları hatalı olabilir: başlığı
    konuyla birebir eşleşen dosyayı seç ve `file` ile adını aynen yaz. Uygun aday yoksa `photo` koyma.
    - Giriş sahnesine (ilk sahne) konunun ana kişisi/mekânı/kurumunun fotoğrafı konursa tam ekran gösterilir.
    - Fotoğraf yalnızca adı geçen kişiyi, mekânı, kurumu ya da nesneyi göstermeli. Başka bir olayın
      fotoğrafını bu olaymış gibi kullanma (ör. başka bir yangının fotoğrafı). Kaza, afet, suç ve
      mağdur içeren haberlerde fotoğraf kullanma; harita ve ikon kullan. Özel kişilerin fotoğrafı yok.
    - `photo` ile `stat` aynı sahnede olursa rakam fotoğrafın üstünde gösterilir.
    - Wikimedia 429 (çok fazla istek) verirse betik bekleyip yeniden dener; olmazsa sahne fotoğrafsız
      devam eder. Her videoda en fazla 3 fotoğraf kullan.
  - Öncelik: `photo` > `map` > `chart` > `stat` > `points` > `icon`; bir sahnede yalnızca biri gösterilir.
  - Haber ajansı fotoğrafları (AA, Reuters, Getty vb.) ve yapay zekâ görselleri KULLANILMAZ (telif ve
    yanıltma riski); yalnızca `photos.py`'nin bulduğu serbest lisanslı fotoğraflar.
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

Betik aynı videoyu iki kez yüklemez (`state/uploaded.json`). Yüklemeyi yalnızca `upload.py`'nin kendi
verdiği hata durdurur: o zaman videoları üretilmiş bırak, yeniden deneme döngüsüne girme ve hatayı
raporla. Üretim adımındaki seslendirme bilgileri (ör. "Google sesi kullanılamadı; ücretsiz sese
geçildi") beklenen durumlardır; yüklemeyi **engellemez**, yüklemeye devam et.

## 8. Raporla

Commit ve push YAPMA: zamanlanmış oturumların bu depoya yazma izni yok, kayıt da gerekmiyor (aynı
konuyu tekrarlamamak için 3. adımda kanalın son videolarına bakılıyor). Bir "push edilmemiş commit"
uyarısı görürsen yok say.

Son mesajında yüklenen videoların başlık + bağlantı listesini, atlanan/başarısız adımları ve
nedenlerini yaz.
