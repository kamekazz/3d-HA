// Outdoor environment: grass lawn, scattered low-poly trees, foundation
// bushes hugging the house, and a soft contact shadow that grounds it on the
// lawn. All trees/bushes merge into two meshes (one trunk draw call, one
// vertex-colored foliage draw call); placement uses a seeded RNG so the yard
// never reshuffles across rebuilds. Rebuilt from the house bbox on every
// reloadHouse. Visible in view mode on the House level only — edit mode shows
// the grid, single-floor view shows a dark backdrop (floorview.js) instead.
import * as THREE from 'three';
import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';
import { scene } from './scene.js';
import { getShellRoot, isOutdoorRoom, getBuildingBox } from './house.js';

let root = null;     // whole environment (grass + yard)
let yard = null;     // house-dependent part, rebuilt by setEnvironmentData
let grassMat = null;
let lastHouse = null;
let shellRect = null; // {x0,z0,x1,z1} of the loaded shell GLB, if any
let roofRect = null;  // {x0,z0,x1,z1} of the shell's roof masses = the building
// lawn materials owned by the current yard (patches laid over the shell's own
// pale site pad). repaintGrass tints these alongside the main lawn disc; they
// are rebuilt/disposed with the yard, so grassMat itself is never in here.
let yardGrassMats = [];

// Metered off "Front of the house.jpg", not chosen by eye. The photographed
// lawn is a HAZY summer turf: clean patches read RGB 116-123 / 128-136 /
// 122-130, i.e. G-R only +11..+14 and G-B around +8. The old 0x53703c
// rendered 125,158,95 — G-R +33, roughly 2.5x too saturated on the green-red
// axis, which is most of what made the front read as flat paint. Solved by
// inverting the render's own response (measured, not assumed) rather than by
// picking a prettier hex.
const GRASS_BASE = new THREE.Color(0x67716a);
const GRASS_SNOW = new THREE.Color(0xe9edf2);
let snowF = 0, wetF = 0; // weather.js drives these (eased on its side)

let center = { x: 13, z: 13 };
export function getEnvironmentCenter() { return center; }
export function getEnvironmentRoot() { return root; } // snapshots.js hides the yard while capturing

// deterministic layout — same seed, same yard, every load
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Smooth NON-repeating value noise in world feet. The lawn tile deliberately
// carries no low-frequency content (see makeGrassTexture), so the large-scale
// mown patchiness comes from here instead, written into the lawn mesh's
// vertex colours — a field that cannot tile, because it is not a tile.
function worldNoise(x, z, cell) {
  const h = (i, j) => {
    let n = Math.imul(i, 374761393) ^ Math.imul(j, 668265263);
    n = Math.imul(n ^ (n >>> 13), 1274126177);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
  };
  const fx = x / cell, fz = z / cell;
  const i = Math.floor(fx), j = Math.floor(fz);
  const tx = fx - i, tz = fz - j;
  const sx = tx * tx * (3 - 2 * tx), sz = tz * tz * (3 - 2 * tz);
  return (h(i, j) * (1 - sx) + h(i + 1, j) * sx) * (1 - sz)
       + (h(i, j + 1) * (1 - sx) + h(i + 1, j + 1) * sx) * sz;
}

// Tileable value noise, seamless because the lattice wraps. Used by the lawn
// tile; `cells` is the lattice resolution across the 128 px tile.
function valueNoise(rnd, cells) {
  const grid = new Float32Array(cells * cells);
  for (let i = 0; i < grid.length; i++) grid[i] = rnd();
  const at = (i, j) => grid[(((j % cells) + cells) % cells) * cells
                            + (((i % cells) + cells) % cells)];
  return (u, v) => {                       // u,v in 0..1 over the tile
    const fx = u * cells, fy = v * cells;
    const x0 = Math.floor(fx), y0 = Math.floor(fy);
    const tx = fx - x0, ty = fy - y0;
    const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
    return (at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx) * (1 - sy)
         + (at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx) * sy;
  };
}

// Near-white lawn tile so grassMat.color tints it (same pattern as
// textures.js). ONE tile serves the 1200-radius disc and every yard patch.
//
// The tile SIZE was already right and is unchanged: repeat 280 over the
// 2400 ft disc is 8.57 ft per tile, about 1.3 screen px per texel at the
// exterior fly-to pose, so nothing here is averaged away by the mipmap. What
// was missing was AMPLITUDE. The old tile was a white plate with 33% coverage
// of 1.5 px dots — relative sd 8%, which rendered as 3.4% (sd 4.6 on a lawn
// at lum 136) against the photograph's 8-15%. That is the "flat paint" read,
// and no amount of extra scatter geometry fixes it.
//
// Two bands of variation, each doing a different job at a different scale:
//   CLUMP  ~1.1 ft patch noise: wear, clover, thatch.
//   GRAIN  per-texel blade noise. This is the term that carries mean |Δ|
//          between ADJACENT pixels, which is the number sd cannot see.
// Anisotropy matters as much as the numbers: the lawn is viewed at a grazing
// angle, and without it the depth axis is minified into mush.
//
// The tile carries NO low-frequency content on purpose. A first attempt gave
// it mower stripes (a half-tile sine) and a 2.9 ft octave, and the whole lawn
// came back as a visible 8.6 ft PLAID — anything slower than about a foot
// makes the tile's own period readable at this scale, which is a worse
// artefact than the flat paint it was meant to fix. Large-scale lawn
// variation has to come from somewhere other than a repeating tile.
const LAWN_MEAN = 194, LAWN_GRAIN = 50, LAWN_CLUMP = 13;
function makeGrassTexture() {
  const N = 128;
  const c = document.createElement('canvas');
  c.width = c.height = N;
  const g = c.getContext('2d');
  const img = g.createImageData(N, N);
  const rnd = mulberry32(0x1a2b3c);
  const nFine = valueNoise(rnd, 12);    // ~0.7 ft cells
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      const u = x / N, v = y / N;
      const clump = (nFine(u, v) - 0.5) * 2 * LAWN_CLUMP;
      const grain = (rnd() - 0.5) * 2 * LAWN_GRAIN;
      let vv = LAWN_MEAN + clump + grain;
      vv = Math.max(40, Math.min(255, vv));
      const i = (y * N + x) * 4;
      // a touch of per-texel hue drift: real turf is not one colour scaled
      img.data[i] = Math.min(255, vv - 6 + (rnd() - 0.5) * 14);
      img.data[i + 1] = vv;
      img.data[i + 2] = Math.max(0, vv - 10 + (rnd() - 0.5) * 14);
      img.data[i + 3] = 255;
    }
  }
  g.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(280, 280);
  tex.anisotropy = 8;   // clamped to the device max by WebGLTextures
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// Aggregate/grit tile for the hardscape (driveway, walk, rock beds, slate).
// Authored below white so it MULTIPLIES the vertex colour rather than replacing
// it (mean ~0.83). The blob size and the 6 ft tile are chosen TOGETHER against
// the render scale, not for prettiness: at the front photo-matched pose one
// screen pixel is about 0.05 ft, so a 128 px tile over 6 ft puts one texel on
// one pixel and anything finer is averaged away by the mipmap before it
// reaches the eye. The first attempt (1.3 px speckle on a 4 ft tile) metered
// mean|Δ| 1.3-1.9 against the photograph's 4.8 for exactly that reason.
function makeGritTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#d6d6d4';
  g.fillRect(0, 0, 128, 128);
  for (let i = 0; i < 3600; i++) {
    const v = 168 + Math.floor(Math.random() * 88);
    g.fillStyle = `rgb(${v},${v},${v - 3})`;
    g.fillRect(Math.random() * 128, Math.random() * 128, 3.0, 3.0);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeShadowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 30, 128, 128, 128);
  grad.addColorStop(0, 'rgba(0,0,0,1)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}

export function initEnvironment() {
  root = new THREE.Group();
  root.name = 'environment';
  scene.add(root);

  grassMat = new THREE.MeshStandardMaterial({
    color: GRASS_BASE.clone(), map: makeGrassTexture(), roughness: 1 });
  // radius past fog far (1000) so the lawn fades into the horizon seamlessly
  const grass = new THREE.Mesh(new THREE.CircleGeometry(1200, 48), grassMat);
  grass.rotation.x = -Math.PI / 2;
  grass.position.y = -0.05; // below edit ground (-0.02); the two never co-show
  grass.receiveShadow = true; // the lawn catches the house-shell's sun shadow
  root.add(grass);

  // yard shows only in view mode on the whole-house level — edit mode shows
  // the grid, single-floor view shows floorview.js's studio backdrop
  let inViewMode = true;
  let onHouseLevel = true;
  const applyVisibility = () => { root.visible = inViewMode && onHouseLevel; };
  window.addEventListener('appModeChanged', (e) => {
    inViewMode = e.detail.mode === 'view';
    applyVisibility();
  });

  // The whole-house shell GLB loads async and its real footprint is far
  // bigger than the traced room rects; setLevel fires levelChanged once it
  // lands — measure it and replant the yard around the true bounds.
  window.addEventListener('levelChanged', (e) => {
    onHouseLevel = e.detail.level === 'all';
    applyVisibility();
    if (!lastHouse) return;
    const shell = getShellRoot();
    const r = shell ? rectOfShell(shell) : null;
    const rr = shell ? rectOfRoof() : null;
    if (JSON.stringify(r) !== JSON.stringify(shellRect)
        || JSON.stringify(rr) !== JSON.stringify(roofRect)) {
      shellRect = r;
      roofRect = rr;
      buildYard();
    }
  });
}

// Union of the shell's tall meshes only — the GLB ships flat hardscape
// (driveway/walkways) that would otherwise inflate the bounds to the lot line.
function rectOfShell(shell) {
  shell.updateWorldMatrix(true, true);
  const box = new THREE.Box3();
  const mb = new THREE.Box3();
  shell.traverse((o) => {
    if (!o.isMesh) return;
    mb.setFromObject(o);
    if (mb.max.y - mb.min.y > 3) box.union(mb);
  });
  if (box.isEmpty()) return null;
  return { x0: box.min.x, z0: box.min.z, x1: box.max.x, z1: box.max.z };
}

// The BUILDING footprint, as opposed to rectOfShell's whole-lot bounds above,
// which lands on the lot line. Anchors the foundation beds and driveway props,
// which have to sit against the real walls. The derivation lives in house.js
// (getBuildingBox) because focus.js frames the yards against the same box.
function rectOfRoof() {
  const box = getBuildingBox();
  if (!box) return null;
  return { x0: box.min.x, z0: box.min.z, x1: box.max.x, z1: box.max.z };
}

// weather.js tints the lawn: darker when wet, whitened as snow settles
function repaintGrass() {
  const c = GRASS_BASE.clone()
    .multiplyScalar(1 - 0.3 * wetF)
    .lerp(GRASS_SNOW, snowF);
  grassMat.color.copy(c);
  for (const m of yardGrassMats) m.color.copy(c);
}
export function setGroundSnow(f) {
  if (Math.abs(f - snowF) < 1e-3) return;
  snowF = f; repaintGrass();
}
export function setGroundWet(f) {
  if (Math.abs(f - wetF) < 1e-3) return;
  wetF = f; repaintGrass();
}

// ------------------------------------------------------------- yard build

function paint(geo, color) {
  const n = geo.attributes.position.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    arr[i * 3] = color.r; arr[i * 3 + 1] = color.g; arr[i * 3 + 2] = color.b;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(arr, 3));
}

