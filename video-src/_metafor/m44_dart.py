"""M44 «Dart» — THE THROWER vs THE GAMER (2026-11-28, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: hər gün 10 dəq dart atır; əvvəl oxlar lövhədən qaçır (divara dəyib yerə düşür — CLACK), getdikcə mərkəzə yığılır (THUNK, bullseye DING).
Day 30: çiyin ağrıyır (−5). Aşağı: divanda telefonda dart oyunu oynayır («PERFECT 180!»), rəfdə açılmamış dart qutusu tozlanır.
Yenilik: kəsimli kadr — hər 3-cü atış lövhəyə çatanda kamera lövhənin ÖNDƏN yaxın planına kəsilir (flaş, xal cəmi).
İşlətmə: python3 m44_dart.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m33_gitara as M33  # noqa: E402
from m37_basketbol import R, noise  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME BOARD.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE THROWS\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE PLAYS IT\nON HIS PHONE.", "ON HIS PHONE.", "red"),
    (7.00, 9.45, "DAY 30.\nSORE ARM.", "SORE ARM.", "red"),
    (9.55, 11.85, "DAY 30.\n\"NEW HIGH SCORE!\"", "\"NEW HIGH SCORE!\"", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE THROWS AGAIN.", "THROWS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE LEVEL.", "ONE MORE LEVEL.", "red"),
    (17.40, 21.05, "SCREEN POINTS\nDON'T COUNT.", "DON'T COUNT.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO'S A PRO ON HIS PHONE.", "ON HIS PHONE.", "gold"),
]
VO = [(0.2, "Same board. Two plans."), (2.45, "One throws, ten minutes a day."), (4.65, "One plays it on his phone."), (7.15, "Day thirty. Sore arm."),
      (9.6, "Day thirty. New high score."), (12.05, "Next day, he throws again."), (15.0, "The other one? One more level."),
      (17.5, "Screen points don't count."), (21.35, "Send this to someone who's a pro on his phone.")]
DAYS = [[0, 1], [2.2, 1], [7.0, 30], [11.8, 31], [13.6, 100], [16.0, 180], [18.6, 365]]


def day_at(t):
    d = DAYS[0][1]
    for i in range(len(DAYS) - 1):
        (a, d0), (b, d1) = DAYS[i], DAYS[i + 1]
        if t >= a:
            u = min(1, max(0, (t - a) / (b - a))); u = u * u * (3 - 2 * u); d = d0 + (d1 - d0) * u
    return d


def pause(t):
    return min(1, max(0, math.exp(-((t - (SINK + 1.1)) / .95) ** 2) * 1.6))


def cl(v):
    return min(1, max(0, v))


FLY = .3


def gen_throws():
    """[t_buraxma, dx, dy, ok] — dx/dy lövhə radiusu vahidində (mərkəz 0,0)"""
    th, t, rng = [], .55, np.random.default_rng(7)
    while t < REVEAL - .6:
        if 6.75 < t < 12.1:
            t = 12.1; continue
        d = day_at(t); lvl = cl(d / 180); sg = .95 * (1 - lvl) ** 1.4 + .05
        dx, dy = rng.normal(0, sg, 2); dy -= .25 * (1 - lvl)
        th.append([round(t, 3), round(float(dx), 3), round(float(dy), 3), int(math.hypot(dx, dy) <= 1)])
        t += 1.1 - .5 * lvl + float(rng.normal(0, .04))
        if len(th) % 3 == 0: t += .4 * (1 - lvl) + .3
    th[0][1:] = [.62, -.92, 0]  # 1-ci gün: ilk ox lövhədən qaçır
    return th


THROWS = gen_throws()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE THROWER", "THE GAMER"], hits=[], throws=THROWS, fly=FLY)


def thunk(v):
    n = int(.25 * S.SR); x = np.arange(n) / S.SR
    body = np.sin(2 * np.pi * (140 + 90 * np.exp(-x * 60)) * x) * np.exp(-x * 30)
    tick = S.bp(noise(n, 9), 1500, 6000) * np.exp(-x * 160)
    return ((body * .8 + tick * .7) * v * .55).astype(np.float32)


def clack(v, seed):
    n = int(.3 * S.SR); x = np.arange(n) / S.SR; s = np.zeros(n)
    for f in (1900, 2700, 3900): s += np.sin(2 * np.pi * f * x + seed) * np.exp(-x * 40)
    return ((s * .18 + S.bp(noise(n, seed), 2000, 7000) * np.exp(-x * 90) * .6) * v * .45).astype(np.float32)


def ding(v):
    n = int(.9 * S.SR); x = np.arange(n) / S.SR; s = np.zeros(n)
    for f, a in ((1568, 1), (2349, .5), (3136, .3)): s += a * np.sin(2 * np.pi * f * x) * np.exp(-x * 5)
    return (s * v * .09).astype(np.float32)


def swish(v):
    n = int(.22 * S.SR); x = np.arange(n) / S.SR
    return (S.bp(noise(n, 21), 900, 4500) * np.sin(np.pi * x / .22) ** 2 * v * .1).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    for i, (t0, dx, dy, ok) in enumerate(THROWS):
        fx.add(t0 - .02, swish(.8), pan=-.2)
        tl = t0 + FLY
        if ok:
            fx.add(tl, thunk(.8 + .2 * cl(day_at(t0) / 150)), pan=.3)
            if math.hypot(dx, dy) < .11: fx.add(tl + .02, ding(1.0), pan=.3)
        else:
            fx.add(tl, clack(.9, i), pan=.35); fx.add(tl + .45, clack(.5, i + 50), pan=.2); fx.add(tl + .58, clack(.25, i + 90), pan=.2)
    fx.add(SINK + .15, S.boom(.25))
    n = int(1.2 * S.SR); x = np.arange(n) / S.SR  # ağır nəfəs
    for j in range(3): fx.add(SINK + .4 + j * .6, (S.bp(noise(n, 50 + j), 300, 1800) * np.sin(np.pi * np.minimum(1, x / .45)) * np.exp(-x * 4) * .05).astype(np.float32), pan=0)
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=480 + 35 * k3, v=.16 + .012 * k3, att=.4))
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(.8, 6000, 5), .1)[:N]
    vo = M33.voice_track(N)
    out = S.mix(vo, m, f, duck_db=8.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm44_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'atış:', len(THROWS), 'boşa:', sum(1 for h in THROWS if not h[3]), 'bull:', sum(1 for h in THROWS if math.hypot(h[1], h[2]) < .11))


if __name__ == '__main__':
    run(sys.argv[1])
