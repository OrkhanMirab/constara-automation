"""M45 «Çəkic» — THE BUILDER vs THE WATCHER (2026-11-28, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: hər gün 10 dəq masada mismar vurur; əvvəl çox zərbə, mismar əyilir (DINK), getdikcə «tak-BANG-BANG» — 3 zərbəyə bir mismar.
Divarda hazır işlər yığılır (qutu → quş evi → rəf → tabure → çərçivə → kitab şkafı). Day 30: barmağına vurur (−5).
Aşağı: divanda makeover videoları izləyir («I'LL BUILD THAT»), divara söykənmiş açılmamış SHELF KIT tozlanır.
İşlətmə: python3 m45_cekic.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
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
    (0.05, 2.25, "SAME IDEA.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE BUILDS\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE WATCHES\nMAKEOVER VIDEOS.", "MAKEOVER VIDEOS.", "red"),
    (7.00, 9.45, "DAY 30.\nHIT HIS THUMB.", "HIT HIS THUMB.", "red"),
    (9.55, 11.85, "DAY 30.\n\"I'LL BUILD THAT.\"", "\"I'LL BUILD THAT.\"", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE BUILDS AGAIN.", "BUILDS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE EPISODE.", "ONE MORE EPISODE.", "red"),
    (17.40, 21.05, "SAVED IDEAS\nDON'T HOLD BOOKS.", "DON'T HOLD BOOKS.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO'LL BUILD IT \"ONE DAY.\"", "\"ONE DAY.\"", "gold"),
]
VO = [(0.2, "Same idea. Two plans."), (2.45, "One builds, ten minutes a day."), (4.65, "One watches makeover videos."), (7.15, "Day thirty. Hit his thumb."),
      (9.6, "Day thirty. I'll build that."), (12.05, "Next day, he builds again."), (15.0, "The other one? One more episode."),
      (17.5, "Saved ideas don't hold books."), (21.35, "Send this to someone who'll build it, one day.")]
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


NAILX = [.18, .34, .5, .66, .26, .42, .58, .74]


def gen_nails():
    """[t, mismar, ok, k (dəyən zərbə sırası), n (lazım olan zərbə)]"""
    ev, t, nail, rng = [], .5, 0, np.random.default_rng(45)
    while t < REVEAL - .5:
        if 6.85 < t < 12.1:
            t = 12.1; continue
        d = day_at(t); lvl = cl(d / 170); n = 3 if lvl > .6 else (4 if lvl > .25 else 5); k = 0
        while k < n and t < REVEAL - .3 and not (6.85 < t < 12.1):
            ok = int(rng.random() > .35 * (1 - lvl) ** 1.5)
            ev.append([round(t, 3), nail, ok, k, n])
            if not ok:  # əyildi → yeni mismar
                t += .55 * (1 - lvl) + .25; break
            k += 1; t += (.5 - .3 * lvl) + float(rng.normal(0, .05 * (1 - lvl)))
        nail += 1; t += .55 - .3 * lvl
    return ev


NAILS = gen_nails()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE BUILDER", "THE WATCHER"], hits=[], nails=NAILS, nailx=NAILX)


def strike(v, heavy, seed):
    n = int(.35 * S.SR); x = np.arange(n) / S.SR
    ping = sum(a * np.sin(2 * np.pi * f * x + seed) * np.exp(-x * dk) for f, a, dk in ((2650, 1, 22), (4100, .6, 30), (5900, .3, 40)))
    knock = np.sin(2 * np.pi * (180 + 120 * np.exp(-x * 50)) * x) * np.exp(-x * 26)
    click = S.bp(noise(n, seed), 2500, 8000) * np.exp(-x * 200)
    return ((ping * (.12 + .06 * heavy) + knock * (.5 + .5 * heavy) + click * .5) * v * .5).astype(np.float32)


def dink(v, seed):
    n = int(.5 * S.SR); x = np.arange(n) / S.SR
    f = 1800 - 500 * x / .5
    s = np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.exp(-x * 9) * .25 + S.bp(noise(n, seed), 2000, 7000) * np.exp(-x * 120) * .4
    return (s * v * .5).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    for i, (t0, nl, ok, k, n) in enumerate(NAILS):
        d = day_at(t0); v = .75 + .25 * cl(d / 150)
        if ok: fx.add(t0, strike(v, 1 if k > 0 else 0, i), pan=.2)
        else: fx.add(t0, dink(v, i), pan=.25)
    fx.add(SINK - .02, strike(.9, 1, 99), pan=.2)  # barmağa
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
    html = open(os.path.join(HERE, 'm45_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'zərbə:', len(NAILS), 'əyilən:', sum(1 for h in NAILS if not h[2]), 'mismar:', len(set(h[1] for h in NAILS)))


if __name__ == '__main__':
    run(sys.argv[1])
