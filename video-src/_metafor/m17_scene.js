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
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

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
window.__gy = crestY;

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

// ---------------- insan fiquru (Mixamo X Bot, mocap yerişi) ----------------
// Bədən: real anatomiya (çiyin, əzələ, barmaqlar), material — fil sümüyü rəngli heykəl (üzsüz, «uncanny» yox).
// Poza: mocap kliplər (idle/walk) + üstündən istiqamət-hədəfli düzəlişlər (aim): hər əza üçün personaj fəzasında istiqamət.
const skin = new THREE.MeshPhysicalMaterial({ color: '#cfc7ba', roughness: .5, clearcoat: .25, clearcoatRoughness: .4, sheen: .4, sheenRoughness: .6, sheenColor: new THREE.Color('#fff1dc') });
const seam = new THREE.MeshPhysicalMaterial({ color: '#c4bcae', roughness: .55, clearcoat: .2 });
let GLTF = null, STRIDE = 1.4, HIP0 = 1.0;
const CHILD = { Spine: 'Spine1', Spine1: 'Spine2', Spine2: 'Neck', Neck: 'Head', LeftArm: 'LeftForeArm', LeftForeArm: 'LeftHand', RightArm: 'RightForeArm', RightForeArm: 'RightHand',
  LeftUpLeg: 'LeftLeg', LeftLeg: 'LeftFoot', LeftFoot: 'LeftToeBase', RightUpLeg: 'RightLeg', RightLeg: 'RightFoot', RightFoot: 'RightToeBase' };