const _leaf = new THREE.Color();

function addDeciduous(rng, x, z, s, trunks, leaves) {
  const h = 6 + rng() * 5;
  const trunk = new THREE.CylinderGeometry(0.28 * s, 0.45 * s, h, 5);
  trunk.translate(x, h / 2, z);
  trunks.push(trunk);
  const hue = 0.26 + rng() * 0.09;
  const blobs = 3 + Math.floor(rng() * 3);
  for (let i = 0; i < blobs; i++) {
    const r = (2.2 + rng() * 1.8) * s;
    const blob = new THREE.IcosahedronGeometry(r, 1);
    blob.scale(1, 0.85, 1);
    const a = rng() * Math.PI * 2, d = rng() * 1.8 * s;
    blob.translate(x + Math.cos(a) * d, h - 0.5 + rng() * 2.5 * s, z + Math.sin(a) * d);
    // sRGB, not the linear working space: setHSL defaults to linear in r160,
    // which rendered this treeline as pale mint against the deep green of the
    // reference photo (the same trap documented at the `hsl` helper below).
    paintNoisy(blob, _leaf.setHSL(hue, 0.45 + rng() * 0.16, 0.19 + rng() * 0.09,
                                  THREE.SRGBColorSpace), rng, 0.34);
    leaves.push(blob);
  }
}

function addConifer(rng, x, z, s, trunks, leaves) {
  const h = 2 + rng();
  const trunk = new THREE.CylinderGeometry(0.2 * s, 0.32 * s, h, 5);
  trunk.translate(x, h / 2, z);
  trunks.push(trunk);
  const total = (9 + rng() * 5) * s;
  _leaf.setHSL(0.34 + rng() * 0.04, 0.42, 0.15 + rng() * 0.05,
               THREE.SRGBColorSpace);
  let y = h;
  for (let i = 0; i < 3; i++) {
    const tierH = (total / 3) * 1.35;
    const cone = new THREE.ConeGeometry((2.8 - i * 0.75) * s, tierH, 7);
    cone.translate(x, y + tierH / 2, z);
    paintNoisy(cone, _leaf, rng, 0.30);
    leaves.push(cone);
    y += tierH * 0.62;
  }
}

function addBush(rng, x, z, leaves) {
  const r = 1.1 + rng() * 1.2;
  const bush = new THREE.IcosahedronGeometry(r, 1);
  bush.scale(1, 0.65, 1);
  bush.translate(x, r * 0.45, z);
  paintNoisy(bush, _leaf.setHSL(0.3 + rng() * 0.06, 0.46, 0.18 + rng() * 0.07,
                                THREE.SRGBColorSpace), rng, 0.34);
  leaves.push(bush);
}

// ------------------------------------------------------- front yard detail
// Everything the front photo shows between the siding and the street and that
// the shell GLB does not model: planting beds of river rock with clipped
// boxwood and purple perennials, flagstone, the SUV on the driveway, the wheeled
// bin by the garage, porch planters/bench, path lights and the street lamp post.
//
// Geometry only — no lights are created (a change in the scene's light count
// recompiles every MeshStandard shader). Everything merges into three extra
// draw calls: `beds` (matte, vertex-coloured), `props` (semi-gloss,
// vertex-coloured) and one lawn patch; foliage joins the existing merged
// leaves mesh, so shrubs and flowers cost nothing extra.

// Metered off "Front of the house.jpg": the rock bed reads lum 131 against
// the driveway's 187 -- it is markedly DARKER than the concrete, not the same
// brightness as the old comment claimed, and cooler.
const ROCK = new THREE.Color(0x646569);
const _c = new THREE.Color();

// Color.setHSL defaults to the WORKING colour space (linear) in three r160, so
// plain setHSL(h, s, 0.2) is a linear 0.2 — about sRGB 0.48, i.e. roughly twice
// as light as the number reads. Everything below is authored off the photos in
// sRGB, so say so explicitly. (The tree/bush palette above predates this and is
// left alone deliberately — restating it would repaint the whole treeline.)
const hsl = (h, s, l) => _c.setHSL(h, s, l, THREE.SRGBColorSpace);

// base at y, centred on x/z
function boxAt(w, h, d, x, y, z, ry = 0) {
  const g = new THREE.BoxGeometry(w, h, d);
  if (ry) g.rotateY(ry);
  g.translate(x, y + h / 2, z);
  return g;
}
function slab(x0, z0, x1, z1, y, sx = 1, sz = 1) {
  const g = new THREE.PlaneGeometry(x1 - x0, z1 - z0, sx, sz);
  g.rotateX(-Math.PI / 2);
  g.translate((x0 + x1) / 2, y, (z0 + z1) / 2);
  return g;
}
function cylAt(rTop, rBot, h, seg, x, y, z) {
  const g = new THREE.CylinderGeometry(rTop, rBot, h, seg);
  g.translate(x, y + h / 2, z);
  return g;
}
// wheel/axle: cylinder laid on its side, axis along X
function wheelAt(r, w, x, y, z) {
  const g = new THREE.CylinderGeometry(r, r, w, 10);
  g.rotateZ(Math.PI / 2);
  g.translate(x, y, z);
  return g;
}
// A free 4-corner quad carrying position/normal/uv, so it can be merged into
// the same buffer as slab()'s PlaneGeometry. Used for the grass banks that
// clothe the shell pad's 2 ft vertical edges — a horizontal slab cannot.
// Corners in order, seen from above.
function quadAt(p0, p1, p2, p3) {
  const g = new THREE.BufferGeometry();
  const v = [...p0, ...p1, ...p2, ...p0, ...p2, ...p3];
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(v), 3));
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(12), 2));
  g.computeVertexNormals();
  return g;
}
// Per-vertex value jitter around a base colour. The merged foliage mesh is
// non-indexed and flat-shaded, so this costs nothing and gives every facet a
// gradient across it — which is the ONLY fine-scale texture a 42-triangle
// icosahedron shrub can have. Round 1's boxwood metered mean|dx| 6.9 / |dy|
// 10.0 against the photographed shrub's 14.3 / 23.1 for exactly this reason.
function paintNoisy(geo, color, rng, amt) {
  const n = geo.attributes.position.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const f = 1 + (rng() - 0.5) * amt;
    arr[i * 3] = color.r * f;
    arr[i * 3 + 1] = color.g * f;
    arr[i * 3 + 2] = color.b * f;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(arr, 3));
}

// per-vertex jitter around a base colour — turns one plane into gravel
function speckle(geo, base, rng, amt) {
  const n = geo.attributes.position.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const f = 1 + (rng() - 0.5) * amt;
    arr[i * 3] = base.r * f; arr[i * 3 + 1] = base.g * f; arr[i * 3 + 2] = base.b * f;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(arr, 3));
}

// A rock-mulch bed: gravel plane plus cobbles PACKED over the whole of it.
//
// Round 1 laid 0.5 cobbles per sq ft (r 0.20-0.48 flattened to 0.55 in y,
// mean footprint ~0.35 sq ft), which covers about 17% of the bed and leaves
// a grey plate showing between. "Front of the house.jpg" x 1230-1500 is
// wall-to-wall stone, mixed sizes, lit tops at RGB 190,194,202 against a bed
// mean of 125 — a 65-point spread only a packed field produces. Metered:
// photo lum 125-126, sd 37.6-46.2, mean|dx| 12.7-13.1, |dy| 19.2-21.1;
// round 1 rendered lum 146, sd 21.8, |dx| 5.9, |dy| 8.1.
//
// So `dens` is cobbles per square foot and the default is 5.4x round 1's, the
// size range is nearly 3x wider (small grit through 7-inch stones), and the
// value spread is opened right up. `edge` adds the coarse rim of larger white
// stones the photographs show where the rock meets the lawn — round 1 used a
// single straight dark board on the front face only, which read as a CAD
// outline; no photograph has one.
// 5.4 cobbles per square foot, 10.8x round 1's 0.5. Each stone is also
// SMALLER: measured off "Front of the house.jpg" x 1230-1560, where the bed
// is ~10 ft across in ~350 px, the stones run 0.15-0.38 ft across, i.e.
// radius 0.07-0.19 — round 1's 0.20-0.48 were two to four times too big,
// which is why its bed metered mean|dx| 5.9 against the photo's 12.7 even
// once the coverage was right. Small stones are what put edges under pixels.
// They are OCTAHEDRA below about 0.24 ft: at 4-8 screen px an 8-triangle
// blob and a 20-triangle one are indistinguishable, and this bed field is
// ~6,700 stones across both yards.
const BED_DENSITY = 7.0;
function addBed(rng, x0, z0, x1, z1, y, beds, dens = BED_DENSITY, edge = true) {
  const g = slab(x0, z0, x1, z1, y, Math.max(2, Math.round((x1 - x0) / 2)),
                 Math.max(2, Math.round((z1 - z0) / 2)));
  speckle(g, ROCK, rng, 0.5);
  beds.push(g);
  const n = Math.round((x1 - x0) * (z1 - z0) * dens);
  for (let i = 0; i < n; i++) {
    // heavy-tailed: mostly grit, a few big stones. r**2.2 keeps the mean
    // footprint small enough that the count stays honest while still
    // producing the photograph's mixed-size read.
    const t = rng();
    const r = 0.075 + (t * t * t) * 0.40;
    const s = r < 0.24 ? new THREE.OctahedronGeometry(r, 0)
                       : new THREE.IcosahedronGeometry(r, 0);
    s.scale(1 + rng() * 0.4, 0.5 + rng() * 0.25, 1 + rng() * 0.4);
    s.rotateY(rng() * 6.283);
    s.translate(x0 + rng() * (x1 - x0), y + r * 0.16, z0 + rng() * (z1 - z0));
    // cool blue-grey, not the warm hue round 1 used: the photographed rock
    // meters B > G > R (121,127,136). The 0.18..0.64 lightness span is what
    // gives lit tops against dark shadow gaps.
    paint(s, hsl(0.58, 0.075, 0.145 + rng() * 0.40));
    beds.push(s);
  }
  if (edge) addCobbleRim(rng, x0, z0, x1, z1, y, beds);
}

// The coarse rim of larger, paler stones where a rock bed meets the lawn.
// Visible on every edge of the east bed in "Front of the house.jpg".
function addCobbleRim(rng, x0, z0, x1, z1, y, beds) {
  const run = (ax, az, bx, bz) => {
    const L = Math.hypot(bx - ax, bz - az);
    const n = Math.max(2, Math.round(L / 0.62));
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      const r = 0.30 + rng() * 0.26;
      const s = new THREE.IcosahedronGeometry(r, 0);
      s.scale(1.15, 0.62, 1.15);
      s.translate(ax + (bx - ax) * t + (rng() - 0.5) * 0.4, y + r * 0.2,
                  az + (bz - az) * t + (rng() - 0.5) * 0.4);
      paint(s, hsl(0.58, 0.05, 0.34 + rng() * 0.22));
      beds.push(s);
    }
  };
  run(x0, z0, x1, z0); run(x0, z1, x1, z1);
  run(x0, z0, x0, z1); run(x1, z0, x1, z1);
}

