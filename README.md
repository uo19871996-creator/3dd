# Gündem Shorts

Türkiye'de son 3 günde en çok konuşulan 5 konuyu her gün seçip her biri için dikey (1080x1920)
bir YouTube Shorts videosu üreten ve kanala yükleyen otomasyon.

## Nasıl çalışır

| Adım | Dosya | Ne yapar |
| --- | --- | --- |
| Aday toplama | `pipeline/trends.py` | Google Trends TR + Google Haberler TR başlıklarını listeler |
| Video izleme | `araclar/izle.py` | Bir videoyu kare, OCR, döküm ve tempo olarak inceler (skill: `video-izle`) |
| Viral araştırma | `pipeline/viral.py` | YouTube TR trendleri + en çok izlenen/etkileşim alan Türkçe kısa videolar (yalnız konu fikri) |
| Günlük karışım | `pipeline/upload.py --today` | Bugün kaç haber/viral yüklendi, bu çalışma hangi türü üretmeli (`daily_mix`: 7 haber + 3 viral) |
| Senaryo | `scripts/TARIH.json` | Seçilen 5 konunun metni (günlük oturum yazar, kaynaklarıyla) |
| Üretim | `pipeline/build.py` | Türkçe seslendirme + altyazı zamanlaması + Remotion ile MP4 |
| Ses | `pipeline/tts_chatterbox_worker.py`, `pipeline/voice.py` | Chatterbox ile kanal sahibinin sesi; ses örneği şifreli saklanır |
| Ses kontrolü | `pipeline/check_audio.py` | Seslendirmeyi yazıya döker (telaffuz kontrolü, isteğe bağlı) |
| Müzik ve efekt | `pipeline/audio_fx.py`, `pipeline/el_sounds.py` | Miks; ElevenLabs müzik/efekt kütüphanesi (`assets/sounds`, bir kez üretilir) |
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

- **Ses motoru** `config.json` içindeki `"tts"` ile seçilir. Motor açılamazsa ya da video sırasında
  kullanılamaz olursa video `"tts_fallback"` sırasındaki motorla (varsayılan: Chatterbox, sonra Piper)
  baştan üretilir; bir videoda iki ses karışmaz.
  - `"elevenlabs"`: ElevenLabs API. Ses `elevenlabs_voice` (hazır ses adı: george, brian, daniel,
    sarah, alice ya da klon sesin kimliği), model `elevenlabs_model` (`eleven_v4`: harf başına 1
    kredi; `eleven_v4_turbo`: 0,5 kredi). Anahtar `api.elevenlabs.io` için ortamın ağ kimliği
    (`xi-api-key`) ya da `ELEVENLABS_API_KEY` ile verilir. Ticari kullanım (para kazanan kanal) ücretli
    planda serbesttir. Video başına ~600–700 harf okunur; `[ok]` satırı harcanan krediyi yazar.
  - `"chatterbox"`: Resemble AI Chatterbox Multilingual (MIT lisansı, ticari kullanım serbest).
    `assets/ses-ornegi.wav.enc` varsa kanal sahibinin sesiyle konuşur; yoksa modelin kendi sesini
    kullanır. İşlemcide video başına yaklaşık 6–7 dakika sürer; `setup.sh` ayrı bir sanal ortam
    (`.venv-tts`) kurar ve modeli (~3,5 GB) indirir.
  - `"google"`: Google Cloud Text-to-Speech (`google_voice`); anahtar `texttospeech.googleapis.com`
    için ortamın ağ kimliği (`X-Goog-Api-Key`) ya da `GOOGLE_TTS_API_KEY` ile verilir.
  - `"piper"`: çevrimdışı Piper `tr_TR-dfki-medium`; diğerleri çalışmazsa otomatik yedek. Eğitim
    verisi CC BY-NC-SA 4.0 lisanslıdır; para kazanan bir kanalda ana ses olarak kullanılmamalıdır.
- **Müzik ve efektler:** `assets/sounds` ElevenLabs ile üretildi (`pipeline/el_sounds.py`, Creator planı;
  ücretli planda ticari kullanım serbest). 4 ruh hali x 2 parça müzik (haber, gergin, enerjik, modern;
  kategoriye göre seçilir) ve 8 efektin 2'şer çeşidi. Videolar üretilirken API çağrılmaz, kredi
  harcanmaz. Kütüphane yoksa ya da `config.json` → `"sounds": "synth"` ise eski sentez müzik/efekt
  kullanılır. Müzik seviyesi `library_music_db` ile ayarlanır (varsayılan -3 dB). Yeniden üretmek:
  `python3 pipeline/el_sounds.py --force` (müzik dakikası ~900 kredi).
- **Ses örneği:** yalnızca kanal sahibinin kendi sesi kullanılır. Örnek, ortamdaki
  `YT_REFRESH_TOKEN`'dan türetilen anahtarla AES-256 şifreli saklanır; refresh token değişirse
  `python3 pipeline/voice.py encrypt <kayıt>` ile yeniden şifrelenmelidir.
- **Remotion:** bireyler ve 3 kişiye kadar ekipler için ücretsizdir; daha büyük şirketler lisans almalıdır.
- **Yazı tipi:** Montserrat (SIL Open Font License).
