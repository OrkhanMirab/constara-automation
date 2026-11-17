"""M28 «10 səhifə» (2026-11-18, YENİ TİP: tək sabit kadr timelapse; ÖNİZLƏMƏ — istifadəçi təsdiqindən əvvəl MP4 YOX).

İLK İŞIQLI video (istifadəçi 11-17: «videolar çox qaranlıqdır» → .claude/skills/ssenari): günəşli səhər, rəngli personajlar (pal),
yuxarı: velosiped yolu, paralaks şəhər/ağac/bulud, IK pedal (ayaqlar pedalda fırlanır), Day 30 yağış + deşik təkər (−5);
aşağı: tıxacda maşın, əyləc işıqları, BEEP/HONK, IN TRAFFIC: N H. Sonda ağ kartda qrafik (+N vs 0).
İşlətmə: python3 m28_sehife.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 6.8, 19.3, 22.3
TEXTS = [
    (0.05, 2.50, "10 PAGES A DAY.\nTHAT'S IT.", "10 PAGES", "gold"),
    (2.60, 6.40, "DAY 1.\nFEELS LIKE NOTHING.", "NOTHING.", "gold"),
    (6.60, 9.40, "DAY 30.\nTHE PHONE WINS.", "PHONE WINS.", "red"),
    (9.50, 12.80, "DAY 31.\n10 PAGES AGAIN.", "AGAIN.", "green"),
    (12.90, 16.30, "AUTUMN.\nBOOK NUMBER 10.", "BOOK NUMBER 10.", "green"),
    (16.40, 19.20, "WINTER.\nBOOK NUMBER 16.", "BOOK NUMBER 16.", "green"),
    (19.30, 22.20, "ONE YEAR.\n18 BOOKS.", "18 BOOKS.", "gold"),
    (22.30, 25.80, "SEND THIS TO SOMEONE\nWHO WANTS TO READ MORE.", "READ MORE.", "gold"),
]
VO = [(0.2, "Ten pages a day. That's it."), (2.8, "Day one. Feels like nothing."), (6.75, "Day thirty. The phone wins."),
      (9.65, "Day thirty-one. Ten pages again."), (13.05, "Autumn. Book number ten."), (16.55, "Winter. Book number sixteen."),
      (19.45, "One year. Eighteen books."), (22.45, "Send this to someone who wants to read more.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.6, 1], [6.6, 30], [9.4, 31], [12.9, 150], [16.4, 290], [19.2, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["", ""])


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


def step(seed, v=.16):
    n = int(.12 * S.SR); tt = np.arange(n) / S.SR
    return ((S.bp(noise(n, seed), 300, 3500) * np.exp(-tt * 45) + S.lp(noise(n, seed + 1), 200) * np.exp(-tt * 60) * 2) * v).astype(np.float32)


def chirp(seed, v=.08):
    n = int(.5 * S.SR); tt = np.arange(n) / S.SR; x = np.zeros(n, np.float32)
    for q in range(3):
        j = int(q * .11 * S.SR); u = tt[:int(.08 * S.SR)]; f = 3200 + 900 * np.sin(np.pi * u / .08) + 200 * (seed % 3)
        y = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.sin(np.pi * u / .08); x[j:j + len(y)] += y[:n - j]
    return (x * v).astype(np.float32)


def ding(seed, v=.12):
    n = int(.6 * S.SR); tt = np.arange(n) / S.SR; f = [880, 1175][seed % 2]
    return ((np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2 * tt)) * np.exp(-tt * 6) * v).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(noise(N, 7), 80, 600) * .02 * (1 + .4 * np.sin(2 * np.pi * .13 * tt))).astype(np.float32))  # səhər şəhər uğultusu
    for k in range(int((REVEAL - 2.6) / .25)):
        t = 2.6 + k * .25
        if not (SINK - .2 < t < SINK + 2.2):
            fx.add(t, step(k, .07), pan=.25)
    for k in range(5):
        fx.add(.7 + k * .33, step(100 + k, .1))
    for i in range(4):
        fx.add(SINK + .1 + i * .5, ding(i, .1), pan=-.3)
    fx.add(SINK + .3, S.boom(.25))
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
    html = open(os.path.join(HERE, 'm28_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