// Dry-stacked SCALLOPED stone edging: the flat slate/flagstone course that
// holds up every raised bed on this property ("Side of the house Outside.jpg"
// bottom, "Frontyard v3 2.jpg" foreground, "Front of the house.jpg" x 200-500).
// It curves, and each stone tilts a little differently, so the top line
// scallops instead of running dead straight. `pts` is a world polyline.
function addStoneEdge(rng, pts, y, h, beds) {
  for (let k = 0; k < pts.length - 1; k++) {
    const [ax, az] = pts[k], [bx, bz] = pts[k + 1];
    const L = Math.hypot(bx - ax, bz - az);
    if (L < 0.2) continue;
    const ux = (bx - ax) / L, uz = (bz - az) / L;
    const ang = Math.atan2(-uz, ux);
    const courses = Math.max(2, Math.round(h / 0.34));
    for (let c = 0; c < courses; c++) {
      const cy = y + c * (h / courses);
      const off = (c % 2) * 0.45;             // stagger the joints
      for (let d = off; d < L; d += 0.85 + rng() * 0.55) {
        const len = Math.min(0.75 + rng() * 0.7, L - d);
        if (len < 0.25) break;
        const t = d + len / 2;
        const g = boxAt(len, (h / courses) * 1.18 + rng() * 0.05,
                        0.52 - c * 0.05, ax + ux * t, cy, az + uz * t, ang);
        // slate: dark, cool, and a WIDE value range — a dry-stacked wall
        // reads as stone because every slab catches the light differently
        paint(g, hsl(0.08, 0.045, 0.17 + rng() * 0.16));
        beds.push(g);
      }
    }
  }
}

// Clipped shrub. `sp` picks the species: the front bed in the photographs is
// NOT one repeated boxwood ball — it is a mixed row of boxwood, a paler
// yellow-green euonymus, a fine-textured juniper and a low spreading
// groundcover, with the mounds at visibly different sizes and squashes.
const SPECIES = {
  //          hue    sat   light  squash  spread
  boxwood:  [0.295, 0.40, 0.255, 0.92, 1.00],
  euonymus: [0.235, 0.30, 0.270, 0.80, 1.14],
  juniper:  [0.345, 0.24, 0.230, 0.55, 1.42],
  yew:      [0.320, 0.36, 0.185, 1.05, 0.86],
};
function addBoxwood(rng, x, z, r, y, leaves, sp = 'boxwood') {
  const [h, s, l, sq, sd] = SPECIES[sp] || SPECIES.boxwood;
  const g = new THREE.IcosahedronGeometry(r, 1);
  g.scale(sd, sq, sd * (0.92 + rng() * 0.18));
  g.rotateY(rng() * 6.283);
  g.translate(x, y + r * sq * 0.86, z);
  paintNoisy(g, hsl(h + (rng() - 0.5) * 0.03, s, l + rng() * 0.055), rng, 0.30);
  leaves.push(g);
}

// Low spreading groundcover mass — the sheet of green that carpets the
// lamp-post bed in "Front of the house, a little bit of the garage...".
function addGroundCoverMass(rng, x, z, rx, rz, y, leaves) {
  const n = Math.max(3, Math.round(rx * rz * 0.5));
  for (let i = 0; i < n; i++) {
    const r = 0.55 + rng() * 0.75;
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(1.4, 0.34, 1.4);
    g.rotateY(rng() * 6.283);
    const a = rng() * Math.PI * 2, d = Math.sqrt(rng());
    g.translate(x + Math.cos(a) * d * rx, y + r * 0.28, z + Math.sin(a) * d * rz);
    paintNoisy(g, hsl(0.28 + rng() * 0.05, 0.36, 0.20 + rng() * 0.07), rng, 0.34);
    leaves.push(g);
  }
}

// Drift of purple flowering perennials (the salvia/catmint masses in the
// photo). `n` scales it from a single clump to the 8 ft mass that sits in the
// middle of the east bed.
function addPerennial(rng, x, z, y, leaves, n = 3, spread = 1.6) {
  for (let i = 0; i < n; i++) {
    const r = 0.38 + rng() * 0.26;
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(1.15, 0.8, 1.05);
    g.translate(x + (rng() - 0.5) * spread, y + r * 0.55,
                z + (rng() - 0.5) * spread * 0.82);
    paintNoisy(g, hsl(0.74 + (rng() - 0.5) * 0.05, 0.44,
                      0.38 + rng() * 0.12), rng, 0.36);
    leaves.push(g);
  }
}

// upright ornamental grass clump (they flank the lamp post in the street photo)
function addGrassClump(rng, x, z, y, leaves) {
  const h = 2.4 + rng() * 1.4;
  hsl(0.20, 0.38, 0.33 + rng() * 0.06);
  for (let i = 0; i < 7; i++) {
    const a = rng() * Math.PI * 2;
    const g = new THREE.ConeGeometry(0.28, h * (0.7 + rng() * 0.5), 4);
    g.rotateX((rng() - 0.5) * 0.5);
    g.rotateZ((rng() - 0.5) * 0.5);
    g.translate(x + Math.cos(a) * 0.5 * rng(), y + h * 0.42, z + Math.sin(a) * 0.5 * rng());
    paintNoisy(g, _c, rng, 0.34);
    leaves.push(g);
  }
}

// Big clipped mound — the standalone specimen shrubs standing free on the back
// lawn in Backyard v3 5/7: 4-9 ft across. Much larger than addBush.
//
// Round 1 gave every one of these the SAME squash (1.05, 0.72, 1.0) and the
// same hue, so twenty of them read as twenty copies of one object. `kind`
// and the per-mound squash below are what break that up; `sphere` is for the
// specimens the photographs show as full globes rather than domes.
const MOUND_KIND = {
  green: [0.30, 0.42, 0.190],
  dark:  [0.335, 0.34, 0.140],
  olive: [0.250, 0.26, 0.200],
  grey:  [0.315, 0.13, 0.265],
};
function addMound(rng, x, z, r, y, kind, leaves, sphere = false) {
  const [h, s, l] = MOUND_KIND[kind] || MOUND_KIND.green;
  const sq = sphere ? 0.92 + rng() * 0.12 : 0.58 + rng() * 0.30;
  const g = new THREE.IcosahedronGeometry(r, 2);
  g.scale(0.9 + rng() * 0.3, sq, 0.9 + rng() * 0.3);
  g.rotateY(rng() * 6.283);
  g.translate(x, y + r * sq * 0.86, z);
  paintNoisy(g, hsl(h + (rng() - 0.5) * 0.045, s, l + rng() * 0.06), rng, 0.34);
  leaves.push(g);
}

// The big specimen beside the deck in "Backyard v3 9" / "v3 5".
//
// Round 1 built this as a BURGUNDY PANCAKE: RGB 114,60,66 (R-G +54), ~12 ft
// wide and ~4 ft tall. The photographs show something else entirely — a
// SPHERE about 9 ft each way whose body is olive-green (metered 99,94,68 and
// 92,97,74, i.e. R-G between -5 and +5) carrying red new growth only on the
// sunlit outer tips. So it is authored green-dominant here and the red is a
// minority of the upper vertices, not the base colour.
function addPhotinia(rng, x, z, r, y, leaves) {
  const g = new THREE.IcosahedronGeometry(r, 2);
  g.scale(1.06, 0.96, 1.0);
  g.translate(x, y + r * 0.90, z);
  const body = hsl(0.215, 0.30, 0.225).clone();  // olive green
  const tip = hsl(0.030, 0.30, 0.245).clone();   // red new growth
  const pos = g.attributes.position;
  const n = pos.count;
  const arr = new Float32Array(n * 3);
  const top = y + r * 0.90;
  for (let i = 0; i < n; i++) {
    const up = (pos.getY(i) - top) / r;          // -1 bottom .. +1 top
    const red = rng() < 0.14 + 0.26 * Math.max(0, up);
    const c = red ? tip : body;
    const f = 1 + (rng() - 0.5) * 0.32;
    arr[i * 3] = c.r * f; arr[i * 3 + 1] = c.g * f; arr[i * 3 + 2] = c.b * f;
  }
  g.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  leaves.push(g);
}

// Weeping / layered specimen tree: a slim trunk carrying three or four broad
// flattened tiers. "Backyard v3 7" has one standing free on the lawn beyond
// the deck and "v3 5" shows a second by the boundary — they are the only
// vertical accents in the middle of the yard and their silhouette is nothing
// like a shade tree's.
function addWeeper(rng, x, z, s, trunks, leaves) {
  const h = (5.5 + rng() * 2.2) * s;
  const t = new THREE.CylinderGeometry(0.16 * s, 0.30 * s, h, 6);
  t.translate(x, h / 2, z);
  trunks.push(t);
  const tiers = 2 + Math.floor(rng() * 2);
  for (let i = 0; i < tiers; i++) {
    const r = (2.9 - i * 0.5 + rng() * 0.7) * s;
    const g = new THREE.IcosahedronGeometry(r, 1);
    // round 1's first pass used 0.30 in y, which rendered as brown lily pads
    g.scale(1.18, 0.62, 1.18);
    g.rotateY(rng() * 6.283);
    g.translate(x + (rng() - 0.5) * 1.0 * s, h - i * 1.55 * s + 0.5 * s,
                z + (rng() - 0.5) * 1.0 * s);
    // bronze-OLIVE. A first pass at hue 0.09-0.14 rendered these as brown
    // mud blobs; the photographed specimen is a bronzed green, not a rock.
    paintNoisy(g, hsl(0.155 + rng() * 0.045, 0.26, 0.175 + rng() * 0.05),
               rng, 0.34);
    leaves.push(g);
  }
}

// Pole bird feeder — "Backyard v3 5" has one standing at the boundary bed
// (x 1140-1170, y 145-215): a slim dark post with a small hipped-roof house.
function addFeeder(rng, x, z, y, props) {
  const dark = _c.setHex(0x2a2723).clone();
  const p = cylAt(0.07, 0.09, 5.4, 6, x, y, z);
  paint(p, dark); props.push(p);
  const b = boxAt(1.15, 0.75, 1.15, x, y + 5.1, z);
  paint(b, _c.setHex(0xcfc7b4)); props.push(b);
  // rotate BEFORE translating: cylAt has already moved the geometry, and
  // rotateY spins about the origin, not about the piece
  const roof = new THREE.CylinderGeometry(0.05, 0.95, 0.55, 4);
  roof.rotateY(Math.PI / 4);
  roof.translate(x, y + 6.12, z);
  paint(roof, dark); props.push(roof);
}

// Mature shade tree. addDeciduous fixes its trunk height at 6-11 ft whatever
// `s` is, which caps the treeline at shrub height; the front and back photos
// are framed by 30-45 ft canopies, so this one scales the height too.
function addShadeTree(rng, x, z, s, trunks, leaves) {
  const h = (13 + rng() * 7) * s;
  const trunk = new THREE.CylinderGeometry(0.5 * s, 0.95 * s, h, 6);
  trunk.translate(x, h / 2, z);
  trunks.push(trunk);
  const hue = 0.27 + rng() * 0.07;
  for (let i = 0; i < 6; i++) {
    const r = (4.0 + rng() * 3.2) * s;
    const blob = new THREE.IcosahedronGeometry(r, 1);
    blob.scale(1.1, 0.8, 1.1);
    const a = rng() * Math.PI * 2, d = rng() * 4.2 * s;
    blob.translate(x + Math.cos(a) * d, h + (rng() - 0.2) * 4 * s, z + Math.sin(a) * d);
    paintNoisy(blob, _leaf.setHSL(hue, 0.42 + rng() * 0.14, 0.15 + rng() * 0.07,
                                  THREE.SRGBColorSpace), rng, 0.32);
    leaves.push(blob);
  }
}

