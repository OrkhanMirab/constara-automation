"""M39 «Baraban» — THE DRUMMER vs THE WATCHER (2026-11-25, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: otaqda hər gün 10 dəq baraban; əvvəl taktdan qaçır (OFF), getdikcə tempo artır və groove sıxlaşır (ON BEAT 40% → 98%).
Day 30: yorğun, çubuqlar yerdə (−5); ertəsi gün yenə çalır. Aşağı: divanda cover videoları, baraban qutuda tozlanır.
Fərziyyə (11-25): M33 Gitara + M37 Basketbol partlayışlarının ortaq cəhəti = SƏSDƏ EŞİDİLƏN irəliləyiş. Bu video həmin xətti davam etdirir.
İşlətmə: python3 m39_baraban.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
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
    (2.35, 4.50, "ONE PLAYS DRUMS\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE WATCHES\nDRUM COVERS.", "DRUM COVERS.", "red"),
    (7.00, 9.45, "DAY 30.\nOFF BEAT AGAIN.", "OFF BEAT AGAIN.", "red"),
    (9.55, 11.85, "DAY 30.\n75 COVERS WATCHED.", "75 COVERS", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE PLAYS AGAIN.", "PLAYS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE COVER.", "ONE MORE COVER.", "red"),
    (17.40, 21.05, "YOU CAN'T WATCH\nYOUR WAY TO RHYTHM.", "RHYTHM.", "gold"),
    (21.20, 25.80, "SEND THIS TO A\nFUTURE DRUMMER.", "FUTURE DRUMMER.", "gold"),
]
VO = [(0.2, "Same dream. Two plans."), (2.45, "One plays drums, ten minutes a day."), (4.65, "One watches drum covers."), (7.15, "Day thirty. Off beat again."),
      (9.6, "Day thirty. Seventy five covers watched."), (12.05, "Next day, he plays again."), (15.0, "The other one? One more cover."),
      (17.5, "You can't watch your way to rhythm."), (21.35, "Send this to a future drummer.")]
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


def gen_hits():
    hits, t, step, rng = [], .3, 0, np.random.default_rng(39)
    while t < REVEAL - .25:
        d = day_at(t)
        if pause(t) > .3:
            t += .05; step = 0; continue
        e = 60 / (72 + 63 * cl(d / 250)) / 2  # sekizlik
        i = step % 8
        jit = (1 - cl(d / 150)) * .055
        kinds = [2]
        if i in (0, 4) or (d > 120 and i == 5): kinds.append(0)
        if i in (2, 6): kinds.append(1)
        for k in kinds:
            if k == 2 and d < 40 and rng.random() < .25:  # başlanğıcda hi-hat da itir
                continue
            dev = float(rng.normal(0, jit)) if jit > 0 else 0.0
            hits.append([round(t + dev, 3), k, int(abs(dev) < .03)])
        t += e; step += 1
    hits.sort(key=lambda h: h[0])
    return hits


HITS = gen_hits()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE DRUMMER", "THE WATCHER"], hits=HITS)


def snare(v):
    n = int(.25 * S.SR); x = np.arange(n) / S.SR
    return ((S.bp(noise(n, 21), 900, 9000) * np.exp(-x * 22) * .5 + np.sin(2 * np.pi * 190 * x) * np.exp(-x * 30) * .6) * v * .45).astype(np.float32)


def hat(v):
    n = int(.08 * S.SR); x = np.arange(n) / S.SR
    return (S.bp(noise(n, 23), 7000, 15000) * np.exp(-x * 70) * v * .35).astype(np.float32)


def kick(v):
    n = int(.3 * S.SR); x = np.arange(n) / S.SR
    return (np.sin(2 * np.pi * (55 + 90 * np.exp(-x * 30)) * x) * np.exp(-x * 9) * v * .8).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    rng = np.random.default_rng(7)
    for t0, k, ok in HITS:
        d = day_at(t0); vel = (.75 + .25 * cl(d / 150)) * (1 - (1 - cl(d / 150)) * .3 * rng.random())
        fx.add(t0, [kick, snare, hat][k](vel * (1.0 if ok or d > 150 else .85)), pan=[0, .1, .35][k])
    fx.add(SINK + .15, S.boom(.25))
    n = int(.25 * S.SR); x = np.arange(n) / S.SR
    for j in range(2):  # yerə düşən çubuqlar
        fx.add(SINK + .55 + j * .18, (np.sin(2 * np.pi * (900 + 300 * j) * x) * np.exp(-x * 25) * .08).astype(np.float32), pan=.2)
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=450 + 30 * k3, v=.14 + .01 * k3, att=.4))
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
    html = open(os.path.join(HERE, 'm39_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'zərbə:', len(HITS), 'OFF:', sum(1 for h in HITS if not h[2]))


if __name__ == '__main__':
    run(sys.argv[1])
