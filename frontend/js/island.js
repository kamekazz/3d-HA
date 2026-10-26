// The floating island (2026-10-25; bar: the two diorama renders in
// scratchpad/island/ref). The lot is cut out of the generated world and shown
// as a plate of lawn with a soil edge, floating in a dark void, instead of a
// yard that runs on to the street, the neighbours and the lake.
//
// Nothing about the yard BUILD changes -- every factory still runs, every key
// is the same, and an edit still lands where it did. The island is laid on
// top of the finished build (applyIsland, called from environment.js just
// before the swap):
//   - one outline, a rounded rectangle with a slow wobble, defined ONCE as a
//     signed distance in JS (islandSdf) and the same maths in GLSL (SDF_GLSL);
//   - whatever stands wholly off the island (lake, street, neighbours, the
//     backdrop ring, items whose pivot is outside) is hidden, so it is neither
//     drawn nor compiled;
//   - the ground that crosses the outline (lawn, turf, paving, the 1200 ft
//     grass disc, the edge fringe) is clipped in its fragment shader -- only
//     below CLIP_TOP, so a canopy may still overhang the edge;
//   - a soil edge is built along the outline at the height the ground really
//     has there, with a grass (or concrete) lip that covers the clipped rim.
// `?island=0` turns all of it off.
import * as THREE from 'three';
import { onFrame } from './scene.js';
import { getNightFactor } from './daylight.js';
import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';

export const ISLAND = (() => {
  try {
    const q = new URLSearchParams(location.search).get('island');
    return q !== '0' && q !== 'off';
  } catch { return true; }
})();

const CLIP_TOP = 4.5;   // ft: ground and low planting are clipped, canopies are not

// The outline. Rounded box (centre, half sizes, corner radius) plus a sum of
// slow sines in the polar angle, so the edge reads as dug, not drawn.
const shape = { cx: 19, cz: -14, hx: 69, hz: 94, r: 34 };
const WOB = [   // [amplitude ft, frequency in theta, phase] -- round 2: gentler (r1 read "lumpy blob")
  [1.2, 2, 0.7], [0.8, 3, 2.1], [0.35, 7, 4.0],
];
// Round 3: bays and bulges (r2 critic: "a smooth symmetric blob"), each a
// gaussian in the polar angle: [amplitude ft (+ = out), centre angle, width].
// theta = atan2(z - cz, x - cx), so +z (the street side) is +pi/2.
const BUMPS = [
  // r4: halved -- r3's framing critic read the full set as "a lumpy potato";
  // r5: smoothed, and then read as "a mechanical rounded rectangle". r6: the
  // reference's answer -- a kidney: few, BROAD lobes (0.5-0.8 rad), so the
  // silhouette is one flowing curve with character, not lumps
  [8.0, 1.25, 0.55],    // the driveway's lobe, swelling out at front-right
  [-7.0, 2.25, 0.65],   // the kidney's broad, shallow front-west bay
  [5.0, 2.95, 0.50],    // ...and the full west end it curls round to
  [-4.5, -1.10, 0.75],  // a long soft bay along the back-east
];

export function setIslandFrom(L) {
  // From the yard's own landmarks (environment.js landmarks()): the lot runs
  // from the lake shore planting behind the house to just short of the
  // sidewalk, and from inside the west fence line to inside the east one.
  // Round 2: tighter round the house (r1: "house too small in frame").
  const x0 = L.padW - 46, x1 = L.padE + 44;   // r4: wider and shallower, to sit across a 16:9 frame
  // Round 3: 8 ft less back yard (r2: "trees cover the back half"), a little wider
  const z0 = L.yardN - 10, z1 = L.street - 20;
  shape.cx = (x0 + x1) / 2; shape.cz = (z0 + z1) / 2;
  shape.hx = (x1 - x0) / 2; shape.hz = (z1 - z0) / 2;
  shape.r = 42;
  uniforms.islandBox.value.set(shape.cx, shape.cz, shape.hx, shape.hz);
  uniforms.islandR.value = shape.r;
}

export function islandSdf(x, z) {
  const px = x - shape.cx, pz = z - shape.cz;
  const qx = Math.abs(px) - (shape.hx - shape.r), qz = Math.abs(pz) - (shape.hz - shape.r);
  let d = Math.hypot(Math.max(qx, 0), Math.max(qz, 0)) + Math.min(Math.max(qx, qz), 0) - shape.r;
  const th = Math.atan2(pz, px);
  for (const [a, f, p] of WOB) d -= a * Math.sin(f * th + p);
  for (const [a, c, w] of BUMPS) { const dt = Math.atan2(Math.sin(th - c), Math.cos(th - c)); d -= a * Math.exp(-(dt * dt) / (w * w)); }
  return d;
}

// The camera frames this box. The plate's corners are rounded off, so the
// bbox's own corners are empty and fitting them leaves the island small in a
// wide margin of void (r2: "fills half the frame"); 0.9 of it lets the curves
// come to the reference's ~5% margin.
export function islandBox(yTop = 30) {
  const k = 0.96;   // r3: 0.9 cropped the plate at the frame edge
  return new THREE.Box3(
    new THREE.Vector3(shape.cx - shape.hx * k, -8, shape.cz - shape.hz * k),
    new THREE.Vector3(shape.cx + shape.hx * k, yTop, shape.cz + shape.hz * k));
}

