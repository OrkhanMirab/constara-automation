"""M41 «Piano» — THE PLAYER vs THE WAITER (2026-11-26, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format).

Yuxarı: hər gün 10 dəq piano; əvvəl yanlış not → dayanır → frazanı yenidən başlayır (səsdə eşidilir), getdikcə melodiya axıcı, sol əl akkordları qoşulur.
Day 30: yanlış not, əllər dizdə (−5); ertəsi gün yenə çalır. Aşağı: «boş vaxt gözləyən» divanda telefonla, piano paltar asılqanına çevrilir (paltar yığını böyüyür).
Mesaj: «Free time never comes. You make it.» Səsdə eşidilən irəliləyiş (M33/M37/M40 xətti, 11-26: 4/5 partlayış).
Yenilik: öz sintez piano (harmonik + çəkic səsi), frazanın yenidən başlaması = səsdə «büdrəmə».
İşlətmə: python3 m41_piano.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m33_gitara as M33  # noqa: E402
from m37_basketbol import noise  # noqa: E402
from m39_baraban import day_at, pause, cl, DAYS, SINK, REVEAL, END, FPS, DUR  # noqa: E402

TEXTS = [
    (0.05, 2.25, "SAME DREAM.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE PLAYS PIANO\n10 MINUTES A DAY.", "10 MINUTES", "green"),
    (4.60, 6.85, "ONE WAITS FOR\nFREE TIME.", "FREE TIME.", "red"),
    (7.00, 9.45, "DAY 30.\nWRONG NOTE AGAIN.", "WRONG NOTE AGAIN.", "red"),
    (9.55, 11.85, "DAY 30.\nSTILL NO TIME.", "STILL NO TIME.", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE PLAYS AGAIN.", "PLAYS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\n\"MAYBE TOMORROW.\"", "\"MAYBE TOMORROW.\"", "red"),
    (17.40, 21.05, "FREE TIME NEVER\nCOMES. YOU MAKE IT.", "YOU MAKE IT.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWAITING FOR FREE TIME.", "WAITING FOR FREE TIME.", "gold"),
]
VO = [(0.2, "Same dream. Two plans."), (2.45, "One plays piano, ten minutes a day."), (4.65, "One waits for free time."), (7.15, "Day thirty. Wrong note again."),
      (9.6, "Day thirty. Still no time."), (12.05, "Next day, he plays again."), (15.0, "The other one? Maybe tomorrow."),
      (17.5, "Free time never comes. You make it."), (21.35, "Send this to someone waiting for free time.")]
# öz melodiyamız (C major), 16 not; sol əl akkordu hər 4 notda
MEL = [64, 67, 69, 67, 64, 62, 60, 62, 64, 67, 72, 71, 69, 67, 69, 72]
CH = [[48, 55, 60], [45, 52, 57], [41, 48, 53], [43, 50, 55]]


def gen_notes():
    """[t, kind(0 sağ əl / 1 sol əl akkord), midi, ok, akkord idx]"""
    ev, t, i, rng = [], .35, 0, np.random.default_rng(41)
    while t < REVEAL - .3:
        if pause(t) > .3:
            t += .05; i = 0; continue
        d = day_at(t); step = .46 - .24 * cl(d / 200)
        wrong = rng.random() < .5 * (1 - cl(d / 120)) and i % 4 > 0
        n = MEL[i % 16]
        if wrong:
            ev.append([round(t, 3), 0, n + int(rng.choice([-1, 1])), 0, 0])
            t += step + .5; i = (i // 4) * 4  # dayanır, frazanı yenidən başlayır
            continue
        ev.append([round(t, 3), 0, n, 1, 0])
        if d > 60 and i % 4 == 0:
            ev.append([round(t, 3), 1, 0, 1, (i // 4) % 4])
        t += step * (1 + float(rng.normal(0, .12 * (1 - cl(d / 150))))); i += 1
    return ev


EV = gen_notes()
TL = dict(fps=FPS, dur=DUR, days=DAYS, sink=SINK, reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE PLAYER", "THE WAITER"], hits=EV)


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


def piano(m, v, d=1.6):
    f = mtof(m); n = int(d * S.SR); x = np.arange(n) / S.SR; s = np.zeros(n)
    for h, a in enumerate([1, .55, .3, .18, .1, .06], 1):
        fh = f * h * (1 + .0004 * h * h)
        s += a * np.sin(2 * np.pi * fh * x) * np.exp(-x * (2.2 + 1.3 * h) * (f / 400) ** .3)
    s += .25 * np.sin(2 * np.pi * f * 1.003 * x) * np.exp(-x * 2.4)  # detune xoru
    s *= np.minimum(1, x / .004)
    s += S.bp(noise(n, int(m)), 1500, 6000) * np.exp(-x * 120) * .25  # çəkic
    return (s * v * .16).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(0, (S.bp(noise(N, 5), 200, 1500) * .003).astype(np.float32))
    for t0, k, m, ok, ci in EV:
        d = day_at(t0)
        if k == 0:
            fx.add(t0, piano(m, (.7 + .3 * cl(d / 150)) * (1.15 if not ok else 1)), pan=.15)
            if not ok:  # büdrəmə: yanlış notun üstünə doğru not yarım səslə
                fx.add(t0 + .18, piano(m + 1 if m % 12 in (1, 3, 6, 8, 10) else m, .35), pan=.15)
        else:
            for mm in CH[ci]: fx.add(t0, piano(mm, .5, 2.0), pan=-.2)
    fx.add(SINK + .15, S.boom(.25))
    fx.add(SINK + .3, piano(49, .9, 2.2) + piano(50, .9, 2.2) + piano(56, .8, 2.2), pan=0)  # Day 30: klaster (əllər klaviaturaya düşür)
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=420 + 30 * k3, v=.11 + .01 * k3, att=.4))
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    # final: melodiya strings üstündə tam səslə (qazanılmış ifa)
    for j, m in enumerate(MEL[:12]):
        fx.add(REVEAL + .1 + j * .31, piano(m + 12 if j > 7 else m, .55, 1.4), pan=.1)
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.4, 6000, 5), .22)[:N]
    vo = M33.voice_track(N)
    out = S.mix(vo, m, f, duck_db=8.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm41_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr, 'not:', sum(1 for e in EV if e[1] == 0), 'yanlış:', sum(1 for e in EV if not e[3]))


if __name__ == '__main__':
    run(sys.argv[1])
