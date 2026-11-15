"""M17 «Yol» — M14 «Fənər» hekayəsinin 3D premium versiyası (Metafor, 2026-11-15).

Səbəb: M14 ilk «~130 tavanı»nı keçən metafor videosu oldu (17 saatda ikinci dalğa, 219 baxış). İstifadəçi: «o hekayəyə uyğun
daha gerçəkçi, premium görünüşlü animasiya». Hekayə eyni (pis planla başla > mükəmməl planı gözlə), mühərrik YENİ: three.js
(WebGL, fiziki işıq, kölgə, duman, bloom, film dənəsi), manekən fiqurlar, real relyef. Starter fənərlə dağ silsiləsinə qalxır,
ayağının altındakı iz işıqlanır; Planner masa lampası altında plan çəkib atır (PLAN vN). Sonda kamera geri çəkilir:
silsilənin profili + qızılı iz = Constara qrafiki (iki −5 enişi), aşağıda Planner-in lampası «0».
Asılılıq: _build/node_modules (npm i --prefix _build three@0.170.0 esbuild@0.24.0), scipy (səs),
_build/models/Xbot-slim.glb (three.js r170 examples/models/gltf/Xbot.glb — Mixamo X Bot; _build/slim.mjs ilə
yalnız idle+walk saxlanılır, quantize + meshopt → ~0.8 MB; telefon önizləməsi 6 MB faylı açmadı).
İşlətmə: python3 m17_yol.py <scratch> [--no-audio] [--tts <kokoro qovluğu>]
         önizləmə: python3 onizleme.py <scratch> <out.html> (sonra m17_yol.py --fix-preview <out.html>)
         kadrlar: cp render3d.mjs <scratch>/ ; node render3d.mjs <scratch>   (WebGL üçün swiftshader bayraqları)
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
RIDGE = [[-80, 0], [-6, 0], [0, 0], [4, .75], [8, 1.65], [10.5, 2.15], [12.1, .95], [15, 2.2], [20, 3.9], [26, 5.8], [32, 7.6],
         [37, 9.2], [40.3, 9.9], [42.2, 8.0], [46, 9.6], [53, 12.8], [61, 16], [69, 19], [77, 22.4], [85, 25.3], [93, 28.9],
         [101, 32.6], [109, 36.4], [116, 40.2], [121, 42.6], [126, 43.6], [132, 42], [150, 31], [180, 12], [230, 0]]
DIPS = [[10.5, 12.1], [40.3, 42.2]]           # qrafikdəki −5 enişləri (qırmızı iz)
XS = [[0, 0], [2.95, 0], [4.6, 1.85], [7.0, 9.55], [7.42, 10.1], [7.9, 11.6], [8.62, 11.75], [9.4, 12.75], [11.8, 66], [14.8, 70],
      [17.2, 108], [20.0, 120.5], [26, 120.6]]  # Starter-in mövqeyi (kəsimlər arası vaxt sıçrayışı)
SHOTS = [['A', 0, 2.3], ['B', 2.3, 4.6], ['C', 4.6, 7.0], ['D', 7.0, 9.4], ['E', 9.4, 11.8], ['F', 11.8, 14.8], ['G', 14.8, 17.2], ['H', 17.2, 26.01]]
DAYS = [[0, 1], [2.3, 1], [7.0, 30], [11.7, 31], [12.0, 100], [14.8, 180], [17.2, 300], [20.0, 365]]
TOSSES = [6.3, 8.0, 8.8, 10.65] + [12.0 + .22 * i for i in range(12)] + [18.6 + .27 * i for i in range(24)]   # 40 plan → v41
IGNITE, STUMBLE, LOOKUP, RAISE, REVEAL, END = 2.55, [7.42, 8.62], 15.3, 20.6, 17.2, 21.2
TEXTS = [
    (0.05, 2.25, "DAY ONE.\nSAME DREAM.", "SAME DREAM.", "gold"),
    (2.35, 4.50, "ONE STARTS WITH\nA BAD PLAN.", "A BAD PLAN.", "gold"),
    (4.60, 6.85, "ONE WAITS FOR\nA PERFECT ONE.", "A PERFECT ONE.", "red"),
    (7.00, 9.30, "DAY 30. HE TRIPS.", "TRIPS.", "red"),
    (9.45, 11.70, "DAY 30. PLAN #4.", "PLAN #4.", "red"),
    (11.85, 14.70, "THE BAD PLAN GOT\nBETTER ON THE WAY.", "BETTER", "gold"),
    (14.85, 17.10, "THE PERFECT PLAN\nIS STILL ON PAPER.", "ON PAPER.", "red"),
    (17.40, 21.05, "YOU DON'T NEED THE WHOLE ROAD.\nJUST THE NEXT STEP.", "THE NEXT STEP.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nSTILL WAITING FOR\nTHE PERFECT PLAN.", "THE PERFECT PLAN.", "gold"),
]
VO = [
    (0.20, "Day one. Same dream."), (2.40, "One starts with a bad plan."), (4.65, "One waits for a perfect one."),
    (7.15, "Day thirty. He trips."), (9.60, "Day thirty. Plan number four."),
    (12.05, "The bad plan got better on the way."), (15.00, "The perfect plan is still on paper."),
    (17.50, "You don't need to see the whole road. Just the next step."),
    (21.35, "Send this to someone still waiting for the perfect plan."),
]
TL = dict(fps=FPS, dur=DUR, ridge=RIDGE, dips=DIPS, xs=XS, shots=SHOTS, days=DAYS, tosses=TOSSES, ignite=IGNITE, stumble=STUMBLE,
          lookup=LOOKUP, raise_=RAISE, end=END, texts=TEXTS, score=355, xend=120.5, peak=126)
TL['raise'] = TL.pop('raise_')


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def voice_track(N):
    if '--tts' not in sys.argv:
        return None
    from kokoro_onnx import Kokoro
    from scipy.signal import resample_poly
    d = sys.argv[sys.argv.index('--tts') + 1]
    k = Kokoro(os.path.join(d, 'kokoro-v1.0.onnx'), os.path.join(d, 'voices-v1.0.bin'))
    v = np.zeros(N, np.float32)
    for t0, txt in VO:
        a, sr = k.create(txt, voice='am_michael', speed=0.92, lang='en-us')
        i = np.where(np.abs(a) > .01)[0]; a = a[max(0, i[0] - 200):i[-1] + 800]
        a = resample_poly(a, S.SR, sr).astype(np.float32)
        j = int(t0 * S.SR); v[j:j + len(a)] += a[:N - j]
    return S.voice_chain(v)


def step(seed, v=1.0):  # çınqıl üstündə addım
    n = 3200; e = np.exp(-np.arange(n) / 420)
    g = S.bp(noise(n, seed), 250, 3500) * e * (np.random.default_rng(seed + 1).random(n) > .55)
    return (S.lp(g, 4000) * .3 * v + S.lp(noise(n, seed + 2) * e, 300) * .25 * v).astype(np.float32)


def scratch(d, seed):  # qələm cızıltısı
    t = S.tarr(d); n = noise(len(t), seed)
    am = .5 + .5 * np.sin(2 * np.pi * 7 * t + np.sin(2 * np.pi * 1.3 * t) * 3)
    return (S.bp(n, 2500, 7000) * am * .05).astype(np.float32)


def crumple(seed, d=.55):  # kağız əzilir
    n = int(d * S.SR); x = noise(n, seed) * (np.random.default_rng(seed).random(n) > .9)
    return (S.bp(x, 1200, 9000) * np.minimum(1, np.arange(n) / 800) * np.exp(-np.arange(n) / (n / 2.5)) * .55).astype(np.float32)


def strike():  # kibrit/fənər alışır
    n = int(.5 * S.SR); x = noise(n, 77); e = np.exp(-np.arange(n) / 2500)
    s = S.hp(x, 2500) * e * .5 + S.bp(noise(n, 78), 120, 900) * np.minimum(1, np.arange(n) / 3000) * np.exp(-np.arange(n) / 9000) * .5
    return s.astype(np.float32)


def hum(d, v=1.0):  # lampa vızıltısı
    t = S.tarr(d)
    return ((np.sin(2 * np.pi * 100 * t) * .6 + np.sin(2 * np.pi * 200 * t) * .3) * .012 * v * np.minimum(1, t / .2) * np.minimum(1, (d - t) / .2)).astype(np.float32)


def xs_at(t):
    for (a, xa), (b, xb) in zip(XS, XS[1:]):
        if a <= t <= b:
            return xa + (xb - xa) * (t - a) / (b - a)
    return XS[-1][1]


def audio(path):
    N = int(DUR * S.SR)
    mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    on_mount = np.zeros(N, np.float32)
    for sh, a, b in SHOTS:
        if sh in 'ABDFH':
            on_mount[int(a * S.SR):int(min(b, DUR) * S.SR)] = 1
    wind = S.bp(noise(N, 7), 180, 1500) * (.025 + .03 * on_mount) * (1 + .4 * np.sin(2 * np.pi * .13 * tt))
    fx.add(0, wind.astype(np.float32))
    # addımlar: yalnız Starter kadrlarında, ayaq yerə dəyəndə (hər 0.725 m)
    for sh, a, b in SHOTS:
        if sh not in 'BDF':
            continue
        t, last = a, None
        while t < b:
            k = int(xs_at(t) / .725)
            if last is not None and k != last and not (STUMBLE[0] < t < STUMBLE[1]):
                fx.add(t, step(int(t * 100), .9 if sh != 'F' else .7), pan=.15)
            last = k; t += 1 / 120
    fx.add(STUMBLE[0] + .05, S.whoosh(.3, .5)); fx.add(STUMBLE[0] + .2, step(901, 1.6)); fx.add(STUMBLE[0] + .45, S.kick(.55))
    for i in range(6):
        fx.add(STUMBLE[0] + .25 + i * .05, step(910 + i, .7))
    fx.add(IGNITE - .05, strike()); fx.add(IGNITE + .05, S.whoosh(.4, .4))
    # Planner kadrları: lampa vızıltısı, qələm, kağız
    for sh, a, b in SHOTS:
        if sh in 'CEG':
            fx.add(a, hum(b - a, 1.0), pan=-.2)
    for a, b in [(4.75, 5.5), (9.5, 9.9), (14.85, 15.2)]:
        fx.add(a, scratch(b - a, int(a * 10)), pan=-.25)
    for rt in TOSSES:
        if any(s[0] in 'CEG' and s[1] <= rt - .6 and rt < s[2] for s in SHOTS):
            fx.add(rt - .55, crumple(int(rt * 10)), pan=-.3); fx.add(rt, S.whoosh(.25, .25), pan=-.3)
            fx.add(rt + .55, (crumple(int(rt * 10) + 5, .15) * .6).astype(np.float32), pan=-.3)
    fx.add(REVEAL, S.whoosh(.9, .7)); fx.add(REVEAL + .25, S.boom(.4))
    # musiqi (M14 ilə eyni əhval: sakit Am pulsu → yüksələn C–G–Am–F → REVEAL-də açılış)
    for k, ch in enumerate(['Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G', 'Am', 'G', 'F', 'G']):
        t0 = .1 + k * 1.24
        mus.add(t0, S.pad(ch, 1.35, cut=600 + 60 * k, v=.5 + .03 * k, att=.25)); mus.add(t0, S.sub(ch, 1.2, v=.35))
        notes = S.CHORDS[ch][1]
        for q in range(2 if k < 4 else 4):
            mus.add(t0 + q * (.62 if k < 4 else .31), S.piano(S.hz(notes[2 + q % 3]) * 2, 1.4, .22 + .01 * k))
    mus.add(REVEAL - 1.2, S.riser(1.2, .5)); mus.add(REVEAL, S.shimmer('C', 3.0, 1.0))
    for k, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k * 1.25
        mus.add(t0, S.strings(ch, 1.45, v=.55 + .06 * k, att=.3)); mus.add(t0, S.pad(ch, 1.45, cut=1000 + 100 * k, v=.6, att=.15))
        mus.add(t0, S.sub(ch, 1.3, v=.4))
    for i, nm in enumerate(['E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'C6', 'E6']):
        mus.add(REVEAL + .3 + i * .6, S.piano(S.hz(nm), 2.0, .3))
    mus.add(RAISE, S.shimmer('C', 2.4, .6))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.8), .28)[:N]
    f = S.apply_reverb(fx.x, S.reverb_ir(1.2, 5000, 5), .14)[:N]
    vo = voice_track(N)
    if vo is not None:
        out = S.mix(vo, m, f, duck_db=10.0)[:N]
    else:
        out = (m * .6 + f * .9)[:N]
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def bundle():
    env = dict(os.environ, NODE_PATH=os.path.join(HERE, '_build', 'node_modules'))
    r = subprocess.run([os.path.join(HERE, '_build', 'node_modules', '.bin', 'esbuild'), os.path.join(HERE, 'm17_scene.js'),
                        '--bundle', '--format=iife', '--minify', '--target=chrome110', '--log-level=warning'],
                       capture_output=True, text=True, env=env, check=True)
    return r.stdout


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm17_scene.html')).read()
    import base64
    xbot = base64.b64encode(open(os.path.join(HERE, '_build', 'models', 'Xbot-slim.glb'), 'rb').read()).decode()
    html = html.replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';window.XBOT="' + xbot + '";').replace('/*BUNDLE*/', bundle().replace('</script', '<\\/script'))
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


def fix_preview(p):  # onizleme.py-dən sonra: WebGL səhnəsi gizli 1080×1920-də çəkilir, hər kadr 2D «view» kanvasına köçürülür
    h = open(p).read()     # (WebGL kanvasını birbaşa kiçiltmək bəzi brauzerlərdə qara ekran verir)
    fit = ('<canvas id="view" width="1080" height="1920" style="display:block;height:calc(100vh - 70px);width:auto;max-width:100vw;aspect-ratio:9/16;border-radius:8px"></canvas>'
           '<script>(function(){const w=document.getElementById("wrap");w.style.cssText="position:fixed;left:-3000px;top:0;width:1080px;height:1920px;overflow:hidden";'
           'const v=document.getElementById("view").getContext("2d"),g=document.getElementById("gl"),o=document.getElementById("ov"),d=window.draw;'
           'window.draw=function(t){d(t===0?1.2:t);v.drawImage(g,0,0);v.drawImage(o,0,0);};})();</script>')
    h = h.replace('<div id="bar">', fit + '<div id="bar">', 1)
    open(p, 'w').write(h); print('önizləmə düzəldildi:', p)


if __name__ == '__main__':
    if sys.argv[1] == '--fix-preview':
        fix_preview(sys.argv[2])
    else:
        run(sys.argv[1])