// Dry-stacked slate retaining course. This is the signature hardscape of the
// property — "Front of the house" and "Side of the house Outside" both show a
// dark thin-slab stone wall holding the raised lawn up, and it is exactly where
// the shell GLB leaves a bare 2 ft white face at the edge of its site pad.
// Runs along one axis; `along` is 'x' or 'z'.
function addSlate(rng, along, a0, a1, b, yBot, yTop, beds) {
  const courses = Math.max(2, Math.round((yTop - yBot) / 0.42));
  const ch = (yTop - yBot) / courses;
  for (let c = 0; c < courses; c++) {
    const y = yBot + c * ch;
    const out = 0.34 - c * (0.16 / courses);      // slight batter, front-heavy
    for (let a = a0; a < a1; a += 1.5 + rng() * 1.1) {
      const len = Math.min(1.4 + rng() * 1.0, a1 - a);
      const g = along === 'x'
        ? boxAt(len, ch * 1.06, out, a + len / 2, y, b)
        : boxAt(out, ch * 1.06, len, b, y, a + len / 2);
      paint(g, hsl(0.09, 0.05, 0.20 + rng() * 0.08));
      beds.push(g);
    }
  }
}

// Poured-concrete apron: one flat plate plus scored control joints. The shell
// GLB's own site pad reads as unbroken white, and the joint grid is most of
// what tells a driveway from a blank plane at this distance.
function addConcrete(x0, z0, x1, z1, y, joints, beds) {
  const g = slab(x0, z0, x1, z1, y, 2, 2);
  paint(g, hsl(0.10, 0.02, 0.57));
  beds.push(g);
  const dk = hsl(0.10, 0.02, 0.42).clone();
  for (const [jx, jz, jw, jd] of joints) {
    const j = slab(jx, jz, jx + jw, jz + jd, y + 0.012);
    paint(j, dk);
    beds.push(j);
  }
}

// Flagstone stepping stones: irregular slabs, blue-grey, set proud of the
// gravel. Both yards have a run of them (front bed, and the back gravel bed).
function addFlagstones(rng, pts, y, beds) {
  for (const [x, z] of pts) {
    const g = boxAt(2.0 + rng() * 0.5, 0.16, 1.5 + rng() * 0.4, x, y, z,
                    (rng() - 0.5) * 0.45);
    paint(g, hsl(0.55, 0.05, 0.36 + rng() * 0.09));
    beds.push(g);
  }
}

// Neighbouring house. Both the front and the back photographs have one in
// frame on each side — without them the house stands in an empty field, which
// is the loudest thing wrong with the whole-house view.
//
// Round 1's version read as a "roofless grey placeholder box": the gable rise
// was 5.5 ft on a 30 ft depth (a 20-degree pitch that vanishes from above),
// there were no eaves, no windows and no fascia, and it was merged into the
// `beds` bucket — whose UVs are derived from world X/Z, so every VERTICAL
// face sampled one line of the grit tile and smeared it top to bottom. It
// sits at the left of the PRIMARY front view; "Front of the house.jpg" and
// "Frontyard v3 2.jpg" both show a proper white gabled house there.
//
// Now: a 38-degree gable with a real overhang, a fascia band, window
// openings and garage doors, pushed into its own matte bucket.
function addNeighbour(x, z, w, d, h, ry, doors, masses, rng) {
  // hsl() returns the SHARED _c instance, so anything held in a local has to
  // be cloned. Round 1's version did not, which is why its neighbour rendered
  // as one flat grey mass with no roof/wall distinction: `wall` and `roof`
  // were the same object.
  const wall = hsl(0.10, 0.035, 0.80).clone();
  const roofC = hsl(0.08, 0.025, 0.40).clone();
  const fascia = hsl(0.10, 0.02, 0.88).clone();
  const glass = hsl(0.58, 0.10, 0.24).clone();
  const push = (g, c) => { paintNoisy(g, c, rng, 0.10); masses.push(g); };
  const cr = Math.cos(ry), sr = Math.sin(ry);
  // local (a = along the ridge / width, b = across) -> world
  const W = (a, b) => [x + a * cr + b * sr, z - a * sr + b * cr];

  push(boxAt(w, h, d, x, 0, z, ry), wall);
  // fascia band under the eave
  push(boxAt(w + 1.6, 0.65, d + 1.6, x, h - 0.2, z, ry), fascia);

  // gable prism sitting on the walls, ridge along the local X (width) axis.
  // rise/half-depth = 0.78 -> a 38 degree pitch, which is what reads as a
  // roof from a camera 34 ft up.
  const rise = d * 0.39;
  const pr = new THREE.BufferGeometry();
  const hw = w / 2 + 0.85, hd = d / 2 + 0.85;
  const V = [[-hw, 0, -hd], [hw, 0, -hd], [hw, 0, hd], [-hw, 0, hd],
             [-hw, rise, 0], [hw, rise, 0]];
  // wound so the OUTWARD normal is the front face: MeshStandardMaterial is
  // FrontSide, and the first attempt at this prism was inverted, which left
  // every neighbour reading as a flat-topped grey box with no roof at all
  const F = [[0, 5, 1], [0, 4, 5], [2, 4, 3], [2, 5, 4],
             [0, 3, 4], [1, 5, 2], [0, 2, 3], [0, 1, 2]];
  const pos = [];
  for (const f of F) for (const i of f) pos.push(...V[i]);
  pr.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
  // uv is unused here but mergeGeometries refuses a set that does not match
  pr.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(pos.length / 3 * 2), 2));
  pr.computeVertexNormals();
  pr.rotateY(ry); pr.translate(x, h + 0.45, z);
  push(pr, roofC);

  // windows on the two long faces, two storeys where the house is tall enough
  const rows = h > 16 ? [3.2, 11.0] : [3.2];
  for (const b of [d / 2 + 0.2, -d / 2 - 0.2]) {
    for (let i = 0; i < 3; i++) {
      const a = (i - 1) * (w / 3.4);
      for (const wy of rows) {
        const [px, pz] = W(a, b);
        push(boxAt(2.6, 4.0, 0.35, px, wy, pz, ry), glass);
        push(boxAt(3.1, 4.5, 0.22, px, wy - 0.25, pz, ry), fascia);
      }
    }
  }
  for (let i = 0; i < doors; i++) {
    const [px, pz] = W((i - (doors - 1) / 2) * 9.5, d / 2 + 0.15);
    push(boxAt(8.4, 7.2, 0.4, px, 0.2, pz, ry), hsl(0.10, 0.02, 0.90));
  }
}

// --------------------------------------------------------------- lot edge
// A Sims lot always terminates. Round 1's driveway ran out into open lawn and
// stopped in a square stub at z 75.4 — `landmarks()` even names that z
// `street`, a street that was never built. "Front of the house, a little bit
// of the garage and car pointing to a different house.jpg" shows the whole
// sequence: lawn, a concrete SIDEWALK, a grass verge, a CURB, and the asphalt
// with cars parked on it.
//
// Heights are tight here. The 1200 ft grass disc sits at y -0.05 and the
// shell's own pale pad at 0.16, so the carriageway cannot be sunk below the
// lawn the way a real one is — it goes at y 0.00, just clear of the disc, and
// the curb does the work of reading as a kerb.
function addStreet(L, rng, beds, props) {
  const x0 = L.driveL - 190, x1 = L.driveR + 150;
  const kerbZ = L.street + 0.6;          // face of the curb
  // set back 7.6 ft from the kerb, with a grass verge between, as in the
  // street photograph. A first pass ran it at street-4.9 and the walk
  // filled the bottom-left of the exterior fly-to as a second driveway.
  const walkZ0 = L.street - 12.0, walkZ1 = L.street - 7.6;

  // carriageway
  const road = slab(x0, kerbZ + 0.9, x1, kerbZ + 27, 0.0, 8, 2);
  speckle(road, _c.setHex(0x4c4b49).clone(), rng, 0.22);
  beds.push(road);
  // centre line, dashed
  for (let cx = x0; cx < x1; cx += 16) {
    const d = slab(cx, kerbZ + 13.2, cx + 8, kerbZ + 13.6, 0.02);
    paint(d, _c.setHex(0x9a9280));
    beds.push(d);
  }
  // curb, both sides, broken where the driveway apron crosses
  const curb = (a, b) => {
    const g = boxAt(b - a, 0.34, 0.9, (a + b) / 2, 0.0, kerbZ + 0.45);
    paint(g, hsl(0.10, 0.02, 0.60)); beds.push(g);
  };
  curb(x0, L.driveL - 4.5); curb(L.driveR + 4.5, x1);
  const farCurb = boxAt(x1 - x0, 0.34, 0.9, (x0 + x1) / 2, 0.0, kerbZ + 26.6);
  paint(farCurb, hsl(0.10, 0.02, 0.60)); beds.push(farCurb);

  // sidewalk, with the drive crossing it
  addConcrete(x0 + 40, walkZ0, x1 - 30, walkZ1, L.lo + 0.03,
              (() => { const j = []; for (let cx = x0 + 44; cx < x1 - 30; cx += 5)
                j.push([cx, walkZ0, 0.14, walkZ1 - walkZ0]); return j; })(), beds);

  // driveway apron: flares out from the drive across the verge to the kerb
  const ap = quadAt([L.driveL, L.lo + 0.02, walkZ1], [L.driveR, L.lo + 0.02, walkZ1],
                    [L.driveR + 4.2, 0.03, kerbZ + 0.9], [L.driveL - 4.2, 0.03, kerbZ + 0.9]);
  paint(ap, hsl(0.10, 0.02, 0.56)); beds.push(ap);

  // Mailbox. INFERRED, not measured: the street photograph shows a
  // post-mounted black object at the kerb by the neighbouring lot but our own
  // is out of frame in every shot. Reported as such.
  const mx = L.driveR + 3.0, mz = L.street - 2.6;
  const post = boxAt(0.30, 3.6, 0.30, mx, L.lo, mz);
  paint(post, _c.setHex(0x1d1e20)); props.push(post);
  const arm = boxAt(0.26, 0.26, 1.5, mx, L.lo + 3.3, mz - 0.5);
  paint(arm, _c.setHex(0x1d1e20)); props.push(arm);
  const bxg = boxAt(0.72, 0.78, 1.55, mx, L.lo + 3.6, mz - 0.5);
  paint(bxg, _c.setHex(0x24262a)); props.push(bxg);
}

// Two cast-concrete geese standing in the front bed, immediately west of the
// porch steps — "Front of the house.jpg" x 660-590, y 875-900 (see the
// enlargement in scratchpad/ext/p_porch.png). Small, but they are exactly the
// kind of lived-in ornament a render never has and a real garden always does.
function addGoose(rng, x, z, y, ry, props) {
  const white = _c.setHex(0xe6e2d8).clone();
  const push = (g) => { paint(g, white); props.push(g); };
  const c = Math.cos(ry), s = Math.sin(ry);
  const at = (a, b) => [x + a * c + b * s, z - a * s + b * c];
  let [bx2, bz] = at(0, 0);
  push(cylAt(0.30, 0.34, 0.72, 8, bx2, y, bz));            // body
  [bx2, bz] = at(0, -0.34);
  push(boxAt(0.18, 0.72, 0.18, bx2, y + 0.55, bz));        // neck
  [bx2, bz] = at(0, -0.46);
  push(boxAt(0.22, 0.24, 0.42, bx2, y + 1.18, bz));        // head
}