// ---------------------------------------------------------------- clipping
const uniforms = {
  islandBox: { value: new THREE.Vector4(shape.cx, shape.cz, shape.hx, shape.hz) },
  islandR: { value: shape.r },
  islandNight: { value: 0 },
};
// one night factor for the lawn lift, the soil rim and the path-light pools
const nightTickers = [];
let ticking = false;
function onNight(fn) {
  nightTickers.push(fn);
  if (ticking) return;
  ticking = true;
  onFrame(() => {
    const n = getNightFactor?.() ?? 0;
    uniforms.islandNight.value = n;
    for (const f of nightTickers) f(n);
  });
}
const SDF_GLSL = `
uniform vec4 islandBox;
uniform float islandR;
uniform float islandNight;
varying vec3 vIslW;
float islandSdf(vec2 p) {
  p -= islandBox.xy;
  vec2 q = abs(p) - (islandBox.zw - islandR);
  float d = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - islandR;
  float th = atan(p.y, p.x);
  ${WOB.map(([a, f, p]) => `d -= ${a.toFixed(3)} * sin(${f.toFixed(1)} * th + ${p.toFixed(3)});`).join('\n  ')}
  float dt;
  ${BUMPS.map(([a, c, w]) => `dt = atan(sin(th - ${c.toFixed(3)}), cos(th - ${c.toFixed(3)})); d -= ${a.toFixed(3)} * exp(-(dt * dt) / ${(w * w).toFixed(4)});`).join('\n  ')}
  return d;
}`;

// The island's lawn: soft mowing bands and broad patchiness in world feet,
// a little less chroma and value than the Sims grade's lime (r1 critic: "flat
// neon green, no mowing stripes, no variation"). Runs after the vertex colour,
// so the lawn's own tint and edge AO still ride underneath.
const LAWN_GLSL = `
float islH(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float islN(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(islH(i), islH(i + vec2(1, 0)), f.x), mix(islH(i + vec2(0, 1)), islH(i + vec2(1, 1)), f.x), f.y);
}
vec3 islandLawn(vec3 c, vec2 w) {
  // bands 7 ft wide, run diagonally across the lot (as a mower would, corner to corner)
  // r7: the bands wander (a slow warp across them) and their contrast swells
  // and fades over ~40 ft, so they read mown, not ruled (r6: "a mechanical
  // diagonal stripe ... oversaturated lime")
  float warp = (islN(w / 31.0) - 0.5) * 1.4;
  float b = (w.x * 0.82 + w.y * 0.57) / 7.5 + warp;
  float stripe = smoothstep(0.25, 0.75, abs(fract(b) * 2.0 - 1.0));
  float strength = 0.45 + 0.55 * islN(w / 40.0 + 7.3);
  float mott = islN(w / 26.0) * 0.6 + islN(w / 9.0 + 3.1) * 0.4;
  float fine = islN(w * 1.7);
  c *= mix(1.0, mix(0.88, 1.05, stripe), strength) * (0.84 + 0.28 * mott) * (0.94 + 0.12 * fine);
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, 0.70) * vec3(0.98, 0.80, 0.70);
  return c;
}`;

const patched = new WeakSet();
export function clipMaterial(m, { lawn = false } = {}) {
  if (!m || patched.has(m) || m.isShaderMaterial || m.isRawShaderMaterial) return;
  patched.add(m);
  const prev = m.onBeforeCompile;
  const ownKey = Object.prototype.hasOwnProperty.call(m, 'customProgramCacheKey') ? m.customProgramCacheKey : null;
  m.onBeforeCompile = function (shader, renderer) {
    prev.call(this, shader, renderer);
    let vs = shader.vertexShader, fs = shader.fragmentShader;
    const anchor = vs.includes('#include <fog_vertex>') ? '#include <fog_vertex>' : '#include <project_vertex>';
    if (!vs.includes(anchor) || !fs.includes('#include <clipping_planes_fragment>')) return;
    vs = vs.replace('#include <common>', '#include <common>\nvarying vec3 vIslW;');
    vs = vs.replace(anchor, `${anchor}
  {
    vec4 iw = vec4(transformed, 1.0);
    #ifdef USE_INSTANCING
      iw = instanceMatrix * iw;
    #endif
    vIslW = (modelMatrix * iw).xyz;
  }`);
    fs = fs.replace('#include <common>', '#include <common>\n' + SDF_GLSL + (lawn ? LAWN_GLSL : ''));
    if (lawn) {
      fs = fs.replace('#include <color_fragment>', '#include <color_fragment>\n  diffuseColor.rgb = islandLawn(diffuseColor.rgb, vIslW.xz);');
      // a faint cool lift after dark so the plate still reads as lawn, not
      // as a hole (r2 night critic: "the lawn sinks into near-black murk")
      fs = fs.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance += diffuseColor.rgb * vec3(0.10, 0.15, 0.22) * islandNight;');   // r5: 2x, "a near-black lawn" 
    }
    fs = fs.replace('#include <clipping_planes_fragment>',
      `if (vIslW.y < ${CLIP_TOP.toFixed(2)} && islandSdf(vIslW.xz) > 0.0) discard;\n#include <clipping_planes_fragment>`);
    shader.vertexShader = vs;
    shader.fragmentShader = fs;
    Object.assign(shader.uniforms, uniforms);
  };
  // three keys programs by this; the default is onBeforeCompile's SOURCE, which
  // is now this wrapper for every patched material -- so key by what it wraps.
  m.customProgramCacheKey = function () {
    return (ownKey ? ownKey.call(this) : prev.toString()) + (lawn ? '|island-v5-lawn' : '|island-v3');
  };
  m.needsUpdate = true;
}

// ------------------------------------------------------------- hide / clip
const _b = new THREE.Box3();
function boxSdfCorners(b) {
  let inside = 0, outside = 0;
  for (const [x, z] of [[b.min.x, b.min.z], [b.max.x, b.min.z], [b.min.x, b.max.z], [b.max.x, b.max.z]]) {
    if (islandSdf(x, z) > 0) outside++; else inside++;
  }
  return { inside, outside };
}
function rectsMiss(b) {
  return b.max.x < shape.cx - shape.hx - 6 || b.min.x > shape.cx + shape.hx + 6 ||
         b.max.z < shape.cz - shape.hz - 6 || b.min.z > shape.cz + shape.hz + 6;
}
const NEVER_CLIP = /sky-dome|driveway-car/;
// the world beyond the lot: hidden outright, whatever their bounds say
const HIDE_NAMES = /backdrop-street|atmosphere|lake-surface/;

