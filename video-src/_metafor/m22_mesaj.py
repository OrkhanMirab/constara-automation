"""M22 «Gələcək sən yazır» — YENİ TİP: chat POV (2026-11-16, istifadəçi: «hər gün 1 yeni tip video yoxla»).

Bir il sonrakı «sən» gecə 23:47-də sənə yazır: «you're about to scroll for 3 hours again… I remember tonight… 10 pages, 20 pushups, phone in another room».
Mesajlar typing… ilə gəlir, diktor oxuyur; sonda qrafik şəkli (+355, Day 30 −5 dipi) mesaj kimi gəlir; sən «ok. starting now.» yazırsan.
İşlətmə: python3 m22_mesaj.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 24.0
END = 20.4
MSGS = [
    dict(t=0.9, text="hey. it's you. from one year later."),
    dict(t=3.6, text="you're about to scroll for 3 hours again."),
    dict(t=6.0, text="how do you know?", me=True),
    dict(t=7.4, text="because I remember tonight."),
    dict(t=9.5, text="it's the night I almost didn't start."),
    dict(t=11.9, text="10 pages. 20 pushups. phone in another room."),
    dict(t=14.6, text="it felt like nothing. it changed everything."),
    dict(t=16.9, text="", chart=True),
    dict(t=19.4, text="ok. starting now.", me=True),
]
TEXTS = [
    (0.05, 3.40, "YOUR FUTURE SELF\nJUST TEXTED YOU.", "FUTURE SELF", "gold"),
    (16.9, 20.3, "THIS IS WHAT\nTONIGHT TURNS INTO.", "TONIGHT", "gold"),
    (20.4, 23.9, "SEND THIS TO SOMEONE\nWHO NEEDS THIS TEXT.", "THIS TEXT.", "gold"),
]
VO = [(0.95, "Hey. It's you. From one year later."), (3.65, "You're about to scroll for three hours again."), (7.45, "Because I remember tonight."),
      (9.55, "It's the night I almost didn't start."), (11.95, "Ten pages. Twenty push-ups. Phone in another room."),
      (14.65, "It felt like nothing. It changed everything."), (17.0, "This is my year. Your year."), (20.6, "Send this to someone who needs this text.")]
TL = dict(fps=FPS, dur=DUR, end=END, texts=TEXTS, msgs=MSGS)


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


def pop(seed, v=.35, up=True):
    n = int(.12 * S.SR); tt = np.arange(n) / S.SR; f0 = 700 if up else 500
    return (np.sin(2 * np.pi * (f0 + (900 if up else 400) * tt / .12) * tt) * np.exp(-tt * 40) * v).astype(np.float32)


def key(seed, v=.12):
    n = int(.03 * S.SR); tt = np.arange(n) / S.SR
    return (S.bp(noise(n, seed), 2000, 8000) * np.exp(-tt * 200) * v).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR + 1), S.Bus(DUR + 1)
    for i, m in enumerate(MSGS):
        if m.get('me'):
            for k in range(int(len(m['text']) * .7)):
                fx.add(m['t'] - 1.1 + k * .95 / max(1, len(m['text']) * .7), key(300 + i * 40 + k), pan=.2)
            fx.add(m['t'], pop(i, .3, True), pan=.3)
        else:
            fx.add(m['t'], pop(i, .35, False), pan=-.2)
    # yumşaq gecə musiqisi: Am → F → C → G, sonda böyük akkord
    prog = ['Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G', 'F', 'G', 'C', 'G', 'Am', 'F', 'C', 'C']
    for k, ch in enumerate(prog):
        t0 = .1 + k * 1.5
        if t0 > DUR: break
        mus.add(t0, S.pad(ch, 1.6, cut=500 + 50 * k, v=.45 + .02 * k, att=.3)); mus.add(t0, S.sub(ch, 1.4, v=.3))
        nt = S.CHORDS[ch][1]
        for q in range(3):
            mus.add(t0 + q * .5, S.piano(S.hz(nt[2 + q % 3]) * 2, 1.4, .16 + .008 * k))
    mus.add(16.9 - 1.0, S.riser(1.0, .4)); mus.add(16.9, S.shimmer('C', 3.0, .9))
    for i, nm in enumerate(['E5', 'G5', 'C6', 'G5', 'E5', 'G5', 'C6', 'E6']):
        mus.add(17.0 + i * .5, S.piano(S.hz(nm), 1.8, .26))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.6), .3)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(.6, 6000, 5), .08)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.2 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm22_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
