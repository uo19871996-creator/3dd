# Haftalık belgesel: siber saldırılar ve korunma

Bu dosya haftalık zamanlanmış oturumun izleyeceği adımlardır. Görev **her cuma** çalışır, bir
bölümü baştan sona üretir ve **gizli** yükler. Video **cumartesi 12:00'de (İstanbul) kendiliğinden
yayına girer**. Kanal sahibi o zamana kadar videoyu YouTube Studio'da izleyip isterse siler.
Shorts hattından (GUNLUK.md) bağımsızdır; Shorts'un günlük 10 video sayımına girmez (`#belgesel`).

Bölüm: **4 dakika** (3:40-4:30), yatay 1920x1080, belgesel tarzı (tek kamera, arşiv görselleri,
rakam kartları, haritalar). Konu her hafta **gerçek bir siber saldırı, sonuçları ve izleyicinin o
tür saldırıdan korunması için 3-4 somut öneri**.

Motor: `belgesel/engine` (cinematic-film; MIT, github.com/Moh4696/cinematic-skill'den uyarlandı).
Motorun kendi kılavuzu `belgesel/engine/SKILL.md` ve `belgesel/engine/references/*.md`; sahne
yazmadan önce `SKILL.md` ile `references/film.md`'yi oku. Örnek pilot (45 sn):
`belgesel/ornek-wannacry/` (script.json + scene.py).

## 1. Kurulum

```bash
bash setup.sh && bash belgesel/setup.sh
```

## 2. Konu seç

Kanalın önceki bölümleri (tekrar etme):

```bash
python3 pipeline/upload.py --recent 300 | grep belgesel
```

Adaylar (önce izleyicinin kendi hayatına dokunanlar; korunma önerileri ona göre işe yarar):
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
Toplam **520-600 kelime** (4 dakika). Akış:

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

Brian (ElevenLabs, `config.json` → `belgesel_model`, tam model); okunuş sözlüğü uygulanır. Süre
3:40'ın altında ya da 4:30'un üstündeyse senaryoyu kısalt/uzat, yeniden seslendir.

## 7. Görseller

- Arşiv fotoğrafları: `python3 belgesel/engine/fetch_commons.py search "..."` ve `get` (yalnızca
  serbest lisanslılar; atıf `credits.md`'ye yazılır). Liste `photos.json`'da. Kişi fotoğrafı yalnızca
  hikâyede adı geçen kamuya mal olmuş kişiler için.
- Yayılmayı ya da yerleri göstermek için harita: `map.json` + `python3 belgesel/engine/make_map.py`.
- Sonra: `python3 belgesel/engine/prep_assets.py --project belgesel/projeler/SLUG`.

## 8. Sahne ve kontrol

`scene.py`'yi `references/film.md`'ye göre yaz (örnek: `belgesel/ornek-wannacry/scene.py`).
Görünüm `night`, vurgu kırmızı (saldırı) ve sarı (rakam, öneri). Her satırda tek kahraman; korunma
önerileri bölümünde her öneri ayrı kart, sırayla.

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
python3 ../../engine/mix_soundtrack.py --project . --music ../../../assets/sounds/music/gergin-1.mp3 --music-eq-dip 3
python3 ../../engine/render.py --project . --size 1920x1080 --out out/film.mp4 --audio audio/mix.m4a
python3 ../../engine/burn_captions.py --project . --video out/film.mp4 --audio audio/mix.m4a --style clean --out out/final.mp4
python3 ../../thumbnail.py --project . --t SANIYE --text "2-4 KELİME" --small "KONU · YIL" --accent-word KELİME
cd ../../..
```

Render 1080p'de 4 dakika için ~20-30 dk sürer; komutlara yeterli zaman aşımı ver. `final.mp4`'ten
birkaç kare al ve bak. Müzik için `gergin-1` ya da `gergin-2` kullan (haftadan haftaya değiştir).
Küçük resimde en çarpıcı karenin üstüne 2-4 kelime; başlıkla aynı vaadi taşısın.

## 10. Yükle (gizli, cumartesi 12:00'de yayın)

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

- `yt_title` en fazla 70 karakter; konu ilk 40 karakterde; tık tuzağı yok.
- `chapters`: ilki 0, en az 3 bölüm, her biri en az 10 sn; sürelerini `audio/timing.json`'dan al.
- `publish_at`: bu haftanın cumartesisi 12:00 (İstanbul).

```bash
python3 pipeline/upload.py --belgesel belgesel/projeler/SLUG/yukleme.json
```

Küçük resim yüklenemezse (kanal doğrulaması) video yine yüklenir; raporda belirt.

## 11. Rapor

Commit ve push YAPMA. Son mesajda: konu, video bağlantısı (gizli, yayın zamanı), süre, kullanılan
kaynaklar, ElevenLabs kredisi, atlanan/sorunlu adımlar.
