# Gecə işçisi: hər 2 gündən bir YENİ söhbət (istifadəçi 11-15: «hər dəfə analiz bu söhbətdə başlayır… 2 gündə bir yeni söhbətdə et»)

Hər gecə 02:37 TR scheduled task bu söhbətə (gecə işçisi sessiyasına) yazır: «gece-sessiyasi.md-ni oxu və əməl et».
Bir işçi sessiya **2 gecə** işləyir, 2-ci gecənin sonunda növbəti işçini açır və tapşırığı ona ötürür (§3).
İstifadəçi Orxan bu işi tam həvalə edib — təsdiq gözləmə. Cavablar Azərbaycanca, qısa.

## 1. Qurulum (hər yeni sessiyada BİR dəfə, ilk mesajda)
1. `/home/user/constara-instagram` (sessiya mənbəyi) → `git fetch origin main && git checkout -B claude/kind-goldberg-uxtrft origin/main`. CLAUDE.md-ni oxu.
2. `pip install -q kokoro-onnx soundfile scipy` ; `mkdir -p /home/user/kokoro && cd /home/user/kokoro` →
   `curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx` və `.../voices-v1.0.bin`.
3. `add_repo` (OrkhanMirab / constara-stats, access push) → `git clone https://github.com/OrkhanMirab/constara-stats /home/user/constara-stats`.
4. `add_repo` (OrkhanMirab / Constara, access read) → `git clone --depth 1 https://github.com/OrkhanMirab/Constara /home/user/Constara`.
5. CLAUDE.md «Gecə tapşırığı» sətrində işçi sessiya ID-sini yenilə (get_session → öz id), commit + `git push origin HEAD:main` (main push-un işlədiyini də yoxlayır).
   Push alınmasa → PushNotification ilə istifadəçiyə xəbər ver.

## 2. Hər gecə (trigger gələndə)
1. `cd /home/user/constara-instagram && git fetch origin main && git checkout -B claude/kind-goldberg-uxtrft origin/main`. CLAUDE.md-də «⭐ YALNIZ METAFOR ÜSLUBU», «🧪 DAİMİ YARADICILIQ», «🤖 Avtomatik gündəlik sistem», «🧠 Analiz agenti» və `video-src/_alet/gun-plani.md`. `plan/<bugün>.json` artıq varsa — toxunma, yalnız çatışmayanı tamamla.
2. ANALİZ: constara-stats `git pull`; `cedvel.md` 4 saatdan köhnədirsə `topla.yml`-ı actions_run_trigger ilə işə sal və yenilənməsini gözlə; `python3 analiz.py 14` + son postların snapshot-ları; `analiz/<tarix>.md` yaz + push; nəticələri `video-src/_alet/oyrenilenler.md`-yə (xam rəqəmsiz).
3. PLAN — **yalnız 2 Reels (14:30, 20:30), YALNIZ METAFOR ÜSLUBU**, istifadəçinin son istəyi: **10–12 s, sürətli, LOOP, rəngli, pro; ortalama izləmə əsasdır** (M15, M07 nümunələri). `video-src/_metafor/` mühərriki, `ideyalar.md` (istifadə olunmamış və ya yeni), diktor `--tts /home/user/kokoro`. Kopyalama yox. Hər gün 1 yaradıcı yenilik. Arxivdə uyğun «paylaşılmayıb» video varsa — işlət. Render → açar kadrlara bax → `reels/<tarix>` budağına (`video-src/_alet/reels.py` push_branch) → planı 12:00-dan əvvəl `git push origin HEAD:main`. Platformaya məxsus xəta olmuş videonu yalnız o platformaya təkrar göndər (`"platforms": ["instagram"]`).
4. ARXİV: `python3 /home/user/constara-stats/arxiv.py /home/user/constara-instagram`. Budaq SİLMƏ. Dünənki `posted/*/result.json` platforma xətalarına bax.
5. Meta xətası (code 200/190, «restricted») və ya push xətası → kökdə `PAUSE` + PushNotification.
6. Hesabat (Azərbaycanca 4–6 sətir) + hər iki MP4 SendUserFile + `paylasim.md` (TikTok/YouTube; başlıq ≤100 simvol, açıklama linksiz).

## 3. Rotasiya (bu sessiyanın 2-ci gecəsinin SONUNDA)
Bu söhbətdə artıq bir gecə işi görülübsə (söhbət tarixçəsinə bax), hesabatdan sonra:
1. `create_session(source_url="https://github.com/OrkhanMirab/constara-instagram", title="Constara gecə işçisi <sabahkı tarix>", permission_mode="auto",
   prompt="Sən Constara gecə işçisisən. /home/user/constara-instagram-da `git fetch origin main && git checkout -B claude/kind-goldberg-uxtrft origin/main`, sonra video-src/_alet/gece-sessiyasi.md-ni oxu və §1 Qurulumu indi et. Sonra gecə tapşırığını gözlə.")`
2. `create_trigger(name="Constara: gecə analiz + plan", cron_expression="CRON_TZ=Europe/Istanbul 37 2 * * *", persistent_session_id=<yeni sessiya>, initiation="human_schedule",
   prompt="Gecə tapşırığı (istifadəçi Orxan bu işi tam həvalə edib; təsdiq gözləmə): /home/user/constara-instagram-da git fetch origin main && git checkout -B claude/kind-goldberg-uxtrft origin/main, sonra video-src/_alet/gece-sessiyasi.md-ni oxu və §2-yə (lazım olsa §3-ə) tam əməl et.")`
3. Öz trigger-ini söndür: `list_triggers` → persistent_session_id = bu sessiya olan aktiv trigger → `update_trigger(enabled=false)`.
4. İstifadəçiyə 1 sətir: «Növbəti 2 gecə yeni söhbətdə: <başlıq>». Bu sessiyada başqa iş görmə.
