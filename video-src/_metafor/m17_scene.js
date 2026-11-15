// M17 «Yol» — M14 «Fənər» hekayəsinin 3D premium versiyası (three.js, 2026-11-15).
// Starter fənərlə dağ silsiləsinə qalxır, ayağının altındakı iz işıqlanır; Planner masada plan çəkib atır.
// Sonda kamera geri çəkilir: silsilənin profili + işıqlı iz = Constara qrafiki (iki −5 enişi ilə), Planner hələ 0-da.
// Qurulum: m17_yol.py bunu esbuild ilə IIFE-yə yığır və m17_scene.html-ə yerləşdirir. window.draw(t) — t-nin saf funksiyası.
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { Line2 } from 'three/examples/jsm/lines/Line2.js';
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js';
import { LineGeometry } from 'three/examples/jsm/lines/LineGeometry.js';

const T = window.TL;
const W = 1080, H = 1920;
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, u) => a + (b - a) * u;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = u => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
const eio = u => .5 - .5 * Math.cos(Math.PI * clamp(u));
const sstep = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
const R = k => { const x = Math.sin(k * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const GOLD = '#F7C04A', RED = '#FF5A4A', WHITE = '#F4F1EA';

// ---------------- dünya: silsilə profili = qrafik ----------------
function monotone(pts) {  // Fritsch–Carlson
  const n = pts.length, xs = pts.map(p => p[0]), ys = pts.map(p => p[1]), d = [], m = new Array(n);
  for (let i = 0; i < n - 1; i++) d.push((ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]));
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; }
    const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b;
    if (s > 9) { const k = 3 / Math.sqrt(s); m[i] = k * a * d[i]; m[i + 1] = k * b * d[i]; }
  }
  return x => {
    if (x <= xs[0]) return ys[0]; if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0; while (x > xs[i + 1]) i++;
    const h = xs[i + 1] - xs[i], u = (x - xs[i]) / h, u2 = u * u, u3 = u2 * u;
    return (2 * u3 - 3 * u2 + 1) * ys[i] + (u3 - 2 * u2 + u) * h * m[i] + (-2 * u3 + 3 * u2) * ys[i + 1] + (u3 - u2) * h * m[i + 1];
  };
}
const P = monotone(T.ridge);
const zp = x => 1.1 * Math.sin(x * .07) * sstep(2, 14, x);
const XEND = T.xend;
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const h = (a, b) => R(a * 57.13 + b * 311.7 + 7.1);
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return lerp(lerp(h(xi, yi), h(xi + 1, yi), u), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), u), v) * 2 - 1;
}
const fbm = (x, y) => vnoise(x, y) * .55 + vnoise(x * 2.03, y * 2.03) * .28 + vnoise(x * 4.1, y * 4.1) * .12 + vnoise(x * 8.3, y * 8.3) * .05;
function Hgt(x, z) {
  const p = Math.max(0, P(x)), d = z - zp(x), w = 4.6 + .42 * p;
  let h = p * (.72 * Math.exp(-(d * d) / (w * w)) + .28 * Math.exp(-(d * d) / (9 * w * w)));
  const away = sstep(.7, 4.5, Math.abs(d)) * sstep(3.5, 8, Math.hypot(x + 2.6, z - 1.3));
  h += fbm(x * .11, z * .11) * (.5 + .05 * p) * away + fbm(x * .9, z * .9) * .06 * away;
  if (p > .3) h = Math.min(h, p - .06 * Math.min(d * d, 40));   // yol həmişə silsilənin ən yüksək yeridir (yan «bıçaq» qalmasın)
  return h;
}
const crestY = x => Hgt(x, zp(x));

// ---------------- render ----------------
const canvas = document.getElementById('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const FOG = new THREE.Color('#0d121c');
scene.fog = new THREE.FogExp2(FOG, .02);
const camera = new THREE.PerspectiveCamera(40, W / H, .05, 3000);

// səma: qradiyent + ay işığı (dumansız)
const sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { moon: { value: new THREE.Vector3(-.35, .42, -.84).normalize() } },
  vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }',
  fragmentShader: `varying vec3 vD; uniform vec3 moon;
    void main(){ float y = clamp(vD.y, -1., 1.);
      vec3 hor = vec3(.075,.095,.14), zen = vec3(.006,.008,.016);
      vec3 c = mix(hor, zen, pow(clamp(y*1.6+.05,0.,1.), .7));
      float m = max(dot(vD, moon), 0.); c += vec3(.16,.19,.26) * pow(m, 60.) * .9 + vec3(.05,.065,.1) * pow(m, 6.);
      c += vec3(.9,.95,1.) * smoothstep(.99965,.9998,m);
      gl_FragColor = vec4(c, 1.); }`,
}));
scene.add(sky);
{ // ulduzlar
  const n = 2200, pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const u = R(i * 3 + 1), v = R(i * 3 + 2), th = u * Math.PI * 2, y = .06 + .94 * Math.pow(v, .8), r = Math.sqrt(1 - y * y);
    pos.set([Math.cos(th) * r * 1400, y * 1400, Math.sin(th) * r * 1400], i * 3);
    const b = .25 + .75 * Math.pow(R(i * 7 + 5), 5); col.set([b, b * .97, b * (R(i) > .8 ? .85 : 1.05)], i * 3);
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ size: 2.2, sizeAttenuation: false, vertexColors: true, fog: false, transparent: true, depthWrite: false })));
}
// uzaq dağ qatları
function farRange(z, hmax, seed, color) {
  const n = 400, pos = [], idx = [];
  for (let i = 0; i <= n; i++) {
    const x = -1400 + 2800 * i / n, y = hmax * (.45 + .4 * fbm(x * .004 + seed, seed) + .25 * Math.abs(vnoise(x * .011, seed * 2)));
    pos.push(x, -20, z, x, y, z);
    if (i < n) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx);
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, fog: true })); scene.add(m); return m;
}
farRange(-330, 95, 3.3, '#06080d'); farRange(-520, 170, 7.7, '#05070b');

