"""M30 «Pilləkən» — THE CLIMBER vs THE WAITER (2026-11-19, gecə planı; bölünmüş ekran, təsdiqlənmiş format).

İLK İŞIQLI video (istifadəçi 11-17: «videolar çox qaranlıqdır» → .claude/skills/ssenari): günəşli səhər, rəngli personajlar (pal),
yuxarı: velosiped yolu, paralaks şəhər/ağac/bulud, IK pedal (ayaqlar pedalda fırlanır), Day 30 yağış + deşik təkər (−5);
aşağı: tıxacda maşın, əyləc işıqları, BEEP/HONK, IN TRAFFIC: N H. Sonda ağ kartda qrafik (+N vs 0).
İşlətmə: python3 m30_pillekan.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME BUILDING.\nTWO WAYS UP.", "TWO WAYS UP.", "gold"),
    (2.35, 4.50, "ONE TAKES\nTHE STAIRS.", "THE STAIRS.", "green"),
    (4.60, 6.85, "ONE WAITS FOR\nTHE ELEVATOR.", "THE ELEVATOR.", "red"),
    (7.00, 9.45, "DAY 30.\nOUT OF BREATH.", "OUT OF BREATH.", "red"),
    (9.55, 11.85, "DAY 30.\nSTILL WAITING.", "STILL WAITING.", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE CLIMBS AGAIN.", "CLIMBS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nSAME BUTTON.", "SAME BUTTON.", "red"),
    (17.40, 21.05, "SAME STAIRS.\nDIFFERENT YEAR.", "DIFFERENT YEAR.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO SKIPS THE STAIRS.", "SKIPS THE STAIRS.", "gold"),
]
VO = [(0.2, "Same building. Two ways up."), (2.45, "One takes the stairs."), (4.65, "One waits for the elevator."), (7.15, "Day thirty. Out of breath."),
      (9.6, "Day thirty. Still waiting."), (12.05, "Next day, he climbs again."), (15.0, "The other one? Same button."),
      (17.5, "Same stairs. Different year."), (21.35, "Send this to someone who skips the stairs.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE CLIMBER", "THE WAITER"])


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


def step(seed, v=.18):
    n = int(.12 * S.SR); tt = np.arange(n) / S.SR
    return ((S.bp(noise(n, seed), 400, 4000) * np.exp(-tt * 55) + S.lp(noise(n, seed + 1), 180) * np.exp(-tt * 70) * 2.5) * v).astype(np.float32)


def beep(seed, v=.1):
    n = int(.25 * S.SR); tt = np.arange(n) / S.SR
    return (np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt * 10) * v).astype(np.float32)


def breath(seed, v=.12):
    n = int(.45 * S.SR); tt = np.arange(n) / S.SR
    return (S.bp(noise(n, 40 + seed), 500, 2500) * np.sin(np.pi * tt / .45) ** 2 * v).astype(np.float32)


def noop():
    pass


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(noise(N, 7), 80, 600) * .02 * (1 + .4 * np.sin(2 * np.pi * .13 * tt))).astype(np.float32))  # səhər şəhər uğultusu
    t, k = .4, 0
    while t < REVEAL:
        if not (SINK - .2 < t < SINK + 2.2):
            fx.add(t, step(k), pan=.3)
        t += .385; k += 1
    t, k = 4.6, 0
    while t < REVEAL:
        fx.add(t, beep(k, .07), pan=-.35); t += 1.25; k += 1
    for k in range(4):
        fx.add(SINK + .3 + k * .55, breath(k))
    fx.add(SINK + .1, S.boom(.25))
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
    html = open(os.path.join(HERE, 'm30_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
