"""M14 «Fənər» — Starter vs Planner, bölünmüş ekran (Metafor + yeni format, 2026-11-14).

İstifadəçi mindset.therapy «Action Taker vs Perfectionist» reelsini göstərdi («bunun kimi»). Mesaj eyni (kobud başla > mükəmməli gözlə),
səhnə ÖZÜMÜZÜNKÜ: yuxarıda STARTER kiçik fənərlə qaranlığa yeriyir, arxasında qalan iz = Constara qrafiki (büdrəmə −5 ilə enir, yenə qalxır),
aşağıda PLANNER divar xəritəsində marşrut çəkib silir (PLAN v1→v46), kağız topları yığılır, xətti düz 0. Sonda kamera geri çəkilir: iz bütöv qrafikdir.
İşlətmə: python3 m14_fener.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
DAYS = [[0, 1], [2.2, 1], [7.0, 30], [12.0, 100], [16.0, 180], [18.6, 365]]   # (vaxt, gün)
STUMBLE = [7.0, 12.9]       # büdrəmə anları (gün ~30 və ~120)
REVEAL = 17.4               # kamera geri çəkilir: iz = qrafik
END = 21.2
TEXTS = [
    (0.05, 2.25, "DAY ONE.\nSAME DREAM.", "SAME DREAM.", "gold"),
    (2.35, 4.50, "ONE STARTS WITH\nA BAD PLAN.", "A BAD PLAN.", "gold"),
    (4.60, 6.85, "ONE WAITS FOR\nA PERFECT ONE.", "A PERFECT ONE.", "red"),
    (7.00, 9.45, "DAY 30. HE TRIPS.", "TRIPS.", "red"),
    (9.55, 11.85, "DAY 30. PLAN #4.", "PLAN #4.", "red"),
    (12.00, 14.85, "THE BAD PLAN GOT\nBETTER ON THE WAY.", "BETTER", "gold"),
    (14.95, 17.25, "THE PERFECT PLAN\nIS STILL ON PAPER.", "ON PAPER.", "red"),
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
TL = dict(fps=FPS, dur=DUR, days=DAYS, stumble=STUMBLE, reveal=REVEAL, end=END, texts=TEXTS)


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


def step(seed, v=1.0):  # ayaq səsi (çınqıl)
    n = 2600; e = np.exp(-np.arange(n) / 380)
    return (S.bp(noise(n, seed), 300, 3000) * e * .16 * v).astype(np.float32)


def scratch(d, seed):  # qələm cızıltısı
    t = S.tarr(d); n = noise(len(t), seed)
    am = .5 + .5 * np.sin(2 * np.pi * 7 * t + np.sin(2 * np.pi * 1.3 * t) * 3)
    return (S.bp(n, 2500, 7000) * am * .05).astype(np.float32)


def crumple(seed):  # kağız əzilir
    n = int(.4 * S.SR); x = noise(n, seed) * (np.random.default_rng(seed).random(n) > .93)
    return (S.bp(x, 1500, 8000) * np.exp(-np.arange(n) / (n / 3)) * .5).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR)
    mus, fx = S.Bus(DUR), S.Bus(DUR)
    t = 2.3
    while t < REVEAL:  # starter-in addımları (sağda)
        fx.add(t, step(int(t * 100), .9), pan=.3); t += .42
    for s0 in STUMBLE:
        fx.add(s0 + .15, S.kick(.5)); fx.add(s0 + .1, S.whoosh(.3, .5))
    for c in range(2, 16):  # planner: cızıltı + kağız (solda)
        fx.add(c * 1.12, scratch(.8, c), pan=-.35); fx.add(c * 1.12 + .95, crumple(c), pan=-.35)
    fx.add(REVEAL, S.whoosh(.8, .7)); fx.add(REVEAL + .2, S.boom(.4))
    # musiqi: sakit Am pulsu → yuxarı qalxan C–G–Am–F → REVEAL-də açılış
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
    m = S.apply_reverb(mus.x, S.reverb_ir(2.8), .28)[:N]
    f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = voice_track(N)
    if vo is not None:
        out = S.mix(vo, m, f, duck_db=10.0)[:N]
    else:
        out = (m * .6 + f * .9)[:N]
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm14_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
