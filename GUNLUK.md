# Çalışma talimatı

Bu dosya, otomatik açılan oturumun izleyeceği adımlardır. Görev **İstanbul saatiyle günde 10 kez**
(09, 10, 12, 13, 15, 16, 18, 19, 21 ve 22'de) çalışır ve her çalışmada **1 video** (görev metni
başka bir sayı söylüyorsa o kadar) üretip yükler. Günde 10'dan fazla yükleme yapılmaz: kanal
verisinde günün 10. videosundan sonrakiler neredeyse hiç izlenmedi. Amaç: Türkiye'de şu an en çok
konuşulan ve kanalda henüz işlenmemiş konuyu, kanalda en çok izlenen konu türlerine öncelik vererek
seçmek, YouTube Shorts videosu üretmek ve kanala yüklemek.
Tarih olarak İstanbul saatine göre bugünü kullan (`TZ=Europe/Istanbul date +%F`).
Senaryo dosyasının adı: `scripts/TARIH-SSDD.json` (ör. `scripts/2026-11-14-1407.json`).
Dosyanın içindeki `"date"` alanı yine yalnızca tarihtir (`"2026-11-14"`).

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
python3 pipeline/upload.py --today
python3 pipeline/upload.py --recent
```

`--today` bugün yüklenen video sayısını verir. **10 ya da fazlaysa dur**: video üretme ve yükleme,
raporda "bugünkü 10 video tamam" de ve bitir (`upload.py` de bu sınırda yüklemeyi kendisi atlar).

Liste kanalın son ~50 videosudur (yaklaşık son 3 gün). Son 48 saatte işlenmiş bir konuyu
(aynı olay ya da aynı kişi/kurumun aynı haberi) yalnızca önemli YENİ bir gelişme varsa ve yeni
gelişmeyi anlatarak tekrar seç.

## 4. Konu seç (bu çalışmada 1 konu)

- Son 24-48 saatin en çok konuşulan, kanalda henüz işlenmemiş konusunu seç; son dakika gelişmeler önceliklidir.
- Çeşitlilik: kanalın son 5 videosunda aynı kategoriden (GÜNDEM, EKONOMİ, SPOR, SİYASET, DÜNYA,
  TEKNOLOJİ, MAGAZİN, SAĞLIK, EĞİTİM, YAŞAM, BİLİM, KÜLTÜR) 3'ten fazla olmasın; denk gelirse
  bir sonraki en güçlü konuya geç.
- **En çok izlenen konu türlerinden üret** (kanal sahibinin isteği). Seçmeden önce bak:

  ```bash
  python3 pipeline/stats.py --top 5
  ```

  Her video, kanal medyanının kaç katı izlendiğiyle sıralanır (yalnızca 24 saati dolanlar).
  Listenin dibindeki çok düşük videoları (onlarca izlenme) konu zayıflığı sayma: bunlar 11 Kasım'da
  aynı anda toplu yüklenenler ve eski düzende günün 11.+ yüklemeleri; YouTube onları dağıtmadı.
  13-17 Kasım verisine göre güçlü adaylar arasında bu sırayla öncelik ver:
  1. **Futbol ve sporcular:** milli takım, büyük kulüpler, Türk ve yıldız sporcular (Alperen
     Şengün 1349, Lukaku 1251, Galatasaray stadı 1180, milli maçlar 940-1172 izlenme).
  2. **Cebe ve günlük hayata dokunan, geniş kitleyi ilgilendiren haberler:** zam, maaş, fiyat,
     ceza, sınav, tatil, hava uyarısı (emekli zammı 1304, MEB sınav yasağı 1042, hız cezası 943).
  3. **Büyük siyasi gelişmeler, tanınan isimlerle** (Özgür Özel 1796).
  Geri planda kalsın: dar kitleli destek programları (KOBİ desteği 154, GSS prim borcu 251),
  sıradan mahkeme ve yargı kararları, uzay/bilim (Voyager 373) ve eğlence (James Bond 314).
  **Siyaset ve yargı haberleri günde en fazla 3:** `--recent` listesinde bugün bu türden 3 video
  varsa başka türden aday seç. Yine de önemli bir son dakika gelişmesini sırf türü yüzünden atlama;
  doğrulama, yayın yasağı ve tarafsızlık kuralları her zaman önce gelir; çeşitlilik kuralını koru.
- **Uygun yeni konu yoksa video ÜRETME ve YÜKLEME** (dolgu, zayıf ya da tekrar içerik kanalı
  bastırır); raporda "bu saat yeni konu yok" de ve bitir.
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

## 5. Senaryoyu yaz: `scripts/TARIH-SSDD.json`

Örnek için `scripts/` klasöründeki önceki dosyalara bak. Kurallar:

Oturumda `social-media-skills:hook-writer` ve `social-media-skills:youtube-shorts` skill'leri
varsa açılış ve başlık için onlardan da yararlan; yoksa aşağıdaki kurallar yeterli.

- `slug`: küçük harf, ASCII, tireli. `category`: yukarıdaki listeden.
- Shorts kuralı: izleyici ilk 1-3 saniyede kaydırıp geçerse video yayılmaz. Her şey bunun için:
  - `title` (ilk karede ekranda duran yazı, ses kapalı da okunur): en fazla 50 karakter, açılışla
    AYNI vaadi taşısın. Kalıplar: soru/açık döngü ("BDDK Başkanı neden istifa etti?"), rakam
    ("17 can kaybı: 3 soruda Aliağa"), doğrudan uyarı ("Yarın vapura binecekseniz dikkat").
  - İlk sahne (`heading` yok): TEK cümle, en fazla 12 kelime; `title` ile aynı merakı açar.
    Selamlama yok ("Merhaba", "Bugün sizlere..."), kanal adı yok, boş giriş yok.
  - Vaat edilen bilgi videoda mutlaka verilir (tık tuzağı yok; yanıltıcı açılış izlenmeyi düşürür).
- `scenes`: 4-5 sahne, toplam 70-100 kelime (25-35 saniye; kapanış otomatik eklenir).
  - Diğer sahnelerde `heading` (en fazla 20 karakter) ve 1-2 kısa cümlelik `text`.
  - Her sahne YENİ bir bilgi verir; dolgu ve tekrar cümlesi yok. Videolar arasında aynı kalıp
    cümleleri tekrarlama ("Peki ne oldu?", "Detaylar şöyle" gibi her videoda aynı açılış/geçiş):
    YouTube birbirinin aynısı şablon içeriği bastırıyor.
  - `stat` isteğe bağlı büyük rakam kartı: `value` en fazla 10 karakter, `label` kısa.
    Sayıyla başlayan değerler (`17+`, `%42`, `7,7 milyon`, `$79,99`) ekranda sayarak açılır.
  - Son sahne: konuyla ilgili TEK kısa soru, en fazla 8 kelime (ekranda "Yorumunu bekliyorum"
    kartı çıkar). Kanal logolu "abone ol" kapanışı (2-3 sn) her videonun sonuna OTOMATİK eklenir
    (`config.json` > `outro_text`); senaryoya ayrıca "abone ol / takipte kal" cümlesi yazma.
- `yt_title`: **en fazla 60 karakter**; konu (kişi/kurum/olay adı ve ne olduğu) **ilk 40
  karakterde**. Mobilde yalnızca ilk ~40 karakter görünür, masaüstü aramada 60'tan sonrası kesilir.
  `#shorts` YAZMA: açıklamada zaten var, başlıkta yer kaplar (yazılırsa yükleme betiği siler).
  Anahtar kelimeler açık yazılsın. Örnek: "Alperen Şengün 43 sayıyla Rockets tarihine geçti" (48).
  Üretim çıktısında yt_title için `[uyarı]` çıkarsa yalnızca senaryodaki `yt_title`'ı kısalt;
  video yeniden üretilmez.
