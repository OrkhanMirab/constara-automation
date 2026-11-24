"""M40 «Stolüstü tennis» — THE PLAYER vs THE BUYER (2026-11-25, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: masanın yarısı divar kimi qaldırılıb, hər gün 10 dəq; əvvəl ralli 2–4 zərbədə kəsilir (MISS), getdikcə «tok-tok» fasiləsiz və sürətli.
Day 30: yorğun, top yerdə (−5). Aşağı: divanda yeni raketkalar sifariş edir, divarda istifadə olunmamış raketkalar çoxalır.
Mesaj: «Better gear won't fix it. Reps will.» Səsdə eşidilən irəliləyiş (M33/M37 xətti).
İşlətmə: python3 m40_tennis.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m33_gitara as M33  # noqa: E402
from m37_basketbol import noise, thump  # noqa: E402
from m39_baraban import day_at, pause, cl, DAYS, SINK, REVEAL, END, FPS, DUR  # noqa: E402

TEXTS = [
    (0.05, 2.25, "SAME GOAL.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE PRACTICES\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE BUYS\nBETTER GEAR.", "BETTER GEAR.", "red"),
    (7.00, 9.45, "DAY 30.\nMISSES AGAIN.", "MISSES AGAIN.", "red"),
    (9.55, 11.85, "DAY 30.\n2 NEW PADDLES.", "2 NEW PADDLES.", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE PLAYS AGAIN.", "PLAYS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE PADDLE.", "ONE MORE PADDLE.", "red"),
    (17.40, 21.05, "BETTER GEAR WON'T\nFIX IT. REPS WILL.", "REPS WILL.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO BUYS GEAR FIRST.", "BUYS GEAR FIRST.", "gold"),
]
VO = [(0.2, "Same goal. Two plans."), (2.45, "One practices ten minutes a day."), (4.65, "One buys better gear."), (7.15, "Day thirty. Misses again."),
      (9.6, "Day thirty. Two new paddles."), (12.05, "Next day, he plays again."), (15.0, "The other one? One more paddle."),
      (17.5, "Better gear won't fix it. Reps will."), (21.35, "Send this to someone who buys gear first.")]
P, B = (-.12, 1.0), (.45, .79)


def gen_events():
    ev, t, rng = [], .35, np.random.default_rng(40)
    while t < REVEAL - .4:
        if pause(t) > .3:
            t += .05; continue
        d = day_at(t)
        rally = 99 if d > 95 else int(rng.integers(2, 5)) + int(d / 40)
        ev.append([round(t, 3), 4, -.2, .85])  # topu atır (serve)
        t += .35; hits = 0
        while t < REVEAL - .4 and pause(t) < .3:
            d = day_at(t); c = .8 - .42 * cl(d / 200)
            ev.append([round(t, 3), 0, *P]); hits += 1
            wy = 1.12 + float(rng.normal(0, .06 * (1 - cl(d / 150))))
            ev.append([round(t + c * .4, 3), 1, 1.0, round(wy, 3)])
            ev.append([round(t + c * .7, 3), 2, *B])
            if hits >= rally:
                ev.append([round(t + c * .7 + .35, 3), 3, -.85, .03]); t += c * .7 + .85; break
            t += c
        if ev[-1][1] != 3:
            ev.append([round(t, 3), 3, -.85, .03]); t += .3
    ev.append([round(REVEAL, 3), 3, -.85, .03])
    return [[e[0], e[1], round(e[2], 3), round(e[3], 3)] for e in ev]


EV = gen_events()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE PLAYER", "THE BUYER"], ev=EV)


def tok(f, v, dk=55):
    n = int(.12 * S.SR); x = np.arange(n) / S.SR
    s = np.sin(2 * np.pi * f * x) * np.exp(-x * dk) + S.bp(noise(n, int(f)), 2000, 9000) * np.exp(-x * 160) * .5
    return (s * v * .35).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(0, (S.bp(noise(N, 7), 200, 1500) * .004).astype(np.float32))
    for t0, k, x, y in EV:
        if t0 >= REVEAL - .05: continue
        if k == 0: fx.add(t0, tok(880, 1.0, 45), pan=-.2)
        elif k == 1: fx.add(t0, tok(1250, .8), pan=.35)
        elif k == 2: fx.add(t0, tok(1650, .75), pan=.15)
        elif k == 3:
            for j in range(4): fx.add(t0 + j * .16 * (1 + j * .35), tok(1500, .5 / (1 + j), 70), pan=-.3)
    fx.add(SINK + .15, S.boom(.25))
    t = 4.6
    while t < REVEAL:  # sifariş bildirişi
        n = int(.3 * S.SR); x = np.arange(n) / S.SR
        fx.add(t, (np.sin(2 * np.pi * 1318 * x) * np.exp(-x * 14) * .05).astype(np.float32), pan=-.35); t += 2.2
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=500 + 40 * k3, v=.2 + .015 * k3, att=.3))
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(.9, 6000, 5), .14)[:N]
    vo = M33.voice_track(N)
    out = S.mix(vo, m, f, duck_db=9.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm40_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'zərbə:', sum(1 for e in EV if e[1] == 0), 'miss:', sum(1 for e in EV if e[1] == 3))


if __name__ == '__main__':
    run(sys.argv[1])
