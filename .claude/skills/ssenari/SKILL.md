---
name: ssenari
description: Constara Reels/Shorts üçün yeni video ssenarisi yaz (sadə, işıqlı, hamıya aydın). Yeni video, yeni metafor, gündəlik plan videosu və ya «ssenari yaz/qur» istənəndə HƏMİŞƏ bu skill-dən istifadə et — render və önizləmədən ƏVVƏL.
---

# Ssenari skill-i (istifadəçi qərarı 2026-11-17)

İstifadəçi: «Videolar çox qaranlıqdır. Daha başa düşülən olmalıdır. Bəsit, amma hamıya xitab edən.»
Bu skill hər yeni ssenaridən əvvəl işlənir. Nəticə: qısa ssenari kartı (aşağıdakı format) → sonra CLAUDE.md «MUTLƏQ QAYDA #1» (canlı HTML önizləmə → təsdiq → render).

## 1. Əsas test: «Səssiz, 3 saniyə, 12 yaşlı uşaq»
Ssenari yalnız bu üç suala «bəli» cavabı alanda keçir:
1. **Səssiz** baxan (diktorsuz, mətnsiz) ilk 3 saniyədə **nə baş verdiyini** anlayırmı? (adam telefona baxır / adam qaçır — aydın hərəkət)
2. 12 yaşlı uşaq sonda **mesajı bir cümlə ilə** deyə bilərmi?
3. Bu vəziyyəti **hər kəs** yaşayıb? (yuxudan dura bilməmək, telefon, «sabahdan başlayaram», tənbəllik, idman, dostlar, pul xərcləmək). Niş (vape, qumar, narkotik) YOX.
Biri «xeyr»-dirsə — sadələşdir, yenidən yaz.

## 2. Sadəlik qaydaları
- **Bir video = bir fikir = bir səhnə dünyası.** Abstrakt metafor (bank, buz, fənər, kölgə, güzgü) yalnız **ilk baxışda** aydındırsa. Şübhə varsa — **gündəlik real vəziyyət** seç (otaq, mətbəx, park, ofis, avtobus).
- **Personaj = izləyicinin özü.** Tanış əşyalar: telefon, yataq, zəngli saat, idman ayaqqabısı, kitab, su butulkası, kompüter.
- **Səbəb → nəticə görünsün:** hərəkət et → sayğac/qrafik dərhal reaksiya verir (+1 yaşıl yuxarı, −5 qırmızı aşağı). Gizli simvolika YOX.
- **Ekranda ən çox 1 sətir mətn** (≤7 söz) + sayğac. Uzun izah diktorda, ekranda yox. «Ancaq mətn oxunan» video RƏDD (chat POV kimi).
- **Diktor:** qısa, danışıq dili, 6–9 cümlə, hər cümlə ≤10 söz. Çətin söz yox (A2 ingilis dili).
- **Uzunluq 15–25 s.** Hekayə 3 hissə: problem (0–3 s) → dəyişiklik (3–18 s) → nəticə + qrafik (son 4–5 s).

## 3. İşıq və rəng (qaranlıq YOX)
- **Susmaya görə GÜNDÜZ / işıqlı səhnə:** isti səhər, açıq otaq, gün batımı, açıq səma. Gecə yalnız hekayə tələb edirsə (məs. «gecə 2-də telefon») və onda da otaq lampa ilə işıqlı olsun.
- Fon heç vaxt tam qara olmasın: ən tünd rəng ≈ `#1E2533`-dən açıq; orta tonlar üstünlük təşkil etsin. Vinyet/dənə yüngül (və ya yox).
- Personaj **siluet deyil, oxunan fiqur:** üz istiqaməti, paltar rəngi, əşya aydın görünür; personajla fon arasında güclü kontrast.
- Rənglər: brendin yaşıl `#26D67F` (+), narıncı `#FF6B35` (−/aksent), qızıl `#F7C04A` (final), açıq göy/krem fon. İki personaj varsa — iki fərqli rəng (məs. yaşıl köynək vs boz köynək) ki, bölünmüş ekranda dərhal ayrılsın.
- Yoxlama: önizləmə kadrlarının orta parlaqlığı (luma) ≥ 0.35 olsun (`ffmpeg ... signalstats` və ya Pillow `ImageStat`). Aşağıdırsa — işıqlandır.

## 4. Hook (ilk 1–2 s)
- Sual və ya tanış ağrı, **gündəlik dillə**: «Why can't you wake up early?», «You said 'tomorrow' again.», «Same day. Two choices.»
- Hook-dakı söz ekranda + diktorda + caption-un 1-ci sətrində eynidir (Instagram axtarışı).
- İlk kadrda artıq hərəkət var (statik giriş yox).

## 5. Sübut olunmuş quruluşlar (əvvəl bunları seç)
1. **Bölünmüş ekran «X vs Y»** (M14, M19 partladı): eyni gün, eyni insan, iki seçim; sayğaclar; sonda iki qrafik yan-yana. Ən aydın format.
2. **Fasiləsiz kamera / «bir çəkiliş»** (M23, sınaqda).
Yeni quruluş yalnız həftədə 1 dəfə və yalnız önizləmə + istifadəçi təsdiqi ilə.

## 6. Constara bağı (həmişə, amma sadə)
Sonda: həyat xətti qrafikə çevrilir (+1 / −5 görünən) → «Send this to someone who…» → `@constara.app`. Tətbiqin adı/LINK hər videoda deyil.

## 7. Çıxış formatı (ssenari kartı) — istifadəçiyə və ya plana bunu yaz
```
Ad: Mxx «...»               Quruluş: bölünmüş ekran / bir çəkiliş / yeni
Mövzu (hamıya aid): ...      Səhnə + işıq: (gündüz otaq, səhər günəşi ...)
Hook (ekran + diktor): ...
Səssiz anlaşılma: «adam ... edir, sayğac ...» (1 cümlə)
Kadrlar (zaman): 0–3 s ... | 3–8 s ... | ... | son 5 s qrafik + CTA
Diktor (6–9 cümlə): ...
Mesaj (12 yaşlı üçün 1 cümlə): ...
Caption 1-ci sətri: ...    Hashtag (≤5): ...
Test: səssiz ✔ / 12 yaş ✔ / hamıya aid ✔ / luma ≥0.35 ✔
```

## 8. Qadağalar
- Tam qara fon, yalnız siluet, ay işığında gecə səhnəsi (susmaya görə).
- Chat/mətn ekranı videoları, 3D, çubuq fiqur.
- Başqa hesabın konkret səhnəsini/mətnini kopyalamaq.
- Narkotik, niş asılılıq mövzuları; `oyrenilenler.md` «Bazada qalanlar».