- `description`: 1-2 cümle; ilk cümle konunun anahtar kelimelerini içersin. `sources`: 2 kaynak URL'si.
- `tags`: 4-6 etiket. `hashtags`: konuya özel 2-3 hashtag (ör. `["#BDDK", "#ekonomi"]`);
  açıklamada en üstte görünür. Genel `#shorts #gündem #haber` otomatik eklenir.
- **Görseller (v2 şablonu)** — her sahneye konuya uygun EN AZ BİR görsel alanı ekle, sahneler
  arasında çeşitlilik olsun (her videoda en az bir `map` ya da `chart` ya da `points`):
  - `icon`: her sahnede (giriş dahil) konuya uygun bir Lucide ikon adı, ör. `landmark` (kurum/banka),
    `trending-up`, `trophy`, `cloud-lightning`, `plane`, `gavel`, `factory`, `shirt`, `cpu`,
    `gamepad-2`, `users`, `briefcase`, `heart-pulse`, `map-pin`, `chart-column`, `flame`, `zap`.
    Listeyi görmek için: `cd video && node -e "console.log(Object.keys(require('lucide-react').icons).join(' '))"`
    (PascalCase adı tireli yaz: `CloudLightning` → `cloud-lightning`).
  - `map`: olayın geçtiği yer `{"place": "İzmir", "lat": 38.42, "lon": 27.14, "label": "9 Kasım · Aliağa"}`.
    Türkiye içindeki yerler Türkiye haritasında, yurt dışı yerler dönen dünya küresinde gösterilir.
    Harita sahnesi 3D'dir ve tam ekran açılır: Türkiye içinde kamera şehre iner ve il yükselir;
    yurt dışında küre Türkiye'den hedefe döner. `place` ekranın ortasında büyük yazılır: en fazla
    16 karakter. `label` en fazla 24 karakter. Koordinatları doğrula; emin değilsen `map` kullanma.
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
  Rakamları yazıyla ("on yedi") yaz. Yabancı kelime ve kısaltmalar `okunus.json` sözlüğüyle
  OTOMATİK çevrilir (CEO → Si-İ-O, Apple → Epıl, BDDK → Be-De-De-Ka); bunları `say`'de olduğu gibi
  bırakabilirsin. Sözlükte olmayan kısaltmayı BÜYÜK harf ve tireyle ("Ka-Ye-Ka"), yabancı adı
  okunduğu gibi ("Pleysteyşın") yaz. Boşluklu küçük harf ("si i o") YAZMA: önceki kelimeyle
  birleşip bozuluyor. **Cümle sayısı `text` ile aynı olmalı.**

