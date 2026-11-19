"""M31 «Latte» — finans: $5/gün qəhvə = 30 ildə $172K (7%). YENİ MOTION ÜSLUBU (11-19, istifadəçi: «maraqlı ssenari + gözəl animasiya»):
düz vektor, spring easing, söz-söz kinetik yazı, dairəvi wipe, squash. Constara bağı yoxdur (səhifə strategiyası 11-19).
python3 m31_latte.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; önizləmə: python3 onizleme.py <scratch> <out.html>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 27.0
SC = dict(hook=.5, coins=5.0, invest=9.6, draw=10.4, drawEnd=15.4, pile=16.0, twist=19.6, cta=23.3)
G, O = '#17A862', '#FF6B35'
TEXTS = [
    (0.10, 3.80, "THIS COFFEE COSTS", 86, None),
    (3.95, 5.2, "OVER 30 YEARS.", 100, ["30", O]),
    (5.35, 7.25, "$5 A DAY.", 120, ["$5", O]),
    (7.35, 9.40, "EVERY SINGLE MORNING.", 80, None),
    (9.75, 12.30, "NOW INVEST IT INSTEAD.", 80, ["INVEST", G]),
    (12.45, 15.70, "7% A YEAR. 30 YEARS.", 86, ["7%", G]),
    (16.10, 19.35, "SAME COFFEE MONEY.", 86, None),
    (19.85, 23.1, "IT WAS NEVER THE COFFEE.", 76, ["NEVER", O]),
    (23.3, 26.7, "SEND THIS TO|YOUR COFFEE FRIEND.", 84, ["COFFEE", O]),
]
VO = [(0.2, "This coffee costs a hundred and seventy two thousand dollars."), (4.0, "Over thirty years."),
      (5.5, "Five dollars a day."), (7.45, "Every single morning."), (9.85, "Now, invest it instead."),
      (12.55, "Seven percent a year. For thirty years."), (16.2, "Same coffee money."),
      (17.6, "A hundred and seventy two thousand."), (19.95, "It was never about the coffee."),
      (21.75, "It's the small things you don't see."), (23.65, "Send this to your coffee friend.")]
TL = dict(fps=FPS, dur=DUR, s=SC, texts=TEXTS, hits=[SC['hook'], SC['pile'] + 1.5])


def spawns():
    t, dt, out = SC['coins'], .5, []
    while t < SC['invest'] - .55:
        out.append(t); t += dt; dt = max(.035, dt * .84)
    return out


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


def audio(path):
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(SC['hook'], S.boom(.35)); fx.add(SC['hook'], S.whoosh(.4, .5))
    for k, s in enumerate(spawns()):
        fx.add(s, S.whoosh(.2, .12), pan=.3 if k % 2 else -.3); fx.add(s + .42, ding(k, .07 if k < 12 else .045))
    fx.add(SC['invest'] - .15, S.whoosh(.6, .7))
    fx.add(SC['pile'] - .2, S.whoosh(.7, .7)); fx.add(SC['pile'] + 1.5, S.boom(.5))
    for k in range(10):
        fx.add(SC['pile'] + 1.5 + k * .07, ding(k, .05))
    fx.add(SC['twist'], S.rev_swell(.8, .4))
    prog = ['F', 'G', 'C', 'Am'] * 6
    for k, ch in enumerate(prog):
        t0 = .1 + k * 1.1
        if t0 > DUR - 1: break
        late = t0 > SC['invest']
        mus.add(t0, S.pad(ch, 1.25, cut=800 + 40 * k, v=.45, att=.15)); mus.add(t0, S.sub(ch, 1.1, v=.3))
        notes = S.CHORDS[ch][1]
        for q in range(4):
            mus.add(t0 + q * .275, S.piano(S.hz(notes[2 + q % 3]) * 2, .9, .16 + (.06 if late else 0)))
        if late and not (SC['twist'] - .1 < t0 < SC['cta']):
            mus.add(t0, S.kick(.32)); mus.add(t0 + .55, S.kick(.25))
    mus.add(SC['pile'] - 1.1, S.riser(1.1, .45)); mus.add(SC['pile'] + 1.5, S.shimmer('C', 3.0, .8))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.2), .22)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = voice_track(N)
    out = S.mix(vo, m, f, duck_db=9.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.2 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm31_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
