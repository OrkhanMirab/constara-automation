"""M34 «Zəng» — THE CALLER vs THE TEXTER (2026-11-21, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format, yeni mövzu: ailə/münasibət).

Yuxarı: isti otaq, pəncərədə fəsillər keçir (yaz→yay→payız→qış: ləçək/yarpaq/qar), anasına zəng (MOM balonu, taymer, ürəklər), Day 30 «busy day» (−5),
ertəsi gün geri zəng edir. Aşağı: masada laptop, «talk soon!» baloncuqları, MOM CALLING titrəyir və buraxılır, «Missed call · Mom» kartları yığılır.
Səs: yumşaq akustik gitara (Karplus-Strong, M33-dən) + telefon zəngi. Göndərmə siqnalı üçün emosional, hamıya aid mövzu.
İşlətmə: python3 m34_zeng.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME PARENTS.\nTWO CHOICES.", "TWO CHOICES.", "gold"),
    (2.35, 4.50, "ONE CALLS HOME\nEVERY OTHER DAY.", "CALLS HOME", "green"),
    (4.60, 6.85, "ONE TEXTS\n'TALK SOON!'", "'TALK SOON!'", "red"),
    (7.00, 9.45, "DAY 30.\nBUSY DAY. FORGETS.", "FORGETS.", "red"),
    (9.55, 11.85, "DAY 30.\n'TALK SOON' AGAIN.", "AGAIN.", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE CALLS BACK.", "CALLS BACK.", "green"),
    (14.95, 17.25, "THE OTHER?\nMISSED CALL.", "MISSED CALL.", "red"),
    (17.40, 21.05, "SAME PARENTS.\nDIFFERENT YEAR.", "DIFFERENT YEAR.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO SHOULD CALL HOME.", "CALL HOME.", "gold"),
]
VO = [(0.2, "Same parents. Two choices."), (2.45, "One calls home every other day."), (4.65, "One texts, talk soon."), (7.15, "Day thirty. Busy day. He forgets."),
      (9.6, "Day thirty. Talk soon, again."), (12.05, "Next day, he calls back."), (15.0, "The other one? Missed call."),
      (17.5, "Same parents. Different year."), (21.35, "Send this to someone who should call home.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE CALLER", "THE TEXTER"])


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


def ks(f, d=1.6, v=.25, bright=.5, seed=0):
    """Karplus-Strong simli səs."""
    n = int(d * S.SR); P = max(2, int(S.SR / f)); rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, P).astype(np.float32); buf = S.lp(buf, 1500 + 5000 * bright) if P > 64 else buf
    out = np.zeros(n, np.float32); q = list(buf); k = 0; damp = .996
    for i in range(n):
        x = q[k]; nx = q[(k + 1) % P]; q[k] = damp * .5 * (x + nx); out[i] = x; k = (k + 1) % P
    return out * v


SHAPES = {'C': ['C3', 'E3', 'G3', 'C4', 'E4'], 'G': ['G2', 'B2', 'D3', 'G3', 'B3', 'G4'], 'Am': ['A2', 'E3', 'A3', 'C4', 'E4'], 'F': ['F2', 'C3', 'F3', 'A3', 'C4', 'F4']}
_cache = {}


def strum(ch, v=.2, down=True, sloppy=0.0, seed=0):
    rng = np.random.default_rng(seed); notes = SHAPES[ch] if down else SHAPES[ch][::-1]
    sp = .012 + .02 * sloppy; n = int(1.8 * S.SR); out = np.zeros(n, np.float32)
    for i, nm in enumerate(notes):
        f = S.hz(nm) * (1 + (rng.uniform(-.02, .02) * sloppy))  # pərdə «tutmur»
        key = (round(f, 1), round(sloppy, 1)); s = _cache.get(key)
        if s is None: s = ks(f, 1.5, 1.0, .35 + .4 * (1 - sloppy), seed=int(f)); _cache[key] = s
        j = int(i * sp * S.SR); L = min(len(s), n - j); out[j:j + L] += s[:L] * v * (1 if rng.uniform() > sloppy * .4 else .2)
    return out


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(np.random.default_rng(7).standard_normal(N).astype(np.float32), 200, 1200) * .01).astype(np.float32))  # otaq
    # gitara: 0–7 s yöndəmsiz (sloppy, ritm sürüşür), Day 30 dayanır, sonra getdikcə təmiz
    prog = ['C', 'G', 'Am', 'F']; t, k = .35, 0
    while t < REVEAL - .2:
        if SINK - .1 < t < SINK + 2.1:
            t += .3; continue
        sl = 0.0
        ch = prog[(k // 4) % 4]; down = k % 2 == 0
        mus.add(t, strum(ch, .11 if down else .07, down, sl, seed=k))
        jit = np.random.default_rng(k).uniform(-.12, .12) * sl
        t += (.42 if t < SINK else .36) + jit; k += 1
    fx.add(SINK + .15, S.boom(.25))
    for k2 in range(3):
        fx.add(SINK + .6 + k2 * .4, S.tick(.4))
    # aşağı: MOM CALLING zəngi (t % 2.2 < .9)
    for kk in range(3, 8):
        t0 = kk * 2.2
        if t0 < 4.6 or t0 > REVEAL: continue
        for q in range(3):
            n = int(.12 * S.SR); x = np.arange(n) / S.SR
            fx.add(t0 + q * .28, ((np.sin(2 * np.pi * 1318 * x) + np.sin(2 * np.pi * 1568 * x)) * np.exp(-x * 8) * .03).astype(np.float32), pan=-.35)
    # yumşaq fon padı
    for k3, ch in enumerate(['C', 'G', 'Am', 'F'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=500 + 40 * k3, v=.22 + .015 * k3, att=.3))
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    # final: təmiz, inamlı ritm + strings
    t, k = REVEAL + .1, 0
    while t < DUR - 1.2:
        ch = ['C', 'G', 'Am', 'F'][(k // 4) % 4]; mus.add(t, strum(ch, .2 if k % 2 == 0 else .13, k % 2 == 0, 0, seed=100 + k)); t += .31; k += 1
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def clamp01(v):
    return max(0.0, min(1.0, v))


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm34_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
