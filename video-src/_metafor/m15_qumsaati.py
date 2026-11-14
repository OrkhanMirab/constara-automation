"""M15 «Qum saatı» — telefon = qum saatı, 11 s LOOP (yeni format: qısa + loop, 2026-11-14).

İstifadəçi: «videolar 10–12 s olsun, sürətli, loop, rəngli, pro; mövzu: insanlar telefonda vaxt itirir, ömrün keçdiyini hiss etmir».
Qum saatında qum yerinə rəngli lent kartları (like/play/bildiriş) tökülür, aşağıda telefona baxan fiqur yavaş-yavaş basdırılır;
AGE 18→74, YEARS ON PHONE 0→9.3 (gündə ~4 saat). Son dənə → fiqur dənələrə çevrilir → qum saatı çevrilir → başa qayıdır (loop).
İşlətmə: python3 m15_qumsaati.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR, BPM = 30, 11.0, 120
BEAT = 60 / BPM
DRAIN = 9.6     # son dənə
FLIP = 10.15    # çevrilmə başlayır (10.15–10.95)
TEXTS = [
    (0.00, 2.30, "EVERY SWIPE\nFEELS FREE.", "FREE.", "gold"),
    (2.40, 4.70, "IT'S PAID\nIN TIME.", "TIME.", "gold"),
    (4.80, 7.30, "MINUTES. DAYS.\nYEARS.", "YEARS.", "red"),
    (7.40, 10.05, "PUT IT DOWN\nBEFORE IT RUNS OUT.", "RUNS OUT.", "red"),
]
VO = [(0.15, "Every swipe feels free."), (2.45, "But it's paid in time."),
      (4.85, "Minutes. Days. Years."), (7.45, "Put it down, before it runs out.")]
TL = dict(fps=FPS, dur=DUR, beat=BEAT, drain=DRAIN, flip=FLIP, texts=TEXTS)


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
        a, sr = k.create(txt, voice='am_michael', speed=1.02, lang='en-us')
        i = np.where(np.abs(a) > .01)[0]; a = a[max(0, i[0] - 200):i[-1] + 800]
        a = resample_poly(a, S.SR, sr).astype(np.float32)
        j = int(t0 * S.SR); v[j:j + len(a)] += a[:N - j]
    return S.voice_chain(v)


def hat(v=1.0, seed=0):
    n = int(.05 * S.SR)
    return (S.hp(noise(n, seed), 7000) * np.exp(-np.arange(n) / (n / 6)) * .12 * v).astype(np.float32)


def clap(v=1.0, seed=0):
    n = int(.18 * S.SR); x = S.bp(noise(n, seed), 900, 5000)
    env = np.exp(-np.arange(n) / (n / 5)); env[:int(.012 * S.SR)] *= 1.6
    return (x * env * .22 * v).astype(np.float32)


def ping(v=1.0, f='E6'):
    t = S.tarr(.5)
    return (np.sin(2 * np.pi * S.hz(f) * t) * np.exp(-t * 9) * .07 * v).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR)
    mus, fx = S.Bus(DUR + 1), S.Bus(DUR + 1)
    nb = int(DUR / BEAT)
    for b in range(nb):
        t0 = b * BEAT
        if t0 > DRAIN + .2:
            continue
        mus.add(t0, S.kick(.75 if t0 > .1 else .9))
        if b % 2 == 1 and t0 > 2.3:
            mus.add(t0, clap(.8, b))
        for h in range(2):
            mus.add(t0 + h * BEAT / 2, hat(.9 if h else .6, b * 2 + h), pan=.25)
        fx.add(t0 + .05, S.whoosh(.22, .35), pan=(-.4 if b % 2 else .4))   # swipe
        if b % 3 == 2:
            fx.add(t0 + .2, ping(.8, ['E6', 'G6', 'B6'][b % 3]), pan=.5)
    # bas + akkordlar (bar = 2 s): Am F C G Am
    for k, ch in enumerate(['Am', 'F', 'C', 'G', 'Am']):
        t0 = k * 2.0
        if t0 > DRAIN:
            break
        mus.add(t0, S.sub(ch, 1.95, v=.55)); mus.add(t0, S.pad(ch, 2.0, cut=900 + 250 * k, v=.45, att=.05))
        notes = S.CHORDS[ch][1]
        for q in range(16):  # 16-lıq arpecio
            tq = t0 + q * BEAT / 4
            if tq < DRAIN:
                mus.add(tq, S.piano(S.hz(notes[1 + q % 4]) * 2, .35, .18 + .015 * k), pan=(q % 2 - .5) * .4)
    # son: hər şey kəsilir, ürək döyüntüsü + son dənə + çevrilmə
    fx.add(DRAIN - .05, S.heartbeat(.8)); fx.add(DRAIN + .1, ping(1.2, 'B6'))
    mus.add(DRAIN - .2, S.rev_swell(1.2, .5))
    fx.add(FLIP, S.whoosh(.75, 1.2)); fx.add(FLIP + .1, S.riser(.75, .6))
    m = S.apply_reverb(mus.x, S.reverb_ir(1.6), .18)[:N]
    f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = voice_track(N)
    if vo is not None:
        out = S.mix(vo, m, f, duck_db=7.0)[:N]
    else:
        out = (m * .65 + f * .9)[:N]
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    # loop: son 30 ms başlanğıca yumşaq keçsin (klik olmasın)
    k = int(.03 * S.SR); out[-k:] *= np.linspace(1, 0, k)[:, None]; out[:k] *= np.linspace(0, 1, k)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm15_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
