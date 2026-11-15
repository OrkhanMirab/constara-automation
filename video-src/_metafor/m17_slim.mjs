// İşlətmə: cd _build && NODE_PATH=node_modules node ../m17_slim.mjs   (npm i --prefix _build @gltf-transform/cli@4)
// Xbot.glb → Xbot-slim.glb: yalnız idle + walk animasiyası, resample, prune, quantize, meshopt
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune, resample, quantize, meshopt, dedup } from '@gltf-transform/functions';
import { MeshoptEncoder } from 'meshoptimizer';
await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read('models/Xbot.glb');
for (const a of doc.getRoot().listAnimations()) if (!['idle', 'walk'].includes(a.getName())) a.dispose();
await doc.transform(dedup(), resample(), prune(), quantize(), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
await io.write('models/Xbot-slim.glb', doc);