// Dark SUV parked nose-in on the driveway (facing -Z, i.e. at the garage).
// Read from behind, which is the front-photo angle: wide body, narrower
// greenhouse with a dark glass band, taillights, bumper, tyres proud of the sides.
function addCar(x, z, props) {
  const body = new THREE.Color(0x1b1e23);
  const dark = new THREE.Color(0x0e1014);
  const glass = new THREE.Color(0x07080b);
  const tire = new THREE.Color(0x0b0b0c);
  const push = (g, c) => { paint(g, c); props.push(g); };
  push(boxAt(6.4, 2.7, 15.4, x, 1.5, z), body);               // body sides
  push(boxAt(6.0, 0.9, 14.2, x, 0.75, z), dark);              // rocker/underbody
  push(boxAt(6.2, 0.6, 5.4, x, 4.2, z - 4.6), body);          // bonnet
  push(boxAt(5.9, 1.9, 9.0, x, 4.2, z - 0.4), glass);         // greenhouse
  push(boxAt(5.5, 0.3, 8.4, x, 6.1, z - 0.4), body);          // roof
  push(boxAt(6.35, 1.3, 0.5, x, 2.9, z + 7.7), body);         // tailgate panel
  push(boxAt(6.4, 0.85, 0.55, x, 1.35, z + 7.7), dark);       // rear bumper
  push(boxAt(2.1, 0.45, 0.3, x - 2.05, 3.5, z + 7.85), new THREE.Color(0x7a1418));
  push(boxAt(2.1, 0.45, 0.3, x + 2.05, 3.5, z + 7.85), new THREE.Color(0x7a1418));
  for (const dx of [-3.05, 3.05]) {
    for (const dz of [-4.9, 4.7]) push(wheelAt(1.4, 0.95, x + dx, 1.4, z + dz), tire);
  }
}

// 96-gal wheeled bin, blue body / black lid — parked beside the garage door
function addBin(x, z, props) {
  const blue = new THREE.Color(0x1d4f96);
  const push = (g, c) => { paint(g, c); props.push(g); };
  push(boxAt(2.2, 2.9, 2.4, x, 0.35, z), blue);
  push(boxAt(2.35, 0.28, 2.55, x, 3.2, z), new THREE.Color(0x16181c));
  for (const dx of [-0.95, 0.95]) push(wheelAt(0.35, 0.28, x + dx, 0.35, z + 0.95), new THREE.Color(0x111214));
}

// squat black path light: post + shade, geometry only (never a real light)
function addPathLight(x, z, y, props) {
  const dark = _c.setHex(0x1b1c1e);
  const p = cylAt(0.09, 0.09, 1.25, 6, x, y, z);
  paint(p, dark); props.push(p);
  const cap = cylAt(0.1, 0.42, 0.3, 8, x, y + 1.15, z);
  paint(cap, dark); props.push(cap);
}

// ------------------------------------------------------- measured landmarks
// Everything below is anchored to landmarks MEASURED off this shell GLB
// (2026-08-22) rather than guessed from the roof rect, which is what put the
// old front beds 5 ft out on the lawn. Method: a downward raycast grid at
// y=3.2 (above the terrain, below the first floor) for the ground, and
// horizontal +Z / -Z sweeps at 1 ft steps for the wall planes.
//
//   grade        2.13 ft over the house pad, 0.16 ft on the driveway strip and
//                everywhere past the pad. The pad's edges are 2 ft VERTICAL
//                faces in the GLB, and they are pale concrete like the rest of
//                it - grass banks and the slate course below clothe them.
//   site pad     x -6..46.5, z -74..50, plus the driveway strip x 22..46 out
//                to z 76. One unbroken pale slab in the GLB: the single
//                biggest error in the exterior was that the whole back yard
//                rendered as concrete.
//   porch        front edge z 40.6, x -7..20.3; deck top y 8.0; rail top 10.4
//   house front  z 29.5 (x -7..20)      garage front  z 29.8 (x 20.3..46.5)
//   block rear   z -24.5 (x -7..20)     wing rear     z -10.9 (x 21..48)
//   porch steps  x 12..19.5, projecting to z 44.5
//
// Re-expressed as offsets from the roof rect R (x -11.7..48, z -25.4..41.4) so
// they still travel if the shell is moved or rescaled.
function landmarks(R) {
  return {
    hi: 2.16, lo: 0.19,          // the two terrain levels, +0.03 to clear z-fight
    padW: R.x0 + 5.7,            // -6.0
    padE: R.x1 - 1.5,            // 46.5
    padF: R.z1 - 0.4,            // 41.0   front face of the raised pad
    apronF: R.z1 + 9.0,          // 50.4   front edge of the flat apron
    padN: R.z0 - 25.6,           // -51.0  rear edge of the raised pad
    yardN: R.z0 - 48.6,          // -74.0  rear edge of the site pad
    lowE: R.x1 - 21.5,           // 26.5   x where the raised pad drops at the rear
    houseF: R.z1 - 11.9,         // 29.5
    houseW: R.x0 + 2.7,          // -9.0
    blockE: R.x1 - 28.0,         // 20.0   east wall of the main block
    blockN: R.z0 + 0.9,          // -24.5
    wingN: R.z0 + 14.5,          // -10.9
    porchF: R.z1 - 0.8,          // 40.6
    porchW: R.x0 + 4.7,          // -7.0
    porchE: R.x1 - 27.7,         // 20.3
    porchY: 8.02,
    driveL: R.x1 - 27.2,         // 20.8
    driveR: R.x1 - 0.9,          // 47.1  runs to the pad's own east edge
    street: R.z1 + 34,           // 75.4
    stepW: R.x1 - 36.2,          // 11.8
    stepE: R.x1 - 28.3,          // 19.7
    stepF: R.z1 + 3.1,           // 44.5
  };
}

// Grass over the shell's pale site pad, at the two heights it actually has,
// with sloped banks clothing the 2 ft vertical faces between them. Everything
// the photographs show as lawn; only the driveway, the walk and the planting
// beds are left as hardscape, and those are drawn back on top.
function addGroundCover(L, lawns) {
  const g = (x0, z0, x1, z1, y) => lawns.push(slab(x0, z0, x1, z1, y));
  // --- ONE base sheet at the low grade, covering the whole site pad and 8 ft
  //     past every edge of it. Round 1 patched the pad region by region and
  //     left slivers of the GLB's pale slab showing wherever a patch stopped
  //     short: a 0.8 ft strip west of the driveway from z 54 to the street,
  //     the pad's east kerb at x 47.2 running the length of the back yard,
  //     and its rear edge at z -51. All three rendered as thin WHITE LINES
  //     lying on the lawn and read as leftover fence rails. (Probed with
  //     scratchpad/ext/probe.py: every one of them is Root_Node at y 0.16 -
  //     the shell, not our geometry.) The raised slabs below draw over this
  //     sheet where the ground really is 2 ft higher, so it costs one quad.
  //     It is also the only lawn geometry with enough vertices to carry the
  //     world-space mown-patch tint (see buildYard), so it runs 45 ft past
  //     the pad on every side: outside it the 1200 ft disc takes over and
  //     that IS one flat plate.
  g(L.padW - 45, L.yardN - 45, L.padE + 45, L.street + 30, L.lo);
  // --- back yard: the big one. All of this was bare concrete before.
  g(L.padW, -31, L.padE, L.wingN, L.hi);                  // raised, full width
  g(L.padW, L.padN, L.lowE, -31, L.hi);                   // raised, west half
  g(L.lowE, L.padN, L.padE, -31, L.lo);                   // dropped, east half
  g(L.padW, L.yardN, L.padE, L.padN, L.lo);               // beyond the pad
  // banks over the pad's 2 ft vertical faces
  lawns.push(quadAt([L.lowE, L.hi, -32.4], [L.lowE, L.hi, L.padN],
                    [L.lowE + 2.6, L.lo, L.padN], [L.lowE + 2.6, L.lo, -32.4]));
  lawns.push(quadAt([L.padW, L.hi, L.padN], [L.lowE, L.hi, L.padN],
                    [L.lowE, L.lo, L.padN - 2.6], [L.padW, L.lo, L.padN - 2.6]));
  lawns.push(quadAt([L.lowE, L.lo, -32.4], [L.padE, L.lo, -32.4],
                    [L.padE, L.hi, -30.6], [L.lowE, L.hi, -30.6]));
  // --- side yards, west and east of the house
  g(L.padW, L.wingN, L.houseW, L.houseF, L.hi);
  g(L.driveL - 0.4, L.wingN, L.padE, L.houseF - 0.2, L.lo);
  // --- front: the apron in front of the porch, west of the driveway. Runs
  //     PAST the pad's own front edge and all the way to the street, so no
  //     sliver of the GLB's slab is left to read as a kerb across the lawn.
  g(L.padW - 9, L.padF, L.driveL + 0.4, L.street + 4, L.lo);
  g(L.driveR - 0.4, L.houseF - 1, L.padE + 9, L.street + 4, L.lo);
  g(L.porchE, L.houseF, L.driveL, L.padF, L.hi);
  // the pad's east kerb, clothed as a bank rather than left as a white line
  lawns.push(quadAt([L.padE, L.hi, L.wingN], [L.padE, L.hi, -31],
                    [L.padE + 2.4, L.lo, -31], [L.padE + 2.4, L.lo, L.wingN]));
  lawns.push(quadAt([L.padW, L.hi, L.padF], [L.driveL, L.hi, L.padF],
                    [L.driveL, L.lo, L.padF + 2.2], [L.padW, L.lo, L.padF + 2.2]));
}