## 6. Videoları üret ve kontrol et

```bash
python3 pipeline/build.py scripts/TARIH-SSDD.json
```

Her videodan birkaç kare çıkarıp bak (taşan/bozuk yazı var mı) ve süreleri kontrol et (60 sn altı):

```bash
for f in out/TARIH/*.mp4; do ffmpeg -v error -y -ss 8 -i "$f" -frames:v 1 -vf scale=540:-1 "${f%.mp4}.png"; done
```

Sorun varsa senaryoyu düzeltip yalnızca o videoyu yeniden üret (`--only 3`).

`[ok]` satırındaki `ses:` bilgisi okuyan motoru gösterir (ör. `ElevenLabs george (eleven_v4), 640
kredi` ya da `Chatterbox, kanal sahibinin sesi`). Ana ses kullanılamazsa (ör. ElevenLabs kredisi
bitti) betik bunu `[bilgi]` satırıyla yazar ve videoyu yedek sesle baştan üretir; hata değildir.
`[uyarı] ElevenLabs kredisi bitmek üzere` görürsen (kalan kredi satırı, anahtarda izin varsa yazılır)
yüklemeye devam et ve raporda belirt.

`[ok]` satırındaki `miks:` bilgisi sesi özetler (ör. `19 efekt + müzik, -14.0 LUFS / tepe -1.9 dBTP`).
Efektler görsel olaylara (sahne geçişi, fotoğraf, harita iğnesi, sayaç, abone ol tıklaması) otomatik
bağlanır; senaryoya ek alan gerekmez. `basit miks (yedek)` yazıyorsa gelişmiş miks o makinede
çalışmamıştır; bu hata değildir, yüklemeye devam et ve raporda belirt.

`altyazı:` bilgisi altyazı zamanlamasını gösterir: `kelime hizalı 11/12 cümle` normaldir (her kelime
sesteki anında vurgulanır; hizalanamayan cümle orantılı zamanlanır). `oransal` yazıyorsa kelime
hizalama o makinede çalışmamıştır; hata değildir, yüklemeye devam et. Görüntüdeki hafif film greni
bilinçlidir (`config.json` → `grain`); dosyalar bu yüzden ~50 MB olabilir.
`harita: 3D` normaldir; `harita: 2D (yedek)` 3D'nin o makinede çizilemediğini ve videonun eski 2D
haritayla otomatik yeniden üretildiğini gösterir; hata değildir, yüklemeye devam et.

## 7. Yükle

Yüklemeden hemen önce `python3 pipeline/upload.py --recent | head -5` ile son yüklemelere tekrar
bak: başka bir çalışma az önce aynı konuyu yüklediyse YÜKLEME, raporda belirt.

```bash
python3 pipeline/upload.py scripts/TARIH-SSDD.json
```

Betik aynı videoyu iki kez yüklemez (`state/uploaded.json`). Yüklemeyi yalnızca `upload.py`'nin kendi
verdiği hata durdurur: o zaman videoları üretilmiş bırak, yeniden deneme döngüsüne girme ve hatayı
raporla. Üretim adımındaki seslendirme bilgileri (ör. "ElevenLabs ... bu videoda kullanılamadı;
video yedek sesle baştan üretiliyor") beklenen durumlardır; yüklemeyi **engellemez**, yüklemeye
devam et ve raporda hangi sesin kullanıldığını belirt.

## 8. Raporla

Commit ve push YAPMA: zamanlanmış oturumların bu depoya yazma izni yok, kayıt da gerekmiyor (aynı
konuyu tekrarlamamak için 3. adımda kanalın son videolarına bakılıyor). Bir "push edilmemiş commit"
uyarısı görürsen yok say.

Son mesajında yüklenen videoların başlık + bağlantı listesini, atlanan/başarısız adımları ve
nedenlerini yaz.