// Decide, per top-level object of the yard group, whether it is hidden (wholly
// off the island, or a small thing standing off it), clipped (crosses the
// outline), or left alone (wholly on the island).
export function applyIsland(yardGroup, extra = []) {
  const stats = { hidden: 0, clipped: 0, mats: 0 };
  const clip = (o) => o.traverse((m) => {
    if (!m.isMesh) return;
    for (const mat of [].concat(m.material)) if (mat && !patched.has(mat)) { clipMaterial(mat); stats.mats++; }
  });
  const consider = (o) => {
    if (NEVER_CLIP.test(o.name) || o.userData?.kind === 'driveway-car' || o.userData?.island) return;
    if (!o.visible && !o.userData?.yardKey) return;
    if (HIDE_NAMES.test(o.name)) { o.visible = false; o.userData.offIsland = true; stats.hidden++; return; }
    // a yard piece stands where its pivot is (a tree's is its trunk): off the
    // plate it goes, however far its crown reaches over (r3: the lake's nine
    // mature oaks, trunks on the shore, piled up behind the roof as one blob)
    if (o.userData?.yardKey && islandSdf(o.position.x, o.position.z) > 0) {
      o.visible = false; o.userData.offIsland = true; stats.hidden++; return;
    }
    _b.setFromObject(o);
    if (_b.isEmpty()) return;
    const { inside, outside } = boxSdfCorners(_b);
    if (!outside) return;
    const cx = (_b.min.x + _b.max.x) / 2, cz = (_b.min.z + _b.max.z) / 2;
    const half = Math.hypot(_b.max.x - _b.min.x, _b.max.z - _b.min.z) / 2;
    const centreOut = islandSdf(cx, cz) > 0;
    if (rectsMiss(_b) || (!inside && centreOut && half < 400 && _b.min.y > -50 && !isGround(o)) ||
        (centreOut && half < 18)) {
      o.visible = false;
      o.userData.offIsland = true;
      stats.hidden++;
      return;
    }
    clip(o);
    stats.clipped++;
  };
  for (const o of yardGroup.children) consider(o);
  for (const o of extra) if (o) consider(o);
  return stats;
}
// a ground surface that spans the island must be clipped, never hidden
function isGround(o) {
  return /turf|lawn|fringe|gravel|leaves/i.test(o.name) || o.userData?.yardKind === 'lawn';
}

// ------------------------------------------------------------- the soil edge
const N_SEG = 560;          // samples round the outline (~0.9 ft apart)

function hash(n) { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); }
function noise1(t, period) {   // smooth periodic value noise in [0,1]
  const x = t * period, i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  const a = hash(((i % period) + period) % period), b = hash((((i + 1) % period) + period) % period);
  return a + (b - a) * u;
}

// the outline as N_SEG points, outward normals and arc length (star-shaped
// about the centre: march out along each ray to the zero crossing)
function outline() {
  const pts = [];
  for (let i = 0; i < N_SEG; i++) {
    const th = (i / N_SEG) * Math.PI * 2;
    const dx = Math.cos(th), dz = Math.sin(th);
    let lo = 0, hi = Math.hypot(shape.hx, shape.hz) + 30;
    for (let k = 0; k < 40; k++) {
      const mid = (lo + hi) / 2;
      if (islandSdf(shape.cx + dx * mid, shape.cz + dz * mid) > 0) hi = mid; else lo = mid;
    }
    pts.push({ x: shape.cx + dx * lo, z: shape.cz + dz * lo });
  }
  let s = 0;
  for (let i = 0; i < N_SEG; i++) {
    const a = pts[(i + N_SEG - 1) % N_SEG], b = pts[(i + 1) % N_SEG], p = pts[i];
    let tx = b.x - a.x, tz = b.z - a.z; const tl = Math.hypot(tx, tz) || 1; tx /= tl; tz /= tl;
    p.nx = tz; p.nz = -tx;   // CCW in (x,z) with +z down the screen: right-hand normal points out
    if (islandSdf(p.x + p.nx * 0.5, p.z + p.nz * 0.5) < islandSdf(p.x, p.z)) { p.nx = -p.nx; p.nz = -p.nz; }
    p.s = s;
    s += Math.hypot(pts[(i + 1) % N_SEG].x - p.x, pts[(i + 1) % N_SEG].z - p.z);
  }
  return { pts, len: s };
}

// Points along the rim, `inset` ft inside it, every `spacing` ft of arc:
// where the planting that frames the plate stands (environment.js addBackdrop).
export function islandRim(inset, spacing) {
  const { pts, len } = outline();
  const out = [];
  for (let s = 0, i = 0; s < len; s += spacing) {
    while (i < N_SEG - 1 && pts[i + 1].s <= s) i++;
    const p = pts[i];
    out.push({ x: p.x - p.nx * inset, z: p.z - p.nz * inset, nx: p.nx, nz: p.nz, t: s / len });
  }
  return out;
}