function addFrontYard(L, rng, leaves, beds, props, lawns, trunks, masses) {
  // 1. Driveway and the walk to the porch steps, scored with control joints.
  //    ("Front of the house.jpg": one longitudinal joint down the middle and
  //    transverse ones roughly every 12 ft.) The concrete itself PASSED round
  //    1 on every number (render |dx| 4.71 / |dy| 6.91 against the photo's
  //    3.62 / 4.10, joints correct, 27.4 ft wide against ~29) — do not
  //    retune it. The only change is that the west edge now starts at 20.0
  //    instead of 20.8, because the shell's own pale driveway strip runs to
  //    x 20.0 and the 0.8 ft of it left uncovered rendered as a white
  //    6-inch border band down the side of the slab (probed: Root_Node,
  //    y 0.16, x 20.0-20.8, z 54-76 — the shell showing through, not an
  //    outline we drew).
  const joints = [];
  for (let z = L.houseF + 12; z < L.street; z += 12.5) {
    joints.push([L.driveL, z, L.driveR - L.driveL, 0.16]);
  }
  joints.push([(L.driveL + L.driveR) / 2 - 0.08, L.houseF, 0.16, L.street - L.houseF]);
  addConcrete(L.driveL, L.houseF, L.driveR, L.street - 7.6, L.lo + 0.02, joints, beds);
  addConcrete(L.stepW - 0.6, L.padF + 0.4, L.driveL + 0.2, L.stepF + 1.6,
              L.lo + 0.03, [], beds);

  // 2. Where the lot ends: sidewalk, verge, curb, carriageway, apron, mailbox.
  addStreet(L, rng, beds, props);

  // 3. The slate retaining course. The shell pad's front face is a bare 2 ft
  //    white cliff running the width of the house; in the photographs it is a
  //    dry-stacked thin-slab stone wall, which is also what holds the front
  //    bed up. The same wall turns the west corner.
  addSlate(rng, 'x', L.houseW - 1.2, L.stepW - 0.9, L.padF + 0.1, L.lo, L.hi + 0.1, beds);
  addSlate(rng, 'z', L.wingN + 6, L.padF, L.houseW - 1.1, L.lo, L.hi + 0.1, beds);

  // 4. THE WEST PLANTING, as ONE CONTINUOUS SWEEP.
  //
  //    Round 1 built this as a rectangle with a single straight dark edge
  //    board on its front face, plus a DETACHED 10 x 10.5 ft island bed with
  //    a lamp post stranded in open lawn at x 10.4-20.5, z 52.8-63.3. No
  //    photograph has either. "Front of the house.jpg" and "Frontyard v3 3"
  //    both show one bed running from the porch's west return, round the
  //    front of the raised pad, and then down the whole west edge of the
  //    driveway to the street as a rock border. It is edged in dry-stacked
  //    SCALLOPED stone where it retains the raised lawn (which is also what
  //    "Side of the house Outside.jpg" and "Frontyard v3 2" show) and simply
  //    runs rock-to-lawn where it is flat.
  const bedF0 = L.padF + 0.5, bedF1 = L.padF + 6.6;
  addBed(rng, L.houseW - 1.4, bedF0, L.stepW - 0.8, bedF1, L.lo + 0.05, beds,
         BED_DENSITY, false);
  // the border carrying on down the drive, in three overlapping runs so the
  // outer line steps in toward the drive instead of running dead straight
  addBed(rng, L.driveL - 6.4, bedF1 - 2.2, L.driveL, L.apronF + 3, L.lo + 0.045, beds,
         BED_DENSITY, false);
  addBed(rng, L.driveL - 4.8, L.apronF + 3, L.driveL, L.street - 12, L.lo + 0.045, beds,
         BED_DENSITY, false);
  addBed(rng, L.driveL - 3.4, L.street - 15, L.driveL, L.street - 12.2, L.lo + 0.045, beds,
         BED_DENSITY, false);
  // ONE scalloped stone edge tracing the whole outer line of the sweep
  addStoneEdge(rng, [
    [L.houseW - 1.6, bedF0 - 0.6], [L.houseW - 1.7, bedF1 - 1.2],
    [L.houseW + 3.0, bedF1 + 0.15], [L.stepW - 6.0, bedF1 + 0.25],
    [L.stepW - 0.9, bedF1 - 0.9],
  ], L.lo, 0.62, beds);
  addStoneEdge(rng, [
    [L.driveL - 6.5, bedF1 - 2.0], [L.driveL - 6.6, L.apronF + 3],
    [L.driveL - 4.9, L.apronF + 3.2], [L.driveL - 3.5, L.street - 15],
    [L.driveL - 3.4, L.street - 12.2],
  ], L.lo, 0.44, beds);

  // A mixed row, not nine copies of one boxwood ball: four species, sizes
  // from 0.9 to 2.1 ft, and a salvia drift in front of them.
  const SP = ['boxwood', 'boxwood', 'euonymus', 'juniper', 'yew'];
  for (let x = L.houseW - 0.6; x < L.stepW - 1.4; x += 1.55 + rng() * 0.85) {
    addBoxwood(rng, x, bedF0 + 1.2 + rng() * 1.5, 0.9 + rng() * 1.2, L.lo + 0.05,
               leaves, SP[Math.floor(rng() * SP.length)]);
  }
  for (let x = L.houseW + 1.5; x < L.stepW - 2.6; x += 3.4 + rng() * 2.4) {
    addPerennial(rng, x, bedF1 - 1.4 - rng() * 0.9, L.lo + 0.05, leaves,
                 4 + Math.floor(rng() * 4), 2.6);
  }
  // and along the drive border: low junipers and groundcover, as photographed
  for (let z = bedF1; z < L.street - 14; z += 4.6 + rng() * 3.4) {
    addBoxwood(rng, L.driveL - 3.6 - rng() * 2.0, z, 0.85 + rng() * 0.8,
               L.lo + 0.045, leaves, 'juniper');
  }
  addFlagstones(rng, [[L.stepW - 2.2, bedF1 - 0.7], [L.stepW - 3.4, bedF1 - 2.1],
                      [L.stepW - 2.0, bedF1 - 3.4], [L.stepW - 3.2, bedF1 - 4.7]],
                L.lo + 0.06, beds);
  // the two cast geese, west of the porch steps
  addGoose(rng, L.stepW - 6.4, bedF1 - 1.4, L.lo + 0.05, 0.5, props);
  addGoose(rng, L.stepW - 5.5, bedF1 - 1.9, L.lo + 0.05, 0.9, props);

  // 5. The EAST bed: the rock border down the far side of the drive, running
  //    the whole way to the street, with the salvia mass, the low hedge
  //    behind it and the small tree of "Front of the house.jpg" x 1230-1560.
  addBed(rng, L.driveR + 0.6, L.houseF + 4, L.driveR + 10.5, L.street - 19,
         L.lo + 0.04, beds, BED_DENSITY, false);
  addStoneEdge(rng, [[L.driveR + 10.8, L.houseF + 4], [L.driveR + 11.0, L.apronF],
                     [L.driveR + 10.4, L.street - 19]], L.lo, 0.40, beds);
  for (let z = L.houseF + 6; z < L.street - 21; z += 3.0 + rng() * 1.8) {
    const x = L.driveR + 3.0 + rng() * 6.0;
    if (rng() < 0.6) {
      addBoxwood(rng, x, z, 0.95 + rng() * 1.0, L.lo + 0.04, leaves,
                 SP[Math.floor(rng() * SP.length)]);
    } else {
      addPerennial(rng, x, z, L.lo + 0.04, leaves, 4 + Math.floor(rng() * 3), 2.4);
    }
  }
  addShadeTree(rng, L.driveR + 8.5, L.apronF - 3, 0.62, trunks, leaves);
  addPathLight(L.driveR + 1.4, L.houseF + 9, L.lo + 0.04, props);
  addPathLight(L.driveR + 2.0, L.houseF + 19, L.lo + 0.04, props);
  addPathLight(L.driveR + 1.8, L.apronF + 6, L.lo + 0.04, props);
  addPathLight(L.stepW - 5.0, bedF1 - 0.8, L.lo + 0.05, props);

  // 6. The lamp-post bed, at the street end and EAST of the drive, between
  //    the drive and the sidewalk — which is where "Front of the house, a
  //    little bit of the garage and car pointing to a different house.jpg"
  //    puts it: a black lantern on a slim post standing in a sheet of green
  //    groundcover with ornamental grasses behind, edged in river rock.
  //    (Round 2's critic said this bed appears in no photograph; that
  //    photograph is the evidence it does — what was wrong was its SITE.)
  addBed(rng, L.driveR + 1.2, L.street - 19, L.driveR + 12.5, L.street - 8.0,
         L.lo + 0.03, beds, BED_DENSITY, false);
  addStoneEdge(rng, [[L.driveR + 12.7, L.street - 19], [L.driveR + 12.2, L.street - 13],
                     [L.driveR + 11.4, L.street - 8.2]], L.lo, 0.38, beds);
  addGroundCoverMass(rng, L.driveR + 7.4, L.street - 12.5, 4.6, 3.0, L.lo + 0.03, leaves);
  const lx = L.driveR + 5.0, lz = L.street - 12.2;
  const post = cylAt(0.12, 0.16, 6.2, 8, lx, L.lo, lz);
  paint(post, _c.setHex(0x191a1c)); props.push(post);
  const lamp = boxAt(0.8, 1.1, 0.8, lx, L.lo + 6.2, lz);
  paint(lamp, _c.setHex(0xd8cda4)); props.push(lamp);
  const lcap = cylAt(0.02, 0.62, 0.42, 4, lx, L.lo + 7.3, lz);
  paint(lcap, _c.setHex(0x191a1c)); props.push(lcap);
  for (let i = 0; i < 5; i++) {
    addGrassClump(rng, L.driveR + 3.0 + rng() * 7.0, L.street - 18 + rng() * 4.5,
                  L.lo + 0.03, leaves);
  }

  // 7. Vehicles and hardware. The bin is BLUE with a black lid - the v3 front
  //    shots were taken at dusk and it reads black there, but "Side of the
  //    house.jpg" shows it in daylight against the garage flank.
  addCar((L.driveL + L.driveR) / 2 - 1.4, L.houseF + 13, props);
  addBin(L.driveR - 1.4, L.houseF + 1.9, props);
  // black urns standing against the wall where the porch meets the garage
  for (const [ux, uz] of [[L.porchE + 0.9, L.houseF + 1.4], [L.driveL + 1.1, L.houseF + 1.4]]) {
    const urn = cylAt(0.85, 0.55, 1.25, 10, ux, L.lo, uz);
    paint(urn, _c.setHex(0x24252a)); props.push(urn);
  }

  // 8. Framing trees. The front photograph is framed top-left and top-right by
  //    mature canopies overhanging the drive; without them the house reads as
  //    standing in an open field.
  // This one also stands over the Sketchup scale FIGURE baked into the shell's
  // merged Root_Node mesh at x -16.5, z 44.7 — it cannot be hidden separately.
  addShadeTree(rng, L.driveL - 37, L.apronF - 5.6, 1.8, trunks, leaves);
  addShadeTree(rng, L.driveR + 22, L.apronF + 2, 1.35, trunks, leaves);
  addShadeTree(rng, L.driveR + 26, L.houseF + 4, 1.2, trunks, leaves);

  // 9. The neighbouring house at the west, two garage doors facing the street
  addNeighbour(L.driveL - 78, L.houseF + 7, 26, 30, 18, 0, 2, masses, rng);
  // and two more across the street, so the lot reads as one of a row
  addNeighbour(L.driveL - 46, L.street + 52, 24, 28, 17, 0, 0, masses, rng);
  addNeighbour(L.driveR + 26, L.street + 56, 26, 28, 18, 0, 0, masses, rng);

  // 10. Woodland across the far side of the street. Both yards' fly-to poses
  //    look straight past the house at open horizon otherwise, which reads as
  //    a model on a putting green; every photograph is closed off by trees.
  //    Planted past z = 108 so neither exterior camera (z 97 front, z -78 back)
  //    ever stands inside one.
  for (let x = L.driveL - 130; x < L.driveR + 110; x += 11 + rng() * 9) {
    addShadeTree(rng, x, L.street + 34 + rng() * 22, 1.0 + rng() * 0.6,
                 trunks, leaves);
  }
}

