"""M21 «Zəngli saat» — THE RISER vs THE SNOOZER (2026-11-16, gecə planı).

M14/M19 bölünmüş ekran quruluşu + 2D insan siluetləri, yeni dünya: şəfəq yolu və yataq otağı.
Yuxarı: hər səhər qaçır, yol = qrafik; səma günlərlə gecədən şəfəqə keçir (YENİLİK). Day 30 yıxılır (−5), qalxır.
Aşağı: zəngli saat çalır, əl yorğanın altından çıxıb snooze basır, SNOOZED: N TIMES; pərdə arxasında gün artır.
İşlətmə: python3 m21_saat.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "DAY ONE.\nSAME ALARM.", "SAME ALARM.", "gold"),
    (2.35, 4.50, "ONE GETS UP.", "GETS UP.", "gold"),
    (4.60, 6.85, "ONE HITS SNOOZE.", "SNOOZE.", "red"),
    (7.00, 9.45, "DAY 30. HE FALLS.", "FALLS.", "red"),
    (9.55, 11.85, "DAY 30.\n90 SNOOZES.", "90 SNOOZES.", "red"),
    (12.00, 14.85, "HE GETS UP.\nKEEPS RUNNING.", "KEEPS RUNNING.", "gold"),
    (14.95, 17.25, "THE SNOOZER IS\nSTILL IN BED.", "STILL IN BED.", "red"),
    (17.40, 21.05, "THE ALARM RANG\nFOR BOTH OF THEM.", "FOR BOTH", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO HITS SNOOZE.", "HITS SNOOZE.", "gold"),
]
VO = [(0.2, "Day one. Same alarm."), (2.4, "One gets up."), (4.65, "One hits snooze."), (7.15, "Day thirty. He falls."),
      (9.6, "Day thirty. Ninety snoozes."), (12.05, "He gets up. Keeps running."), (15.0, "The snoozer is still in bed."),
      (17.5, "The alarm rang for both of them."), (21.35, "Send this to someone who hits snooze.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE RISER", "THE SNOOZER"])


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


def clink(seed, v=.5):
    n = int(.25 * S.SR); tt = np.arange(n) / S.SR; rng = np.random.default_rng(seed); f = 1800 + rng.random() * 900
    x = (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 2.7 * tt)) * np.exp(-tt * 38) * .25
    x += S.bp(noise(n, seed), 300, 2500) * np.exp(-tt * 60) * .35
    return (x * v).astype(np.float32)


def step(seed, v=.5):
    n = int(.12 * S.SR); tt = np.arange(n) / S.SR
    return (S.lp(noise(n, seed), 500) * np.exp(-tt * 45) * .5 * v).astype(np.float32)


def rumble(d=1.6, seed=5):
    n = int(d * S.SR); tt = np.arange(n) / S.SR; e = np.exp(-tt * 2.2) * np.minimum(1, tt * 30)
    x = S.lp(noise(n, seed), 180) * e * 1.2
    rng = np.random.default_rng(seed)
    for _ in range(14):
        j = rng.integers(0, int(n * .7)); y = clink(seed + j, .9 * rng.random()); x[j:j + len(y)] += y[:n - j]
    return x.astype(np.float32)


def ping(seed, v=.3):
    n = int(.22 * S.SR); tt = np.arange(n) / S.SR; f = [1320, 1568, 1760][seed % 3]
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 18) * v + np.sin(2 * np.pi * f * 1.5 * tt) * np.exp(-tt * 25) * v * .4).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(noise(N, 7), 80, 600) * .02 * (1 + .4 * np.sin(2 * np.pi * .13 * tt))).astype(np.float32))  # şəhər uğultusu
    t, k = 2.5, 0
    while t < REVEAL:
        if not (SINK - .1 < t < SINK + 1.3):
            fx.add(t, step(100 + k, .5), pan=.25)
        t += .34; k += 1
    fx.add(SINK + .35, S.boom(.3)); fx.add(SINK + .35, step(9, 1.2))
    for i in range(int(REVEAL / 1.6) + 1):
        for q in range(3):
            fx.add(i * 1.6 + q * .11, ping(0, .16), pan=-.4)
    fx.add(REVEAL, S.whoosh(.8, .7)); fx.add(REVEAL + .2, S.boom(.4))
    for k, ch in enumerate(['Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G', 'Am', 'G', 'F', 'G']):
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
    html = open(os.path.join(HERE, 'm21_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
