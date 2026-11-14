"""M16 «Çay» — axına təslim olan vs axına qarşı avar çəkən (Metafor, illüstrasiya üslubu, 2026-11-15).

İstifadəçi tq_malek «Easy choices, hard life» reelsini göstərdi: «bu keyfiyyətdə qur». Mesaj eyni (asan seçim → çətin həyat,
uğur şans deyil), səhnə ÖZÜMÜZÜNKÜ: kreslo/qaya/qanad/bayraq yox — iskələ, DRIFT/ROW lövhəsi, şişmə dairə vs avarlı qayıq,
gecə fırtınası, dağ gölündə gün doğumu, aşağıda duman/şəlalə, «Must be luck.» → «It was never luck. It was every stroke.»
İşlətmə: python3 m16_cay.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_kino'))
import sound as S  # noqa: E402

FPS, DUR = 30, 16.0
SPLIT, NIGHT, BOLT, DAWN, WHIP, WIDE, XFADE = 2.0, 4.6, 6.25, 9.4, 11.0, 13.3, 15.3
TEXTS = [
    (0.10, 2.10, "Every morning,\nyou pick a boat.", "pick a boat.", "gold"),
    (2.20, 4.40, "One drifts.\nFeels good now.", "Feels good now.", "pink"),
    (4.50, 6.20, "One rows.\nHurts now.", "Hurts now.", "red"),
    (6.30, 9.20, "The current fights back.\nHe keeps rowing.", "He keeps rowing.", "gold"),
    (9.50, 10.90, "Day 365.", "365.", "gold"),
    (11.20, 13.20, "From down here,\nit looks like luck.", "luck.", "pink"),
    (13.40, 15.90, "It was never luck.\nIt was every stroke.", "every stroke.", "gold"),
]
VO = [
    (0.20, "Every morning, you pick a boat."), (2.30, "One drifts. It feels good now."),
    (4.60, "One rows. It hurts now."), (6.45, "The current fights back. He keeps rowing."),
    (9.55, "Day three sixty five."), (11.30, "From down here, it looks like luck."),
    (13.45, "It was never luck. It was every stroke."),
]
TL = dict(fps=FPS, dur=DUR, split=SPLIT, night=NIGHT, bolt=BOLT, dawn=DAWN, whip=WHIP, wide=WIDE, xfade=XFADE, texts=TEXTS)


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def voice_track(N):
    if '--tts' not in sys.argv:
        return None
    from kokoro_onnx import Kokoro
    from scipy.signal import resample_poly
    d = sys.argv[sys.argv.index('--tts') + 1]
    k = Kokoro(os.path.join(d, 'kokoro-v1.0.onnx'), os.path.join(d, 'voices-v1.0.bin'))
    v = np.zeros(N, np.float32)
    for t0, txt in VO:
        a, sr = k.create(txt, voice='am_michael', speed=1.0, lang='en-us')
        i = np.where(np.abs(a) > .01)[0]; a = a[max(0, i[0] - 200):i[-1] + 800]
        a = resample_poly(a, S.SR, sr).astype(np.float32)
        j = int(t0 * S.SR); v[j:j + len(a)] += a[:N - j]
    return S.voice_chain(v)


def splash(seed, v=1.0):
    n = int(.35 * S.SR)
    return (S.bp(noise(n, seed), 400, 3500) * np.exp(-np.arange(n) / (n / 4)) * .12 * v).astype(np.float32)


def thunder(v=1.0):
    d = 2.6; t = S.tarr(d); n = noise(len(t), 77)
    crack = S.hp(n, 1500) * np.exp(-t * 18) * .8
    roll = S.lp(n, 260) * (np.exp(-t * 1.2) * (.6 + .4 * np.sin(2 * np.pi * 3.3 * t) ** 2)) * 3.0
    return ((crack + roll) * .25 * v).astype(np.float32)


def audio(path):
    N = int(DUR * S.SR)
    mus, fx = S.Bus(DUR + 1), S.Bus(DUR + 1)
    tt = np.arange(N) / S.SR
    # su axını (həmişə), yağış (gecə), külək (aşağıda duman)
    water = S.bp(noise(N, 3), 250, 2200) * np.interp(tt, [0, 2, 4.6, 9.4, 11, 13.3, 16], [.05, .06, .08, .08, .03, .05, .05])
    rain = S.bp(noise(N, 5), 1800, 9000) * np.interp(tt, [0, 4.3, 4.9, 9.0, 9.6, 16], [0, 0, .09, .09, 0, 0])
    fx.add(0, water.astype(np.float32)); fx.add(0, rain.astype(np.float32), pan=.1)
    for i, ts in enumerate(np.arange(2.25, 9.4, .55)):   # avar zərbələri
        fx.add(ts, splash(i, .9 if ts < 4.6 else 1.2), pan=.3)
    fx.add(BOLT, thunder(1.2)); fx.add(BOLT - .02, S.boom(.5))
    fx.add(WHIP - .1, S.whoosh(.5, 1.0)); fx.add(WIDE, S.whoosh(.7, .6))
    # musiqi: axşam (F–C–Am–G, yumşaq) → gecə (Am pulsu + taiko, gərgin) → şəfəq (C major strings) → aşağı (tək piano) → final
    for k, ch in enumerate(['F', 'C', 'Am', 'G']):
        t0 = k * 1.15
        mus.add(t0, S.pad(ch, 1.25, cut=900, v=.5, att=.3)); mus.add(t0, S.piano(S.hz(S.CHORDS[ch][1][3]) * 2, 1.6, .3))
    for k in range(8):                         # gecə
        t0 = NIGHT + k * .6
        mus.add(t0, S.taiko(.6 + .05 * k)); mus.add(t0, S.sub('Am', .55, v=.5))
        if k % 2 == 0:
            mus.add(t0, S.strings('Am' if k < 4 else 'F', 1.25, v=.45 + .05 * k, att=.2))
    mus.add(DAWN - 1.2, S.riser(1.2, .7)); mus.add(DAWN, S.shimmer('C', 3.0, 1.2))
    for k, ch in enumerate(['C', 'G', 'Am']):
        mus.add(DAWN + k * .55, S.strings(ch, .7, v=.8, att=.08)); mus.add(DAWN + k * .55, S.sub(ch, .6, v=.5))
    for j, nm in enumerate(['A4', 'E4', 'C4']):  # aşağıda: tək piano
        mus.add(WHIP + .1 + j * .7, S.piano(S.hz(nm), 2.2, .32))
    mus.add(WHIP, S.pad('Am', 2.3, cut=420, v=.45, att=.4))
    for k, ch in enumerate(['F', 'G', 'C']):   # final
        mus.add(WIDE + k * .85, S.strings(ch, 1.0, v=.75, att=.2)); mus.add(WIDE + k * .85, S.pad(ch, 1.0, cut=1300, v=.55))
        mus.add(WIDE + k * .85, S.sub(ch, .9, v=.45))
    for i, nm in enumerate(['C5', 'E5', 'G5', 'C6']):
        mus.add(WIDE + 2.6 + i * .3, S.piano(S.hz(nm), 1.4, .3))
    m = S.apply_reverb(mus.x, S.reverb_ir(2.6), .25)[:N]
    f = S.apply_reverb(fx.x, S.reverb_ir(1.2, 5000, 5), .12)[:N]
    vo = voice_track(N)
    if vo is not None:
        out = S.mix(vo, m, f, duck_db=8.0)[:N]
    else:
        out = (m * .65 + f * .9)[:N]
        out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / (np.max(np.abs(out)) + 1e-9) * .9
    k = int(.5 * S.SR); out[-k:] *= np.linspace(1, 0, k)[:, None]; k2 = int(.03 * S.SR); out[:k2] *= np.linspace(0, 1, k2)[:, None]
    import soundfile as sf
    sf.write(path, out, S.SR)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm16_scene.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