// relyef: silsilə ətrafında sıx tor
const terrainMat = new THREE.MeshStandardMaterial({ color: '#3a3530', roughness: .96, metalness: 0, vertexColors: true });
{
  const NX = 620, NS = 360, X0 = -70, X1 = 210, pos = new Float32Array((NX + 1) * (NS + 1) * 3), col = new Float32Array(pos.length), idx = [];
  for (let j = 0; j <= NS; j++) for (let i = 0; i <= NX; i++) {
    const x = X0 + (X1 - X0) * i / NX, s = -1 + 2 * j / NS, z = zp(x) + 320 * s * Math.abs(s) + 6 * s, y = Hgt(x, z), k = (j * (NX + 1) + i) * 3;
    pos[k] = x; pos[k + 1] = y; pos[k + 2] = z;
    const c = .62 + .38 * (fbm(x * .3 + 9, z * .3) * .5 + .5) - .18 * sstep(0, 1, Math.abs(vnoise(x * 1.7, z * 1.7)));
    col[k] = c; col[k + 1] = c * .97; col[k + 2] = c * .93;
  }
  for (let j = 0; j < NS; j++) for (let i = 0; i < NX; i++) { const a = j * (NX + 1) + i, b = a + NX + 1; idx.push(a, b, a + 1, a + 1, b, b + 1); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setIndex(idx); g.computeVertexNormals();
  const m = new THREE.Mesh(g, terrainMat); m.receiveShadow = true; scene.add(m);
}
{ // qayalar
  const n = 520, geo = new THREE.DodecahedronGeometry(1, 1), p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(p, i); v.multiplyScalar(.8 + .35 * R(i * 1.3 + Math.floor(v.x * 9 + v.y * 5))); p.setXYZ(i, v.x, v.y * .7, v.z); }
  geo.computeVertexNormals();
  const im = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ color: '#4a443d', roughness: .9, flatShading: true }), n);
  const M = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  let k = 0;
  for (let i = 0; i < 4000 && k < n; i++) {
    const x = -20 + R(i * 5 + 1) * 160, side = R(i * 5 + 2) > .5 ? 1 : -1, d = side * (1.1 + Math.pow(R(i * 5 + 3), 1.8) * 22);
    const z = zp(x) + d; if (Math.hypot(x + 2.6, z - 1.3) < 5 || x > XEND + 6 || Math.abs(d) < 2.6) continue;
    const s = (.08 + Math.pow(R(i * 5 + 4), 3) * .9) * (Math.abs(d) < 2 ? .5 : 1);
    e.set(R(i) * 3, R(i + 9) * 6, R(i + 4) * 3); q.setFromEuler(e);
    M.compose(new THREE.Vector3(x, Hgt(x, z) + s * .15, z), q, new THREE.Vector3(s * (1 + R(i + 2)), s, s * (1 + R(i + 3))));
    im.setMatrixAt(k++, M);
  }
  im.count = k; im.castShadow = true; im.receiveShadow = true; scene.add(im);
}

// işıqlar
const moon = new THREE.DirectionalLight('#a9bde0', 1.6); moon.position.set(-60, 90, -160); scene.add(moon); scene.add(moon.target);
const hemi = new THREE.HemisphereLight('#2a3a58', '#0a0908', .7); scene.add(hemi);

// ---------------- manekən ----------------
const skin = new THREE.MeshPhysicalMaterial({ color: '#e7e1d6', roughness: .4, clearcoat: .35, clearcoatRoughness: .3, sheen: .3, sheenColor: new THREE.Color('#fff4e0') });
const jointMat = new THREE.MeshPhysicalMaterial({ color: '#d8d0c2', roughness: .3, clearcoat: .6 });
function lathe(profile, mat, sx = 1, sz = 1) {
  const g = new THREE.LatheGeometry(profile.map(([r, y]) => new THREE.Vector2(r, y)), 28); g.scale(sx, 1, sz);
  const m = new THREE.Mesh(g, mat); m.castShadow = true; m.receiveShadow = true; return m;
}
function limb(r0, r1, len, mat = skin) {  // 0-dan -len-ə, uclar yumru
  const pr = [];
  for (let a = 0; a <= 6; a++) { const t = a / 6 * Math.PI / 2; pr.push([r0 * Math.sin(t) + 1e-4, r0 * Math.cos(t)]); }
  for (let a = 0; a <= 6; a++) { const t = Math.PI / 2 + a / 6 * Math.PI / 2; pr.push([r1 * Math.sin(t) + 1e-4, -len + r1 * Math.cos(t)]); }
  return lathe(pr, mat);
}
function ball(r, mat = jointMat, s = [1, 1, 1]) { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 20, 14), mat); m.scale.set(...s); m.castShadow = true; return m; }
function G(parent, x = 0, y = 0, z = 0) { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); return g; }
function makeFigure() {
  const root = new THREE.Group(); scene.add(root);
  const J = {};
  root.add(lathe([[.0001, -.12], [.1, -.11], [.135, -.06], [.14, 0], [.125, .07], [.0001, .09]], skin, 1.22, .8));
  J.spine = G(root, 0, .07, 0);
  J.spine.add(lathe([[.0001, 0], [.115, .0], [.11, .08], [.125, .2], [.15, .33], [.162, .42], [.145, .5], [.09, .555], [.0001, .565]], skin, 1.25, .78));
  J.neck = G(J.spine, 0, .55, .005); const nk = limb(.042, .046, .1); nk.rotation.x = Math.PI; nk.position.y = 0; J.neck.add(nk);
  J.head = G(J.neck, 0, .1, .0); const hd = ball(.104, skin, [.9, 1.17, 1]); hd.position.set(0, .11, .012); J.head.add(hd);
  for (const s of [-1, 1]) {
    const k = s < 0 ? 'L' : 'R';
    const sh = G(J.spine, s * .19, .47, 0); sh.add(ball(.056));
    sh.add(limb(.052, .041, .29)); const el = G(sh, 0, -.3, 0); el.add(ball(.043)); el.add(limb(.041, .032, .25));
    const hn = G(el, 0, -.265, 0); const hm = ball(.046, skin, [.62, 1.35, .42]); hm.position.y = -.05; hn.add(hm);
    J['sh' + k] = sh; J['el' + k] = el; J['hand' + k] = hn;
    const hp = G(root, s * .093, -.065, 0); hp.add(ball(.06));
    hp.add(limb(.076, .054, .44)); const kn = G(hp, 0, -.445, 0); kn.add(ball(.052)); kn.add(limb(.053, .04, .42));
    const an = G(kn, 0, -.43, 0); const ft = ball(.05, skin, [.82, .62, 2.25]); ft.position.set(0, -.04, .06); an.add(ft);
    const m1 = G(an, 0, -.075, .0), m2 = G(an, 0, -.075, .16), m3 = G(kn, 0, .0, 0);
    J['hip' + k] = hp; J['knee' + k] = kn; J['ank' + k] = an; J['fa' + k] = m1; J['fb' + k] = m2; J['kc' + k] = m3;
  }
  return { root, J };
}
const POSE0 = { spine: 0, spineY: 0, spineZ: 0, neck: 0, head: 0, headY: 0, shL: 0, shLz: 0, elL: 0, shR: 0, shRz: 0, elR: 0, hipL: 0, kneeL: 0, ankL: 0, hipR: 0, kneeR: 0, ankR: 0, hipLz: 0, hipRz: 0 };
function mix(a, b, u) { const o = {}; for (const k in POSE0) o[k] = lerp(a[k] ?? 0, b[k] ?? 0, u); return o; }
function applyPose(F, p) {
  const J = F.J;
  J.spine.rotation.set(p.spine, p.spineY, p.spineZ); J.neck.rotation.x = p.neck; J.head.rotation.set(p.head, p.headY, 0);
  J.shL.rotation.set(p.shL, 0, -.08 - p.shLz); J.elL.rotation.x = p.elL;
  J.shR.rotation.set(p.shR, 0, .08 + p.shRz); J.elR.rotation.x = p.elR;
  J.hipL.rotation.set(p.hipL, 0, -p.hipLz); J.kneeL.rotation.x = p.kneeL; J.ankL.rotation.x = p.ankL;
  J.hipR.rotation.set(p.hipR, 0, p.hipRz); J.kneeR.rotation.x = p.kneeR; J.ankR.rotation.x = p.ankR;
}
const _v = new THREE.Vector3();
function ground(F, extra = []) {  // ən aşağı ayaq nöqtəsini relyefə oturt
  F.root.updateMatrixWorld(true);
  let best = 1e9;
  for (const o of ['faL', 'fbL', 'faR', 'fbR', ...extra]) { o.getWorldPosition ? o.getWorldPosition(_v) : F.J[o].getWorldPosition(_v); best = Math.min(best, _v.y - Hgt(_v.x, _v.z)); }
  F.root.position.y -= best; F.root.updateMatrixWorld(true);
}
function walkPose(ph, amp, lean, lantern) {
  const s = Math.sin(ph), c = Math.cos(ph);
  const p = { ...POSE0 };
  p.hipL = -.42 * s * amp; p.hipR = .42 * s * amp;
  p.kneeL = .08 + amp * (.78 * Math.pow(Math.max(0, c), 1.3) + .1 * Math.max(0, -s));
  p.kneeR = .08 + amp * (.78 * Math.pow(Math.max(0, -c), 1.3) + .1 * Math.max(0, s));
  p.ankL = -(p.hipL + p.kneeL) * .55 + .05; p.ankR = -(p.hipR + p.kneeR) * .55 + .05;
  p.shL = .34 * s * amp; p.elL = -.18 - .22 * amp * Math.max(0, -s);
  p.shR = lantern ? -.22 - .04 * s * amp : -.34 * s * amp; p.shRz = lantern ? .1 : 0; p.elR = lantern ? -.32 : -.18 - .22 * amp * Math.max(0, s);
  p.spine = .06 + lean; p.spineY = .07 * s * amp; p.head = -.04 - lean * .5; p.hipLz = .02; p.hipRz = .02;
  return p;
}

