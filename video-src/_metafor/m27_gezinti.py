"""M27 «Gəzinti» — THE WALKER vs THE SITTER (2026-11-18, gecə planı; bölünmüş ekran, təsdiqlənmiş format).

İLK İŞIQLI video (istifadəçi 11-17: «videolar çox qaranlıqdır» → .claude/skills/ssenari): günəşli səhər, rəngli personajlar (pal),
yuxarı: velosiped yolu, paralaks şəhər/ağac/bulud, IK pedal (ayaqlar pedalda fırlanır), Day 30 yağış + deşik təkər (−5);
aşağı: tıxacda maşın, əyləc işıqları, BEEP/HONK, IN TRAFFIC: N H. Sonda ağ kartda qrafik (+N vs 0).
İşlətmə: python3 m27_gezinti.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME EVENING.\n20 FREE MINUTES.", "20 FREE MINUTES.", "gold"),
    (2.35, 4.50, "ONE GOES\nFOR A WALK.", "FOR A WALK.", "green"),
    (4.60, 6.85, "ONE PICKS\nTHE SOFA.", "THE SOFA.", "red"),
    (7.00, 9.45, "DAY 30.\nTOO TIRED. SKIPS.", "SKIPS.", "red"),
    (9.55, 11.85, "DAY 30.\nSAME SOFA.", "SAME SOFA.", "red"),
    (12.00, 14.85, "NEXT EVENING.\nHE WALKS AGAIN.", "WALKS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE EPISODE.", "ONE MORE EPISODE.", "red"),
    (17.40, 21.05, "SAME 20 MINUTES.\nDIFFERENT YEAR.", "DIFFERENT YEAR.", "gold"),
    (21.20, 25.80, "SEND THIS TO\nYOUR SOFA FRIEND.", "SOFA FRIEND.", "gold"),
]
VO = [(0.2, "Same evening. Twenty free minutes."), (2.45, "One goes for a walk."), (4.65, "One picks the sofa."), (7.15, "Day thirty. Too tired. He skips."),
      (9.6, "Day thirty. Same sofa."), (12.05, "Next evening, he walks again."), (15.0, "The other one? One more episode."),
      (17.5, "Same twenty minutes. Different year."), (21.35, "Send this to your sofa friend.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE WALKER", "THE SITTER"])


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
    for k in range(int((REVEAL - .3) / .41)):
        t = .3 + k * .41
        if not (SINK - .2 < t < SINK + 2.4):
            fx.add(t, step(k), pan=.3)
    for k in range(7):
        fx.add(1.0 + k * 2.3, chirp(k), pan=.5)
    for i in range(4):
        fx.add(5.2 + i * 2.86, ding(i), pan=-.4)
    fx.add(SINK, S.boom(.25))
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
    html = open(os.path.join(HERE, 'm27_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
