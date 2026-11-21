"""M36 «Mətbəx» — THE COOK vs THE ORDERER (2026-11-22, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format; həyat bacarığı + pul).

Yuxarı: işıqlı mətbəx, hər gün 1 yemək bişirir (qarışdırır, buxar), rəfdə qənaət bankası dolur, boşqablar yığılır. Day 30 yemək yanır, tüstü (−5),
ertəsi gün yenə bişirir. Aşağı: divanda telefonla sifariş, qapı zəngi, paketlər qapı ağzında qalanır, SPENT sayğacı.
Twist: «Every chef burned dinner once.» YENİLİK (11-22): buxar/tüstü hissəcikləri, əşya qalağı sayğac kimi, tüstü siqnalı + qapı zəngi foley.
İşlətmə: python3 m36_metbex.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
import m33_gitara as M33  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME KITCHEN.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE COOKS\nONE MEAL A DAY.", "ONE MEAL", "green"),
    (4.60, 6.85, "ONE ORDERS\nDELIVERY.", "DELIVERY.", "red"),
    (7.00, 9.45, "DAY 30.\nBURNT DINNER.", "BURNT DINNER.", "red"),
    (9.55, 11.85, "DAY 30.\n$360 ON DELIVERY.", "$360", "red"),
    (12.00, 14.85, "NEXT DAY.\nHE COOKS AGAIN.", "COOKS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE ORDER.", "ONE MORE ORDER.", "red"),
    (17.40, 21.05, "EVERY CHEF\nBURNED DINNER ONCE.", "BURNED DINNER", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWHO ORDERS EVERY NIGHT.", "EVERY NIGHT.", "gold"),
]
VO = [(0.2, "Same kitchen. Two plans."), (2.45, "One cooks one meal a day."), (4.65, "One orders delivery."), (7.15, "Day thirty. Burnt dinner."),
      (9.6, "Day thirty. Three hundred sixty dollars on delivery."), (12.05, "Next day, he cooks again."), (15.0, "The other one? One more order."),
      (17.5, "Every chef burned dinner once. Keep cooking."), (21.35, "Send this to someone who orders every night.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE COOK", "THE ORDERER"])


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def tone(f, d, v, dec=6):
    n = int(d * S.SR); x = np.arange(n) / S.SR
    return (np.sin(2 * np.pi * f * x) * np.exp(-x * dec) * v).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR); tt = np.arange(N) / S.SR
    # cızıltı (tava): REVEAL-ə qədər, Day 30-da güclü
    siz = S.bp(noise(N, 3), 3000, 9000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7.3 * tt)))
    env = np.where(tt < REVEAL, .018, 0) * (1 + 1.5 * np.exp(-((tt - SINK - .8) / .7) ** 2))
    fx.add(0, (siz * env).astype(np.float32), pan=.2)
    # bıçaq doğrama başlanğıcda
    for k in range(8):
        fx.add(.3 + k * .26, (S.bp(noise(int(.05 * S.SR), 40 + k), 1500, 6000) * np.exp(-np.arange(int(.05 * S.SR)) / 300) * .25).astype(np.float32))
    # Day 30: tüstü siqnalı
    for k in range(4):
        fx.add(SINK + .25 + k * .32, tone(3100, .18, .05, 2))
    fx.add(SINK + .15, S.boom(.25))
    # aşağı: qapı zəngi
    t = 4.6
    while t < REVEAL:
        fx.add(t, tone(659, .5, .06, 4), pan=-.35); fx.add(t + .32, tone(523, .7, .06, 3), pan=-.35); t += 2.2
    for k3, ch in enumerate(['Am', 'F', 'C', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=500 + 40 * k3, v=.22 + .015 * k3, att=.3))
        if k3 % 2 == 0 and not (SINK - .2 < t0 < SINK + 2): mus.add(t0, S.kick(.14))
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
    html = open(os.path.join(HERE, 'm36_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