// ---------------- fənər ----------------
function makeLantern() {
  const g = new THREE.Group(); scene.add(g);
  const metal = new THREE.MeshStandardMaterial({ color: '#2a2622', roughness: .35, metalness: .85 });
  const brass = new THREE.MeshStandardMaterial({ color: '#8a6a3a', roughness: .3, metalness: .9 });
  const ring = new THREE.Mesh(new THREE.TorusGeometry(.035, .005, 8, 20), metal); ring.position.y = -.0; g.add(ring);
  const top = new THREE.Mesh(new THREE.CylinderGeometry(.025, .06, .045, 20), brass); top.position.y = -.06; g.add(top);
  const glassMat = new THREE.MeshStandardMaterial({ color: '#000', emissive: new THREE.Color('#ffae55'), emissiveIntensity: 0, roughness: .2, transparent: true, opacity: .92 });
  const glass = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, .11, 24, 1, true), glassMat); glass.position.y = -.14; g.add(glass);
  const flame = new THREE.Mesh(new THREE.SphereGeometry(.016, 12, 10), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 2.4, 1) })); flame.scale.set(1, 1.8, 1); flame.position.y = -.14; g.add(flame);
  for (let i = 0; i < 4; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(.006, .11, .006), metal); const a = i * Math.PI / 2 + .4; b.position.set(Math.cos(a) * .047, -.14, Math.sin(a) * .047); g.add(b); }
  const bot = new THREE.Mesh(new THREE.CylinderGeometry(.055, .05, .03, 20), brass); bot.position.y = -.21; g.add(bot);
  const light = new THREE.PointLight('#ffb062', 0, 0, 2); light.position.y = -.14; light.castShadow = true;
  light.shadow.mapSize.set(512, 512); light.shadow.camera.near = .06; light.shadow.camera.far = 40; light.shadow.bias = -.004; light.shadow.radius = 4;
  g.add(light);
  return { g, glassMat, flame, light };
}
function glowTex(stops) {
  const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d');
  const gr = x.createRadialGradient(64, 64, 0, 64, 64, 64); stops.forEach(([o, s]) => gr.addColorStop(o, s)); x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const halo = glowTex([[0, 'rgba(255,255,255,1)'], [.15, 'rgba(255,255,255,.5)'], [.45, 'rgba(255,255,255,.1)'], [1, 'rgba(255,255,255,0)']]);
function sprite(color, scale, att = true, op = 1) {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: halo, color, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, sizeAttenuation: att, fog: false, opacity: op }));
  s.scale.set(scale, scale, 1); scene.add(s); return s;
}

