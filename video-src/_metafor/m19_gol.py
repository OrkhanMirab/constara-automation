"""M19 «Göl» — THE SWIMMER vs THE READER (2026-11-15).

İstifadəçi: M14 «Fənər» (sadə bölünmüş ekran, Starter vs Planner) 1.2K baxışı keçdi → «onun kimi birini də et, eyni mövzuda,
amma fərqli video»; M14-də fiqurlar tərs (dizlər) idi → M17 insan siluetləri (IK, rim işıq) ilə.
Yuxarı panel: suya tullanır, Day 30 batır (−5), pis üzür, sonra yaxşı; aşağı panel: qayada «HOW TO SWIM» oxuyur, kitab yığını (#41).
Sonda yuxarı panel geri çəkilir → qrafik (+355), oxucu 0. «You don't learn to swim on the shore.»
İşlətmə: python3 m19_gol.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 26.0
JUMP, SINK, REVEAL, END = 2.4, 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "DAY ONE.\nSAME LAKE.", "SAME LAKE.", "gold"),
    (2.35, 4.50, "ONE JUMPS IN.", "JUMPS IN.", "gold"),
    (4.60, 6.85, "ONE READS ABOUT\nSWIMMING.", "READS", "red"),
    (7.00, 9.45, "DAY 30. HE SINKS.", "SINKS.", "red"),
    (9.55, 11.85, "DAY 30. BOOK #4.", "BOOK #4.", "red"),
    (12.00, 14.85, "HE SWIMS BADLY.\nTHEN BETTER.", "BETTER.", "gold"),
    (14.95, 17.25, "THE READER IS STILL\nON THE SHORE.", "ON THE SHORE.", "red"),
    (17.40, 21.05, "YOU DON'T LEARN TO SWIM\nON THE SHORE.", "ON THE SHORE.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nSTILL READING ABOUT IT.", "STILL READING ABOUT IT.", "gold"),
]
VO = [(0.2, "Day one. Same lake."), (2.4, "One jumps in."), (4.65, "One reads about swimming."), (7.15, "Day thirty. He sinks."),
      (9.6, "Day thirty. Book number four."), (12.05, "He swims badly. Then better."), (15.0, "The reader is still on the shore."),
      (17.5, "You don't learn to swim on the shore."), (21.35, "Send this to someone still reading about it.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [12.0, 100], [16.0, 180], [18.6, 365]], jump=JUMP, sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4)


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


def splash(v=1.0, seed=1, d=.9):
    n = int(d * S.SR); e = np.exp(-np.arange(n) / (n / 5))
    x = S.bp(noise(n, seed), 400, 6000) * e * (np.random.default_rng(seed).random(n) > .5)
    return (x * .55 * v + S.lp(noise(n, seed + 1), 250) * e * .4 * v).astype(np.float32)


def stroke(seed, v=.4):
    n = int(.35 * S.SR); e = np.sin(np.pi * np.arange(n) / n) ** 2
    return (S.bp(noise(n, seed), 600, 4000) * e * .18 * v).astype(np.float32)


def page(seed):
    n = int(.3 * S.SR); x = noise(n, seed) * (np.random.default_rng(seed).random(n) > .8)
    return (S.bp(x, 2000, 9000) * np.exp(-np.arange(n) / (n / 3)) * .22).astype(np.float32)


def bubbles(d, seed=4):
    N = int(d * S.SR); out = np.zeros(N, np.float32); rng = np.random.default_rng(seed)
    for _ in range(int(d * 18)):
        j = rng.integers(0, N - 3000); f = 300 + rng.random() * 600; tt = np.arange(2500) / S.SR
        out[j:j + 2500] += np.sin(2 * np.pi * f * (1 + 3 * tt) * tt) * np.exp(-tt * 40) * .2
    return out


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    tt = np.arange(N) / S.SR
    fx.add(0, (S.bp(noise(N, 7), 100, 900) * .025 * (1 + .5 * np.sin(2 * np.pi * .2 * tt))).astype(np.float32))  # su/külək fonu
    fx.add(JUMP + .1, S.whoosh(.4, .5)); fx.add(JUMP + .72, splash(1.0, 3))
    t, k = JUMP + 1.3, 0
    while t < REVEAL:
        skill = min(1, max(0, (t - 3) / 9)); fx.add(t, stroke(100 + k, .5 + .3 * skill), pan=.3)
        t += .62 - .2 * skill + (1 - skill) * .15 * np.sin(k * 2.3); k += 1
    fx.add(SINK + .3, splash(.6, 9, .5)); fx.add(SINK + .3, bubbles(1.2))
    for i in range(int((REVEAL - 2.2) / 1.1)):
        fx.add(2.2 + i * 1.1, page(50 + i), pan=-.35)
    fx.add(REVEAL, S.whoosh(.8, .7)); fx.add(REVEAL + .2, S.boom(.4))
    for k, ch in enumerate(['Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G', 'Am', 'G', 'F', 'G']):
        t0 = .1 + k * 1.24
        mus.add(t0, S.pad(ch, 1.35, cut=600 + 60 * k, v=.5 + .03 * k, att=.25)); mus.add(t0, S.sub(ch, 1.2, v=.35))
        notes = S.CHORDS[ch][1]
        for q in range(2 if k < 4 else 4):
            mus.add(t0 + q * (.62 if k < 4 else .31), S.piano(S.hz(notes[2 + q % 3]) * 2, 1.4, .22 + .01 * k))
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
    html = open(os.path.join(HERE, 'm19_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
