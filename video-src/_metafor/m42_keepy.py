"""M42 «Top sektirmə» (keepy-uppy) — THE KICKER vs THE SAVER (2026-11-27, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).
Yuxarı: parkda hər gün 10 dəq top sektirmə; əvvəl 2–4 toxunuşda düşür, getdikcə ritmik «tup-tup» fasiləsiz (ayaq + diz). Aşağı: freestyle videolarını «save» edir.
Yenilik: topun uçuşu hadisə vaxtlarından fizikaya uyğun parabolla (h ~ dt²), ayaq/diz IK ilə topu qarşılayır; açıq hava səhnəsi (park, ağaclar, quşlar).
Əsas: M40 mühərriki (m40_tennis.py).
İşlətmə: python3 m42_keepy.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
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
    (0.05, 2.25, "SAME BALL.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE PRACTICES\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE SAVES\nFREESTYLE VIDEOS.", "FREESTYLE VIDEOS.", "red"),
    (7.00, 9.45, "DAY 30.\nDROPS IT AGAIN.", "DROPS IT AGAIN.", "red"),
    (9.55, 11.85, "DAY 30.\n75 VIDEOS SAVED.", "75 VIDEOS SAVED.", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE KICKS AGAIN.", "KICKS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE SAVE.", "ONE MORE SAVE.", "red"),
    (17.40, 21.05, "SAVING IT\nISN'T DOING IT.", "DOING IT.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO SAVES EVERYTHING.", "SAVES EVERYTHING.", "gold"),
]
VO = [(0.2, "Same ball. Two plans."), (2.45, "One practices ten minutes a day."), (4.65, "One saves freestyle videos."), (7.15, "Day thirty. Drops it again."),
      (9.6, "Day thirty. Seventy five videos saved."), (12.05, "Next day, he kicks again."), (15.0, "The other one? One more save."),
      (17.5, "Saving it isn't doing it."), (21.35, "Send this to someone who saves everything.")]
FOOT, KNEE, HAND, GROUND = (.36, .29), (.28, .62), (.3, .95), (.8, .06)


def gen_events():
    """[t, kind(0 ayaq / 1 diz / 3 düşdü / 4 əldən atır), x, y]"""
    ev, t, rng = [], .3, np.random.default_rng(42)
    while t < REVEAL - .4:
        if pause(t) > .3:
            t += .05; continue
        d = day_at(t)
        run = 99 if d > 90 else int(rng.integers(2, 5)) + int(d / 25)
        ev.append([t, 4, *HAND]); t += .45; n = 0
        while t < REVEAL - .4 and pause(t) < .3:
            d = day_at(t); knee = d > 100 and n % 4 == 3
            ev.append([t, 1 if knee else 0, *(KNEE if knee else FOOT)]); n += 1
            c = .52 - .2 * cl(d / 200) + float(rng.normal(0, .07 * (1 - cl(d / 120))))
            if n >= run:
                ev.append([t + c * .9, 3, *GROUND]); t += c * .9 + .55; break
            t += c
        if ev[-1][1] != 3:
            ev.append([t, 3, *GROUND]); t += .3
    ev.append([REVEAL, 3, *GROUND])
    return [[round(e[0], 3), e[1], round(e[2], 3), round(e[3], 3)] for e in ev]


EV = gen_events()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE KICKER", "THE SAVER"], ev=EV)


def kickS(v, knee=False):
    n = int(.16 * S.SR); x = np.arange(n) / S.SR
    f0 = 150 if knee else 210
    s = np.sin(2 * np.pi * (f0 - 60 * x / .16) * x) * np.exp(-x * 30) + S.bp(noise(n, f0), 600, 3500) * np.exp(-x * 90) * .7
    return (s * v * .5).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(0, (S.bp(noise(N, 9), 300, 2500) * .005).astype(np.float32))  # açıq hava
    rng = np.random.default_rng(3)
    for k in range(9):  # quşlar
        t0 = float(rng.uniform(.5, REVEAL)); n = int(.25 * S.SR); x = np.arange(n) / S.SR
        f = 3200 + 900 * np.sin(2 * np.pi * 9 * x); fx.add(t0, (np.sin(2 * np.pi * np.cumsum(f) / S.SR) * np.sin(np.pi * x / .25) * .02).astype(np.float32), pan=.5)
    for t0, k, x, y in EV:
        if t0 >= REVEAL - .05: continue
        d = day_at(t0)
        if k in (0, 1): fx.add(t0, kickS(.75 + .25 * cl(d / 150), k == 1), pan=.1)
        elif k == 3:
            for j in range(4): fx.add(t0 + j * .22 * (1 - j * .18), thump(.7 / (1 + j * 1.3)), pan=.3)
    fx.add(SINK + .15, S.boom(.25))
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=500 + 40 * k3, v=.18 + .015 * k3, att=.3))
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(.7, 6000, 5), .08)[:N]
    vo = M33.voice_track(N)
    out = S.mix(vo, m, f, duck_db=8.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm42_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'toxunuş:', sum(1 for e in EV if e[1] in (0, 1)), 'düşdü:', sum(1 for e in EV if e[1] == 3))


if __name__ == '__main__':
    run(sys.argv[1])
