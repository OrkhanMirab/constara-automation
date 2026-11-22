"""M37 «Basketbol» — THE SHOOTER vs THE WATCHER (2026-11-23, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: açıq həyət meydançası, hər gün 100 atış; top parabola ilə halqaya uçur, əvvəl çox vaxt CLANK, getdikcə SWISH (ACCURACY 18% → 90%).
Day 30: 0/10, yorğun, top yuvarlanıb gedir (−5); ertəsi gün yenə atır. Aşağı: divanda/TV-də highlight klipləri, divan altında top sönür.
Fərziyyə sınağı (11-23): M33-ün partlayışı «səsdə eşidilən irəliləyiş»dəndirsə — bu video da baza üstü olmalıdır.
İşlətmə: python3 m37_basketbol.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m33_gitara as M33  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
PER = 1.25
TEXTS = [
    (0.05, 2.25, "SAME BALL.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE SHOOTS\n100 SHOTS A DAY.", "100 SHOTS", "green"),
    (4.60, 6.85, "ONE WATCHES\nHIGHLIGHTS.", "HIGHLIGHTS.", "red"),
    (7.00, 9.45, "DAY 30.\n0 FOR 10.", "0 FOR 10.", "red"),
    (9.55, 11.85, "DAY 30.\n75 CLIPS WATCHED.", "75 CLIPS", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE SHOOTS AGAIN.", "SHOOTS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE CLIP.", "ONE MORE CLIP.", "red"),
    (17.40, 21.05, "EVERY SWISH\nSTARTED AS A MISS.", "STARTED AS A MISS.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO ONLY WATCHES.", "ONLY WATCHES.", "gold"),
]
VO = [(0.2, "Same ball. Two plans."), (2.45, "One shoots a hundred shots a day."), (4.65, "One watches highlights."), (7.15, "Day thirty. Zero for ten."),
      (9.6, "Day thirty. Seventy five clips watched."), (12.05, "Next day, he shoots again."), (15.0, "The other one? One more clip."),
      (17.5, "Every swish started as a miss."), (21.35, "Send this to someone who only watches.")]
DAYS = [[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]]
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE SHOOTER", "THE WATCHER"])


def R(k):
    x = math.sin(k * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def day_at(t):
    d = DAYS[0][1]
    for i in range(len(DAYS) - 1):
        (a, d0), (b, d1) = DAYS[i], DAYS[i + 1]
        if t >= a:
            u = min(1, max(0, (t - a) / (b - a))); u = u * u * (3 - 2 * u); d = d0 + (d1 - d0) * u
    return d


def pause(t):
    return min(1, max(0, math.exp(-((t - (SINK + 1.1)) / .95) ** 2) * 1.6))


def made(k):
    return R(k * 7.3 + 1) < .18 + .72 * min(1, max(0, day_at((k + .45) * PER) / 300))


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def clank(v):
    n = int(.6 * S.SR); x = np.arange(n) / S.SR
    s = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * dk) * a for f, dk, a in [(523, 7, 1), (1347, 9, .7), (2210, 12, .5), (3170, 16, .35)])
    s[:200] += noise(200, 3) * .8
    return (s * v * .12).astype(np.float32)


def swish(v):
    n = int(.35 * S.SR); x = np.arange(n) / S.SR
    return (S.bp(noise(n, 9), 1800, 6500) * np.sin(np.pi * x / .35) ** 2 * v * .22).astype(np.float32)


def thump(v):
    n = int(.18 * S.SR); x = np.arange(n) / S.SR
    return (np.sin(2 * np.pi * (95 - 40 * x / .18) * x) * np.exp(-x * 26) * v * .5).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(0, (S.bp(noise(N, 7), 300, 2500) * .006).astype(np.float32))  # açıq hava
    k = 0
    while (k + .85) * PER < REVEAL:
        t0 = k * PER
        if pause(t0 + .45 * PER) < .3:
            for j in range(2):
                tb = t0 + (j + .5) * .3 * PER / 2
                fx.add(tb, thump(.9), pan=-.2)
            fx.add(t0 + .85 * PER, swish(1.0) if made(k) else clank(1.0), pan=.3)
            if not made(k):
                fx.add(t0 + 1.25 * PER, thump(.4), pan=0)
        k += 1
    fx.add(SINK + .15, S.boom(.25))
    for j in range(5):
        fx.add(SINK + .6 + j * .22 * (1 + j * .3), thump(.5 / (1 + j)), pan=.1 * j)
    t = 4.6
    while t < REVEAL:
        n = int(.25 * S.SR); x = np.arange(n) / S.SR; fx.add(t, (np.sin(2 * np.pi * 1760 * x) * np.exp(-x * 14) * .05).astype(np.float32), pan=-.35); t += 1.1
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=500 + 40 * k3, v=.22 + .015 * k3, att=.3))
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = M33.voice_track(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm37_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
