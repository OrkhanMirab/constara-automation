"""M23 «Bir çəkiliş» — YENİ TİP: fasiləsiz kamera + fəsillər + REWIND loop (2026-11-16, istifadəçi «axıcı animasiya» istədi; ÖNİZLƏMƏ, təsdiqsiz MP4 YOX).

Gecə divanda telefon → telefonu qoyur, qalxır, kamera kəsilmədən onunla gedir. Fəsillər axır: yağış (Day 30 yıxılır, −5) → qar → çiçək → yay şəfəqi.
Ayağının altındakı iz = qrafik; zirvədə geri çəkilmə (+355). «◀◀ REWIND» → hər şey geri sarınır → yenə həmin divan (video başa qayıdır, loop).
İşlətmə: python3 m23_bircekilis.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; önizləmə: onizleme.py ; render yalnız təsdiqdən sonra.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 27.0
LACE, RUN = False, False
DOWN, STAND, WALK, FALL, REVEAL, REW, REW2, END = 2.4, 2.9, 3.9, 7.05, 16.6, 20.2, 21.6, 23.6
TEXTS = [
    (0.05, 2.30, "THIS IS THE NIGHT\nEVERYTHING CHANGED.", "EVERYTHING CHANGED.", "gold"),
    (2.40, 3.90, "HE PUT THE PHONE DOWN.", "PHONE DOWN.", "gold"),
    (6.90, 9.40, "DAY 30. RAIN.\nHE FALLS.", "HE FALLS.", "red"),
    (9.60, 12.40, "DAY 95. SNOW.\nHE KEEPS GOING.", "KEEPS GOING.", "gold"),
    (12.60, 15.80, "DAY 200.\nNOBODY'S WATCHING.", "NOBODY'S WATCHING.", "red"),
    (16.60, 20.10, "ONE YEAR.\nONE DECISION.", "ONE DECISION.", "gold"),
    (21.60, 23.50, "IT ALL STARTS\nWITH TONIGHT.", "TONIGHT.", "gold"),
    (23.60, 26.90, "SEND THIS TO SOMEONE\nON THE COUCH RIGHT NOW.", "RIGHT NOW.", "gold"),
]
VO = [(0.2, "This is the night everything changed."), (2.45, "He put the phone down."), (7.0, "Day thirty. Rain. He falls."),
      (9.7, "Day ninety-five. Snow. He keeps going."), (12.7, "Day two hundred. Nobody's watching."), (16.7, "One year. One decision."),
      (21.7, "It all starts with tonight."), (23.8, "Send this to someone on the couch right now.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [WALK, 1], [7.0, 30], [7.8, 33], [9.6, 95], [11.2, 110], [12.6, 200], [14.2, 220], [15.8, 365]], down=DOWN, stand=STAND, walk=WALK,
          fall=FALL, reveal=REVEAL, lace=LACE, run=RUN, rew=REW, rew2=REW2, end=END, texts=TEXTS, stride=1.4)


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


def step(seed, v=.5):
    n = int(.12 * S.SR); tt = np.arange(n) / S.SR
    return (S.lp(noise(n, seed), 500) * np.exp(-tt * 45) * .5 * v).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR + 1), S.Bus(DUR + 1); tt = np.arange(N) / S.SR
    def env(a, b, c, d):  # trapesiya zərf (s)
        return np.clip(np.minimum((tt - a) / max(1e-3, b - a), (d - tt) / max(1e-3, d - c)), 0, 1).astype(np.float32)
    fx.add(0, S.bp(noise(N, 11), 900, 7000) * .05 * env(4.5, 5.5, 9.0, 10.0))       # yağış
    fx.add(0, S.bp(noise(N, 12), 150, 900) * .05 * env(9.0, 10.0, 12.5, 13.5))      # qar küləyi
    for k in range(20):                                                                # quşlar (yaz)
        t0 = 12.8 + k * .14 + (k % 3) * .05; n = int(.08 * S.SR); x = np.arange(n) / S.SR
        fx.add(t0, (np.sin(2 * np.pi * (2800 + 900 * np.sin(x * 90)) * x) * np.exp(-x * 30) * .05).astype(np.float32), pan=.5 - (k % 2))
    t, k = WALK + .1, 0
    while t < REVEAL:
        if not (FALL - .1 < t < FALL + 1.0):
            fx.add(t, step(100 + k, .45), pan=.2)
        t += .42 if t < 7 else .3; k += 1
    fx.add(DOWN, step(5, .6)); fx.add(FALL + .3, S.boom(.3)); fx.add(FALL + .3, step(9, 1.2))
    fx.add(REW, S.riser(REW2 - REW, .5)[::-1].copy())
    n = int((REW2 - REW) * S.SR); x = np.arange(n) / S.SR
    fx.add(REW, (np.sin(2 * np.pi * np.cumsum(400 + 2600 * (x / x[-1]) ** 2) / S.SR) * .08 + S.bp(noise(n, 31), 2000, 9000) * .06).astype(np.float32))
    prog = ['Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G', 'Am', 'G', 'F', 'G']
    for k, ch in enumerate(prog):
        t0 = .1 + k * 1.18
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.3, cut=600 + 60 * k, v=.5 + .03 * k, att=.25)); mus.add(t0, S.sub(ch, 1.2, v=.35))
        nt = S.CHORDS[ch][1]
        for q in range(2 if k < 3 else 4):
            mus.add(t0 + q * (.59 if k < 3 else .295), S.piano(S.hz(nt[2 + q % 3]) * 2, 1.4, .2 + .01 * k))
        if k >= 3: mus.add(t0, S.kick(.22 + .015 * k)); mus.add(t0 + .59, S.kick(.18 + .015 * k))
    mus.add(REVEAL - 1.0, S.riser(1.0, .5)); mus.add(REVEAL, S.shimmer('C', 3.0, 1.0))
    for k, ch in enumerate(['C', 'G', 'Am']):
        t0 = REVEAL + k * 1.2; mus.add(t0, S.strings(ch, 1.4, v=.6 + .06 * k, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.4))
    for k, ch in enumerate(['Am', 'F', 'C', 'G']):
        t0 = REW2 + k * 1.35; mus.add(t0, S.pad(ch, 1.45, cut=700, v=.5, att=.2)); mus.add(t0, S.piano(S.hz(S.CHORDS[ch][1][3]) * 2, 1.6, .22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.8), .28)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm23_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