const ORDER = ['LeftUpLeg', 'LeftLeg', 'LeftFoot', 'RightUpLeg', 'RightLeg', 'RightFoot', 'LeftArm', 'LeftForeArm', 'RightArm', 'RightForeArm'];
function makeHuman() {
  const model = SkeletonUtils.clone(GLTF.scene), root = new THREE.Group(); root.add(model); scene.add(root);
  const B = {};
  model.traverse(o => {
    if (o.isBone) B[o.name.replace('mixamorig:', '').replace('mixamorig', '')] = o;
    if (o.isMesh) { o.material = /Joint/i.test(o.name + o.material.name) ? seam : skin; o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; }
  });
  const mixer = new THREE.AnimationMixer(model), A = {};
  for (const c of GLTF.animations) { const a = mixer.clipAction(c); a.play(); a.setEffectiveWeight(0); A[c.name] = a; }
  return { root, model, B, mixer, A };
}
const _q = new THREE.Quaternion(), _p = new THREE.Quaternion(), _r = new THREE.Quaternion(), _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3(), QI = new THREE.Quaternion();
function rotWorld(bone, q) {  // dünya fırlanmasını sümüyün lokal fırlanmasına çevir
  bone.parent.getWorldQuaternion(_p); _r.copy(_p).invert().multiply(q).multiply(_p); bone.quaternion.premultiply(_r); bone.updateWorldMatrix(false, true);
}
function rotAxis(C, bone, axis, ang) { C.root.getWorldQuaternion(_q); _a.copy(axis).applyQuaternion(_q); rotWorld(bone, new THREE.Quaternion().setFromAxisAngle(_a, ang)); }
function aim(C, name, dir, w) {
  const bone = C.B[name], ch = C.B[CHILD[name]]; if (!bone || !ch || w <= 0) return;
  bone.updateWorldMatrix(true, true); bone.getWorldPosition(_a); ch.getWorldPosition(_b); _b.sub(_a).normalize();
  C.root.getWorldQuaternion(_q); _c.set(dir[0], dir[1], dir[2]).normalize().applyQuaternion(_q);
  const q = new THREE.Quaternion().setFromUnitVectors(_b, _c); if (w < 1) q.slerpQuaternions(QI, q, w); rotWorld(bone, q);
}
// poza: { lean, twist, head, headY, side, L: { Bone: [x,y,z,w] } } — personaj fəzası: +z irəli, +y yuxarı, +x personajın solu
function mixPose(a, b, u) {
  const o = { L: {} };
  for (const k of ['lean', 'twist', 'head', 'headY', 'side']) o[k] = lerp(a[k] || 0, b[k] || 0, u);
  for (const k of new Set([...Object.keys(a.L || {}), ...Object.keys(b.L || {})])) {
    const p = (a.L || {})[k], q = (b.L || {})[k], pd = p || q, qd = q || p;
    const d = [lerp(pd[0], qd[0], u), lerp(pd[1], qd[1], u), lerp(pd[2], qd[2], u)];
    o.L[k] = [...d, lerp(p ? (p[3] ?? 1) : 0, q ? (q[3] ?? 1) : 0, u)];
  }
  return o;
}
const AX = new THREE.Vector3(1, 0, 0), AY = new THREE.Vector3(0, 1, 0), AZ = new THREE.Vector3(0, 0, 1);
function applyHuman(C, anim, pose) {
  for (const k in C.A) { const a = C.A[k], w = anim[k] ? anim[k][0] : 0; a.setEffectiveWeight(w); a.enabled = w > 0; if (anim[k]) a.time = anim[k][1] % a.getClip().duration; }
  C.mixer.update(0);
  C.root.updateMatrixWorld(true);
  if (pose.lean || pose.twist || pose.side) for (const n of ['Spine', 'Spine1', 'Spine2']) {
    if (pose.lean) rotAxis(C, C.B[n], AX, pose.lean / 3); if (pose.twist) rotAxis(C, C.B[n], AY, pose.twist / 3); if (pose.side) rotAxis(C, C.B[n], AZ, pose.side / 3);
  }
  if (pose.head) { rotAxis(C, C.B.Neck, AX, pose.head * .35); rotAxis(C, C.B.Head, AX, pose.head * .65); }
  if (pose.headY) rotAxis(C, C.B.Head, AY, pose.headY);
  for (const n of ORDER) if (pose.L && pose.L[n]) aim(C, n, pose.L[n], pose.L[n][3] ?? 1);
  if (pose.grip) grip(C, pose.grip);
}
function grip(C, w) {  // sağ əl: barmaqları fənərin sapına bük
  for (const f of ['Index', 'Middle', 'Ring', 'Pinky']) for (let i = 1; i <= 3; i++) { const b = C.B['RightHand' + f + i]; if (b) b.rotateZ(-1.0 * w * (i === 1 ? .8 : 1)); }
  for (let i = 2; i <= 3; i++) { const b = C.B['RightHandThumb' + i]; if (b) b.rotateZ(-.5 * w); }
  C.B.RightHand.updateWorldMatrix(false, true);
}
function groundHuman(C, extra = []) {
  C.root.updateMatrixWorld(true);
  let best = 1e9;
  for (const [n, off] of [['LeftToeBase', .025], ['RightToeBase', .025], ['LeftFoot', .075], ['RightFoot', .075], ...extra]) {
    C.B[n].getWorldPosition(_a); best = Math.min(best, _a.y - off - Hgt(_a.x, _a.z));
  }
  C.root.position.y -= best; C.root.updateMatrixWorld(true);
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
let ST = null, PL = null;
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

// pozalar (personaj fəzası: +z irəli, +x personajın solu)
const P_LANTERN = { grip: .9, L: { RightArm: [-.33, -.92, .18], RightForeArm: [-.3, -.62, .72] } };
const P_LOOKLAMP = { grip: .9, head: .15, L: { RightArm: [-.25, -.55, .8], RightForeArm: [.15, .3, .95] } };
const P_TRIP = { lean: .75, head: .1, grip: .9, L: { LeftArm: [.2, -.25, 1], LeftForeArm: [.1, -.25, 1], RightArm: [-.3, -.45, .85], RightForeArm: [-.1, -.6, .8],
  LeftUpLeg: [0, -.85, .55], LeftLeg: [0, -1, .05], RightUpLeg: [0, -.8, -.55], RightLeg: [0, -.55, -.85] } };
const P_KNEEL = { lean: .42, head: .38, grip: .9, L: { LeftArm: [.15, -.85, .45], LeftForeArm: [.05, -.95, .3], RightArm: [-.18, -.9, .3], RightForeArm: [-.05, -.75, .65],
  LeftUpLeg: [.06, -.12, 1], LeftLeg: [0, -1, -.06], LeftFoot: [0, -.25, 1], RightUpLeg: [-.02, -1, -.08], RightLeg: [0, -.1, -1], RightFoot: [0, -.55, -.85] } };
const P_RAISE = { lean: -.06, head: -.32, grip: .9, L: { RightArm: [-.2, 1, .2], RightForeArm: [-.06, 1, .15], LeftArm: [.12, -1, .05], LeftForeArm: [.05, -1, .15] } };
function poseStarter(t) {
  const x = xsAt(t), sp = (xsAt(t + .05) - xsAt(t - .05)) / .1;
  const amp = clamp(sp / 1.0), slope = Math.atan2(crestY(x + .3) - crestY(x - .3), .6);
  const walkT = x / STRIDE * ST.A.walk.getClip().duration;
  const anim = { walk: [amp, walkT], idle: [1 - amp, t * .9] };
  let pose = { lean: clamp(slope * .6, -.1, .35) * amp, ...JSON.parse(JSON.stringify(P_LANTERN)) };
  pose.lean = clamp(slope * .6, -.1, .35) * amp;
  // Day 1: mayaka baxır; fənəri qaldırıb yandırır
  const look = 1 - seg(t, 2.7, 3.2); pose.head = (pose.head || 0) - .38 * look;
  const lu = seg(t, T.ignite - .55, T.ignite - .1) * (1 - seg(t, T.ignite + .25, T.ignite + .75));
  if (lu > 0) pose = mixPose(pose, P_LOOKLAMP, eio(lu));
  // büdrəmə
  const [s0, s1] = T.stumble, su = (t - s0) / (s1 - s0);
  if (su > 0 && su < 1) {
    if (su < .2) pose = mixPose(pose, P_TRIP, eio(su / .2));
    else if (su < .38) pose = mixPose(P_TRIP, P_KNEEL, eio((su - .2) / .18));
    else if (su < .68) { pose = mixPose(P_KNEEL, P_KNEEL, 0); pose.head = .38 - .3 * seg(su, .5, .68); }
    else pose = mixPose(P_KNEEL, pose, eio((su - .68) / .32));
    anim.walk[0] = su < .2 ? 1 - su / .2 : su > .68 ? (su - .68) / .32 : 0; anim.idle[0] = 1 - anim.walk[0];
  }
  const up = seg(t, T.raise, T.raise + 1.0);
  if (up > 0) pose = mixPose(pose, P_RAISE, eio(up));
  pose.grip = .9;
  const dir = Math.atan2(1, zp(x + .5) - zp(x - .5));
  ST.root.position.set(x, crestY(x), zp(x)); ST.root.rotation.set(0, dir, 0);
  applyHuman(ST, anim, pose);
  groundHuman(ST, su > 0 && su < 1 ? [['LeftLeg', .055], ['RightLeg', .055]] : []);
  return { x, sp, su };
}
const P_SIT = { lean: .5, head: .45, L: { LeftUpLeg: [.14, -.1, 1], LeftLeg: [.03, -1, .1], LeftFoot: [0, -.3, 1], RightUpLeg: [-.14, -.1, 1], RightLeg: [-.03, -1, .1], RightFoot: [0, -.3, 1],
  LeftArm: [.28, -.55, .78], LeftForeArm: [-.3, -.2, .93], RightArm: [-.22, -.55, .8], RightForeArm: [.12, -.28, .95] } };
const LEGS = Object.fromEntries(Object.entries(P_SIT.L).filter(([k]) => /Leg|Foot/.test(k)));
const P_CRUMPLE = { lean: .25, head: .35, L: { ...LEGS, LeftArm: [.1, -.65, .75], LeftForeArm: [-.85, .15, .5], RightArm: [-.1, -.65, .75], RightForeArm: [.85, .15, .5] } };
const P_THROW = { lean: .15, twist: -.4, head: .05, headY: -.5, L: { ...LEGS, LeftArm: [.15, -.7, .6], LeftForeArm: [-.6, -.1, .8], RightArm: [-.95, .15, -.15], RightForeArm: [-.9, .35, -.1] } };
const P_LOOKUP = { lean: .02, head: -.62, headY: .1, L: { ...LEGS, RightArm: [-.2, -.7, .65], RightForeArm: [.2, -.35, .9] } };
function posePlanner(t) {
  let pose = JSON.parse(JSON.stringify(P_SIT));
  // çəkir
  const d = pose.L.RightForeArm; d[0] += .1 * Math.sin(t * 9) + .05 * Math.sin(t * 23); d[2] += .06 * Math.sin(t * 4.3); pose.headY = .06 * Math.sin(t * 1.3);
  const look0 = 1 - seg(t, 2.4, 3.6); pose.lean = lerp(pose.lean, .05, look0); pose.head = lerp(pose.head, -.35, look0);
  for (const rt of T.tosses) {
    const u = (t - (rt - .75)) / 1.15; if (u <= 0 || u >= 1) continue;
    const base = pose;
    if (u < .3) pose = mixPose(base, P_CRUMPLE, eio(u / .3));
    else if (u < .55) { pose = mixPose(base, P_CRUMPLE, 1); pose.L.LeftForeArm[1] += .1 * Math.sin(u * 60); }
    else if (u < .72) pose = mixPose(mixPose(base, P_CRUMPLE, 1), mixPose(base, P_THROW, 1), eio((u - .55) / .17));
    else pose = mixPose(mixPose(base, P_THROW, 1), base, eio((u - .72) / .28));
  }
  const lk = seg(t, T.lookup, T.lookup + .9); if (lk > 0) pose = mixPose(pose, P_LOOKUP, eio(lk));
  PL.root.position.set(DESK.x - .98, 0, DESK.z); PL.root.rotation.set(0, Math.PI / 2, 0);
  applyHuman(PL, { idle: [1, 1.3 + t * .7] }, pose);
  PL.B.Hips.getWorldPosition(_a); PL.root.position.y += .74 - _a.y; PL.root.updateMatrixWorld(true);
}
function initHumans(gltf) {
  GLTF = gltf;
  ST = makeHuman(); PL = makeHuman();
  // ölçü: 1.78 m
  ST.A.idle.setEffectiveWeight(1); ST.mixer.update(0); ST.root.updateMatrixWorld(true);
  const bb = new THREE.Box3().setFromObject(ST.model), s = 1.78 / (bb.max.y - bb.min.y);
  ST.model.scale.multiplyScalar(s); PL.model.scale.multiplyScalar(s);
  // addım uzunluğu: dayaq fazasında ayağın geri sürüşmə sürəti × dövr müddəti
  const wa = ST.A.walk, dur = wa.getClip().duration; let best = null;
  for (let i = 0; i < 60; i++) {
    const tt = i / 60 * dur; applyHuman(ST, { walk: [1, tt] }, {}); ST.B.LeftFoot.getWorldPosition(_a); const y = _a.y, z0 = _a.z;
    applyHuman(ST, { walk: [1, tt + .02] }, {}); ST.B.LeftFoot.getWorldPosition(_a);
    if (!best || y < best[0]) best = [y, Math.abs(_a.z - z0) / .02];
  }
  STRIDE = clamp(best[1] * dur, .9, 2.2);
  for (const b of BALLS) { posePlanner(b.rt); b.start = new THREE.Vector3(); PL.B.RightHand.getWorldPosition(b.start); }
}

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
    pos = V(DESK.x - 2.75 + u * .25, 2.2, DESK.z + 1.35 - u * .1); tgt = V(DESK.x - .2, .9, DESK.z + .05); fov = 42; fog = .02;
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
  if (window.__dbg) { const d = window.__dbg(t, st); pos = V(...d.pos); tgt = V(...d.tgt); fov = d.fov || 35; fog = .01; }
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
  const hand = new THREE.Vector3(); ST.B.RightHand.getWorldPosition(hand); ST.B.RightHandMiddle1.getWorldPosition(_b); hand.lerp(_b, .8);
  const sw = (st.sp > 3 ? 0 : .12 * Math.sin(t * 5.4)) + (st.su > 0 && st.su < 1 ? .6 * Math.sin(st.su * 14) * (1 - st.su) : 0);
  lant.g.position.copy(hand).add(V(0, -.07, 0)); lant.g.rotation.set(0, 0, sw);
  const on = seg(t, T.ignite, T.ignite + .25) * (1 + .5 * Math.exp(-Math.pow((t - T.ignite - .15) / .12, 2)));
  const flick = 1 + .07 * Math.sin(t * 31) * Math.sin(t * 17.3) + .04 * Math.sin(t * 53);
  lant.light.intensity = .75 * on * flick; lant.glassMat.emissiveIntensity = 1.6 * on * flick; lant.flame.visible = on > .02;
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
const glb = Uint8Array.from(atob(window.XBOT), c => c.charCodeAt(0)).buffer;
new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parse(glb, '', g => { initHumans(g); document.fonts.ready.then(() => { window.draw(0); window.READY = true; }); }, e => console.error('GLB', e));
document.fonts.load('40px MO');
