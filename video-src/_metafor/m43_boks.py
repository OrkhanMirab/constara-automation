"""M43 «Boks kisəsi» — THE BOXER vs THE TALKER (2026-11-27, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: hər gün 10 dəq kisəyə zərbə; əvvəl tək, yavaş zərbələr, yarısı boşa (WHIFF), getdikcə sürətli kombinasiyalar (1-2, 1-2-3) — «tup-tup-TUP» ritmi.
Day 30: nəfəsi kəsilir, əllər dizdə (−5). Aşağı: divanda döyüş videoları izləyib «I could do that» deyir, divarda etiketi qopmamış əlcəklər.
Yenilik: kisənin fizikası (hər zərbə yelləncəyə impuls, zəncir cingiltisi), kombinasiya ritmi Python hadisələrindən (vizual + səs bir zaman xəttində).
İşlətmə: python3 m43_boks.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
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
    (0.05, 2.25, "SAME DREAM.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE HITS THE BAG\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE WATCHES\nFIGHTS.", "FIGHTS.", "red"),
    (7.00, 9.45, "DAY 30.\nOUT OF BREATH.", "OUT OF BREATH.", "red"),
    (9.55, 11.85, "DAY 30.\n\"I COULD DO THAT.\"", "\"I COULD DO THAT.\"", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE HITS AGAIN.", "HITS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE FIGHT.", "ONE MORE FIGHT.", "red"),
    (17.40, 21.05, "YOU DON'T GET FAST\nBY WATCHING FAST.", "BY WATCHING FAST.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO SAYS \"I COULD DO THAT.\"", "\"I COULD DO THAT.\"", "gold"),
]
VO = [(0.2, "Same dream. Two plans."), (2.45, "One hits the bag, ten minutes a day."), (4.65, "One watches fights."), (7.15, "Day thirty. Out of breath."),
      (9.6, "Day thirty. I could do that."), (12.05, "Next day, he hits again."), (15.0, "The other one? One more fight."),
      (17.5, "You don't get fast by watching fast."), (21.35, "Send this to someone who says, I could do that.")]
DAYS = [[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]]


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


COMBOS = [[0], [0, 1], [0, 0, 1], [0, 1, 2], [0, 1, 2, 1], [1, 2, 1]]


def gen_hits():
    """[t, kind(0 jab / 1 cross / 2 hook), ok(1 kisəyə dəydi / 0 boşa)]"""
    hits, t, rng = [], .4, np.random.default_rng(43)
    while t < REVEAL - .3:
        if pause(t) > .3:
            t += .05; continue
        d = day_at(t)
        lvl = cl(d / 200); combo = [int(rng.choice([0, 1]))] if d < 25 else COMBOS[min(5, int(rng.integers(1, 3 + int(lvl * 3))))]
        gap = .26 - .11 * lvl
        for k in combo:
            ok = int(rng.random() > .45 * (1 - cl(d / 90)))
            hits.append([round(t, 3), k, ok]); t += gap
        t += (.6 - .38 * lvl) + float(rng.normal(0, .1 * (1 - lvl)))
    return hits


HITS = gen_hits()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE BOXER", "THE TALKER"], hits=HITS)


def punch(v, k):
    n = int(.3 * S.SR); x = np.arange(n) / S.SR
    body = np.sin(2 * np.pi * (70 + 50 * np.exp(-x * 40)) * x) * np.exp(-x * 18)
    slap = S.bp(noise(n, 31 + k), 800, 5000) * np.exp(-x * 70)
    return ((body * .9 + slap * (.6 + .2 * k)) * v * .5).astype(np.float32)


def whiff(v):
    n = int(.2 * S.SR); x = np.arange(n) / S.SR
    return (S.bp(noise(n, 77), 500, 3000) * np.sin(np.pi * x / .2) * v * .12).astype(np.float32)


def chain(v):
    n = int(.35 * S.SR); x = np.arange(n) / S.SR; s = np.zeros(n)
    for f in (2900, 3700, 4600): s += np.sin(2 * np.pi * f * x) * np.exp(-x * 14)
    return (s * v * .02).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    for t0, k, ok in HITS:
        d = day_at(t0); v = .7 + .3 * cl(d / 150)
        fx.add(t0 - .06, whiff(.6 + .4 * ok), pan=.1)
        if ok: fx.add(t0, punch(v, k), pan=.15); fx.add(t0 + .05, chain(v), pan=.3)
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
    html = open(os.path.join(HERE, 'm43_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'zərbə:', len(HITS), 'boşa:', sum(1 for h in HITS if not h[2]))


if __name__ == '__main__':
    run(sys.argv[1])