// ---------------- Planner-in masası ----------------
const DESK = new THREE.Vector3(-2.05, 0, 1.3);
const wood = new THREE.MeshStandardMaterial({ color: '#2b1f17', roughness: .55, metalness: .05 });
const steel = new THREE.MeshStandardMaterial({ color: '#1b1d20', roughness: .4, metalness: .8 });
const paperCv = document.createElement('canvas'); paperCv.width = 1024; paperCv.height = 700;
const paperTex = new THREE.CanvasTexture(paperCv); paperTex.colorSpace = THREE.SRGBColorSpace; paperTex.anisotropy = 4;
let paperVer = -1;
function drawPaper(v) {
  if (v === paperVer) return; paperVer = v;
  const x = paperCv.getContext('2d'), w = 1024, h = 700;
  x.fillStyle = '#e9e2d0'; x.fillRect(0, 0, w, h);
  x.strokeStyle = 'rgba(70,110,160,.22)'; x.lineWidth = 2;
  for (let i = 0; i <= w; i += 48) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, h); x.stroke(); }
  for (let j = 0; j <= h; j += 48) { x.beginPath(); x.moveTo(0, j); x.lineTo(w, j); x.stroke(); }
  // köhnə marşrutlar (silinib)
  for (let k = Math.max(0, v - 4); k <= v; k++) {
    const cur = k === v; x.strokeStyle = cur ? 'rgba(30,40,60,.9)' : 'rgba(30,40,60,.18)'; x.lineWidth = cur ? 6 : 4; x.setLineDash(cur ? [18, 14] : [10, 10]);
    x.beginPath(); x.moveTo(110, 590);
    for (let i = 1; i <= 6; i++) x.lineTo(110 + i * 135, 590 - i * 80 + (R(k * 13 + i) - .5) * 200);
    x.stroke(); x.setLineDash([]);
    if (!cur) { x.strokeStyle = 'rgba(200,50,40,.45)'; x.lineWidth = 6; const cx = 300 + R(k) * 400, cy = 250 + R(k + 3) * 200; x.beginPath(); x.moveTo(cx - 30, cy - 30); x.lineTo(cx + 30, cy + 30); x.moveTo(cx + 30, cy - 30); x.lineTo(cx - 30, cy + 30); x.stroke(); }
  }
  x.fillStyle = '#1f2a3a'; x.beginPath(); x.arc(110, 590, 14, 0, 7); x.fill();
  x.fillStyle = '#c0392b'; x.font = 'bold 64px MO'; x.fillText('★', 905, 125);
  x.fillStyle = 'rgba(25,35,50,.9)'; x.font = 'bold 54px MO'; x.fillText('PLAN v' + v, 52, 82);
  x.font = '28px MO'; x.fillStyle = 'rgba(25,35,50,.55)'; x.fillText('STEP 1: ...', 52, 130);
  paperTex.needsUpdate = true;
}
const desk = new THREE.Group(); desk.position.copy(DESK); scene.add(desk);
{
  const topG = new THREE.Group(); topG.position.set(0, .93, 0); topG.rotation.z = .2; desk.add(topG);  // Planner-ə doğru əyilmiş
  const tb = new THREE.Mesh(new THREE.BoxGeometry(.78, .035, 1.15), wood); tb.castShadow = tb.receiveShadow = true; topG.add(tb);
  const pp = new THREE.Mesh(new THREE.PlaneGeometry(.66, .96), new THREE.MeshStandardMaterial({ map: paperTex, roughness: .85 }));
  pp.rotation.x = -Math.PI / 2; pp.rotation.z = Math.PI / 2; pp.position.y = .019; pp.receiveShadow = true; topG.add(pp);
  for (const [lx, lz] of [[-.32, -.5], [.32, -.5], [-.32, .5], [.32, .5]]) {
    const l = new THREE.Mesh(new THREE.CylinderGeometry(.018, .018, .92, 10), steel); l.position.set(lx, .46, lz); l.castShadow = true; desk.add(l);
  }
  // stul
  const st = new THREE.Group(); st.position.set(-.95, 0, 0); desk.add(st);
  const seat = new THREE.Mesh(new THREE.CylinderGeometry(.19, .19, .045, 24), wood); seat.position.y = .64; seat.castShadow = true; st.add(seat);
  for (let i = 0; i < 3; i++) { const a = i * 2.094; const l = new THREE.Mesh(new THREE.CylinderGeometry(.014, .016, .66, 8), steel); l.position.set(Math.cos(a) * .13, .32, Math.sin(a) * .13); l.rotation.set(Math.sin(a) * .18, 0, -Math.cos(a) * .18); l.castShadow = true; st.add(l); }
  const rg = new THREE.Mesh(new THREE.TorusGeometry(.17, .01, 8, 30), steel); rg.rotation.x = Math.PI / 2; rg.position.y = .2; st.add(rg);
  // lampa
  const base = new THREE.Mesh(new THREE.CylinderGeometry(.07, .08, .03, 20), steel); base.position.set(.3, .99, -.52); desk.add(base);
  const a1 = new THREE.Mesh(new THREE.CylinderGeometry(.01, .01, .55, 8), steel); a1.position.set(.25, 1.25, -.45); a1.rotation.set(.3, 0, .2); desk.add(a1);
  const a2 = new THREE.Mesh(new THREE.CylinderGeometry(.01, .01, .45, 8), steel); a2.position.set(.12, 1.52, -.2); a2.rotation.set(1.15, 0, .3); desk.add(a2);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(.11, .16, 24, 1, true), new THREE.MeshStandardMaterial({ color: '#141619', roughness: .4, metalness: .7, side: THREE.DoubleSide }));
  shade.position.set(.02, 1.5, .02); shade.rotation.z = .25; desk.add(shade);
}
const bulbPos = new THREE.Vector3(DESK.x + .03, 1.45, DESK.z + .02);
const deskLight = new THREE.SpotLight('#d6e4ff', 0, 0, .62, .65, 2); deskLight.position.copy(bulbPos);
deskLight.target.position.set(DESK.x - .08, .9, DESK.z + .05); deskLight.castShadow = true; deskLight.shadow.mapSize.set(1024, 1024); deskLight.shadow.bias = -.0015; deskLight.shadow.radius = 3;
scene.add(deskLight); scene.add(deskLight.target);
const bulb = new THREE.Mesh(new THREE.SphereGeometry(.03, 12, 10), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 3.3, 3.8) })); bulb.position.copy(bulbPos).add(new THREE.Vector3(0, .01, 0)); scene.add(bulb);
const cone = new THREE.Mesh(new THREE.ConeGeometry(.55, 1.0, 40, 1, true), new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false,
  uniforms: { k: { value: 1 } },
  vertexShader: 'varying float vY; varying vec3 vN; varying vec3 vV; void main(){ vY = position.y; vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }',
  fragmentShader: 'uniform float k; varying float vY; varying vec3 vN; varying vec3 vV; void main(){ float h = clamp(.5 - vY, 0., 1.); float f = pow(abs(dot(vN, vV)), 1.6); gl_FragColor = vec4(vec3(.62,.72,.9) * f * pow(1.-h, 1.7) * .045 * k, 1.); }',
}));
cone.position.copy(bulbPos).add(new THREE.Vector3(-.04, -.5, 0)); cone.rotation.z = .08; scene.add(cone);
const deskGlint = sprite(new THREE.Color('#cfe0ff'), .045, false, .9);