// The ground height and surface class right at the rim, from the vertices of
// the ground meshes crossing it (a 2 ft grid of the highest vertex; the 1200 ft
// grass disc at y -0.05 is the floor everywhere else).
function groundProbe(grounds) {
  const CELL = 2, grid = new Map();
  const v = new THREE.Vector3();
  for (const { mesh, cls } of grounds) {
    const pos = mesh.geometry?.attributes?.position;
    if (!pos) continue;
    mesh.updateWorldMatrix(true, false);
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i).applyMatrix4(mesh.matrixWorld);
      if (v.y > 3) continue;
      if (islandSdf(v.x, v.z) < -6) continue;   // only the rim band matters
      const k = Math.floor(v.x / CELL) + ',' + Math.floor(v.z / CELL);
      const c = grid.get(k);
      if (!c || v.y > c.y) grid.set(k, { y: v.y, cls });
    }
  }
  return (x, z) => {
    let best = null;
    for (let r = 0; r <= 1 && !best; r++) {
      for (let i = -r; i <= r; i++) for (let j = -r; j <= r; j++) {
        // step inward a little: the rim itself is where the ground is clipped
        const c = grid.get(Math.floor(x / CELL + i) + ',' + Math.floor(z / CELL + j));
        if (c && (!best || c.y > best.y)) best = c;
      }
    }
    return best || { y: -0.05, cls: 'lawn' };
  };
}

