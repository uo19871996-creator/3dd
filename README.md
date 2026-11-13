# Gündem Shorts

Türkiye'de son 3 günde en çok konuşulan 5 konuyu her gün seçip her biri için dikey (1080x1920)
bir YouTube Shorts videosu üreten ve kanala yükleyen otomasyon.

## Nasıl çalışır

| Adım | Dosya | Ne yapar |
| --- | --- | --- |
| Aday toplama | `pipeline/trends.py` | Google Trends TR + Google Haberler TR başlıklarını listeler |
| Senaryo | `scripts/TARIH.json` | Seçilen 5 konunun metni (günlük oturum yazar, kaynaklarıyla) |
| Üretim | `pipeline/build.py` | Türkçe seslendirme + altyazı zamanlaması + Remotion ile MP4 |
| Ses | `pipeline/tts_chatterbox_worker.py`, `pipeline/voice.py` | Chatterbox ile kanal sahibinin sesi; ses örneği şifreli saklanır |
| Ses kontrolü | `pipeline/check_audio.py` | Seslendirmeyi yazıya döker (telaffuz kontrolü, isteğe bağlı) |
| Yükleme | `pipeline/upload.py` | YouTube Data API ile yükler, `state/uploaded.json`'a kaydeder |

Görsel şablon `video/src/Short.tsx` içindedir (Remotion/React). Kanal adı, görünürlük ve etiketler
`config.json` ile değişir. Günlük adımlar `GUNLUK.md` dosyasındadır.

## Elle çalıştırma

```bash
bash setup.sh
```

```bash
python3 pipeline/build.py scripts/2026-11-11.json
```

```bash
python3 pipeline/upload.py scripts/2026-11-11.json
```

## YouTube bağlantısı

Yükleme için bir Google Cloud projesinde OAuth istemcisi gerekir. Depoya hiçbir gizli bilgi yazılmaz:

- `client_id` ve `client_secret`: bulut ortamının ağ kimliği olarak (`oauth2.googleapis.com`, Basic)
  ya da `YT_CLIENT_ID` / `YT_CLIENT_SECRET` ortam değişkenleri olarak.
- `YT_REFRESH_TOKEN`: ortam değişkeni. Kapsamlar: `youtube.upload` ve `youtube.readonly`.

Bağlantıyı denemek için:

```bash
python3 pipeline/upload.py --check
```

## Lisans notları

- **Ses motoru** `config.json` içindeki `"tts"` ile seçilir:
  - `"chatterbox"`: Resemble AI Chatterbox Multilingual (MIT lisansı, ticari kullanım serbest).
    `assets/ses-ornegi.wav.enc` varsa kanal sahibinin sesiyle konuşur; yoksa modelin kendi sesini
    kullanır. İşlemcide video başına yaklaşık 6–7 dakika sürer; `setup.sh` ayrı bir sanal ortam
    (`.venv-tts`) kurar ve modeli (~3,5 GB) indirir.
  - `"google"`: Google Cloud Text-to-Speech (`google_voice`); anahtar `texttospeech.googleapis.com`
    için ortamın ağ kimliği (`X-Goog-Api-Key`) ya da `GOOGLE_TTS_API_KEY` ile verilir.
  - `"piper"`: çevrimdışı Piper `tr_TR-dfki-medium`; diğerleri çalışmazsa otomatik yedek. Eğitim
    verisi CC BY-NC-SA 4.0 lisanslıdır; para kazanan bir kanalda ana ses olarak kullanılmamalıdır.
- **Ses örneği:** yalnızca kanal sahibinin kendi sesi kullanılır. Örnek, ortamdaki
  `YT_REFRESH_TOKEN`'dan türetilen anahtarla AES-256 şifreli saklanır; refresh token değişirse
  `python3 pipeline/voice.py encrypt <kayıt>` ile yeniden şifrelenmelidir.
- **Remotion:** bireyler ve 3 kişiye kadar ekipler için ücretsizdir; daha büyük şirketler lisans almalıdır.
- **Yazı tipi:** Montserrat (SIL Open Font License).