// The back yard had nothing but the generic treeline: the shell GLB models the
// rear elevation and a ground-level terrace with a white fence, and everything
// else in "Backyard v3 5/7/9" - the lawn, the rock beds that edge it, the big
// free-standing clipped mounds, the grasses, the stepping stones - was missing.
// (The raised composite deck and its furniture are placed objects on room 3,
// not built here: they are discrete pieces the owner can move.)
function addBackYard(L, rng, leaves, beds, props, lawns, trunks, masses) {
  const yN = L.padN;            // where the raised lawn ends
  // The deck (a placed object on room 3) occupies world x 2.7..29.9,
  // z -44.5..-24.3. Nothing below may grow inside it. The deck's NORTH stair
  // lands at x 10.3..14.9, z -42..-45 — round 1 planted a 4.8 ft mound over
  // the head of it (visible in back_cut3.png at 430-570, 700-800); nothing
  // below may grow there either.
  // 1. Rock beds edging the lawn. NARROW: the photographs are lawn-dominated
  //    with the rock confined to a border at the foot of the treeline and one
  //    wider apron beside the deck steps.
  addBed(rng, L.padW - 2, yN - 6.5, L.padE + 2, yN - 1.5, L.lo + 0.04, beds, 4.4);
  addBed(rng, L.padW - 1.5, -46, L.padW + 3.0, L.wingN - 6, L.hi + 0.04, beds, 4.4);
  addBed(rng, L.padE - 7.5, -47, L.padE + 2, -28, L.lo + 0.04, beds, 4.4);
  // stepping stones running away from the deck's east flight, as in the aerial
  addFlagstones(rng, [[L.padE - 5.5, -33], [L.padE - 4.4, -35.4], [L.padE - 5.4, -37.8],
                      [L.padE - 4.2, -40.2], [L.padE - 5.3, -42.6]], L.lo + 0.06, beds);

  // 2. The big clipped specimens standing free on the lawn. "Backyard v3 7"'s
  //    foreground alone carries five large MIXED mounds, a weeping specimen,
  //    four grass clumps and a bird feeder, so this is a mixed group, not a
  //    row of one dome repeated: different species, different squashes, two
  //    weeping specimens and the photinia as a full sphere.
  addMound(rng, L.padW + 3.5, L.blockN - 6, 4.2, L.hi, 'green', leaves);
  addMound(rng, L.padW + 2, L.blockN - 22, 3.4, L.hi, 'dark', leaves);
  addMound(rng, L.padW + 13, -50, 3.8, L.hi, 'olive', leaves);
  addMound(rng, L.padW + 8.5, -47.5, 2.6, L.hi, 'grey', leaves, true);
  // The big specimen beyond the deck rail (v3 9 x 1000-1075, v3 5 x 740-960):
  // an olive-green SPHERE about 9 ft each way with red new growth on its
  // sunlit tips. Round 1 built a 12 x 4 ft burgundy pancake here and its
  // comment said it was "sized and sited to also swallow the shell GLB's
  // leftover parasol RIBS" — the ribs went with the SHELL_CUTS in house.js,
  // so that job no longer exists and this is authored purely to the photograph.
  addPhotinia(rng, L.padE - 11.5, -36.5, 4.6, L.lo, leaves);
  addMound(rng, L.lowE + 9, -25, 3.0, L.hi, 'grey', leaves);
  addMound(rng, L.padE - 4, -45, 3.2, L.lo, 'dark', leaves);
  addMound(rng, L.padE - 8, -39.5, 4.4, L.lo, 'green', leaves, true);
  addMound(rng, L.padE - 15.5, -47.5, 4.2, L.lo, 'olive', leaves);
  // the weeping specimen standing free on the lawn in v3 7
  addWeeper(rng, L.padE - 17, -30, 0.95, trunks, leaves);
  addWeeper(rng, L.padW + 17, -54, 0.8, trunks, leaves);
  addFeeder(rng, L.padE - 3.0, -50.5, L.lo, props);

  // 3. Ornamental grasses and low shrubs along the bed edges
  for (let x = L.padW; x < L.padE; x += 3.4 + rng() * 3.2) {
    addGrassClump(rng, x, yN - 4.5 + (rng() - 0.5) * 3, L.lo + 0.04, leaves);
  }
  for (let z = -46; z < L.wingN - 7; z += 3.6 + rng() * 3) {
    if (rng() < 0.6) addGrassClump(rng, L.padW + 0.8 + rng() * 1.6, z, L.hi + 0.04, leaves);
    else addBoxwood(rng, L.padW + 1.0 + rng() * 1.6, z, 1.1 + rng() * 0.9, L.hi + 0.04,
                    leaves, rng() < 0.5 ? 'juniper' : 'yew');
  }
  for (let z = -46; z < -29; z += 3 + rng() * 2.4) {
    addGrassClump(rng, L.padE - 1.2 - rng() * 4, z, L.lo + 0.04, leaves);
  }

  // 4. Dense mature treeline round the boundary. This is now the loudest thing
  //    in the back-yard view: with the shell's rear boundary fence cut (it was
  //    a closed rectangle enclosing the whole lot, in no photograph), the yard
  //    ran flat green to a razor-straight horizon with nothing on it. "Backyard
  //    v3 5" and "v3 7" show woodland filling the ENTIRE boundary above roof
  //    height and closing right down to the grass.
  //
  //    Planted ON the lot lines (past the site pad's own edges), not just
  //    outside the lawn: the app's exterior fly-to for this yard stands the
  //    camera at (-18.5, -77.9), and a treeline hugging the lawn edge put a
  //    30 ft canopy over the lens. TWO ranks at the rear, at 4.5 ft spacing
  //    and jittered in both axes — a single evenly spaced rank reads as a
  //    fence of trees, which is the same defect the fence had.
  // KEEP-OUT: the exterior fly-to cameras stand at (47.1, 97.2) front and
  // (-18.5, -77.9) back, both at y 34 — inside canopy height. A 33 ft shade
  // tree has a ~12 ft crown, so anything planted within ~22 ft of either
  // ground point puts leaves over the lens. Round 1 hit this once and moved
  // the rank back; a denser rank hit it again from a different direction, so
  // it is a guard now rather than a hand-picked offset.
  const CAMS = [[47.1, 97.2], [-18.5, -77.9]];
  const clear = (x, z) => CAMS.every(
    ([cx, cz]) => Math.hypot(x - cx, z - cz) > 22);
  const bigTree = (x, z, sc) => {
    if (clear(x, z)) addShadeTree(rng, x, z, sc, trunks, leaves);
  };
  for (let x = L.padW - 40; x < L.padE + 42; x += 4.5 + rng() * 4) {
    bigTree(x + (rng() - 0.5) * 5, L.yardN - 10 - rng() * 12,
            0.95 + rng() * 0.7);
  }
  for (let x = L.padW - 44; x < L.padE + 46; x += 7 + rng() * 6) {
    bigTree(x + (rng() - 0.5) * 6, L.yardN - 24 - rng() * 18, 1.1 + rng() * 0.8);
  }
  for (let z = L.yardN + 2; z < L.wingN - 4; z += 5 + rng() * 4) {
    bigTree(L.padW - 22 - rng() * 16, z + (rng() - 0.5) * 4, 0.95 + rng() * 0.6);
  }
  for (let z = L.yardN + 4; z < -18; z += 5 + rng() * 4) {
    bigTree(L.padE + 13 + rng() * 16, z + (rng() - 0.5) * 4, 0.9 + rng() * 0.6);
  }
  // a few smaller flowering trees inside the line, as in v3 5's left edge
  for (let i = 0; i < 4; i++) {
    const wx = L.padW - 8 + rng() * (L.padE - L.padW + 16);
    const wz = L.yardN + 3 + rng() * 6;
    if (clear(wx, wz)) addWeeper(rng, wx, wz, 0.7 + rng() * 0.35, trunks, leaves);
  }

  // 4b. Understory. Without it the treeline is bare trunks over open lawn and
  //     the boundary reads as a park; every back photograph has a dense mass of
  //     shrub and small tree under the canopy right down to the grass.
  const KINDS = ['green', 'dark', 'olive', 'green', 'grey'];
  const K = () => KINDS[Math.floor(rng() * KINDS.length)];
  const mound = (x, z, r, y) => {
    if (clear(x, z)) addMound(rng, x, z, r, y, K(), leaves);
  };
  for (let x = L.padW - 40; x < L.padE + 42; x += 2.6 + rng() * 3) {
    mound(x + (rng() - 0.5) * 3, L.yardN - 5 - rng() * 11, 2.6 + rng() * 3.0, L.lo);
  }
  for (let z = L.yardN + 2; z < L.wingN; z += 3.2 + rng() * 3) {
    mound(L.padW - 11 - rng() * 12, z, 2.6 + rng() * 2.6, L.hi);
    mound(L.padE + 8 + rng() * 12, z, 2.6 + rng() * 2.6, L.lo);
  }

  // 5. Neighbouring houses. "Backyard v3 7" has THREE rooflines across the
  //    boundary — a cream one hard left, a white gabled one centre-right and
  //    a third beyond it — all showing above the treeline. One massing each
  //    side left the middle of the horizon empty.
  addNeighbour(L.padW - 50, L.blockN - 14, 26, 28, 17, 0, 0, masses, rng);
  addNeighbour(L.padE + 44, L.blockN - 18, 26, 28, 17, 0, 0, masses, rng);
  addNeighbour(L.padW + 4, L.yardN - 30, 28, 30, 19, 0, 0, masses, rng);
  addNeighbour(L.padE - 22, L.yardN - 44, 26, 28, 18, 0, 0, masses, rng);
  addNeighbour(L.padW - 44, L.yardN - 36, 24, 26, 16, 0, 0, masses, rng);
}

// The shell GLB ships an outdoor lounge set — a brown sofa, two armchairs, an
// ottoman and an OPEN cream parasol — standing on a ground-level terrace about
// 20 ft off the back of the house. Every rear photograph disagrees with it:
// the real furniture is white/grey wicker, the parasol is a CLOSED cantilever
// on a black mast, and all of it stands on a raised composite deck attached to
// the rear wall. That deck and its furniture are placed as objects on room 3,
// so leaving the GLB's set visible would put two lounge sets in the back yard.
//
// Hidden by BOUNDING BOX rather than by mesh name, because the names in this
// GLB are Sketchup component ids ("sofa+go+do", "106341") that a re-export
// would change: any shell mesh that lies wholly inside the terrace rectangle
// and is under 10 ft tall is furniture. Nine meshes match, and none of them is
// siding, roof or terrain — the terrace slab and the rear elevation stay.
// Set HIDE_TERRACE_PROPS to null to restore them.
//
// (Round 1's comment here and at the photinia said "the fence stays". It does
// not any more: house.js `SHELL_CUTS` now deletes the shell's rear boundary
// fence outright — it was a closed rectangle enclosing the whole rear lot and
// appears in no photograph — along with the leftover parasol frame and the
// SketchUp edge overlay. Nothing in this file masks either of those now.)
const HIDE_TERRACE_PROPS = { x0: 27, x1: 48, z0: -52, z1: -32, maxH: 11 };
const _hidBox = new THREE.Box3();
function hideShellPatioProps() {
  const shell = getShellRoot();
  if (!shell || !HIDE_TERRACE_PROPS) return;
  const B = HIDE_TERRACE_PROPS;
  shell.updateWorldMatrix(true, true);
  shell.traverse((o) => {
    if (!o.isMesh) return;
    _hidBox.setFromObject(o);
    const cx = (_hidBox.min.x + _hidBox.max.x) / 2;
    const cz = (_hidBox.min.z + _hidBox.max.z) / 2;
    if (cx >= B.x0 && cx <= B.x1 && cz >= B.z0 && cz <= B.z1
        && _hidBox.max.x - _hidBox.min.x <= 24
        && _hidBox.max.z - _hidBox.min.z <= 24
        && _hidBox.max.y - _hidBox.min.y <= B.maxH) {
      o.visible = false;
    }
  });
}