let soilTex = null;
function soilTexture() {
  if (soilTex) return soilTex;
  // 1024 x 512, wrapped round the rim every 24 ft and spanning the full depth:
  // dark root-laced topsoil under the turf, a warm crumbly middle with strata
  // and stones, a darker clay base (round 2: r1 read "flat brown, no texture")
  const W = 1024, H = 512;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 0, H);
  grd.addColorStop(0, '#3b2717'); grd.addColorStop(0.10, '#4a311d');
  grd.addColorStop(0.18, '#6e4a2c'); grd.addColorStop(0.5, '#7a5433');
  grd.addColorStop(0.78, '#5e3f27'); grd.addColorStop(1, '#3a281b');
  g.fillStyle = grd; g.fillRect(0, 0, W, H);
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  // crumbly clods: many small dark and light blotches everywhere
  for (let k = 0; k < 9000; k++) {
    const x = rnd() * W, y = rnd() * H, r = 1 + rnd() * 3.5;
    const dark = rnd() < 0.55;
    g.fillStyle = dark ? `rgba(28,17,9,${0.18 + rnd() * 0.25})` : `rgba(160,118,78,${0.10 + rnd() * 0.18})`;
    g.beginPath(); g.ellipse(x, y, r * (1 + rnd()), r, rnd() * 3, 0, Math.PI * 2); g.fill();
  }
  // strata: wandering bands, lighter sandy and darker clay
  for (let k = 0; k < 16; k++) {
    const y0 = H * (0.16 + rnd() * 0.8), amp = 3 + rnd() * 8, th = 3 + rnd() * 10;
    g.strokeStyle = rnd() < 0.5 ? 'rgba(30,18,10,0.30)' : 'rgba(170,128,84,0.22)';
    g.lineWidth = th; g.beginPath();
    for (let x = 0; x <= W; x += 8) g.lineTo(x, y0 + Math.sin(x / W * Math.PI * 2 * (1 + (k % 4)) + k) * amp);
    g.stroke();
  }
  // stones, bigger and more of them toward the base, each with a lit top and a shadow
  for (let k = 0; k < 520; k++) {
    const y = H * (0.15 + Math.pow(rnd(), 0.6) * 0.85), x = rnd() * W;
    const r = 1.5 + rnd() * (2 + 9 * (y / H));
    const l = 92 + rnd() * 70;
    g.fillStyle = 'rgba(16,10,6,0.45)';
    g.beginPath(); g.ellipse(x + r * 0.25, y + r * 0.35, r * 1.15, r * 0.8, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = `rgb(${l + 10},${l},${l - 14})`;
    g.beginPath(); g.ellipse(x, y, r * (1 + rnd() * 0.6), r * 0.75, rnd() * 3, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(255,240,220,0.18)';
    g.beginPath(); g.ellipse(x - r * 0.2, y - r * 0.3, r * 0.6, r * 0.3, 0, 0, Math.PI * 2); g.fill();
  }
  // roots hanging from the turf
  for (let k = 0; k < 140; k++) {
    let x = rnd() * W, y = rnd() * 20;
    g.strokeStyle = `rgba(${45 + rnd() * 40},${30 + rnd() * 20},18,0.75)`; g.lineWidth = 0.8 + rnd() * 2;
    g.beginPath(); g.moveTo(x, y);
    const n = 3 + rnd() * 9;
    for (let s = 0; s < n; s++) { x += (rnd() - 0.5) * 10; y += 4 + rnd() * 8; g.lineTo(x, y); }
    g.stroke();
  }
  soilTex = new THREE.CanvasTexture(c);
  soilTex.colorSpace = THREE.SRGBColorSpace;
  soilTex.wrapS = THREE.RepeatWrapping;
  soilTex.anisotropy = 8;
  return soilTex;
}

let shadowTex = null;
function underShadowTexture() {
  if (shadowTex) return shadowTex;
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d');
  // alphaMap reads the GREEN channel, so this is an opaque grey ramp, not alpha
  const grd = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grd.addColorStop(0, 'rgb(255,255,255)'); grd.addColorStop(0.35, 'rgb(190,190,190)');
  grd.addColorStop(0.7, 'rgb(60,60,60)'); grd.addColorStop(1, 'rgb(0,0,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 256, 256);
  shadowTex = new THREE.CanvasTexture(c);
  return shadowTex;
}

// the same mowing bands as LAWN_GLSL, for the lip's vertex colours
function lawnLookJS(c, x, z) {
  const b = (x * 0.82 + z * 0.57) / 7;
  const t = Math.abs((b - Math.floor(b)) * 2 - 1);
  const st = THREE.MathUtils.smoothstep(t, 0.3, 0.7);
  const k = (0.90 + 0.12 * st) * 0.97;
  let [r, g, bl] = c.map((v) => v * k);
  const l = 0.2126 * r + 0.7152 * g + 0.0722 * bl;
  r = (l + (r - l) * 0.7) * 0.98; g = (l + (g - l) * 0.7) * 0.80; bl = (l + (bl - l) * 0.7) * 0.70;
  return [r, g, bl];
}

// grounds: [{ mesh, cls: 'lawn'|'paving' }]; lawnColor(x, z) -> [r,g,b] linear
export function buildIslandEdge(grounds, lawnColor) {
  const probe = groundProbe(grounds);
  const { pts, len } = outline();
  for (const p of pts) {
    // sample just inside the rim, where the ground is still drawn
    const h = probe(p.x - p.nx * 1.2, p.z - p.nz * 1.2);
    p.y = Math.max(h.y, -0.05);
    p.cls = h.cls;
  }
  // smooth the top line so a single tall vertex cannot spike the lip
  for (let pass = 0; pass < 2; pass++) {
    const ys = pts.map((p) => p.y);
    for (let i = 0; i < N_SEG; i++) pts[i].y = (ys[(i + N_SEG - 1) % N_SEG] + 2 * ys[i] + ys[(i + 1) % N_SEG]) / 4;
  }
  // a paving run must own whole stretches, not flicker sample to sample
  for (let i = 0; i < N_SEG; i++) {
    const a = pts[(i + N_SEG - 1) % N_SEG].cls, b = pts[(i + 1) % N_SEG].cls;
    if (a === b && pts[i].cls !== a) pts[i].cls = a;
  }

  const group = new THREE.Group();
  group.name = 'island-edge';
  group.userData.island = true;

  // --- the soil slab: a lumpy, crumbly face from just under the lip down to a
  // ragged, rounded underside. [outward offset ft, drop below the rim ft, v]
  // round 3: ~16 ft (r2: "still reads as a thin band at frame scale")
  const PROFILE = [[0.62, 0.6, 0], [0.85, 1.8, 0.07], [0.85, 3.8, 0.2], [0.78, 6.0, 0.36], [0.66, 8.3, 0.52],
    [0.45, 10.6, 0.68], [0.0, 12.6, 0.82], [-1.0, 14.2, 0.92], [-3.0, 15.4, 0.98], [-7.0, 16.4, 1]];
  const rows = PROFILE.length;
  const pos = [], uv = [], col = [], idx = [];
  const lump = (t, v) =>
    (noise1(t + v * 0.31, 140) - 0.5) * 0.9 + (noise1(t * 1.7 + v * 0.53, 330) - 0.5) * 0.5;
  for (let i = 0; i <= N_SEG; i++) {
    const p = pts[i % N_SEG];
    const t = (i % N_SEG) / N_SEG;
    const deep = 1 + (noise1(t, 19) - 0.5) * 0.30 + (noise1(t, 53) - 0.5) * 0.16;
    for (let r = 0; r < rows; r++) {
      const [out, drop, v] = PROFILE[r];
      const o = out + lump(t, v) * Math.sin(Math.min(1, v * 1.25) * Math.PI) * 1.7;
      const ragged = r >= rows - 4 ? (noise1(t, 260) - 0.5) * 2.6 + (noise1(t, 77) - 0.5) * 2.0 : 0;
      pos.push(p.x + p.nx * o, p.y - drop * deep + ragged, p.z + p.nz * o);
      uv.push((i === N_SEG ? len : p.s) / 30, 1 - v);
      // r6: darker and less orange (r5: "a uniform orange-brown wall"), and
      // varied along the rim in long patches so no two stretches match
      const patchK = 0.62 + 0.38 * noise1(t, 9) + 0.18 * (noise1(t * 3.1 + v * 0.7, 41) - 0.5);
      const k = (0.78 + 0.18 * noise1(t, 97)) * patchK - 0.25 * Math.max(0, v - 0.75);
      const under = r === 0 ? 0.25 : r === 1 ? 0.6 : 1;   // the lip's shadowed undercut (r8: darker, a crisp line)
      col.push(k * 0.92 * under, k * 0.84 * under, k * 0.78 * under);
    }
  }
  for (let i = 0; i < N_SEG; i++) {
    for (let r = 0; r < rows - 1; r++) {
      const a = i * rows + r, b = (i + 1) * rows + r;
      idx.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  // belly: fan to a point under the middle (never really seen, but closes it)
  const bellyC = pos.length / 3;
  let by = 0; for (const p of pts) by += p.y; by = by / N_SEG - 19;
  pos.push(shape.cx, by, shape.cz); uv.push(0.5, 0); col.push(0.4, 0.4, 0.4);
  for (let i = 0; i < N_SEG; i++) idx.push(i * rows + rows - 1, bellyC, (i + 1) * rows + rows - 1);
  const wall = new THREE.BufferGeometry();
  wall.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  wall.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  wall.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  wall.setIndex(idx);
  wall.computeVertexNormals();
  fixWinding(wall, pts);
  const soilMat = new THREE.MeshStandardMaterial({ map: soilTexture(), vertexColors: true, roughness: 1, metalness: 0 });
  // a cool rim on the slab's silhouette, strongest after dark, so the plate
  // separates from the void (r2 void and night critics: "the soil underside
  // merges into the background")
  soilMat.onBeforeCompile = (sh) => {
    sh.uniforms.islandNight = uniforms.islandNight;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float islandNight;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
  {
    float f = 1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0);
    totalEmissiveRadiance += vec3(0.035, 0.055, 0.11) * pow(f, 4.0) * (0.3 + 0.7 * islandNight);   // r3: 5x r2's glowed white
  }`);
  };
  soilMat.customProgramCacheKey = () => 'island-soil-rim-v3';
  const wallMesh = new THREE.Mesh(wall, soilMat);
  wallMesh.name = 'island-soil';
  wallMesh.userData.ownGeometry = true;
  wallMesh.receiveShadow = true;
  group.add(wallMesh);

  // --- stones set into the face: low-poly, flat-shaded, half buried
  {
    let seed = 99; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const geos = [];
    const tmp = new THREE.Color();
    for (let k = 0; k < 80; k++) {
      const i = Math.floor(rnd() * N_SEG), p = pts[i], t = i / N_SEG;
      const v = 0.18 + rnd() * 0.62;
      // where the face is at this depth: interpolate the profile
      let r = 0; while (r < rows - 2 && PROFILE[r + 1][2] < v) r++;
      const [o0, d0, v0] = PROFILE[r], [o1, d1, v1] = PROFILE[r + 1];
      const f = (v - v0) / Math.max(1e-3, v1 - v0);
      const out = o0 + (o1 - o0) * f + lump(t, v) * Math.sin(Math.min(1, v * 1.25) * Math.PI) * 1.7;
      const drop = d0 + (d1 - d0) * f;
      const rad = 0.6 + Math.pow(rnd(), 2) * 1.4 + v * 0.5;
      const geo = new THREE.IcosahedronGeometry(rad, 0);
      geo.scale(1 + rnd() * 0.5, 0.6 + rnd() * 0.3, 0.8 + rnd() * 0.4);
      geo.rotateY(rnd() * Math.PI); geo.rotateX((rnd() - 0.5) * 0.6);
      geo.translate(p.x + p.nx * (out - rad * 0.55), p.y - drop, p.z + p.nz * (out - rad * 0.55));   // mostly buried
      const n = geo.attributes.position.count, a = new Float32Array(n * 3);
      const l = 0.08 + rnd() * 0.07;   // r2: 0.16-0.32 read as white popcorn; r8: 0.055 read as noise
      tmp.setRGB(l * 1.05, l, l * 0.9);
      for (let j = 0; j < n; j++) { const s = 0.85 + rnd() * 0.3; a[j * 3] = tmp.r * s; a[j * 3 + 1] = tmp.g * s; a[j * 3 + 2] = tmp.b * s; }
      geo.setAttribute('color', new THREE.BufferAttribute(a, 3));
      geos.push(geo.index ? geo.toNonIndexed() : geo);
    }
    const merged = BufferGeometryUtils.mergeGeometries(geos, false);
    for (const g of geos) g.dispose();
    const rocks = new THREE.Mesh(merged, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, flatShading: true }));
    rocks.name = 'island-stones';
    rocks.userData.ownGeometry = true;
    group.add(rocks);
  }

  // --- the lip: turf that rolls over the rim and hangs a little ragged (or
  // concrete where the drive runs off), covering where the ground is clipped
  // r6: a plumper roll that overhangs the face by ~0.6 ft (r5: "stops abruptly")
  const LIP = [[-1.6, 0.025], [-0.6, 0.09], [0.35, 0.10], [1.05, -0.18], [1.38, -0.66], [1.25, -1.25]];
  const PAVE = [[-1.4, 0.03], [-0.4, 0.05], [0.25, 0.04], [0.42, -0.22], [0.48, -0.55], [0.45, -0.75]];
  const lpos = [], lcol = [], lidx = [];
  const lr = LIP.length;
  const MAP_AVG = 0.67;   // the lawn's grass map averages ~214/255: the lip has no map, so fold it in
  for (let i = 0; i <= N_SEG; i++) {
    const p = pts[i % N_SEG];
    const t = (i % N_SEG) / N_SEG;
    const pave = p.cls === 'paving';
    const base = pave ? [0.26, 0.26, 0.255] : lawnLookJS(lawnColor(p.x, p.z).map((v) => v * MAP_AVG), p.x, p.z);
    const prof = pave ? PAVE : LIP;
    const hang = pave ? 0 : (noise1(t, 410) - 0.5) * 0.5 + (noise1(t, 1300) - 0.5) * 0.35;
    for (let r = 0; r < lr; r++) {
      const [o, dy] = prof[r];
      lpos.push(p.x + p.nx * o, p.y + dy + (r >= 4 ? hang * (r - 3) : 0), p.z + p.nz * o);
      // turf darkens as it rolls over the edge (blades seen side-on, self-shadowed)
      // r8: a crisp roll -- lit top, then the blades seen side-on go a deep
      // green fast (r7: "the grass fades straight into brown")
      const k = r < 2 ? 1 : r === 2 ? 1.0 : pave ? 0.8 - 0.06 * (r - 3) : r === 3 ? 0.62 : r === 4 ? 0.36 : 0.22;
      lcol.push(base[0] * k, base[1] * k, base[2] * k);
    }
  }
  for (let i = 0; i < N_SEG; i++) {
    for (let r = 0; r < lr - 1; r++) {
      const a = i * lr + r, b = (i + 1) * lr + r;
      lidx.push(a, a + 1, b, b, a + 1, b + 1);
    }
  }
  const lip = new THREE.BufferGeometry();
  lip.setAttribute('position', new THREE.Float32BufferAttribute(lpos, 3));
  lip.setAttribute('color', new THREE.Float32BufferAttribute(lcol, 3));
  lip.setIndex(lidx);
  lip.computeVertexNormals();
  fixWinding(lip, pts, true);
  const lipMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, metalness: 0 });
  // r9: a cool catch-light along the rolled turf after dark, so the plate's
  // outline reads against the void (asked for in every night/void round)
  lipMat.onBeforeCompile = (sh) => {
    sh.uniforms.islandNight = uniforms.islandNight;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float islandNight;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
  {
    float f = 1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0);
    totalEmissiveRadiance += vec3(0.05, 0.09, 0.16) * pow(f, 3.0) * islandNight;
  }`);
  };
  lipMat.customProgramCacheKey = () => 'island-lip-rim-v1';
  const lipMesh = new THREE.Mesh(lip, lipMat);
  lipMesh.name = 'island-lip';
  lipMesh.userData.ownGeometry = true;
  lipMesh.receiveShadow = true;
  group.add(lipMesh);

  // --- a soft shadow in the void under the plate: it is what makes it float
  // (r1 critic: "no darkening beneath, it reads as a tile on a blue surface")
  const sh = new THREE.Mesh(new THREE.PlaneGeometry(shape.hx * 2.5, shape.hz * 2.1),
    new THREE.MeshBasicMaterial({ color: 0x000206, alphaMap: underShadowTexture(), transparent: true,
      opacity: 0.95, depthWrite: false, fog: false }));
  sh.rotation.x = -Math.PI / 2;
  sh.position.set(shape.cx, by - 34, shape.cz + 22);   // r6: far enough down, and toward the camera, to show under the slab
  sh.name = 'island-under-shadow';
  sh.userData.ownGeometry = true;
  sh.renderOrder = -1000;
  sh.raycast = () => {};
  group.add(sh);

  // ...and a faint cool glow just under the slab's near side, the reflected
  // light the reference's void carries under its rim (r6/r7 void critics,
  // both ways round: "a faint reflected glow under the island's rim")
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(shape.hx * 2.3, shape.hz * 1.2),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(0.035, 0.08, 0.17), alphaMap: underShadowTexture(),
      transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, opacity: 0.4 }));
  onNight((n) => { glow.material.opacity = 0.35 + 0.65 * n; });   // by day it read as a spotlight
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(shape.cx, by - 6, shape.cz + shape.hz * 0.75);
  glow.name = 'island-under-glow';
  glow.userData.ownGeometry = true;
  glow.renderOrder = -999;
  glow.raycast = () => {};
  group.add(glow);
  return group;
}



