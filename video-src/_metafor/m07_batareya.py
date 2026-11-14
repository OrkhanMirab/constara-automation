"""M07 «Batareya» — 11 s rəngli LOOP (Metafor, 2026-11-15, gecə planı).

Fiqurun üstündə batareya 100%. Pis vərdiş kartları boşaldır (SCROLLING −20 … → 25%), fiqur əyilir;
yaxşı vərdiş kartları doldurur (… SLEEP 8H +40 → 100%). Son kadr = ilk kadr (tikişsiz loop). CTA: «What's your biggest leak?»
İstifadəçi 11-14: «10–12 s, sürətli, loop, rəngli, pro; ortalama izləmə əsasdır».
İşlətmə: python3 m07_batareya.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; render.mjs ; ffmpeg.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 11.0
CARDS = [  # (zərbə vaxtı, mətn, dəyişiklik, rəng, tərəf −1 sol / +1 sağ)
    (1.00, "SCROLLING", -20, "#FF4D6D", -1), (1.85, "LATE NIGHT", -30, "#FF7A3D", 1),
    (2.70, "JUNK FOOD", -15, "#FF5ABF", -1), (3.50, "NO MOVEMENT", -10, "#B15CFF", 1),
    (5.40, "WALK", 15, "#2EE59D", -1), (6.20, "WATER", 10, "#3DD6FF", 1),
    (7.10, "SLEEP 8H", 40, "#F7C04A", -1), (8.00, "SUNLIGHT", 10, "#FFE45C", 1),
]
TEXTS = [
    (0.00, 0.95, "WHY AM I\nALWAYS TIRED?", "TIRED?", "red"),
    (3.75, 5.65, "IT'S NOT TIREDNESS.\nIT'S LEAKS.", "LEAKS.", "red"),
    (5.70, 8.60, "PLUG THEM.\nCHARGE ON PURPOSE.", "CHARGE", "gold"),
    (8.70, 10.55, "WHAT'S YOUR\nBIGGEST LEAK? 👇", "BIGGEST LEAK?", "gold"),
    (10.55, 11.00, "WHY AM I\nALWAYS TIRED?", "TIRED?", "red"),   # loop tikişi: ilk kadrla eyni
]
VO = [(0.05, "Why am I always tired?"), (3.75, "It's not tiredness. It's leaks."),
      (5.8, "Plug them. Charge on purpose."), (8.75, "What's your biggest leak?")]
TL = dict(fps=FPS, dur=DUR, cards=CARDS, texts=TEXTS)


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
        a, sr = k.create(txt, voice='am_michael', speed=1.0, lang='en-us')
        i = np.where(np.abs(a) > .01)[0]; a = a[max(0, i[0] - 200):i[-1] + 600]
        a = resample_poly(a, S.SR, sr).astype(np.float32)
        j = int(t0 * S.SR); v[j:j + len(a)] += a[:N - j]
        print(f'  vo {t0:5.2f} +{len(a) / S.SR:.2f}s  {txt}')
    return S.voice_chain(v)


def audio(path):
    N = int(DUR * S.SR)
    mus, fx = S.Bus(DUR + 2), S.Bus(DUR + 2)
    # 120 bpm ritm (loop üçün 11 s = 22 vuruş): kick hər vuruşda, hi-hat arada
    for b in range(22):
        t0 = b * .5
        mus.add(t0, S.kick(.32 if b % 2 else .42))
        d = int(.03 * S.SR); mus.add(t0 + .25, (S.hp(noise(d, b), 7000) * np.exp(-np.arange(d) / (d / 4)) * .12).astype(np.float32))
    prog = [('Am', 0), ('F', 2.0), ('Dm', 4.0), ('C', 5.5), ('G', 7.5), ('Am', 9.5)]   # sonda Am → başlanğıcla tikiş
    for (ch, t0), nxt in zip(prog, prog[1:] + [('Am', 11.0)]):
        d2 = nxt[1] - t0
        mus.add(t0, S.pad(ch, d2 + .05, cut=900, v=.55, att=.05, rel=.2)); mus.add(t0, S.sub(ch, d2, v=.4))
        for j in range(int(d2 / .25)):
            nt = S.CHORDS[ch][1][2 + (j % 3)]
            mus.add(t0 + j * .25, S.piano(S.hz(nt) * 2, .5, .18))
    for t0, txt, delta, col, side in CARDS:
        fx.add(t0 - .3, S.whoosh(.35, .5))
        if delta < 0:
            tt = S.tarr(.4); fx.add(t0, (np.sin(2 * np.pi * (300 * np.exp(-tt * 4)) * tt) * np.exp(-tt * 8) * .35).astype(np.float32))
        else:
            for k, nm in enumerate(['C5', 'E5', 'G5']):
                mus.add(t0 + k * .05, S.piano(S.hz(nm) * 2, .7, .3))
        fx.add(t0, S.tick(.6))
    m = S.apply_reverb(mus.x, S.reverb_ir(1.6), .18)
    f = S.apply_reverb(fx.x, S.reverb_ir(.8, 6000, 5), .1)
    # loop: 11 s-dən sonrakı quyruğu başa qat (tikişsiz)
    def fold(x):
        y = x[:N].copy(); tail = x[N:]; y[:len(tail)] += tail[:N]; return y
    m, f = fold(m), fold(f)
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=8.0)[:N] if vo is not None else np.tanh((m * .6 + f * .9))
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm07_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
