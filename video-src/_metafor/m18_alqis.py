"""M18 «Alqış» — əvvəl gülürlər, sonra unudurlar, zirvədə alqışlayırlar (Metafor, 2D premium siluet formatı, 2026-11-15).

İstifadəçi: «uğur və başqalarının səni qınaması — uğurdan əvvəl lağ edirlər, uğurdan sonra təbrik edib hörmət edirlər» mövzusu, M17 kimi.
Səhnə: dağın ətəyində izdiham (5 siluet) fənərli adama gülür → o, gecə tək qalxır (taunt baloncukları) → izdiham telefonlara
dönür (WATCHING 0), uzaqda fənər qalxır → Day 200 büdrəmə (−5) → Day 365 şəfəq, zirvədə fənəri qaldırır → eyni izdiham
başını qaldırıb alqışlayır («I ALWAYS BELIEVED IN YOU!») → geri çəkilmə: yol = qrafik. «Same people. Different view.»
İşlətmə: python3 m18_alqis.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m17_yol as M  # noqa: E402

FPS, DUR = 30, 26.0
SHOTS = [['A', 0, 3.0], ['B', 3.0, 6.0], ['C', 6.0, 9.5], ['D', 9.5, 12.5], ['E', 12.5, 14.5], ['F', 14.5, 17.5], ['H', 17.5, 26.01]]
XS = [[0, .8], [3.25, .8], [6.0, 4.3], [9.5, 38.7], [10.2, 39.75], [10.68, 41.6], [11.4, 41.75], [12.5, 43.1], [12.5001, 118.9], [13.6, 120.5], [26, 120.6]]
STUMBLE, IGNITE, RAISE = [10.2, 11.4], .3, 13.75
TEXTS = [
    (0.05, 2.90, "FIRST, THEY LAUGH.", "LAUGH.", "red"),
    (3.05, 5.90, "THEN THEY ASK:\n\"WHO DO YOU\nTHINK YOU ARE?\"", "\"WHO DO YOU\nTHINK YOU ARE?\"", "red"),
    (6.05, 9.40, "THEN THEY FORGET\nYOU EXIST.", "FORGET", "red"),
    (9.55, 12.40, "DAY 200.\nNOBODY'S WATCHING.", "NOBODY'S WATCHING.", "red"),
    (12.55, 14.40, "DAY 365.", "DAY 365.", "gold"),
    (14.55, 17.40, "NOW THEY CLAP.", "CLAP.", "gold"),
    (17.55, 21.05, "SAME PEOPLE.\nDIFFERENT VIEW.", "DIFFERENT VIEW.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nTHEY LAUGHED AT.", "THEY LAUGHED AT.", "gold"),
]
VO = [(0.25, "First, they laugh."), (3.15, "Then they ask, who do you think you are?"), (6.15, "Then they forget you exist."),
      (9.65, "Day two hundred. Nobody's watching."), (12.65, "Day three sixty five."), (14.65, "Now they clap."),
      (17.65, "Same people. Different view."), (21.35, "Send this to someone they laughed at.")]
CROWD = [-5.9, -5.1, -4.3, -3.5, -2.7]
TL = dict(fps=FPS, dur=DUR, ridge=M.RIDGE, dips=M.DIPS, xs=XS, shots=SHOTS, stride=1.4, tosses=[], ignite=IGNITE, stumble=STUMBLE,
          lookup=99, end=21.2, texts=TEXTS, score=355, xend=120.5, peak=126, raise_=0,
          days=[[0, 1], [3.0, 1], [6.0, 20], [9.5, 200], [12.4, 201], [12.5, 365]],
          crowd=CROWD, modes=[6.0, 14.5], dawn=[12.3, 14.2],
          laughs=[[.3, 1.7, 0, 'HAHA', 700], [.7, 2.1, 1, 'YOU??', 800], [1.2, 2.6, 3, 'GIVE UP.', 690], [1.7, 2.95, 4, 'LOL', 790], [2.0, 2.95, 2, 'HAHAHA', 900]],
          taunts=[[3.3, 5.0, 720, 'WHO DO YOU THINK YOU ARE?'], [4.2, 5.95, 820, "IT WON'T WORK."]],
          cheers=[[14.8, 16.6, 1, 'SO PROUD OF YOU!', 680], [15.3, 17.1, 3, 'I ALWAYS BELIEVED IN YOU!', 790], [15.9, 17.45, 0, 'LEGEND!', 900], [16.3, 17.45, 4, 'KNEW IT!', 680]])
TL['raise'] = RAISE; TL.pop('raise_')


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


def applause(d, dens=26, seed=5):  # sintetik alqış
    N = int(d * S.SR); out = np.zeros(N, np.float32); rng = np.random.default_rng(seed)
    env = np.minimum(1, np.arange(N) / (.5 * S.SR)) * np.minimum(1, (N - np.arange(N)) / (.8 * S.SR))
    for _ in range(int(dens * d)):
        j = rng.integers(0, N - 900); n = 600 + rng.integers(0, 300)
        b = S.bp(noise(n, int(rng.integers(1e6))), 700 + rng.random() * 900, 2600 + rng.random() * 2000) * np.exp(-np.arange(n) / (60 + rng.random() * 60))
        out[j:j + n] += b * (.5 + .5 * rng.random())
    return (out * env * .5).astype(np.float32)


def murmur(d, seed=3):  # izdiham uğultusu / gülüş əhvalı
    N = int(d * S.SR); t = np.arange(N) / S.SR
    x = S.bp(noise(N, seed), 250, 1800) * (.55 + .45 * np.abs(np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * 1.3 * t + 1)))
    return (x * .06 * np.minimum(1, t / .3) * np.minimum(1, (d - t) / .4)).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR)
    mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(noise(N, 7), 180, 1500) * .03 * (1 + .4 * np.sin(2 * np.pi * .13 * tt))).astype(np.float32))
    fx.add(0, murmur(3.0)); fx.add(3.0, (murmur(2.9, 9) * .45).astype(np.float32))
    for sh, a, b in SHOTS:
        if sh not in 'BDE':
            continue
        t, last = a, None
        while t < b:
            k = int(M.xs_at(t) / .725) if False else int(np.interp(t, [p[0] for p in XS], [p[1] for p in XS]) / .725)
            if last is not None and k != last and not (STUMBLE[0] < t < STUMBLE[1]):
                fx.add(t, M.step(int(t * 100), .85), pan=.15)
            last = k; t += 1 / 120
    fx.add(STUMBLE[0] + .05, S.whoosh(.3, .5)); fx.add(STUMBLE[0] + .2, M.step(901, 1.6)); fx.add(STUMBLE[0] + .45, S.kick(.55))
    fx.add(IGNITE - .05, M.strike())
    fx.add(14.5, applause(3.1, 30)); fx.add(17.5, (applause(3.0, 18, 8) * .55).astype(np.float32))
    fx.add(12.5, S.whoosh(.9, .6)); fx.add(17.5, S.whoosh(.9, .7)); fx.add(17.75, S.boom(.4))
    # musiqi: minor tənha puls → şəfəqdə major açılış → alqışda dolğun
    for k, ch in enumerate(['Am', 'F', 'Am', 'Em', 'Am', 'F', 'Dm', 'Em', 'F', 'G']):
        t0 = .1 + k * 1.24
        mus.add(t0, S.pad(ch, 1.35, cut=550 + 50 * k, v=.45 + .03 * k, att=.25)); mus.add(t0, S.sub(ch, 1.2, v=.33))
        notes = S.CHORDS[ch][1]
        for q in range(2):
            mus.add(t0 + q * .62, S.piano(S.hz(notes[2 + q % 3]) * 2, 1.4, .2 + .01 * k))
    mus.add(12.5 - 1.2, S.riser(1.2, .5)); mus.add(12.5, S.shimmer('C', 3.0, 1.0))
    for k, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'F', 'C', 'G', 'C', 'C']):
        t0 = 12.5 + k * 1.25
        mus.add(t0, S.strings(ch, 1.45, v=.5 + .05 * k, att=.3)); mus.add(t0, S.pad(ch, 1.45, cut=1000 + 90 * k, v=.6, att=.15)); mus.add(t0, S.sub(ch, 1.3, v=.4))
    for i, nm in enumerate(['E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'C6', 'E6', 'G6', 'E6']):
        mus.add(12.8 + i * .62, S.piano(S.hz(nm), 2.0, .28))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.8), .28)[:N]
    f = S.apply_reverb(fx.x, S.reverb_ir(1.2, 5000, 5), .14)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm18_scene2d.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