// ------------------------------------------------------------ clipped hedge
// A crisp, continuous clipped hedge along the back and sides of the rim
// (r8: the ring of round clumps read as "a loose band of blobs, no hedge
// structure" to the planting critic and as "a woodland that buries the house"
// to the framing one). One extruded band per run: a flat-topped, slightly
// battered profile with rounded shoulders, its faces mottled with a leaf
// texture so it is clipped foliage, not a tube.
let hedgeTex = null;
function hedgeTexture() {
  if (hedgeTex) return hedgeTex;
  const S = 256;
  const c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  g.fillStyle = '#c8c8c8'; g.fillRect(0, 0, S, S);   // sRGB: #7a decoded to ~0.19 and blacked the hedge out
  let seed = 31; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let k = 0; k < 2600; k++) {
    const x = rnd() * S, y = rnd() * S, r = 1.5 + rnd() * 3.2, l = 150 + rnd() * 105;
    g.fillStyle = `rgb(${l},${l},${l})`;
    g.beginPath(); g.ellipse(x, y, r * 1.4, r, rnd() * 3, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(0,0,0,0.35)';
    g.beginPath(); g.ellipse(x + r * 0.4, y + r * 0.5, r, r * 0.5, 0, 0, Math.PI * 2); g.fill();
  }
  hedgeTex = new THREE.CanvasTexture(c);
  hedgeTex.colorSpace = THREE.SRGBColorSpace;
  hedgeTex.wrapS = hedgeTex.wrapT = THREE.RepeatWrapping;
  return hedgeTex;
}
// runs: arrays of rim points ({x, z, nx, nz}) in order; y: the ground there
export function buildHedge(runs, y) {
  // cross-section [lateral ft (+ = out), height ft], walked over the top
  const PROF = [[-1.35, 0], [-1.2, 2.7], [-0.85, 3.35], [0.85, 3.35], [1.2, 2.7], [1.35, 0]];
  const pos = [], col = [], uv = [], idx = [];
  const tmp = new THREE.Color();
  for (const run of runs) {
    if (run.length < 3) continue;
    const base = pos.length / 3;
    let s = 0;
    for (let i = 0; i < run.length; i++) {
      const p = run[i];
      if (i) s += Math.hypot(p.x - run[i - 1].x, p.z - run[i - 1].z);
      // rounded ends: the band pinches over its last ~3 ft
      const end = Math.min(i, run.length - 1 - i);
      const k = end >= 2 ? 1 : 0.35 + 0.32 * end;
      for (const [o, h] of PROF) {
        pos.push(p.x + p.nx * o * k, y + h * (0.6 + 0.4 * k), p.z + p.nz * o * k);
        const top = h > 3 ? 1 : h > 2 ? 0.85 : 0.62;
        const n = 0.85 + 0.3 * noise1(s / 400, 97);
        tmp.setRGB(0.15 * top * n, 0.30 * top * n, 0.07 * top * n);
        col.push(tmp.r, tmp.g, tmp.b);
        uv.push(s / 3.5, (o + h) / 3.5);
      }
    }
    const R = PROF.length;
    for (let i = 0; i < run.length - 1; i++) {
      for (let r = 0; r < R - 1; r++) {
        const a = base + i * R + r, b = a + R;
        idx.push(a, a + 1, b, b, a + 1, b + 1);
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, map: hedgeTexture(),
    roughness: 0.95, metalness: 0, side: THREE.DoubleSide }));
  m.name = 'island-hedge';
  m.userData.ownGeometry = true;
  m.userData.island = true;
  m.castShadow = true; m.receiveShadow = true;
  return m;
}

