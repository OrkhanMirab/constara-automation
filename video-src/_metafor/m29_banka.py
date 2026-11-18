"""M29 «Banka» — THE SAVER vs THE SPENDER (2026-11-19, gecə planı; bölünmüş ekran, təsdiqlənmiş format).

İLK İŞIQLI video (istifadəçi 11-17: «videolar çox qaranlıqdır» → .claude/skills/ssenari): günəşli səhər, rəngli personajlar (pal),
yuxarı: velosiped yolu, paralaks şəhər/ağac/bulud, IK pedal (ayaqlar pedalda fırlanır), Day 30 yağış + deşik təkər (−5);
aşağı: tıxacda maşın, əyləc işıqları, BEEP/HONK, IN TRAFFIC: N H. Sonda ağ kartda qrafik (+N vs 0).
İşlətmə: python3 m29_banka.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "$5 A DAY.\nWHERE DOES IT GO?", "WHERE DOES IT GO?", "gold"),
    (2.35, 4.50, "ONE MAKES IT\nAT HOME.", "AT HOME.", "green"),
    (4.60, 6.85, "ONE BUYS IT.\nEVERY DAY.", "EVERY DAY.", "red"),
    (7.00, 9.45, "DAY 30.\nAN IMPULSE BUY.", "IMPULSE BUY.", "red"),
    (9.55, 11.85, "DAY 30.\nCUP NUMBER 30.", "CUP NUMBER 30.", "red"),
    (12.00, 14.85, "NEXT MORNING.\nCOIN IN THE JAR.", "COIN IN THE JAR.", "green"),
    (14.95, 17.25, "THE OTHER?\nCUP NUMBER 180.", "CUP NUMBER 180.", "red"),
    (17.40, 21.05, "SAME COFFEE.\nDIFFERENT YEAR.", "DIFFERENT YEAR.", "gold"),
    (21.20, 25.80, "SEND THIS TO\nYOUR COFFEE FRIEND.", "COFFEE FRIEND.", "gold"),
]
VO = [(0.2, "Five dollars a day. Where does it go?"), (2.45, "One makes it at home."), (4.65, "One buys it. Every day."), (7.15, "Day thirty. An impulse buy."),
      (9.6, "Day thirty. Cup number thirty."), (12.05, "Next morning, coin in the jar."), (15.0, "The other one? Cup number one eighty."),
      (17.5, "Same coffee. Different year."), (21.35, "Send this to your coffee friend.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE SAVER", "THE SPENDER"])


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


def coin(seed, v=.3):
    n = int(.35 * S.SR); tt = np.arange(n) / S.SR; x = np.zeros(n, np.float32)
    for q in range(3):
        j = int(q * .05 * S.SR); u = tt[:n - j]; f = 2600 + 400 * ((seed + q) % 3)
        x[j:] += ((np.sin(2 * np.pi * f * u) + .5 * np.sin(2 * np.pi * f * 2.4 * u)) * np.exp(-u * (30 + 10 * q)) * (.6 ** q)).astype(np.float32)
    return (x * v).astype(np.float32)


def beep(seed, v=.1):
    n = int(.14 * S.SR); tt = np.arange(n) / S.SR
    return (np.sin(2 * np.pi * 1900 * tt) * np.minimum(1, (.14 - tt) * 60) * v).astype(np.float32)


def cafe(d, v=.03):
    n = int(d * S.SR)
    return (S.bp(noise(n, 31), 250, 2500) * v).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(noise(N, 7), 80, 600) * .02 * (1 + .4 * np.sin(2 * np.pi * .13 * tt))).astype(np.float32))  # səhər şəhər uğultusu
    t, k = 2.3 + .9 * .62, 0
    while t < REVEAL:
        if not (SINK - .1 < t < SINK + 1.8):
            fx.add(t, coin(k), pan=.3)
        t += .9; k += 1
    t, k = 4.5 + .9 * .8, 0
    while t < REVEAL:
        fx.add(t, beep(k), pan=-.35); t += .9; k += 1
    fx.add(0, cafe(REVEAL), pan=-.3)
    fx.add(SINK + .1, S.boom(.25)); fx.add(SINK + .15, beep(7, .2))
    fx.add(REVEAL, S.whoosh(.8, .7)); fx.add(REVEAL + .2, S.boom(.4))
    for k, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'Am', 'F', 'Am', 'F', 'C', 'G', 'F', 'G']):
        t0 = .1 + k * 1.24
        mus.add(t0, S.pad(ch, 1.35, cut=600 + 60 * k, v=.5 + .03 * k, att=.25)); mus.add(t0, S.sub(ch, 1.2, v=.35))
        notes = S.CHORDS[ch][1]
        for q in range(2 if k < 4 else 4):
            mus.add(t0 + q * (.62 if k < 4 else .31), S.piano(S.hz(notes[2 + q % 3]) * 2, 1.4, .22 + .01 * k))
        if k >= 5:
            mus.add(t0, S.kick(.25 + .02 * k)); mus.add(t0 + .62, S.kick(.2 + .02 * k))
    mus.add(REVEAL - 1.2, S.riser(1.2, .5)); mus.add(REVEAL, S.shimmer('C', 3.0, 1.0))
    for k, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k * 1.25
        mus.add(t0, S.strings(ch, 1.45, v=.55 + .06 * k, att=.3)); mus.add(t0, S.pad(ch, 1.45, cut=1000 + 100 * k, v=.6, att=.15)); mus.add(t0, S.sub(ch, 1.3, v=.4))
    for i, nm in enumerate(['E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'C6', 'E6']):
        mus.add(REVEAL + .3 + i * .6, S.piano(S.hz(nm), 2.0, .3))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.8), .28)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.2, 5000, 5), .14)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm29_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