// Rebuild the trees/bushes/shadow around the house. Placement mirrors the
// real property's satellite view: a thick treeline down the west property
// line, a treeline across the back, shade trees behind the deck, a
// landscaped mound at the back-right, open lawn to the east, and shrub beds
// at the house front + driveway entrance. Scene front/street = +Z, garage on
// the +X side. Called at boot and after every reloadHouse.
export function setEnvironmentData(house) {
  lastHouse = house;
  const shell = getShellRoot();
  shellRect = shell ? rectOfShell(shell) : null;
  roofRect = shell ? rectOfRoof() : null;
  buildYard();
}

function buildYard() {
  const house = lastHouse;
  // building bbox excludes outdoor pseudo-rooms (Frontyard/Backyard = porch
  // and deck rects) — plants anchor to the building but must dodge every pad
  let minX = Infinity, minZ = Infinity, maxX = -Infinity, maxZ = -Infinity;
  const pads = []; // every room rect (incl. outdoor) — nothing grows on one
  let garage = null;
  for (const floor of house?.floors || []) {
    for (const room of floor.rooms || []) {
      const fp = room.footprint;
      pads.push({ x0: fp.x, z0: fp.z, x1: fp.x + fp.width, z1: fp.z + fp.depth });
      if (!garage && /garage/i.test(room.name || '')) garage = fp;
      if (isOutdoorRoom(room.name)) continue;
      minX = Math.min(minX, fp.x);
      minZ = Math.min(minZ, fp.z);
      maxX = Math.max(maxX, fp.x + fp.width);
      maxZ = Math.max(maxZ, fp.z + fp.depth);
    }
  }
  if (!Number.isFinite(minX)) { minX = 0; minZ = 0; maxX = 26; maxZ = 26; }
  center = { x: (minX + maxX) / 2, z: (minZ + maxZ) / 2 };

  // the shell GLB's measured footprint wins over the traced room rects —
  // trees anchor to what the eye sees, and nothing may grow inside it
  if (shellRect) pads.push(shellRect);
  const bx0 = shellRect ? shellRect.x0 : minX;
  const bz0 = shellRect ? shellRect.z0 : minZ;
  const bx1 = shellRect ? shellRect.x1 : maxX;
  const bz1 = shellRect ? shellRect.z1 : maxZ;

  if (yard) {
    root.remove(yard);
    yard.traverse((o) => {
      if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); }
    });
    yardGrassMats.length = 0; // those materials were just disposed with the yard
  }
  yard = new THREE.Group();
  root.add(yard);

  const rng = mulberry32(1337);
  const trunks = [], leaves = [], beds = [], props = [], lawns = [], masses = [];
  const onPad = (x, z, m = 3) =>
    pads.some((p) => x > p.x0 - m && x < p.x1 + m && z > p.z0 - m && z < p.z1 + m);
  // frontmost pad edge at this x — puts foundation beds in front of the porch
  const frontZ = (x) => pads.reduce(
    (m, p) => (x >= p.x0 && x <= p.x1 ? Math.max(m, p.z1) : m), -Infinity);
  // No conifers in the FRONT half of the lot. Round 1 stood one in the middle
  // of the front lawn (z ~45, west line) and it appears in no front
  // photograph — every tree between this house and the street is a broad
  // deciduous canopy. The back boundary does carry conifers ("Backyard v3 5",
  // bottom left), so the species stays, it is just kept behind the house.
  const tree = (x, z, s) => {
    if (onPad(x, z, 4)) return;
    (z < -8 && rng() < 0.28 ? addConifer : addDeciduous)(rng, x, z, s, trunks, leaves);
  };

  // west property line: dense tree/hedge row from front to back
  for (let z = bz0 - 15; z <= bz1 + 18; z += 10 + rng() * 6) {
    tree(bx0 - 10 - rng() * 9, z, 0.9 + rng() * 0.8);
  }
  // treeline across the back of the lot
  for (let x = bx0 - 40; x <= bx1 + 55; x += 13 + rng() * 8) {
    tree(x, bz0 - 25 - rng() * 20, 0.9 + rng() * 0.9);
  }
  // two shade trees just behind the house, beside the deck
  tree(bx1 - 18, bz0 - 8, 1.05);
  tree(bx1 - 2, bz0 - 13, 0.85);
  // landscaped mound at the back-right corner: bush cluster + a small tree
  tree(bx1 + 20, bz0 - 18, 0.7);
  for (let i = 0; i < 5; i++) {
    addBush(rng, bx1 + 14 + rng() * 16, bz0 - 8 - rng() * 14, leaves);
  }
  // east side stays open lawn — just a few shrubs along the property edge
  for (let i = 0; i < 4; i++) {
    addBush(rng, bx1 + 20 + rng() * 10, bz0 + 20 + rng() * (bz1 - bz0 - 30), leaves);
  }

  // Shrub cluster at the driveway entrance, EAST side only. The west side of
  // the front lawn is open mown grass in every front photograph, and round 1's
  // loose bushes there were stranded in the middle of it once the phantom
  // island bed was removed.
  const dLeft = garage ? garage.x : center.x - 8;
  const dRight = garage ? garage.x + garage.width : center.x + 8;
  for (let i = 0; i < 3; i++) {
    addBush(rng, dRight + 4 + rng() * 6, bz1 + 8 + rng() * 8, leaves);
  }

  // foundation beds only when the generated geometry is the visible house —
  // with a shell GLB the traced rects don't line up with its real walls
  if (!shellRect) {
    for (let x = minX + 2; x <= dLeft - 3; x += 4.5 + rng() * 3.5) {
      const fz = frontZ(x);
      if (Number.isFinite(fz) && rng() < 0.85) {
        addBush(rng, x + rng() - 0.5, fz + 2 + rng() * 1.5, leaves);
      }
    }
    for (let z = minZ + 4; z <= maxZ - 6; z += 7 + rng() * 5) {
      if (rng() < 0.6) addBush(rng, minX - 2.5 - rng() * 1.5, z, leaves);
    }
  }

  // Everything the shell GLB leaves out, front and back: the lawn that covers
  // its pale site pad, the driveway, the planting beds, the SUV, the bin, the
  // slate retaining course, the deck-side planting and the neighbours (see
  // landmarks/addGroundCover/addFrontYard/addBackYard). Anchored to the shell's
  // roof outline, so it only runs when a shell is loaded — the
  // generated-geometry fallback keeps its own bushes above.
  if (roofRect) {
    const L = landmarks(roofRect);
    addGroundCover(L, lawns);
    addFrontYard(L, rng, leaves, beds, props, lawns, trunks, masses);
    addBackYard(L, rng, leaves, beds, props, lawns, trunks, masses);
    hideShellPatioProps();
  }

  // mergeGeometries refuses to mix indexed (cylinder/cone) with non-indexed
  // (icosahedron) geometry — normalize everything to non-indexed first
  const flat = (geos) => geos.map((g) => (g.index ? g.toNonIndexed() : g));
  if (lawns.length) {
    // own material (not grassMat) because the yard disposes its materials on
    // rebuild; registered so weather.js's wet/snow tint still reaches it
    const mat = new THREE.MeshStandardMaterial({
      color: grassMat.color.clone(), map: grassMat.map, roughness: 1,
      vertexColors: true });
    yardGrassMats.push(mat);
    const geo = BufferGeometryUtils.mergeGeometries(flat(lawns), false);
    // re-derive UVs from world position exactly as the 1200-radius grass disc
    // does, so the shared speckle map keeps the same scale across the seam
    const pos = geo.attributes.position, uv = geo.attributes.uv;
    // ...and the large-scale mown patchiness the tile is not allowed to carry.
    // Three octaves at 54 / 19 / 7 ft, sampled in WORLD feet — so it never
    // repeats, and it interpolates smoothly across slab()'s 2 ft cells. The
    // photographed lawn carries heavy broad tonal banding from mowing
    // direction and tree shade; without this the render is one flat plate at
    // any distance where the 8.6 ft tile has mipped away.
    const col = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i);
      uv.setXY(i, x / 2400 + 0.5, -z / 2400 + 0.5);
      const f = 1 + (worldNoise(x, z, 54) - 0.5) * 0.17
                  + (worldNoise(x + 313, z + 129, 19) - 0.5) * 0.22
                  + (worldNoise(x + 91, z - 47, 7) - 0.5) * 0.13;
      col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = f;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    uv.needsUpdate = true;
    const lawn = new THREE.Mesh(geo, mat);
    lawn.receiveShadow = true;
    yard.add(lawn);
  }
  if (beds.length) {
    // Fine grain on the hardscape. Vertex colours alone gave the driveway
    // sd 3.7 / mean|Δ| 0.30 against the photograph's 10.8 / 6.3 — the right
    // average value and no texture at all at the scale the eye reads, which is
    // the "sd is scale-blind" trap. A near-white 4 ft noise tile multiplies
    // into the same vertex colours and costs one 128px canvas for every bed,
    // wall and slab in both yards. UVs re-derived from world position (as the
    // lawn does) so the grain keeps ONE physical scale across slabs of very
    // different sizes.
    const geo = BufferGeometryUtils.mergeGeometries(flat(beds), false);
    const pos = geo.attributes.position, uv = geo.attributes.uv;
    for (let i = 0; i < pos.count; i++) {
      uv.setXY(i, pos.getX(i) / 6, -pos.getZ(i) / 6);
    }
    uv.needsUpdate = true;
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
      vertexColors: true, map: makeGritTexture(), roughness: 1, flatShading: true }));
    m.receiveShadow = true;
    yard.add(m);
  }
  if (props.length) {
    const m = new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(props), false),
      new THREE.MeshStandardMaterial({
        vertexColors: true, roughness: 0.45, metalness: 0.15, flatShading: true }));
    m.castShadow = true; // one extra caster — the car needs to sit on the drive
    yard.add(m);
  }
  if (masses.length) {
    // Background BUILDING massing (the neighbours), in its own bucket for one
    // reason: it must be matte and UNTEXTURED. Round 1 merged it into `beds`,
    // whose UVs are derived from world X/Z so a wall face can only sample one
    // line of the grit tile — every neighbour rendered with its texture
    // smeared vertically from eave to grade. `props`'s semi-gloss metal is
    // equally wrong for painted siding.
    const m = new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(masses), false),
      new THREE.MeshStandardMaterial({
        vertexColors: true, roughness: 0.9, metalness: 0.0, flatShading: true }));
    m.castShadow = true;
    yard.add(m);
  }
  if (trunks.length) {
    yard.add(new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(trunks), false),
      new THREE.MeshStandardMaterial({ color: 0x6d4c33, roughness: 1 })));
  }
  if (leaves.length) {
    yard.add(new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(leaves), false),
      new THREE.MeshStandardMaterial({
        vertexColors: true, roughness: 1, flatShading: true })));
  }

  // Soft contact-occlusion blob under the house: now that the shell casts a
  // real directional sun shadow (see scene.js), this stays subtle — it just
  // grounds the footprint at noon when the real shadow is short and underneath.
  const shadow = new THREE.Mesh(
    new THREE.PlaneGeometry((bx1 - bx0) * 1.4, (bz1 - bz0) * 1.4),
    new THREE.MeshBasicMaterial({
      map: makeShadowTexture(), color: 0x000000,
      transparent: true, opacity: 0.15, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set((bx0 + bx1) / 2, -0.03, (bz0 + bz1) / 2);
  yard.add(shadow);
}
