"""M17 «Yol» 2D — M14 «Fənər» hekayəsinin premium 2D versiyası (2026-11-15).

İstifadəçi 3D versiyanı rədd etdi («3d istəmirəm, 2d et amma yaxşı keyfiyyətdə»). Hekayə, diktor, musiqi, vaxtlar m17_yol.py ilə eyni
(TL + audio oradan gəlir); səhnə 2D kanvas: yan görünüşdə silsilə = qrafik, insan siluetləri (profil üz, bədən forması, çəkmə,
Starter-də çanta/papaq, Planner-də eynək), IK yeriş (ayaq sürüşmür), fənər/lampa/ay rim işığı, qat-qat dağlar, uzaq planda bütöv silsilə.
İşlətmə: python3 m17_yol2d.py <scratch> [--no-audio] [--tts <kokoro qovluğu>] ; cp render.mjs <scratch>/ ; node render.mjs <scratch>
         önizləmə: python3 onizleme.py <scratch> <out.html>
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m17_yol as M  # noqa: E402

TL = dict(M.TL, stride=1.4)


def run(scr):
    os.makedirs(scr, exist_ok=True)
    html = open(os.path.join(HERE, 'm17_scene2d.html')).read().replace('/*TL*/', 'window.TL=' + json.dumps(TL) + ';')
    open(os.path.join(scr, 'index.html'), 'w').write(html)
    if '--no-audio' not in sys.argv:
        M.audio(os.path.join(scr, 'audio.wav'))
    print('hazır:', scr)


if __name__ == '__main__':
    run(sys.argv[1])