// ----------------------------------------------------- landscape light pools
// Warm 2700 K path lights and the pools they throw on the lawn and paving
// (r1/r2 night critics: "no ground-level landscape lighting, no warm pools").
// Faked, not lit: an additive radial decal on the ground per fixture, a small
// dark bollard with a glowing cap, and a soft halo sprite. A real point light
// per fixture would join every material's program key (see eavelights.js), so
// these cost three materials and a uniform, and fade in with the night factor.
let poolTex = null;
function poolTexture() {
  if (poolTex) return poolTex;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  // r6: no plateau -- r5 read the pools as "discs"
  grd.addColorStop(0, 'rgb(255,255,255)'); grd.addColorStop(0.12, 'rgb(170,170,170)');
  grd.addColorStop(0.35, 'rgb(70,70,70)'); grd.addColorStop(0.65, 'rgb(18,18,18)'); grd.addColorStop(1, 'rgb(0,0,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 128, 128);
  poolTex = new THREE.CanvasTexture(c);
  poolTex.colorSpace = THREE.SRGBColorSpace;
  return poolTex;
}
let washTex = null;
function washTexture() {
  // an uplight's scallop on a wall: hot at the foot, fanning out and fading up
  if (washTex) return washTex;
  const W = 64, H = 128;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const img = g.createImageData(W, H);
  for (let y = 0; y < H; y++) {
    const v = 1 - y / (H - 1);              // 0 at the top, 1 at the foot
    const spread = 0.18 + 0.32 * (1 - v);   // wider as it climbs
    for (let x = 0; x < W; x++) {
      const u = (x / (W - 1) - 0.5) / spread;
      const k = Math.exp(-u * u * 2.2) * Math.pow(v, 1.3) * (0.35 + 0.65 * v);
      const i = (y * W + x) * 4, val = Math.round(255 * Math.min(1, k));
      img.data[i] = img.data[i + 1] = img.data[i + 2] = val; img.data[i + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  washTex = new THREE.CanvasTexture(c);
  washTex.colorSpace = THREE.SRGBColorSpace;
  return washTex;
}
// fixtures: [{ x, y, z, r (pool radius ft), post: bool }]
// washes: [{ x, y, z, nx, nz, w, h }] -- an additive scallop against a wall
// facing (nx, nz): the facade uplights reference 1 runs along every pier
export function buildLightPools(fixtures, washes = []) {
  const group = new THREE.Group();
  group.name = 'island-light-pools';
  group.userData.island = true;
  const WARM = new THREE.Color(1.0, 0.58, 0.26);
  const POOL = WARM.clone().multiplyScalar(2.0);   // r7: r6's pools "throw almost no light" 
  const poolMat = new THREE.MeshBasicMaterial({ map: poolTexture(), color: POOL, transparent: true,
    blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0, fog: false, toneMapped: true });
  const capMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.05, 0.04, 0.03) });
  const postMat = new THREE.MeshStandardMaterial({ color: 0x1b1c1e, roughness: 0.6, metalness: 0.3 });
  const haloMat = new THREE.SpriteMaterial({ map: poolTexture(), color: WARM.clone(), blending: THREE.AdditiveBlending,
    depthWrite: false, transparent: true, opacity: 0, fog: false });
  const posts = [], caps = [];
  for (const f of fixtures) {
    const disc = new THREE.Mesh(new THREE.CircleGeometry(f.r, 28), poolMat);
    disc.rotation.x = -Math.PI / 2;
    disc.position.set(f.x, f.y + 0.06, f.z);
    disc.renderOrder = 5;
    disc.raycast = () => {};
    disc.userData.ownGeometry = true;
    group.add(disc);
    if (f.post) {
      const p = new THREE.CylinderGeometry(0.1, 0.12, 1.5, 6); p.translate(f.x, f.y + 0.75, f.z); posts.push(p);
      const c = new THREE.CylinderGeometry(0.34, 0.16, 0.32, 8); c.translate(f.x, f.y + 1.62, f.z); caps.push(c);
    }
    const halo = new THREE.Sprite(haloMat);
    halo.position.set(f.x, f.y + (f.post ? 1.6 : 0.5), f.z);
    halo.scale.setScalar(f.post ? 2.6 : 2.0);
    halo.raycast = () => {};
    group.add(halo);
  }
  if (posts.length) {
    const pm = new THREE.Mesh(BufferGeometryUtils.mergeGeometries(posts, false), postMat);
    pm.userData.ownGeometry = true; pm.raycast = () => {}; group.add(pm);
    const cm = new THREE.Mesh(BufferGeometryUtils.mergeGeometries(caps, false), capMat);
    cm.userData.ownGeometry = true; cm.raycast = () => {}; group.add(cm);
    for (const g of [...posts, ...caps]) g.dispose();
  }
  const washMat = new THREE.MeshBasicMaterial({ map: washTexture(), color: WARM.clone(), transparent: true,
    blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0, fog: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  for (const w of washes) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w.w, w.h), washMat);
    m.position.set(w.x + w.nx * 0.12, w.y + w.h / 2, w.z + w.nz * 0.12);
    m.rotation.y = Math.atan2(w.nx, w.nz);
    m.raycast = () => {};
    m.userData.ownGeometry = true;
    group.add(m);
  }
  const OFF = new THREE.Color(0.05, 0.04, 0.03), ON = new THREE.Color(2.4, 1.5, 0.75);
  onNight((n) => {
    poolMat.opacity = 1.0 * n;
    haloMat.opacity = 1.0 * n;
    washMat.opacity = 0.9 * n;
    capMat.color.copy(OFF).lerp(ON, n);
  });
  return group;
}

// Make the faces point out (wall) / up (lip): flip the index winding if the
// computed normal of the first rim vertex disagrees.
function fixWinding(geo, pts, up = false) {
  const n = geo.attributes.normal;
  const p = pts[0];
  const ok = up ? n.getY(0) > 0 : (n.getX(1) * p.nx + n.getZ(1) * p.nz) > 0;
  if (ok) return;
  const idx = geo.index.array;
  for (let i = 0; i < idx.length; i += 3) { const t = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = t; }
  geo.index.needsUpdate = true;
  geo.computeVertexNormals();
}

window.__island = { shape, islandSdf, on: ISLAND };
