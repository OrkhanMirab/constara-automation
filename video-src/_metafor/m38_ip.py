"""M38 «İp» — THE JUMPER vs THE MEMBER (2026-11-24, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: parkda hər səhər 5 dəq ip tullanır; əvvəl tez-tez ilişir (TRIP), getdikcə ritm sabit və sürətli (IN A ROW 3 → 500).
Day 30: yorğun, ip yerdə (−5); ertəsi gün yenə tullanır. Aşağı: divanda telefon, divarda GYM MEMBER kartı tozlanır, hər ay −$50.
Yenilik (11-24): ip fizikası + səsdə ritm (ipin yerə dəyməsi əvvəl qırıq, sonra metronom kimi sabit).
İşlətmə: python3 m38_ip.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m33_gitara as M33  # noqa: E402
from m37_basketbol import R, noise, thump  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME GOAL.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE JUMPS ROPE\n5 MINUTES A DAY.", "5 MINUTES", "green"),
    (4.60, 6.85, "ONE PAYS\nFOR A GYM.", "FOR A GYM.", "red"),
    (7.00, 9.45, "DAY 30.\nTRIPS AGAIN.", "TRIPS AGAIN.", "red"),
    (9.55, 11.85, "DAY 30.\n0 GYM VISITS.", "0 GYM VISITS.", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE JUMPS AGAIN.", "JUMPS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nPAYS AGAIN.", "PAYS AGAIN.", "red"),
    (17.40, 21.05, "YOU DON'T NEED A GYM.\nYOU NEED 5 MINUTES.", "5 MINUTES.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO PAYS FOR A GYM.", "PAYS FOR A GYM.", "gold"),
]
VO = [(0.2, "Same goal. Two plans."), (2.45, "One jumps rope, five minutes a day."), (4.65, "One pays for a gym."), (7.15, "Day thirty. He trips again."),
      (9.6, "Day thirty. Zero gym visits."), (12.05, "Next day, he jumps again."), (15.0, "The other one? Pays again."),
      (17.5, "You don't need a gym. You need five minutes."), (21.35, "Send this to someone who pays for a gym.")]
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


def rate(t):
    return 0 if pause(t) > .3 else 1.15 + 1.45 * min(1, max(0, day_at(t) / 220))


PHS = [0.0]
for i in range(1, int(math.ceil(DUR * 100)) + 3):
    PHS.append(PHS[-1] + rate((i - .5) / 100) / 100)
# hər tullanmanın (k) başlanğıc anı və günü
KT = []
for i in range(1, len(PHS)):
    while len(KT) <= PHS[i] and len(KT) <= PHS[-1]:
        k = len(KT); a, b = PHS[i - 1], PHS[i]
        KT.append((i - 1 + (k - a) / (b - a + 1e-12)) / 100 if b > a else i / 100)
KDAY = [round(day_at(t), 2) for t in KT]


def trip(k):
    return k > 2 and R(k * 3.7 + 2) < .34 * (1 - min(1, max(0, KDAY[min(k, len(KDAY) - 1)] / 130)))


TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE JUMPER", "THE MEMBER"],
          phs=[round(p, 4) for p in PHS], kday=KDAY)


def slap(v):  # ipin yerə dəyməsi
    n = int(.09 * S.SR); x = np.arange(n) / S.SR
    return (S.bp(noise(n, 11), 1500, 7000) * np.exp(-x * 60) * v * .5).astype(np.float32)


def whirr(v, dur):  # ipin havada fırlanması
    n = int(dur * S.SR); x = np.arange(n) / S.SR
    return (S.bp(noise(n, 13), 600, 2400) * np.sin(np.pi * x / dur) ** 2 * v * .05).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(0, (S.bp(noise(N, 7), 300, 2500) * .006).astype(np.float32))  # açıq hava
    for k, t0 in enumerate(KT):
        if t0 >= REVEAL - .2 or pause(t0) > .3:
            continue
        if trip(k):
            fx.add(t0 + .02, thump(.35), pan=.1)
            fx.add(t0 + .05, (slap(.35) * .6).astype(np.float32), pan=.1)
        else:
            fx.add(t0, slap(1.0), pan=.15); fx.add(t0 + .03, thump(.22), pan=0)
            if k + 1 < len(KT):
                fx.add(t0 + .05, whirr(1.0, max(.15, KT[k + 1] - t0 - .1)), pan=-.1)
    fx.add(SINK + .15, S.boom(.25))
    t = 4.6
    while t < REVEAL:  # −$50 bildirişi
        n = int(.3 * S.SR); x = np.arange(n) / S.SR
        fx.add(t, (np.sin(2 * np.pi * 988 * x) * np.exp(-x * 12) * .05 + np.sin(2 * np.pi * 659 * np.maximum(0, x - .08)) * np.exp(-np.maximum(0, x - .08) * 12) * .04 * (x > .08)).astype(np.float32), pan=-.35)
        t += 2.2
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
    html = open(os.path.join(HERE, 'm38_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'tullanma:', len(KT), 'ilişmə:', sum(trip(k) for k in range(len(KT))))


if __name__ == '__main__':
    run(sys.argv[1])