// kağız topları
const ballGeo = (() => { const g = new THREE.IcosahedronGeometry(.07, 2), p = g.attributes.position; for (let i = 0; i < p.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(p, i); v.multiplyScalar(.78 + .4 * R(Math.floor(v.x * 41 + v.y * 73 + v.z * 19))); p.setXYZ(i, v.x, v.y, v.z); } g.computeVertexNormals(); return g; })();
const paperMat = new THREE.MeshStandardMaterial({ color: '#ebe5d8', roughness: .85, flatShading: true });
const BALLS = T.tosses.map((rt, k) => {
  const m = new THREE.Mesh(ballGeo, paperMat); m.castShadow = true; m.receiveShadow = true; m.visible = false; scene.add(m);
  const a = k * 2.399, r = .12 + .07 * Math.sqrt(k), layer = Math.floor(k / 9);
  const rest = new THREE.Vector3(DESK.x - 1.35 + Math.cos(a) * r * .9, .06 + layer * .075 + R(k) * .03, DESK.z + .95 + Math.sin(a) * r * .7);
  return { m, rt, rest, rot: new THREE.Euler(R(k) * 6, R(k + 1) * 6, R(k + 2) * 6) };
});

// ---------------- iz (qrafik xətti) ----------------
const TRAIL = [];
for (let x = 0; x <= XEND + .001; x += .2) TRAIL.push(x);
const trailGeo = new LineGeometry();
{
  const pos = [], col = [];
  for (const x of TRAIL) {
    pos.push(x, crestY(x) + .025, zp(x));
    const dip = T.dips.some(([a, b]) => x > a - .2 && x < b + .2);
    if (dip) col.push(2.4, .4, .25); else col.push(2.2, 1.35, .4);
  }
  trailGeo.setPositions(pos); trailGeo.setColors(col);
}
const trailMat = new LineMaterial({ vertexColors: true, linewidth: .04, worldUnits: true, transparent: false, fog: false, alphaToCoverage: false });
trailMat.resolution.set(W, H);
const trail = new Line2(trailGeo, trailMat); scene.add(trail);
const trailMat2 = new LineMaterial({ color: '#ffb35a', linewidth: .14, worldUnits: true, transparent: true, opacity: .16, depthWrite: false, blending: THREE.AdditiveBlending, fog: false });
trailMat2.resolution.set(W, H);
const trail2 = new Line2(trailGeo, trailMat2); scene.add(trail2);

