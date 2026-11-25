# Haftalık belgesel

Bu dosya haftalık zamanlanmış oturumun izleyeceği adımlardır. Görev **her cuma** çalışır, bir
bölümü baştan sona üretir ve **gizli** yükler. Normalde video **cumartesi 12:00'de (İstanbul)
kendiliğinden yayına girer**; kanal sahibi o zamana kadar YouTube Studio'da izleyip isterse siler
(istisnalar: bölüm 0 → "Yayın kuralı"). Shorts hattından (GUNLUK.md) bağımsızdır; Shorts'un günlük
10 video sayımına girmez (`#belgesel`).

Bölüm: **4 dakika** (3:40-4:30), yatay 1920x1080, belgesel tarzı (tek kamera, arşiv görselleri,
rakam kartları, haritalar). **Konu: aşağıdaki güncel serinin sıradaki bölümü.** Seri bittiğinde ya da
bölüm kurallara uygun yapılamıyorsa yedek konu: gerçek bir siber saldırı, sonuçları ve korunma
önerileri ("SİBER OTOPSİ" serisi; bölüm 2'deki adaylar).

Motor: `belgesel/engine` (cinematic-film; MIT, github.com/Moh4696/cinematic-skill'den uyarlandı).
Motorun kendi kılavuzu `belgesel/engine/SKILL.md` ve `belgesel/engine/references/*.md`; sahne
yazmadan önce `SKILL.md` ile `references/film.md`'yi oku. Örnek pilot (45 sn):
`belgesel/ornek-wannacry/` (script.json + scene.py).

## 0. Güncel seri: YENİ NESİL SUÇ (Türkiye'de yeni nesil suç örgütleri)

Kanal sahibinin ana serisi. Odak: örgütlerin **gençleri ve çocukları nasıl kullandığı, bunun
bedeli, devletin karşı hamlesi ve ailelerin ne yapabileceği**. Suçluyu değil, kurbanı, aileyi ve
önlemeyi anlat. Bölümler (sırayla):

| # | Bölüm | Odak |
|---|---|---|
| 1 | Tetikçi çocuklar | Örgütler neden çocukları kullanıyor; resmi rakamlar; "kolay para" vaadinin gerçek bedeli; aileler için uyarı işaretleri |
| 2 | Ekrandaki suç ilanı | Sosyal medya ve mesajlaşma uygulamalarından eleman toplama (genel, platform/kanal adı ve ilan ayrıntısı yok); dijital ebeveynlik |
| 3 | Haraç ve kurşunlama | İşyerlerine yönelik tehdit ve kurşunlama olayları, esnafın korkusu, ihbar yolları |
| 4 | Sokaklar Güvende | Devletin karşı hamlesi: operasyonlar, yasal düzenlemeler, resmi bilanço |
| 5 | Kara para ve yasa dışı bahis | Örgütlerin parası nereden geliyor; gençleri borca sokan bahis tuzağı |
| 6 | Sahte polis, sahte savcı | Telefon dolandırıcılığı çağrı merkezleri; yaşlıları koruma |

**Sıradaki bölüm:** `python3 pipeline/upload.py --belgeseller` çıktısında "YENİ NESİL SUÇ Bölüm N"
başlıklarına bak; sıradaki = en büyük N + 1 (hiç yoksa 1). 6 bölüm bittiyse yedek konuya geç.

**Yayın kuralı:** `yukleme.json`'da
- Bölüm 1: `"privacy": "private"`, `publish_at` YOK (kanal sahibi izleyip kendisi yayına alır).
- Sonraki bölümler: listede bu seriden "GİZLİ (tarih yok)" duran bir bölüm varsa (sahibi henüz
  onaylamadı) yine `"privacy": "private"` ve tarih yok; yoksa normal kural (cumartesi 12:00).

**Seri kuralları (zorunlu; bölüm 4'teki genel kurallara ek). Biri sağlanamıyorsa o bilgiyi kullanma:**
- **Çocukların kimliği asla:** suça sürüklenen ya da mağdur çocuğun adı, baş harfi, yaşı+mahallesi,
  okulu, yüzü (bulanık bile), sesi, aile bilgisi yok. Tekil çocuk vakası anlatma; resmi toplu
  rakamlar ve genel örüntü kullan.
- **Örgüte reklam yok (TCK 220/8 örgüt propagandası):** örgüt adı, lider/üye adı ya da lakabı,
  sembol, el işareti, şarkı, sosyal medya videosu, silah/para/lüks yaşam görseli yok. "Bir suç
  örgütü", "örgüt lideri olduğu iddia edilen kişi" de. Operasyon adı örgüt adını içeriyorsa onu da
  kullanma. Anlatım "kazanç" değil **bedel** üzerinden: cezaevi, ölüm, yıkılan aileler.
- **Kişi adı yok:** şüpheli, sanık, mağdur adı yok (kesinleşmiş hüküm olsa bile gerekmez). Ad
  yalnızca resmi açıklama yapan kamu görevlisi için (bakan, başsavcı) ve kimin söylediği belirtilir.
- **Yayın yasağı ve gizlilik kontrolü:** kullanacağın her olay/soruşturma için "yayın yasağı" ve
  "kısıtlama kararı" araması yap (haber metinleri, RTÜK duyuruları); kararı olan olayı hiç kullanma.
  Devam eden davada suçu kesinleşmiş gibi anlatma ("iddianameye göre", "savcılığın açıklamasına göre").
- **Yöntem tarifi yok, taklit riski yok:** silah temini, ödeme ve para aktarma yolu, ilan metni,
  fiyat listesi, uygulama/kanal/kullanıcı adı, polisten kaçma, eylem planı anlatılmaz. Okul
  saldırısı ve benzeri taklit riski yüksek olaylar seri dışı.
- **Şiddet anı yok:** güvenlik kamerası, olay yeri, kan, cenaze, gözaltı görüntüsü, kelepçeli kişi
  yok. Haber ajansı/gazete fotoğrafı yok (telif); Commons'tan genel görseller.
- **Siyaset yok:** hükümeti ya da muhalefeti övme/yerme; rakamı kimin açıkladığını söyle, yorum katma.
- **Kaynak:** her rakam ve iddia için resmi açıklama (İçişleri, Adalet Bakanlığı, Emniyet,
  Jandarma, başsavcılık, TBMM, TÜİK) + **en az 2 ana akım yayın** (BBC Türkçe, DW Türkçe, TRT
  Haber, Anadolu Ajansı, büyük gazeteler). Çelişen rakamı kullanma. `kaynaklar.md`'ye yaz.
- **Önleme bölümü:** aileler ve gençler için 3-4 somut adım (uyarı işaretleri: açıklanamayan
  para/eşya, yeni ve gizli çevre, ikinci telefon/gizli uygulama, okuldan kopma; ne yapmalı:
  yargılamadan konuşmak, okul rehberlik servisi, resmi destek ve ihbar hatları). **Hat numaralarını
  resmi sitesinden doğrula** (ör. 112 Acil Çağrı; Aile ve Sosyal Hizmetler Bakanlığı ALO 183);
  doğrulanamayan numarayı yazma.
- **Kapanış sorusu** örgüt ya da olay hakkında bilgi/yorum istemez; ör. "Sence bu çocukları en çok
  kim koruyabilir: aile mi, okul mu? Yaz."

**Başlık:** `YENİ NESİL SUÇ Bölüm N: ...` (toplam en fazla 70 karakter; kanal sahibinin
"SİBER OTOPSİ Bölüm 1: ..." biçimiyle aynı). Açıklamanın ilk satırı konu; sonda:
"Bu video bilgilendirme ve farkındalık amaçlıdır. Kişilerin adı ve çocukların kimliği bilerek
verilmemiştir; rakamlar resmi açıklamalardan alınmıştır." ve doğrulanmış destek/ihbar hatları.

**Akış (4 dk; bölüm 5'teki tablo yerine):**

| Süre | Bölüm |
|---|---|
| 0:00-0:20 | Soğuk açılış: resmi bir rakam ya da genel bir an, isimsiz ("Bir gece yarısı bir işyerinin camına mermi isabet ediyor. Tetiği çeken on altı yaşında.") |
| 0:20-1:20 | Ne oluyor: olgu, resmi rakamlar, ne zamandan beri |
| 1:20-2:20 | Nasıl işliyor ve neden gençler (genel; tarif yok): vaat edilen ile gerçek |
| 2:20-3:00 | Bedel ve karşı hamle: cezalar, operasyonlar, aileler |
| 3:00-3:50 | **Aileler ve gençler ne yapabilir?** 3-4 adım, her biri tek satır, ikon + kısa kart |
| 3:50-4:10 | Kapanış: tek cümle + tek soru + abone ol |

**Ton:** heyecan = tempo, merak ve gerilim; eğlence ya da hayranlık değil. `narrate_el.py`'ye
`--tone "[dramatic]"`; açılış ve gerilim satırlarına `"tone": "[tense]"`; önleme bölümündeki
satırlara `"tone": ""` (etiketsiz, sakin ve net). `[excited]` kullanma.

**Görseller (bölüm 8'deki asgari sayılar geçerli, içeriği şöyle):** Türkiye haritası (resmi
açıklamadaki il sayısı/dağılım, `look=SIBER`), resmi rakamlar için `Counter` ve `Timeline`,
Commons'tan **genel ve kimliksiz** fotoğraflar "TEMSİLÎ" etiketiyle (gece şehir, adliye ya da
emniyet binası dış cephesi, boş sokak, okul binası, telefon tutan el; yüzü seçilen kişi yok),
canlandırma: `Screen(kind="chat")` (genel ifadeli mesajlaşma: kanal adı "Kanal", mesajlar "Kolay
para. Hemen başla." gibi; gerçek ilan metni, fiyat, kullanıcı adı yok); ölçek için `Counter` ya
da `DeviceGrid` (ör. operasyon yapılan il sayısı). İkonlar: users, users-round,
smartphone, message-circle, messages-square, gavel, scale, landmark, siren, shield, shield-check,
banknote, house, school, hand-heart, handshake, eye, phone, megaphone, ear, triangle-alert.
Küçük resim: karanlık şehir ya da telefon karesi + 2-4 kelime ("TETİKÇİ ÇOCUKLAR"); silah, yüz yok.

## 1. Kurulum

```bash
bash setup.sh && bash belgesel/setup.sh
```

## 2. Konu seç

Güncel seri sürüyorsa konu onun sıradaki bölümüdür (bölüm 0); bu bölümün geri kalanı yedek siber
konular içindir. Kanalın önceki belgeselleri ve durumları (tekrar etme):

```bash
python3 pipeline/upload.py --belgeseller
```

Yedek siber adaylar (başlık `SİBER OTOPSİ Bölüm N: ...`; önce izleyicinin kendi hayatına
dokunanlar, korunma önerileri ona göre işe yarar):
- Fidye yazılımları: WannaCry (2017, pilotta kısaca işlendi; tam bölüm yapılabilir), NotPetya ve
  Maersk (2017), Colonial Pipeline (2021), Kaseya (2021)
- Veri sızıntıları ve hesap ele geçirme: Equifax (2017), Yahoo (2013-2014), 23andMe (2023),
  LinkedIn, Facebook 533 milyon kullanıcı verisi (2021)
- Sosyal mühendislik ve oltalama: Twitter ünlü hesaplar (2020), MGM Resorts (2023), SIM kart
  değiştirme dolandırıcılıkları
- Altyapı ve tedarik zinciri: Stuxnet (2010), SolarWinds (2020), Ukrayna elektrik şebekesi (2015),
  Mirai ve kameralar (2016)
- Banka soygunları: Bangladeş Merkez Bankası (2016)
Türkiye'den bir olay seçersen yalnızca resmi açıklaması ve yargı süreci net olanı seç; kişileri
suçlu ilan etme. Konuyu web aramasıyla ve YouTube'da (Türkçe) ne kadar ilgi gördüğüne bakarak seç.
Aynı türü (ör. iki fidye yazılımı) üst üste seçme.

## 3. Araştır ve doğrula

- Her tarih, rakam ve iddia için **en az 2 güvenilir kaynak**: resmi raporlar (ABD CISA, FBI,
  Europol, İngiltere NAO, mahkeme belgeleri, şirketin kendi açıklaması), ana akım haber (BBC,
  Reuters, AP, Wired), Britannica/Vikipedi ve oradaki kaynaklar. Çelişen rakamda temkinli ifade
  ("en az", "tahminen") ya da o rakamı hiç kullanma.
- Faile dair kesin hüküm verme: "ABD ve İngiltere hükümetleri saldırıyı Kuzey Kore ile
  ilişkilendirdi" gibi, kimin söylediğini belirterek yaz.
- Kaynakları proje klasöründe `kaynaklar.md` dosyasına (URL + hangi bilgi) yaz.

## 4. Güvenlik ve etik kuralları (zorunlu)

- **Saldırı tarifi YOK:** zararlı yazılımın nasıl yazıldığı/çalıştırıldığı, açık kodu, komut,
  araç adı ile kullanım adımı, sistemlere sızma yöntemi adım adım anlatılmaz. "Windows'taki eski bir
  açığı kullandı; yaması iki ay önce yayınlanmıştı" düzeyinde kal.
- Saldırganı övme, kahramanlaştırma; kurbanların kişisel verisini (sızan bilgiler, ekran
  görüntülerindeki adlar) gösterme.
- Gerçek kişi/olay için yapay zekâ görseli yok. Kod içinde çizilen ekran/belge canlandırmasıysa
  üstüne "CANLANDIRMA" yaz; yalnızca gerçekte yazmış metni alıntıla (ör. fidye ekranındaki cümle).
- Şirket logolarını büyük görsel olarak kullanma; adı yazıyla geç.
- Korunma önerileri genel ve güvenli olsun (güncelleme, yedek, iki aşamalı doğrulama, parola
  yöneticisi, şüpheli bağlantı/ek, SIM kilidi, resmi kanaldan teyit); ürün reklamı yapma.

## 5. Senaryo: `belgesel/projeler/SLUG/script.json`

```bash
mkdir -p belgesel/projeler && python3 belgesel/engine/new_project.py belgesel/projeler/SLUG
mkdir -p belgesel/projeler/SLUG/fonts && cp belgesel/fonts/*.ttf belgesel/projeler/SLUG/fonts/
```

Biçim `belgesel/ornek-wannacry/script.json` gibi: `takes` (bölümler) içinde `lines`; her satırda
`text` (ekranda/altyazıda), `spoken` (rakamlar yazıyla, yabancı adlar okunduğu gibi: "Vana Kray",
"Markıs Haçins"), `hero` (o satırda kameranın baktığı tek şey), `typed` (ekrana basılan kısa yazı).
**Anlatım heyecanlı olsun (kanal sahibinin isteği):** şimdiki zamanla anlat ("ekranlar kırmızıya
dönüyor"), kısa ve vurucu cümleler kur, bölüm geçişlerinde merak bırak ("Ve durmuyor:", "Fatura mı?",
"Ve ertesi gün…"), her bölümün sonunda bir sonrakine çeken bir soru ya da ters köşe koy. Satıra
`"tone"` ile duygu etiketi verilebilir: varsayılan `[excited]`; gerilim için `[tense]`, ağır anlar için
`[dramatic]` (etiket okunmaz, tonu belirler). Örnek: `belgesel/ornek-wannacry/script.json`.
Toplam **520-600 kelime** (4 dakika; tempolu okumada 600'e yakın yaz). Akış:

| Süre | Bölüm |
|---|---|
| 0:00-0:20 | Soğuk açılış: en çarpıcı an, tek cümleyle soru ("Bir cuma sabahı 150 ülkede ekranlar kilitlendi.") |
| 0:20-1:30 | Ne oldu: tarih, ilk belirti, nasıl yayıldı (teknik tarif olmadan) |
| 1:30-2:30 | Sonuçlar: etkilenenler, rakamlar, gerçek hayattaki karşılığı (hastane, akaryakıt, banka) |
| 2:30-3:00 | Nasıl durdu, kim sorumlu tutuldu |
| 3:00-3:50 | **"Bu tür saldırıdan nasıl korunursun?"** 3-4 öneri, her biri tek satır ve tek kart |
| 3:50-4:10 | Kapanış: tek cümle ders + tek soru ("Sen hiç böyle bir mesaj aldın mı? Yaz.") + abone ol |

Kontrol: `python3 belgesel/engine/make_beats.py --project belgesel/projeler/SLUG` (uyarıları düzelt).

## 6. Seslendirme

```bash
python3 belgesel/narrate_el.py --project belgesel/projeler/SLUG
python3 belgesel/engine/build_narration.py --project belgesel/projeler/SLUG
```

Brian (ElevenLabs, `config.json` → `belgesel_model`, tam model); okunuş sözlüğü uygulanır.
YENİ NESİL SUÇ serisinde ilk komuta `--tone "[dramatic]"` ekle (bölüm 0, "Ton"). Süre
3:40'ın altında ya da 4:30'un üstündeyse senaryoyu kısalt/uzat, yeniden seslendir.

## 7. Görseller

- Arşiv fotoğrafları: `python3 belgesel/engine/fetch_commons.py search "..."` ve `get` (yalnızca
  serbest lisanslılar; atıf `credits.md`'ye yazılır). Liste `photos.json`'da. Kişi fotoğrafı yalnızca
  hikâyede adı geçen kamuya mal olmuş kişiler için.
- Yayılmayı ya da yerleri göstermek için harita: `map.json` + `python3 belgesel/engine/make_map.py`.
- Sonra: `python3 belgesel/engine/prep_assets.py --project belgesel/projeler/SLUG`.

## 8. Sahne ve kontrol

`scene.py`'yi `references/film.md`'ye göre yaz (örnek: `belgesel/ornek-wannacry/scene.py`).
Görünüm `night`, vurgu kırmızı (saldırı) ve sarı (rakam, öneri). Her satırda tek kahraman.

**Görsel zenginlik (kanal sahibinin isteği; düz yazı/kart videosu YAPMA).** Motorun parçalarına ek
olarak `belgesel/engine/extras.py` var (`from extras import Icon, Screen, DeviceGrid, Timeline, SIBER`):
- `Screen(x, y, w, t_in, kind, title, lines)`: monitörde hareketli CANLANDIRMA. `ransom` (fidye ekranı,
  geri sayım), `terminal` (satır satır kayıt; "[!]" ile başlayan satır kırmızı), `email` (oltalama
  e-postası: Kimden, Konu, gövde, bağlantı), `progress` (dosyalar şifreleniyor), `login` (giriş formu),
  `chat` (mesajlaşma: title kanal adı; ">" ile başlayan satır giden mesaj, diğerleri gelen).
  Ekranda yalnızca genel ifadeler yaz; komut, kod, gerçek kişi verisi yok.
- `DeviceGrid(x, y, cols, rows, cell, t_in, dur)`: bilgisayarlar sırayla kırmızıya döner (yayılma).
- `Icon(ad, x, y, size, t_in, ring=RENK, label="...")`: `belgesel/icons` içindeki 90 Lucide ikonu
  (lock, shield-check, hospital, server, skull, mail-x, smartphone, key-round, refresh-cw, wifi-off,
  fuel, landmark, banknote, credit-card, cloud, users, siren, ...).
- `Timeline(x, y, w, [(t, "TARİH", "olay"), ...], t_in)`, koyu harita: `GeoMap(doc.map(ad), K, look=SIBER)`.
Her bölümde en az: **5 gerçek fotoğraf/belge** (Commons; kişi, kurum, yer, olayın gerçek haritası
ya da belgesi; bulunamazsa sunucu, hastane, şehir gibi temsilî fotoğraf "TEMSİLÎ" etiketiyle),
**1 harita**, **2 ekran canlandırması** (saldırıya uygun tür), **1 ölçek görseli** (DeviceGrid ya da
sayaç) ve korunma bölümünde **her öneri için ikon + kısa kart**. Arka arkaya ikiden fazla satır
yalnızca yazıdan oluşmasın; fotoğrafı büyük ve kameraya yakın kullan, üstüne ikon/ekran bindir.

```bash
python3 belgesel/engine/render.py --project belgesel/projeler/SLUG --probe T1,T2,... --size 1280x720
```

Her satırdan bir kare al, kareleri tek sayfada birleştirip **bak**: yazı okunuyor mu, kadrajdan
taşan var mı, koyu üstüne koyu yazı var mı, boş kare var mı. Düzeltmeden render alma.

## 9. Ses, render, küçük resim

```bash
cd belgesel/projeler/SLUG
python3 ../../engine/render.py --project . --cues
python3 ../../engine/build_sfx.py --project .
python3 ../../engine/mix_soundtrack.py --project . --music ../../../assets/sounds/music/gergin-1.mp3 --music-eq-dip 3 --music-db -4
python3 ../../engine/render.py --project . --size 1920x1080 --out out/film.mp4 --audio audio/mix.m4a
python3 ../../engine/burn_captions.py --project . --video out/film.mp4 --audio audio/mix.m4a --style clean --out out/final.mp4
python3 ../../thumbnail.py --project . --t SANIYE --text "2-4 KELİME" --small "KONU · YIL" --accent-word KELİME
cd ../../..
```

Render 1080p'de 4 dakika için ~20-30 dk sürer; komutlara yeterli zaman aşımı ver. `final.mp4`'ten
birkaç kare al ve bak. Müzik için `gergin-1` ya da `gergin-2` kullan (haftadan haftaya değiştir).
Küçük resimde en çarpıcı karenin üstüne 2-4 kelime; başlıkla aynı vaadi taşısın.

## 10. Yükle (gizli; cumartesi 12:00'de yayın ya da sahibin onayı)

`belgesel/projeler/SLUG/yukleme.json`:

```json
{
  "slug": "wannacry",
  "video": "out/final.mp4",
  "thumbnail": "out/thumbnail.png",
  "yt_title": "WannaCry: 150 ülkeyi bir günde kilitleyen saldırı ve korunma yolları",
  "description": "2017'de ... İlk iki cümlede konu ve anahtar kelimeler.",
  "chapters": [[0, "Giriş"], [20, "Ne oldu?"], [90, "Sonuçlar"], [150, "Nasıl durdu?"], [180, "Nasıl korunursun?"]],
  "sources": ["https://...", "https://..."],
  "credits": ["Fotoğraf adı — yazar, lisans (bağlantı)"],
  "tags": ["wannacry", "fidye yazılımı"],
  "publish_at": "2026-11-28T12:00:00"
}
```

Sahibin onayına bırakılacak bölümde `publish_at` yerine `"privacy": "private"` yaz (bölüm 0,
"Yayın kuralı"): video gizli kalır, tarih konmaz.

- `yt_title` en fazla 70 karakter; konu ilk 40 karakterde; tık tuzağı yok.
- `chapters`: ilki 0, en az 3 bölüm, her biri en az 10 sn; sürelerini `audio/timing.json`'dan al.
- `publish_at`: bu haftanın cumartesisi 12:00 (İstanbul); "Yayın kuralı" aksini söylüyorsa yok.

```bash
python3 pipeline/upload.py --belgesel belgesel/projeler/SLUG/yukleme.json
```

Küçük resim yüklenemezse (kanal doğrulaması) video yine yüklenir; raporda belirt.

## 11. Rapor

Commit ve push YAPMA. Son mesajda: konu (seri ve bölüm no), video bağlantısı (gizli; yayın zamanı ya
da "sahibin onayını bekliyor"), süre, kullanılan kaynaklar, yayın yasağı kontrolünün sonucu,
ElevenLabs kredisi, atlanan/sorunlu adımlar.
