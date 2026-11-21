"""M35 «Eskiz» — THE DRAWER vs THE SAVER (2026-11-22, gecə planı; işıqlı bölünmüş ekran, təsdiqlənmiş format; M33 «Gitara» qalibinin bacarıq xətti).

Yuxarı: günəşli otaq, masada hər gün 1 səhifə rəsm; divar qalereyası dolur və HƏR RƏSM ƏVVƏLKİNDƏN YAXŞIDIR (titrək dairə → rəngli portret).
Day 30 rəsm alınmır, kağız əzilib zibilə atılır (−5), ertəsi gün yenə çəkir. Aşağı: divanda art videolarını saxlayır (+1 SAVED), eskiz dəftəri tozlanır, divardakı çərçivə boş.
YENİLİK (11-22): görünən bacarıq qalereyası + karandaş xışıltısı ritmi (əvvəl dağınıq, sonra musiqi ilə eyni ritmdə).
İşlətmə: python3 m35_eskiz.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402
from m33_gitara import ks, voice_track as _vt  # noqa: E402
import m33_gitara as M33  # noqa: E402

FPS, DUR = 30, 26.0
SINK, REVEAL, END = 7.1, 17.4, 21.2
TEXTS = [
    (0.05, 2.25, "SAME SKETCHBOOK.\nTWO PLANS.", "TWO PLANS.", "gold"),
    (2.35, 4.50, "ONE DRAWS\nONE PAGE A DAY.", "ONE PAGE", "green"),
    (4.60, 6.85, "ONE SAVES\nART VIDEOS.", "ART VIDEOS.", "red"),
    (7.00, 9.45, "DAY 30.\nAN UGLY DRAWING.", "UGLY DRAWING.", "red"),
    (9.55, 11.85, "DAY 30.\n75 VIDEOS SAVED.", "75 VIDEOS", "red"),
    (12.00, 14.85, "NEXT DAY.\nSHE DRAWS AGAIN.", "DRAWS AGAIN.", "green"),
    (14.95, 17.25, "THE OTHER?\nONE MORE SAVE.", "ONE MORE SAVE.", "red"),
    (17.40, 21.05, "SAVING ISN'T\nPRACTICING.", "PRACTICING.", "gold"),
    (21.20, 25.80, "SEND THIS TO SOMEONE\nWITH AN EMPTY SKETCHBOOK.", "EMPTY SKETCHBOOK.", "gold"),
]
VO = [(0.2, "Same sketchbook. Two plans."), (2.45, "One draws one page a day."), (4.65, "One saves art videos."), (7.15, "Day thirty. An ugly drawing."),
      (9.6, "Day thirty. Seventy five videos saved."), (12.05, "Next day, she draws again."), (15.0, "The other one? One more save."),
      (17.5, "Saving isn't practicing. Drawing is."), (21.35, "Send this to someone with an empty sketchbook.")]
TL = dict(fps=FPS, dur=DUR, days=[[0, 1], [2.2, 1], [7.0, 30], [9.6, 31], [12.0, 100], [16.0, 180], [18.6, 365]], sink=SINK,
          reveal=REVEAL, end=END, texts=TEXTS, stride=1.4, labels=["THE DRAWER", "THE SAVER"])


def clamp01(v):
    return max(0.0, min(1.0, v))


def scratch(d, v, seed):
    n = int(d * S.SR); x = np.random.default_rng(seed).standard_normal(n).astype(np.float32)
    x = S.bp(x, 2500, 7000); tt = np.arange(n) / S.SR
    env = np.sin(np.pi * tt / d) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * tt + seed))
    return (x * env * v).astype(np.float32)


def audio(path):
    M33.VO = VO
    N = int(DUR * S.SR); mus, fx = S.Bus(DUR), S.Bus(DUR)
    fx.add(0, (S.bp(np.random.default_rng(7).standard_normal(N).astype(np.float32), 200, 1200) * .01).astype(np.float32))
    # karandaş: əvvəl dağınıq, sonra ritmik (beat .55 s)
    t, k = .4, 0
    while t < REVEAL - .2:
        if SINK - .1 < t < SINK + 2.1:
            t += .3; continue
        sl = clamp01(1 - (t - .3) / 9.0) if t < SINK else clamp01(.3 - (t - SINK - 2) / 10)
        fx.add(t, scratch(.18 + .12 * np.random.default_rng(k).uniform(), .05, k), pan=.25)
        t += .275 + np.random.default_rng(k + 50).uniform(-.12, .12) * sl; k += 1
    # Day 30: kağız əzilir + zibilə düşür
    for j in range(6):
        fx.add(SINK + .15 + j * .07, scratch(.08, .12, 200 + j))
    fx.add(SINK + 1.0, S.tick(.6)); fx.add(SINK + .15, S.boom(.22))
    # aşağı: «save» ding-ləri
    t = 4.6
    while t < REVEAL:
        n = int(.25 * S.SR); x = np.arange(n) / S.SR; fx.add(t, (np.sin(2 * np.pi * 1760 * x) * np.exp(-x * 14) * .05).astype(np.float32), pan=-.35); t += 1.1
    # musiqi: yumşaq pad + KS pluck melodiyası, getdikcə daha «düzgün»
    for k3, ch in enumerate(['C', 'Am', 'F', 'G'] * 4):
        t0 = .1 + k3 * 1.1
        if t0 > REVEAL: break
        mus.add(t0, S.pad(ch, 1.25, cut=500 + 40 * k3, v=.22 + .015 * k3, att=.3))
    mel = ['E4', 'G4', 'C5', 'G4', 'A4', 'C5', 'E5', 'C5', 'F4', 'A4', 'C5', 'A4', 'G4', 'B4', 'D5', 'B4']
    t, k = .35, 0
    while t < REVEAL - .3:
        if not (SINK - .1 < t < SINK + 2.1):
            sl = clamp01(1 - t / 12)
            f = S.hz(mel[k % 16]) * (1 + np.random.default_rng(k).uniform(-.03, .03) * sl)
            mus.add(t, ks(f, .9, .08 + .04 * (1 - sl), .6, seed=k)); k += 1
        t += .55
    mus.add(REVEAL - 1.2, S.riser(1.2, .45)); mus.add(REVEAL, S.shimmer('C', 3.0, .9)); fx.add(REVEAL, S.whoosh(.8, .7))
    t, k = REVEAL + .1, 0
    while t < DUR - 1.2:
        mus.add(t, ks(S.hz(mel[k % 16]), .9, .13, .7, seed=300 + k)); t += .31; k += 1
    for k4, ch in enumerate(['C', 'G', 'Am', 'F', 'C', 'G', 'C']):
        t0 = REVEAL + k4 * 1.24
        mus.add(t0, S.strings(ch, 1.4, v=.4 + .05 * k4, att=.3)); mus.add(t0, S.sub(ch, 1.3, v=.3))
        if k4 >= 1: mus.add(t0, S.kick(.3)); mus.add(t0 + .62, S.kick(.22))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.0), .2)[:N]; f = S.apply_reverb(fx.x, S.reverb_ir(1.0, 5000, 5), .12)[:N]
    vo = _vt(N)
    out = S.mix(vo, m, f, duck_db=10.0)[:N] if vo is not None else (m * .6 + f * .9)[:N]
    if vo is None:
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    fade = int(1.4 * S.SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm35_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