// ---------------- personajlar ----------------
const ST = makeFigure(), PL = makeFigure();
const lant = makeLantern();
const lantHalo = sprite(new THREE.Color('#ffb466'), .8, true, .35), lantGlint = sprite(new THREE.Color('#ffcf8a'), .05, false, 1);
const PEAK = new THREE.Vector3(T.peak, crestY(T.peak) + 2.6, zp(T.peak));
const beacon = new THREE.Mesh(new THREE.SphereGeometry(.18, 16, 12), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 3.4, 1.2) })); beacon.position.copy(PEAK); scene.add(beacon);
const beaconHalo = sprite(new THREE.Color('#ffc766'), 6, true, .6), beaconGlint = sprite(new THREE.Color('#ffd27a'), .07, false, 1);
beaconHalo.position.copy(PEAK); beaconGlint.position.copy(PEAK);
const beaconLight = new THREE.PointLight('#ffc070', 60, 0, 2); beaconLight.position.copy(PEAK); scene.add(beaconLight);
// toz zərrəcikləri
const DN = 500, dustG = new THREE.BufferGeometry(), dustP = new Float32Array(DN * 3); dustG.setAttribute('position', new THREE.BufferAttribute(dustP, 3));
const dust = new THREE.Points(dustG, new THREE.PointsMaterial({ size: .012, color: '#ffd9a8', transparent: true, opacity: .7, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
scene.add(dust);

// xs(t): Starter-in silsilə boyunca x-i (kəsimlər arasında vaxt sıçrayır)
const XS = T.xs;
const xsAt = t => { if (t <= XS[0][0]) return XS[0][1]; for (let i = 0; i < XS.length - 1; i++) if (t <= XS[i + 1][0]) { const u = (t - XS[i][0]) / (XS[i + 1][0] - XS[i][0]); return lerp(XS[i][1], XS[i + 1][1], u); } return XS[XS.length - 1][1]; };
const shotAt = t => T.shots.find(s => t >= s[1] && t < s[2]) || T.shots[T.shots.length - 1];
const dayAt = t => { const D = T.days; if (t <= D[0][0]) return D[0][1]; for (let i = 0; i < D.length - 1; i++) if (t <= D[i + 1][0]) return Math.round(lerp(D[i][1], D[i + 1][1], (t - D[i][0]) / (D[i + 1][0] - D[i][0]))); return D[D.length - 1][1]; };
const SCORE_K = T.score / (crestY(XEND) - crestY(0));
const scoreAt = x => Math.round((crestY(x) - crestY(0)) * SCORE_K);

function poseStarter(t) {
  const x = xsAt(t), sp = (xsAt(t + .05) - xsAt(t - .05)) / .1;
  const amp = clamp(sp / 1.1) * (sp < 3 ? 1 : 0);   // sürətli zaman-sıçrayışında (kəsim xaricində) adi yeriş
  const x2 = x + .3, slope = Math.atan2(crestY(x2) - crestY(x - .3), .6);
  const lit = t > T.ignite;
  let p = walkPose(x / 1.45 * Math.PI * 2, amp, clamp(slope * .5, -.1, .3), lit);
  // Day 1: yuxarı (mayaka) baxır, fənəri qaldırır
  const look = 1 - seg(t, 2.6, 3.1);
  p.head -= .42 * look; p.neck -= .1 * look;
  if (t < T.ignite + .4) { const u = seg(t, T.ignite - .5, T.ignite) * (1 - seg(t, T.ignite + .2, T.ignite + .6)); p.shR = lerp(p.shR, -1.05, u); p.elR = lerp(p.elR, -.7, u); }
  // büdrəmə
  const [s0, s1] = T.stumble; const su = (t - s0) / (s1 - s0);
  if (su > 0 && su < 1) {
    const trip = { ...POSE0, spine: .75, head: .2, shL: -1.25, elL: -.25, shR: -.6, shRz: .3, elR: -.2, hipL: -.75, kneeL: .5, ankL: .2, hipR: .55, kneeR: 1.0, ankR: .3 };
    const kneel = { ...POSE0, spine: .48, head: .42, neck: .15, shL: -.55, shLz: .05, elL: -.1, shR: -.35, shRz: .2, elR: -.4, hipL: -1.45, kneeL: 1.65, ankL: -.15, hipR: .1, kneeR: 1.62, ankR: .6 };
    const w = walkPose(x / 1.45 * Math.PI * 2, 1, .1, true);
    if (su < .2) p = mix(w, trip, eio(su / .2));
    else if (su < .38) p = mix(trip, kneel, eio((su - .2) / .18));
    else if (su < .68) { p = kneel; p.head = .42 - .25 * seg(su, .5, .68); }
    else p = mix(kneel, w, eio((su - .68) / .32));
  }
  // zirvə: fənəri yuxarı qaldırır
  const up = seg(t, T.raise, T.raise + .9);
  if (up > 0) { const r = { ...POSE0, shR: -2.75, shRz: .15, elR: -.15, shL: .05, head: -.25, spine: -.04 }; p = mix(p, r, eio(up)); }
  const y0 = crestY(x), z0 = zp(x), dir = Math.atan2(1, zp(x + .5) - zp(x - .5));
  ST.root.position.set(x, y0 + 1.0, z0); ST.root.rotation.set(0, dir, 0);
  applyPose(ST, p);
  ground(ST, su > 0 && su < 1 ? ['kcL', 'kcR'] : []);
  return { x, sp, su };
}
function posePlanner(t) {
  let p = { ...POSE0, spine: .38, neck: .08, head: .36, hipL: -1.5, kneeL: 1.55, ankL: -.05, hipR: -1.45, kneeR: 1.5, ankR: -.05, hipLz: .07, hipRz: .07,
    shL: -.95, shLz: -.12, elL: -.75, shR: -.9, shRz: -.05, elR: -.85 };
  // çəkir
  p.shR += .07 * Math.sin(t * 9) + .04 * Math.sin(t * 23); p.shRz += .08 * Math.sin(t * 4.3); p.headY = .05 * Math.sin(t * 1.3);
  // Day 1: mayaka baxır
  const look0 = 1 - seg(t, 2.4, 3.6); p.spine = lerp(p.spine, .02, look0); p.head = lerp(p.head, -.4, look0); p.shR = lerp(p.shR, -.55, look0); p.shL = lerp(p.shL, -.55, look0);
  // kağızı əzib atır
  for (const rt of T.tosses) {
    const u = (t - (rt - .75)) / 1.15; if (u <= 0 || u >= 1) continue;
    const crum = { ...p, shL: -.75, shLz: -.42, elL: -1.55, shR: -.75, shRz: -.4, elR: -1.55, spine: .2, head: .25 };
    const thr = { ...p, shL: -.6, shLz: -.2, elL: -1.0, shR: -.35, shRz: .95, elR: -.25, spine: .12, spineY: -.25, head: .1, headY: -.5 };
    if (u < .3) p = mix(p, crum, eio(u / .3)); else if (u < .55) { p = { ...crum }; p.elL += .08 * Math.sin(u * 60); p.elR -= .08 * Math.sin(u * 60); }
    else if (u < .72) p = mix(crum, thr, eio((u - .55) / .17)); else p = mix(thr, p, eio((u - .72) / .28));
  }
  // G: başını qaldırıb dağdakı işığa baxır
  const lk = seg(t, T.lookup, T.lookup + .8);
  if (lk > 0) { p.spine = lerp(p.spine, .05, eio(lk)); p.head = lerp(p.head, -.62, eio(lk)); p.neck = lerp(p.neck, -.1, eio(lk)); p.headY = lerp(p.headY, -.12, eio(lk)); p.shR = lerp(p.shR, -.7, eio(lk)); p.elR = lerp(p.elR, -1.0, eio(lk)); }
  PL.root.position.set(DESK.x - .95, .76, DESK.z); PL.root.rotation.set(0, Math.PI / 2, 0);
  applyPose(PL, p);
  PL.root.updateMatrixWorld(true);
}

for (const b of BALLS) { posePlanner(b.rt); b.start = new THREE.Vector3(); PL.J.handR.getWorldPosition(b.start); }

// ---------------- kamera ----------------
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function shake(t, a) { return V(Math.sin(t * 1.7) * .6 + Math.sin(t * 3.9) * .3, Math.sin(t * 2.3 + 1) * .5 + Math.sin(t * 5.1) * .2, 0).multiplyScalar(a); }
function cam(t, st) {
  const sh = shotAt(t)[0], x = st.x, y = crestY(x), z = zp(x);
  let pos, tgt, fov = 40, fog = .02;
  if (sh === 'A') {        // geniş: ikisi də dağın ətəyində, yuxarıda mayak
    const u = ease(seg(t, 0, 2.3));
    pos = V(lerp(-11.0, -10.0, u), lerp(.6, .66, u), lerp(-2.8, -2.5, u)); tgt = V(20, lerp(7.0, 6.7, u), 6.0); fov = 52; fog = .0035;
  } else if (sh === 'B') { // fənər yanır, ilk addımlar
    const u = seg(t, 2.3, 4.6);
    pos = V(x + lerp(2.0, 2.6, u), y + .9, z + 4.0); tgt = V(x - .1, y + .95, z); fov = 40; fog = .012;
  } else if (sh === 'C') { // Planner, yaxın
    const u = ease(seg(t, 4.6, 7.0));
    pos = V(DESK.x - lerp(.45, .55, u), lerp(1.5, 1.42, u), DESK.z + lerp(2.6, 2.25, u)); tgt = V(DESK.x - .55, 1.08, DESK.z); fov = 40; fog = .02;
  } else if (sh === 'D') { // büdrəmə: önü 3/4
    const u = seg(t, 7.0, 9.4);
    pos = V(10.9 + 2.5 + u * .7, crestY(11) + 1.05, zp(11) + 3.0); tgt = V(lerp(10.3, 11.6, ease(seg(t, 7.0, 8.4))), crestY(11) + .55, zp(11)); fov = 40; fog = .012;
  } else if (sh === 'E') { // Planner, çiynin üstündən
    const u = ease(seg(t, 9.4, 11.8));
    pos = V(DESK.x - 2.25 + u * .25, 1.95, DESK.z + .95 - u * .1); tgt = V(DESK.x - .1, .85, DESK.z + .05); fov = 44; fog = .02;
  } else if (sh === 'F') { // dron: arxadan qalxır, iz aşağıda qıvrılır
    const u = ease(seg(t, 11.8, 14.8));
    pos = V(x - lerp(4.0, 7.5, u), y + lerp(1.4, 5.5, u), z + lerp(3.6, 7.5, u)); tgt = V(x + .8, y + lerp(.9, .2, u), z); fov = 42; fog = .009;
  } else if (sh === 'G') { // Planner-in arxasından dağa baxış
    const u = ease(seg(t, 14.8, 17.2));
    pos = V(DESK.x - 2.55 + u * .15, 1.98 - u * .06, DESK.z + .05); tgt = V(20, lerp(.9, 1.4, u), 2.0); fov = lerp(52, 50, u); fog = .005;
  } else {                 // H/I: geri çəkilmə → bütöv qrafik
    const u = ease(seg(t, 17.2, 20.2)), v = seg(t, 20.2, T.dur);
    const p0 = V(DESK.x - 2.4, 1.92, DESK.z + .05), t0 = V(20, 1.4, 2.0);
    const p1 = V(60, 22 + v * 1.5, 262 - v * 6), t1 = V(60, 21, 0);
    const lift = Math.sin(Math.PI * u) * 10;
    pos = p0.clone().lerp(p1, u); pos.y += lift; tgt = t0.clone().lerp(t1, ease(seg(t, 17.2, 19.4))); fov = lerp(50, 58, u); fog = lerp(.005, .0011, u);
  }
  const close = sh === 'A' || sh === 'H' ? .02 : .035;
  pos.add(shake(t, close)); camera.position.copy(pos); camera.fov = fov; camera.updateProjectionMatrix(); camera.lookAt(tgt);
  scene.fog.density = fog;
  return sh;
}

// ---------------- post: bloom + film ----------------
const composer = new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(W / 2, H / 2), .7, .55, 1.0); composer.addPass(bloom);
composer.addPass(new OutputPass());
const film = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, time: { value: 0 }, fade: { value: 1 } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float time; uniform float fade; varying vec2 vUv;
    float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + time*43.1) * 43758.5453); }
    void main(){ vec2 d = vUv - .5; float r = dot(d,d);
      vec2 o = d * r * .012;
      vec3 c = vec3(texture2D(tDiffuse, vUv + o).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - o).b);
      c *= mix(1., .38, smoothstep(.08, .62, r * 1.9));
      c = c * vec3(1.02, 1., .97) + vec3(.004, .005, .009);
      c += (h(vUv * 1000.) - .5) * .035;
      gl_FragColor = vec4(c * fade, 1.); }`,
});
composer.addPass(film);

// ---------------- 2D üst qat: mətn, HUD, etiketlər ----------------
const ov = document.getElementById('ov'), X = ov.getContext('2d');
function project(v) { const p = v.clone().project(camera); return [(p.x * .5 + .5) * W, (-p.y * .5 + .5) * H, p.z]; }
function caption(t) {
  for (const [a, b, txt, hi, hc] of T.texts) {
    if (t < a || t > b) continue;
    const al = Math.min(seg(t, a, a + .25), 1 - seg(t, b - .2, b));
    X.save(); X.globalAlpha = al; X.font = (txt.length > 40 ? '44px' : '48px') + ' MO'; X.letterSpacing = '4px'; X.textBaseline = 'middle';
    const lines = txt.split('\n'), y0 = 420 - (lines.length - 1) * 34 + (1 - eio(seg(t, a, a + .35))) * 14;
    lines.forEach((ln, li) => {
      let x = W / 2 - X.measureText(ln).width / 2; const y = y0 + li * 68, i = ln.indexOf(hi);
      const parts = i < 0 ? [[ln, WHITE]] : [[ln.slice(0, i), WHITE], [hi, hc === 'red' ? RED : GOLD], [ln.slice(i + hi.length), WHITE]];
      for (const [pp, c] of parts) { if (!pp) continue; X.fillStyle = c; X.shadowColor = c === WHITE ? 'rgba(0,0,0,.85)' : c; X.shadowBlur = c === WHITE ? 14 : 20; X.fillText(pp, x, y); x += X.measureText(pp).width; }
    });
    X.restore();
  }
}
function tag(txt, x, y, col, a, size = 40) {
  if (a <= 0) return; X.save(); X.globalAlpha = a; X.font = size + 'px MO'; X.textAlign = 'center'; X.textBaseline = 'middle'; X.fillStyle = col; X.shadowColor = col; X.shadowBlur = 18; X.fillText(txt, x, y); X.restore();
}
function hud(t, sh, st) {
  if (t > T.end + .3) return;
  const a = (1 - seg(t, T.end, T.end + .3)) * seg(t, .2, .6) * .92, pl = sh === 'C' || sh === 'E' || sh === 'G';
  X.save(); X.globalAlpha = a; X.font = '28px MO'; X.letterSpacing = '6px'; X.textBaseline = 'middle';
  X.shadowColor = 'rgba(0,0,0,.8)'; X.shadowBlur = 10;
  X.fillStyle = 'rgba(214,222,232,.9)'; X.textAlign = 'left'; X.fillText(`DAY ${String(dayAt(t)).padStart(3, '0')}`, 80, 250);
  X.textAlign = 'right';
  if (sh === 'H') { const s = scoreAt(st.x); X.fillStyle = GOLD; X.fillText(`+${s}  vs  0`, 1000, 250); }
  else if (pl) { X.fillStyle = 'rgba(160,190,230,.95)'; X.fillText(`PLANNER  0`, 1000, 250); }
  else { const s = Math.max(0, scoreAt(st.x)); X.fillStyle = st.su > .05 && st.su < 1 ? RED : GOLD; X.fillText(`STARTER  +${s}`, 1000, 250); }
  X.restore();
  const n = BALLS.filter(b => t > b.rt).length;
  if (sh === 'C' || sh === 'E') { const [px, py, pz] = project(V(DESK.x, 1.25, DESK.z - .1)); if (pz < 1) tag(`PLAN v${n + 1}`, clamp(px, 170, W - 170), Math.max(600, py - 40), 'rgba(190,210,240,.95)', .9 * seg(t, shotAt(t)[1] + .2, shotAt(t)[1] + .5), 34); }
}
function labels(t, sh, st) {
  if (sh === 'D') {  // −5
    const u = t - (T.stumble[0] + .25); if (u > 0 && u < 1.4) { const [px, py, pz] = project(V(st.x, crestY(st.x) + 1.9, zp(st.x))); if (pz < 1) tag('−5', px, Math.max(620, py) - u * 60, RED, Math.min(1, u * 6) * (1 - seg(u, 1, 1.4)), 64); }
  }
  if (sh === 'H') {
    const a = seg(t, 18.6, 19.4) * (1 - seg(t, T.dur - .8, T.dur));
    const [sx, sy] = project(V(st.x, crestY(st.x) + 2, zp(st.x))); tag(`+${scoreAt(st.x)}`, sx - 10, sy - 70, GOLD, a, 54);
    const [qx, qy] = project(V(DESK.x, 1.5, DESK.z)); tag('0', qx, qy - 52, 'rgba(170,195,235,1)', a, 46);
    // qrafik oxları (zəif)
    X.save(); X.globalAlpha = a * .5; X.strokeStyle = 'rgba(210,214,220,.35)'; X.lineWidth = 2; X.setLineDash([6, 12]);
    for (const yy of [0, 15, 30, 45]) { const [ax, ay] = project(V(-8, yy, 0)), [bx, by] = project(V(128, yy, 0)); X.beginPath(); X.moveTo(ax, ay); X.lineTo(bx, by); X.stroke(); }
    X.setLineDash([]); X.restore();
    const [d1x, d1y] = project(V(0, -2.5, 0)), [d2x, d2y] = project(V(XEND, -2.5, 0));
    tag('DAY 1', d1x, d1y + 30, 'rgba(210,214,220,.8)', a * .8, 26); tag('DAY 365', d2x, d2y + 30, 'rgba(210,214,220,.8)', a * .8, 26);
  }
}

// ---------------- kadr ----------------
window.draw = function (t) {
  const st = poseStarter(t); posePlanner(t);
  const sh = cam(t, st);
  // fənər: əldə asılır, yırğalanır
  const hand = new THREE.Vector3(); ST.J.handR.getWorldPosition(hand);
  const sw = (st.sp > 3 ? 0 : .12 * Math.sin(t * 5.4)) + (st.su > 0 && st.su < 1 ? .6 * Math.sin(st.su * 14) * (1 - st.su) : 0);
  lant.g.position.copy(hand).add(V(0, -.07, 0)); lant.g.rotation.set(0, 0, sw);
  const on = seg(t, T.ignite, T.ignite + .25) * (1 + .5 * Math.exp(-Math.pow((t - T.ignite - .15) / .12, 2)));
  const flick = 1 + .07 * Math.sin(t * 31) * Math.sin(t * 17.3) + .04 * Math.sin(t * 53);
  lant.light.intensity = 1.1 * on * flick; lant.glassMat.emissiveIntensity = 1.6 * on * flick; lant.flame.visible = on > .02;
  const lw = new THREE.Vector3(); lant.light.getWorldPosition(lw);
  lantHalo.position.copy(lw); lantHalo.material.opacity = .3 * on * flick; lantGlint.position.copy(lw); lantGlint.material.opacity = on * (sh === 'H' || sh === 'G' || sh === 'A' ? 1 : .0);
  lantGlint.scale.setScalar(sh === 'H' ? .028 : .04);
  // masa lampası
  const dl = seg(t, .0, .01);
  deskLight.intensity = 1.0 * dl * (1 - .25 * Math.max(0, Math.sin(t * 47) * Math.sin(t * 13)) * seg(t, 14.8, 15.5));
  deskGlint.position.copy(bulbPos); deskGlint.material.opacity = sh === 'H' || sh === 'A' ? .95 : 0; deskGlint.scale.setScalar(sh === 'H' ? .022 : .04);
  // mayak
  beaconHalo.material.opacity = .55 + .1 * Math.sin(t * 2.1); beaconGlint.material.opacity = sh === 'H' || sh === 'A' || sh === 'G' ? 1 : .4;
  beaconGlint.scale.setScalar(sh === 'H' ? .035 : .05);
  // iz
  const n = Math.max(0, Math.floor(st.x / .2));
  trailGeo.instanceCount = t > T.ignite ? n : 0;
  const wide = sh === 'H' ? seg(t, 17.6, 20) : 0;
  trailMat.linewidth = lerp(sh === 'F' ? .045 : sh === 'G' ? .035 : .022, .5, wide);
  trailMat2.linewidth = lerp(sh === 'G' ? .12 : sh === 'F' ? .1 : .05, 1.8, wide); trailMat2.opacity = lerp(sh === 'D' || sh === 'B' ? .08 : .12, .28, wide);
  // kağız topları + plan versiyası
  let nb = 0;
  for (const b of BALLS) {
    const u = (t - b.rt) / .55; if (u < 0) { b.m.visible = false; continue; } nb++; b.m.visible = true;
    if (u < 1) {
      const p = b.start.clone().lerp(b.rest, u); p.y += Math.sin(Math.PI * u) * .55; b.m.position.copy(p); b.m.rotation.set(b.rot.x + u * 9, b.rot.y + u * 5, b.rot.z);
    } else { b.m.position.copy(b.rest); b.m.rotation.copy(b.rot); }
  }
  drawPaper(nb + 1);
  // toz
  const centre = sh === 'C' || sh === 'E' ? bulbPos : lw;
  for (let i = 0; i < DN; i++) {
    const a = R(i * 3), b = R(i * 3 + 1), c = R(i * 3 + 2);
    dustP[i * 3] = centre.x + (a - .5) * 3 + Math.sin(t * .3 + i) * .15;
    dustP[i * 3 + 1] = centre.y + (b - .5) * 2.2 + ((t * .05 + c) % 1 - .5) * .4;
    dustP[i * 3 + 2] = centre.z + (c - .5) * 3 + Math.cos(t * .23 + i) * .15;
  }
  dustG.attributes.position.needsUpdate = true; dust.material.color.set(sh === 'C' || sh === 'E' ? '#cfe0ff' : '#ffd9a8');
  dust.visible = sh !== 'H' && sh !== 'A' && sh !== 'G' && (t > T.ignite || sh === 'C' || sh === 'E'); dust.material.opacity = .55;
  // film
  film.uniforms.time.value = Math.floor(t * 24) / 24;
  const cutDip = T.shots.reduce((m, s) => Math.min(m, Math.abs(t - s[1])), 9);
  film.uniforms.fade.value = seg(t, 0, .35) * (.82 + .18 * seg(cutDip, 0, .06)) * (1 - .6 * seg(t, T.dur - .9, T.dur));
  composer.render();
  // üst qat
  X.setTransform(1, 0, 0, 1, 0, 0); X.clearRect(0, 0, W, H);
  let tg = X.createLinearGradient(0, 0, 0, 760); tg.addColorStop(0, 'rgba(0,0,0,.55)'); tg.addColorStop(1, 'rgba(0,0,0,0)'); X.fillStyle = tg; X.fillRect(0, 0, W, 760);
  labels(t, sh, st); hud(t, sh, st); caption(t);
  if (t >= T.end) { const a = seg(t, T.end + .6, T.end + 1.1); X.save(); X.globalAlpha = a; X.fillStyle = 'rgba(225,220,205,.92)'; X.font = '34px MO'; X.letterSpacing = '6px'; X.textAlign = 'center'; X.shadowColor = 'rgba(0,0,0,.9)'; X.shadowBlur = 10; X.fillText('@constara.app', W / 2 + 3, 1790); X.restore(); }
};
document.fonts.ready.then(() => { window.draw(0); window.READY = true; });
['MO', 'IB'].forEach(f => document.fonts.load('40px ' + f));
