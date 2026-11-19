"""M32 «Spotlight Effect» — PSİXOLOGİYA seriyası #1 (11-19). Maskot blob-lar (konturlu stiker üslubu), M31 motion dili.
Ssenari: qəhvə tökülür → «hamı baxır» (xəyali qaralma, LOL/EW baloncukları) → «WRONG.» → hər kəsin öz spot işığı/öz dərdi →
statistika kartı (Gilovich 2000: ~50% gözlənti vs ~25% reallıq) → rahatlayır → CTA.
python3 m32_spotlight.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; önizləmə: python3 onizleme.py <scratch> <out.html>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 27.0
SC = dict(spill=1.3, stare=3.0, bubbles=5.6, wrong=8.7, reveal=9.6, stat=15.4, relax=21.0, cta=23.5)
G, O, RD = '#17A862', '#FF6B35', '#E5484D'
TEXTS = [
    (0.10, 2.85, "YOU SPILL COFFEE|ON YOUR SHIRT.", 80, ["COFFEE", O]),
    (3.00, 5.45, "EVERYONE IS STARING.", 84, ["STARING.", RD]),
    (5.60, 8.50, "RIGHT?", 130, None),
    (8.70, 9.50, "WRONG.", 150, ["WRONG.", G]),
    (9.65, 15.20, "THEY'RE BUSY WITH|THEIR OWN SPOTLIGHT.", 76, ["OWN", G]),
    (15.40, 20.80, "THE SPOTLIGHT EFFECT.", 80, ["SPOTLIGHT", O]),
    (21.00, 23.30, "SO GO DO THE THING.", 90, ["THING.", G]),
    (23.50, 26.80, "SEND THIS TO SOMEONE|WHO OVERTHINKS.", 80, ["OVERTHINKS.", O]),
]
VO = [(0.2, "You spill coffee on your shirt."), (3.05, "And suddenly, everyone is staring at you."),
      (5.75, "Right?"), (8.75, "Wrong."),
      (9.8, "Everyone is too busy with their own spotlight."), (12.6, "Their hair. Their phone. Their own mistakes."),
      (15.5, "Psychologists call it the spotlight effect."), (18.1, "You think half the room noticed. Really? One in four."),
      (21.5, "So stop hiding. Go do the thing."), (23.75, "Send this to someone who overthinks.")]
TL = dict(fps=FPS, dur=DUR, s=SC, texts=TEXTS)


def voice_track(N):
    if '--tts' not in sys.argv:
        return None
    from kokoro_onnx import Kokoro
    from scipy.signal import resample_poly
    d = sys.argv[sys.argv.index('--tts') + 1]
    k = Kokoro(os.path.join(d, 'kokoro-v1.0.onnx'), os.path.join(d, 'voices-v1.0.bin'))
    v = np.zeros(N, np.float32); end = 0
    for t0, txt in VO:
        a, sr = k.create(txt, voice='am_michael', speed=0.98, lang='en-us')
        i = np.where(np.abs(a) > .01)[0]; a = a[max(0, i[0] - 200):i[-1] + 800]
        a = resample_poly(a, S.SR, sr).astype(np.float32)
        if t0 < end: print(f'⚠ üst-üstə: {txt!r} {t0} < {end:.2f}')
        end = t0 + len(a) / S.SR
        j = int(t0 * S.SR); v[j:j + len(a)] += a[:N - j]
    return S.voice_chain(v)


def ding(k, v=.07):
    n = int(.3 * S.SR); tt = np.arange(n) / S.SR; f = 2300 * (1 + .06 * (k % 5))
    return ((np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 1.5 * tt)) * np.exp(-tt * 16) * v).astype(np.float32)


def scratch(v=.5):
    n = int(.35 * S.SR); tt = np.arange(n) / S.SR
    f = 1800 * np.exp(-tt * 6) + 200
    return (S.bp(noise(n, 77), 300, 5000) * np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-tt * 6) * v).astype(np.float32)


def pop(k, v=.12):
    n = int(.12 * S.SR); tt = np.arange(n) / S.SR; f = 500 + 120 * (k % 4)
    return (np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * np.exp(-tt * 40))) / S.SR) * np.exp(-tt * 30) * v).astype(np.float32)


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    for k in range(7):
        fx.add(.2 + k * .16, S.tick(.6), pan=-.2)                      # addımlar
    fx.add(SC['spill'], S.boom(.25)); fx.add(SC['spill'] + .05, S.whoosh(.3, .5))
    fx.add(SC['stare'], S.boom(.4)); fx.add(SC['stare'], S.rev_swell(.6, .5))
    for k in range(9):
        fx.add(SC['stare'] + .4 + k * .75, S.heartbeat(.5 + .05 * k))
    for k in range(6):
        fx.add(SC['bubbles'] + k * .22, pop(k))
    fx.add(SC['wrong'], scratch(.6)); fx.add(SC['wrong'] + .05, S.boom(.5))
    fx.add(SC['reveal'], S.whoosh(.7, .6)); fx.add(SC['reveal'] + .3, S.shimmer('C', 2.5, .6))
    fx.add(SC['stat'], S.whoosh(.4, .5)); fx.add(SC['stat'] + .4, pop(1, .1)); fx.add(SC['stat'] + 1.6, pop(3, .1))
    for k in range(4):
        fx.add(SC['relax'] + k * .45, pop(k, .08))
    # musiqi: oynaq pizzicato (0–3) → gərgin dron (3–8.7) → səssizlik → işıqlı (9.6–)
    for k, ch in enumerate(['C', 'G', 'Am', 'F']):
        t0 = .05 + k * .7
        for q in range(4):
            mus.add(t0 + q * .175, S.piano(S.hz(S.CHORDS[ch][1][1 + q % 4]) * 2, .35, .22))
    for k in range(5):
        mus.add(SC['stare'] + k * 1.15, S.pad('Am', 1.3, cut=500, v=.5, att=.3)); mus.add(SC['stare'] + k * 1.15, S.sub('Am', 1.2, v=.45))
    prog = ['C', 'G', 'Am', 'F'] * 5
    for k, ch in enumerate(prog):
        t0 = SC['reveal'] + .2 + k * 1.05
        if t0 > DUR - 1: break
        mus.add(t0, S.pad(ch, 1.2, cut=900 + 30 * k, v=.45, att=.15)); mus.add(t0, S.sub(ch, 1.05, v=.3))
        for q in range(4):
            mus.add(t0 + q * .2625, S.piano(S.hz(S.CHORDS[ch][1][2 + q % 3]) * 2, .7, .2))
        if t0 > SC['relax'] - .1:
            mus.add(t0, S.kick(.3)); mus.add(t0 + .525, S.kick(.25))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .22)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=9.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.2 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm32_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
