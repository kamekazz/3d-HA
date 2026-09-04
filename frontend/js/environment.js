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
import { getInstance } from './models.js';
import { renderer, getEnvIntensity, onFrame } from './scene.js';   // onFrame: the car's sky tick
import { getNightFactor } from './daylight.js';   // used by the car's applyCarSky

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
let applyYardVisibility = () => {};   // set by initEnvironment

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

// NO night floor on the lawn. The night exterior round tried an emissive
// floor here (a dim green-grey scaled by daylight.js's night factor) so the
// unlit lawn would not render as #000000, and the blind critic named it the
// single biggest tell in the frame: a flat, evenly lit green plane ending in
// a ruler-straight edge, brighter than the driveway — inverted from the
// photograph, where the lawn is simply not visible beyond the light pools.
// Night ground levels (drive, walk, lawn, pools) belong to the landscape
// lighting (eavelights.js), never to the ground's own material.

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
  // ...except while the Outside editor is open, which is the one time edit
  // mode needs to see the yard: it IS what is being edited.
  const applyVisibility = () => {
    root.visible = (inViewMode || yardEditing) && onHouseLevel;
  };
  applyYardVisibility = applyVisibility;
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
    if (lastHouse && remeasureShell()) buildYard();
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

// Re-read the two rects the whole yard is anchored to. Returns true when either
// actually moved, which is the caller's cue to rebuild -- the guard matters
// because a Box3 traversal of the shell is cheap but a yard rebuild is not.
function remeasureShell() {
  const shell = getShellRoot();
  const r = shell ? rectOfShell(shell) : null;
  const rr = shell ? rectOfRoof() : null;
  if (JSON.stringify(r) === JSON.stringify(shellRect)
      && JSON.stringify(rr) === JSON.stringify(roofRect)) return false;
  shellRect = r;
  roofRect = rr;
  return true;
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

// ---------------------------------------------------------------- owner flags
// Asked for on 2026-09-01: NO trees anywhere on the lot, and NO neighbouring
// houses on the horizon. Everything else in the yard — lawn, driveway, walks,
// beds, shrubs, clipped mounds, grasses, perennials, the bin, the geese, the
// path lights, the lamp post — stays exactly as it was.
//
// Flags rather than deleted call sites, for two reasons: every tree/neighbour
// call carries a comment recording which photograph put it there, and there
// are 14 tree call sites across three functions, so a guard at the four
// species entry points is the only edit that cannot miss one. The merged
// `trunks` and `masses` meshes then never get built at all (buildYard skips
// an empty bucket), so this costs nothing at runtime.
//
// Consequence worth knowing before flipping either back: the back-yard
// treeline was what closed off the horizon after house.js's SHELL_CUTS
// removed the shell's boundary fence, and the neighbour massing was what kept
// the skyline from reading as open field. With both off, the lot reads as
// isolated — which is what was asked for.
const PLANT_TREES = false;
const BUILD_NEIGHBOURS = false;

const _leaf = new THREE.Color();

function addDeciduous(rng, x, z, s, trunks, leaves) {
  if (!PLANT_TREES) return;
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
  if (!PLANT_TREES) return;
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
// `rmax` caps the tail: the default 0.40 gives the odd 11-inch stone the
// day photograph's east bed does have; the beds in the night frame pass
// ~0.2, since at 40 ft under the porch lights the big ones read as boulders.
function addBed(rng, x0, z0, x1, z1, y, beds, dens = BED_DENSITY, edge = true, rmax = 0.40) {
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
    const r = 0.075 + (t * t * t) * rmax;
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

// The same coarse rim along an arbitrary world polyline — the lawn-side edge
// of a polygon bed (addBedPoly) is not axis-aligned.
function addCobbleRun(rng, pts, y, beds, sc = 1) {
  for (let k = 0; k < pts.length - 1; k++) {
    const [ax, az] = pts[k], [bx, bz] = pts[k + 1];
    const L = Math.hypot(bx - ax, bz - az);
    const n = Math.max(1, Math.round(L / (0.62 * sc)));
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      const r = (0.28 + rng() * 0.24) * sc;
      const s = new THREE.IcosahedronGeometry(r, 0);
      s.scale(1.15, 0.62, 1.15);
      s.translate(ax + (bx - ax) * t + (rng() - 0.5) * 0.35, y + r * 0.2,
                  az + (bz - az) * t + (rng() - 0.5) * 0.35);
      paint(s, hsl(0.58, 0.05, 0.34 + rng() * 0.22));
      beds.push(s);
    }
  }
}

// A rock bed with a POLYGON footprint. Round 2 recorded "beds are still
// composed of rectangles; environment.js has no polygon bed primitive" as an
// open item, and the night photograph (demo/exterior_night.jpg) is where it
// bites: the river-rock strip west of the driveway is a tapering wedge that
// follows the concrete walk's diagonal edge, and three overlapping rectangles
// either left grey slab showing at the corners or pushed cobbles out onto
// the concrete. `pts` is a world polygon [[x,z],...], any winding. The gravel
// base is a ShapeGeometry lying flat (shape (x,-z) then rotateX(-pi/2), the
// same mapping house.js uses for polygon rooms); the cobbles are rejection-
// sampled inside it and any stone whose radius would cross an edge is
// dropped, so the field stops dead at a concrete edge instead of spilling
// half a stone onto it.
// `avoid` is a list of [x, z, r] discs kept clear of cobbles — the steppers
// sit in those, and without it the field buried them.
// Stones here are RIVER PEBBLES: r 0.05..rmax (default 0.22 = a 5-inch
// stone at the very top of the tail), flattened to 35-60% and lying at
// grade. Round 3's critic read the first version — the addBed size ramp,
// r to 0.47, half-height, plus a rim of 0.5 ft stones — as "faceted
// boulders the size of basketballs, stacked above grade".
// `pale`: the night-frame strip is a PALE river-rock mix (the photograph's
// stones meter ~0.45 albedo with some near-white ones), not the cool dark
// bed rock metered off the day photo's east bed — at night it has to hold
// the path-light pool, and the dark mix simply vanished.
const ROCK_PALE = new THREE.Color(0x8e8f92);
function addBedPoly(rng, pts, y, beds, dens = BED_DENSITY, avoid = [], rmax = 0.22, pale = false) {
  const shape = new THREE.Shape();
  pts.forEach(([x, z], i) => (i ? shape.lineTo(x, -z) : shape.moveTo(x, -z)));
  shape.closePath();
  const g = new THREE.ShapeGeometry(shape);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y, 0);
  speckle(g, pale ? ROCK_PALE : ROCK, rng, 0.5);
  beds.push(g);
  let x0 = Infinity, z0 = Infinity, x1 = -Infinity, z1 = -Infinity, area = 0;
  for (let i = 0; i < pts.length; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[(i + 1) % pts.length];
    x0 = Math.min(x0, ax); x1 = Math.max(x1, ax);
    z0 = Math.min(z0, az); z1 = Math.max(z1, az);
    area += ax * bz - bx * az;
  }
  area = Math.abs(area) / 2;
  const inside = (x, z) => {
    let c = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, zi] = pts[i], [xj, zj] = pts[j];
      if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) c = !c;
    }
    return c;
  };
  const edgeDist = (x, z) => {
    let d = Infinity;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, zi] = pts[i], [xj, zj] = pts[j];
      const dx = xj - xi, dz = zj - zi, L2 = dx * dx + dz * dz || 1;
      const t = Math.max(0, Math.min(1, ((x - xi) * dx + (z - zi) * dz) / L2));
      d = Math.min(d, Math.hypot(x - xi - dx * t, z - zi - dz * t));
    }
    return d;
  };
  const n = Math.round(area * dens);
  let placed = 0, tries = 0;
  while (placed < n && tries < n * 4) {
    tries++;
    const x = x0 + rng() * (x1 - x0), z = z0 + rng() * (z1 - z0);
    const t = rng();
    const r = 0.05 + (t * t) * (rmax - 0.05);
    if (!inside(x, z) || edgeDist(x, z) < r * 0.9) continue;
    if (avoid.some(([ax, az, ar]) => Math.hypot(x - ax, z - az) < ar + r * 0.6)) continue;
    const s = r < 0.15 ? new THREE.OctahedronGeometry(r, 0)
                       : new THREE.IcosahedronGeometry(r, 0);
    s.scale(1 + rng() * 0.5, 0.35 + rng() * 0.25, 1 + rng() * 0.5);
    s.rotateY(rng() * 6.283);
    s.translate(x, y + r * 0.05, z);
    if (pale) {
      // grey-blue and tan stones mixed, 0.30..0.72, with one in seven near white
      const w = rng() < 0.15;
      paint(s, w ? hsl(0.10, 0.03, 0.80 + rng() * 0.08)
                 : hsl(rng() < 0.7 ? 0.58 : 0.09, 0.06, 0.30 + rng() * 0.42));
    } else {
      paint(s, hsl(0.58, 0.075, 0.145 + rng() * 0.40));
    }
    beds.push(s);
    placed++;
  }
}

// Big irregular ROUND steppers — the night photograph's flagstones beside
// the walk are 2 ft rounds, not the rectangular slabs addFlagstones lays.
// Pale enough to read under the porch lights against the dark rock.
// Returns the discs it covered, for addBedPoly's `avoid`. Thick (0.3 ft) and
// seated 0.1 above the gravel: round 1 laid them at 0.15 thick flush with it
// and the cobble field swallowed them whole.
// Round 4: ~18 in across (r 0.72-0.82), 0.12 thick and FLAT on the pebbles —
// the pebble field is now low enough that a flat slab stands clear of it.
function addSteppers(rng, pts, y, beds) {
  const discs = [];
  for (const [x, z] of pts) {
    const r = 0.72 + rng() * 0.1;
    const g = new THREE.CylinderGeometry(r, r * 1.04, 0.12, 9);
    const sx = 1 + rng() * 0.2, sz = 0.82 + rng() * 0.16;
    g.scale(sx, 1, sz);
    g.rotateY(rng() * 6.283);
    g.translate(x, y + 0.08, z);
    // bluestone to buff: no two the same value, so they read as separate stones
    // pale flagstone, ~0.5 albedo (round 6: lifted from 0.46-0.62 so the
    // step pool has something to land on)
    paint(g, hsl(0.08 + rng() * 0.5, 0.04 + rng() * 0.03, 0.52 + rng() * 0.12));
    beds.push(g);
    discs.push([x, z, r * Math.max(sx, sz) + 0.12]);
  }
  return discs;
}

// Chrysanthemum mound: a tight ball of colour. The night photograph has an
// orange one lit in the front bed, a dark-red one in a planter beside the
// steps, and an orange one in the urn at the garage corner. `hue`/`sat`/
// `light` in sRGB HSL, as the rest of the palette.
//
// Round 4: not one smooth icosahedron (the critic saw "a perfect orange
// sphere") but a LUMPY cluster — ten or so small flat-shaded blobs jammed
// into an r-wide dome, each its own size, tilt and shade, so the silhouette
// is knobbly and the surface breaks into facets the way a mum's mass of
// flower heads does.
// Round 9: a flatter dome (sq 0.60) and muted tints -- the saturated
// 0.80-sat gold/red read as "red dots in a row" from 40 ft.
function addMum(rng, x, z, r, y, leaves, hue = 0.07, sat = 0.60, light = 0.40) {
  lumpyMass(rng, x, z, r, y, leaves, 0.60, () =>
    hsl(hue + (rng() - 0.5) * 0.035, sat, light + (rng() - 0.5) * 0.12), 0.42);
}
// A dried hydrangea / spent mum clump: the same lumpy dome in muted
// November colours -- cream (papery hydrangea heads), straw, rust.
const DRIED_TINT = {
  cream: [0.10, 0.22, 0.60], straw: [0.12, 0.34, 0.50], rust: [0.045, 0.48, 0.33],
};
function addDriedClump(rng, x, z, r, y, leaves, kind = 'straw') {
  const [h, sat, l] = DRIED_TINT[kind] || DRIED_TINT.straw;
  lumpyMass(rng, x, z, r, y, leaves, 0.72, () =>
    hsl(h + (rng() - 0.5) * 0.03, sat, l + (rng() - 0.5) * 0.14), 0.40);
}
// The lumpy dome itself: `sq` squashes the whole mass, `tint()` gives each
// blob its colour, `amt` is paintNoisy's per-vertex jitter.
//
// The merged foliage mesh is FLAT-SHADED, so smooth normals cannot give a
// mass a lit top and a dark underside; the vertex colours do it instead
// (shadeVertical). Without it the round-4 critic saw "flat-shaded spheres
// with uniform mid-grey".
function lumpyMass(rng, x, z, r, y, leaves, sq, tint, amt) {
  const n = 7 + Math.round(r * 5);
  const top = y + r * sq * 0.6 + r * 0.55;
  for (let i = 0; i < n; i++) {
    const br = r * (0.32 + rng() * 0.26);
    const a = rng() * Math.PI * 2, d = Math.sqrt(rng()) * (r - br * 0.7);
    const bx = x + Math.cos(a) * d, bz = z + Math.sin(a) * d;
    // dome profile: blobs near the rim sit lower
    const by = y + Math.sqrt(Math.max(0, r * r - d * d)) * sq * 0.6 + br * 0.4;
    const g = new THREE.IcosahedronGeometry(br, 0);
    g.scale(0.9 + rng() * 0.35, (0.75 + rng() * 0.3) * sq, 0.9 + rng() * 0.35);
    g.rotateX((rng() - 0.5) * 0.8); g.rotateY(rng() * 6.283);
    g.translate(bx, by, bz);
    paintNoisy(g, tint(), rng, amt);
    shadeVertical(g, y, top);
    leaves.push(g);
  }
}
// Multiply a geometry's vertex colours by a bright-top / dark-base ramp
// (x1.15 at yTop down to x0.35 at yBot). The foliage material is flat-shaded
// and the eave/bed lights come from above and beside, so this is what puts
// a lit crown and a shadowed underside on every shrub and mum.
function shadeVertical(g, yBot, yTop) {
  const pos = g.attributes.position, col = g.attributes.color;
  if (!col) return;
  const span = Math.max(0.01, yTop - yBot);
  for (let i = 0; i < pos.count; i++) {
    const t = Math.min(1, Math.max(0, (pos.getY(i) - yBot) / span));
    const f = 0.35 + (t * t) * 0.80;
    col.setXYZ(i, col.getX(i) * f, col.getY(i) * f, col.getZ(i) * f);
  }
}

// Small black uplight can: the fixture body only, never a light source —
// the landscape lights themselves are eavelights.js's job.
function addUplightCan(x, z, y, props) {
  const dark = _c.setHex(0x1b1c1e);
  const c = cylAt(0.13, 0.15, 0.42, 6, x, y, z);
  paint(c, dark); props.push(c);
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
        // grey slate, NOT the warm 0.08 the first pass used: at hue 0.08
        // a run of these renders as a brown timber edging board, which is
        // the exact thing round 1 was failed for
        paint(g, hsl(0.60, 0.025, 0.185 + rng() * 0.20));
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
// `lumpy` builds the shrub as a knobbly cluster (lumpyMass) instead of one
// smooth icosahedron — for the ones nearest the camera, where a smooth
// sphere is exactly what it looks like.
function addBoxwood(rng, x, z, r, y, leaves, sp = 'boxwood', lumpy = false) {
  const [h, s, l, sq, sd] = SPECIES[sp] || SPECIES.boxwood;
  if (lumpy) {
    lumpyMass(rng, x, z, r * sd, y, leaves, sq, () =>
      hsl(h + (rng() - 0.5) * 0.03, s, l + rng() * 0.07), 0.34);
    return;
  }
  const g = new THREE.IcosahedronGeometry(r, 1);
  g.scale(sd, sq, sd * (0.92 + rng() * 0.18));
  g.rotateY(rng() * 6.283);
  g.translate(x, y + r * sq * 0.86, z);
  paintNoisy(g, hsl(h + (rng() - 0.5) * 0.03, s, l + rng() * 0.055), rng, 0.30);
  shadeVertical(g, y, y + r * sq * 1.86);
  leaves.push(g);
}

// A dark clipped hedge run between two world points: overlapping blobs
// r = h/2, so the mass is h tall, with the top-lit / dark-base ramp.
function addHedgeMass(rng, [[ax, az], [bx, bz]], h, leaves) {
  const L = Math.hypot(bx - ax, bz - az), n = Math.max(2, Math.round(L / (h * 0.55)));
  for (let i = 0; i <= n; i++) {
    const t = i / n, r = h / 2 * (0.92 + rng() * 0.16);
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(0.85 + rng() * 0.2, 1.0, 0.85 + rng() * 0.2);
    g.rotateY(rng() * 6.283);
    const x = ax + (bx - ax) * t + (rng() - 0.5) * 0.8, z = az + (bz - az) * t + (rng() - 0.5) * 0.8;
    g.translate(x, r * 0.9, z);
    paintNoisy(g, hsl(0.33 + (rng() - 0.5) * 0.04, 0.30, 0.11 + rng() * 0.04), rng, 0.3);
    shadeVertical(g, 0, r * 1.9);
    leaves.push(g);
  }
}

// Dark undergrowth: big low blobs (r 3-5 ft, squashed to ~55%) in a
// near-black green, with the top-lit ramp, for the foot of a tree group.
function addUndergrowth(rng, pts, leaves) {
  for (const [x, z, r] of pts) {
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(0.9 + rng() * 0.3, 0.5 + rng() * 0.12, 0.9 + rng() * 0.3);
    g.rotateY(rng() * 6.283);
    g.translate(x, r * 0.42, z);
    paintNoisy(g, hsl(0.32 + (rng() - 0.5) * 0.04, 0.24, 0.075 + rng() * 0.03), rng, 0.3);
    shadeVertical(g, 0, r * 1.1);
    leaves.push(g);
  }
}

// Bare deciduous tree: a trunk and a recursive fork of thinner cylinders,
// no foliage — the winter silhouettes that close both edges of the night
// photograph's sky. Goes in `trunks` (one bark-coloured draw call, no vertex
// colours, so the pieces must stay attribute-compatible with
// CylinderGeometry). Four levels of forking, ~120 cylinders at 5 sides.
// NOT gated by PLANT_TREES: that flag records the owner's "no trees" for the
// day-lit yard; these are planted explicitly by addFrontYard for the night
// frame, and the caller carries the reasoning.
const _up = new THREE.Vector3(0, 1, 0);
const _q = new THREE.Quaternion();
function addBareTree(rng, x, z, h, trunks) {
  const limb = (px, py, pz, dir, len, r, depth) => {
    const g = new THREE.CylinderGeometry(r * 0.62, r, len, 5);
    g.translate(0, len / 2, 0);
    g.applyQuaternion(_q.setFromUnitVectors(_up, dir));
    g.translate(px, py, pz);
    trunks.push(g);
    if (depth === 0) return;
    const ex = px + dir.x * len, ey = py + dir.y * len, ez = pz + dir.z * len;
    const kids = depth >= 3 ? 3 : 2 + (rng() < 0.5 ? 1 : 0);
    for (let i = 0; i < kids; i++) {
      const spread = 0.38 + rng() * 0.42;
      const a = rng() * Math.PI * 2;
      const d = new THREE.Vector3(dir.x + Math.cos(a) * spread, dir.y * (0.85 + rng() * 0.3),
                                  dir.z + Math.sin(a) * spread).normalize();
      limb(ex, ey, ez, d, len * (0.62 + rng() * 0.16), r * 0.62, depth - 1);
    }
  };
  const trunkH = h * 0.34;
  limb(x, 0, z, new THREE.Vector3((rng() - 0.5) * 0.1, 1, (rng() - 0.5) * 0.1).normalize(),
       trunkH, 0.55 * (h / 30), 4);
}

// Low spreading groundcover mass — the sheet of green that carpets the
// lamp-post bed in "Front of the house, a little bit of the garage...".
function addGroundCoverMass(rng, x, z, rx, rz, y, leaves) {
  const n = Math.max(3, Math.round(rx * rz * 1.6));
  for (let i = 0; i < n; i++) {
    const r = 0.34 + rng() * 0.42;
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(1.15, 0.52, 1.15);
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
// `dormant` gives the straw-tan of a November clump (the night photograph),
// the default stays the green of the July ones.
// A dormant clump is also WISPY: twice the blades at half the width,
// leaning further, the way a November miscanthus flops.
function addGrassClump(rng, x, z, y, leaves, dormant = false) {
  const h = 2.4 + rng() * 1.4;
  if (dormant) hsl(0.105, 0.34, 0.40 + rng() * 0.06);
  else hsl(0.20, 0.38, 0.33 + rng() * 0.06);
  const blades = dormant ? 15 : 7, w = dormant ? 0.13 : 0.28, lean = dormant ? 0.8 : 0.5;
  for (let i = 0; i < blades; i++) {
    const a = rng() * Math.PI * 2;
    const g = new THREE.ConeGeometry(w, h * (0.7 + rng() * 0.5), 4);
    g.rotateX((rng() - 0.5) * lean);
    g.rotateZ((rng() - 0.5) * lean);
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
  if (!PLANT_TREES) return;
  const h = (5.5 + rng() * 2.2) * s;
  const t = new THREE.CylinderGeometry(0.16 * s, 0.30 * s, h, 6);
  t.translate(x, h / 2, z);
  trunks.push(t);
  const tiers = 3;
  for (let i = 0; i < tiers; i++) {
    const r = (2.6 - i * 0.42 + rng() * 0.6) * s;
    const g = new THREE.IcosahedronGeometry(r, 1);
    // Two earlier passes used 0.30 and 0.62 in y with 1.55 s tier spacing and
    // both rendered as a stack of brown lily pads. A weeping specimen reads as
    // a soft DOME with a layered edge, so the tiers overlap heavily now.
    g.scale(1.06, 0.66, 1.06);
    g.rotateY(rng() * 6.283);
    g.translate(x + (rng() - 0.5) * 0.7 * s, h - i * 0.95 * s + 0.4 * s,
                z + (rng() - 0.5) * 0.7 * s);
    // bronze-OLIVE. A first pass at hue 0.09-0.14 rendered these as brown
    // mud blobs; the photographed specimen is a bronzed green, not a rock.
    paintNoisy(g, hsl(0.195 + rng() * 0.05, 0.30, 0.175 + rng() * 0.05),
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
  if (!PLANT_TREES) return;
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
      paint(g, hsl(0.62, 0.03, 0.20 + rng() * 0.10));
      beds.push(g);
    }
  }
}

// Poured-concrete apron: one flat plate plus scored control joints. The shell
// GLB's own site pad reads as unbroken white, and the joint grid is most of
// what tells a driveway from a blank plane at this distance.
// A flat concrete POLYGON at y, same pour colour — the front walk is a
// landing plus an angled band, not a rectangle.
function concretePoly(pts, y, beds) {
  const shape = new THREE.Shape();
  pts.forEach(([x, z], i) => (i ? shape.lineTo(x, -z) : shape.moveTo(x, -z)));
  shape.closePath();
  const g = new THREE.ShapeGeometry(shape);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y, 0);
  paintBlotch(g, CONC(), 3.2, 0.08);
  beds.push(g);
}

// Dark shredded-bark mulch bed: a low slab with its own edge, so the
// planting sits IN something instead of floating on the lawn. Warm brown,
// a touch lighter than the lawn's 0x67716a so it reads under the bed lights.
function addMulchBed(rng, x0, z0, x1, z1, y, h, beds) {
  const g = boxAt(x1 - x0, h, z1 - z0, (x0 + x1) / 2, y, (z0 + z1) / 2);
  speckle(g, hsl(0.07, 0.30, 0.34).clone(), rng, 0.45);
  beds.push(g);
}

// Leaf litter / dead-grass flecks: small pale quads lying on the lawn so an
// unlit lawn is not a void once the fixture spill reaches it. `keep(x, z)`
// says where a fleck may land (lawn only — never concrete, rock or bed).
// `drifts` are [cx, cz, r, n]: flecks gather round a centre (density
// falling off to the radius) -- loose piles against an edge, never a field.
function addLeafLitter(rng, drifts, keep, y, beds) {
  for (const [cx, cz, rad, n] of drifts) {
  let placed = 0, tries = 0;
  while (placed < n && tries < n * 6) {
    tries++;
    const a = rng() * Math.PI * 2, dd = rng() * rng() * rad;
    const x = cx + Math.cos(a) * dd, z = cz + Math.sin(a) * dd * 0.8;
    if (!keep(x, z)) continue;
    const w = 0.22 + rng() * 0.3, d = 0.18 + rng() * 0.25;
    const g = slab(x - w / 2, z - d / 2, x + w / 2, z + d / 2, y);
    // muted straw and dead-leaf tones: bright enough to catch spill, not
    // confetti by day
    paint(g, hsl(0.08 + rng() * 0.06, 0.16 + rng() * 0.16, 0.34 + rng() * 0.20));
    beds.push(g);
    placed++;
  }
  }
}

//
// ROUND 7: the pour is NEUTRAL cool grey (the sepia the critics saw was the
// drive spot's warmth), subdivided at ~2.5 ft and painted with a 2-4 ft
// blotch (paintBlotch, +-8%) so it is not a uniform speckle, and `lanes`
// lays two faint darker tyre lanes toward the garage. Heights: base y,
// lanes +0.008, joints +0.016.
const CONC = () => hsl(0.60, 0.012, 0.57);
function paintBlotch(geo, color, cell, amt, rng) {
  const pos = geo.attributes.position, n = pos.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    const f = 1 + (worldNoise(x + 57, z - 23, cell) - 0.5) * 2 * amt
                + (worldNoise(x - 11, z + 71, cell * 0.45) - 0.5) * amt
                + (rng ? (rng() - 0.5) * 0.04 : 0);
    arr[i * 3] = color.r * f; arr[i * 3 + 1] = color.g * f; arr[i * 3 + 2] = color.b * f;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(arr, 3));
}
function addConcrete(x0, z0, x1, z1, y, joints, beds, lanes = [], rng = null) {
  const g = slab(x0, z0, x1, z1, y, Math.max(2, Math.round((x1 - x0) / 2.5)),
                 Math.max(2, Math.round((z1 - z0) / 2.5)));
  paintBlotch(g, CONC(), 3.2, 0.08, rng);
  beds.push(g);
  for (const [lx, lz0, lz1, lw] of lanes) {
    const l = slab(lx - lw / 2, lz0, lx + lw / 2, lz1, y + 0.008, 2,
                   Math.max(2, Math.round((lz1 - lz0) / 2.5)));
    paintBlotch(l, hsl(0.60, 0.012, 0.535), 3.2, 0.06, rng);
    beds.push(l);
  }
  for (const j of joints) addJoint(j, y, beds);
}
// A control joint that reads at 40 ft: a 0.10 ft groove 12% darker than the
// pour, flanked by two 0.07 ft chamfers 10% lighter. `rect` is [x, z, w, d]
// with the thin dimension 0.16 (the old solid dark stripe), which is where
// the groove is centred.
const JOINT_DK = () => hsl(0.60, 0.012, 0.50), JOINT_LT = () => hsl(0.60, 0.012, 0.63);
function addJoint([jx, jz, jw, jd], y, beds) {
  const along = jw >= jd ? 'x' : 'z';                 // the long axis
  const cz = jz + jd / 2, cx = jx + jw / 2;
  const strip = (off, w, col, yy) => {
    const g = along === 'x'
      ? slab(jx, cz + off - w / 2, jx + jw, cz + off + w / 2, yy)
      : slab(cx + off - w / 2, jz, cx + off + w / 2, jz + jd, yy);
    paint(g, col); beds.push(g);
  };
  strip(-0.085, 0.07, JOINT_LT(), y + 0.014);
  strip(0.085, 0.07, JOINT_LT(), y + 0.014);
  strip(0, 0.10, JOINT_DK(), y + 0.016);
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
  if (!BUILD_NEIGHBOURS) return;
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

  // sidewalk, with the drive crossing it. No 5 ft joints across the crossing:
  // the drive slab is poured over the walk there (addFrontYard draws it
  // higher), and the night photograph's foreground — which IS that crossing,
  // the camera stands just past it — shows one longitudinal joint and
  // nothing else.
  addConcrete(x0 + 40, walkZ0, x1 - 30, walkZ1, L.lo + 0.03,
              (() => { const j = []; for (let cx = x0 + 44; cx < x1 - 30; cx += 5) {
                if (cx > L.driveL - 5 && cx < L.driveR + 5) continue;
                j.push([cx, walkZ0, 0.14, walkZ1 - walkZ0]); } return j; })(), beds);

  // driveway apron: flares out from the drive across the verge to the kerb.
  // Starts at the drive slab's own height (lo + 0.05) so the seam is flush.
  const ap = quadAt([L.driveL, L.lo + 0.05, walkZ1], [L.driveR, L.lo + 0.05, walkZ1],
                    [L.driveR + 4.2, 0.03, kerbZ + 0.9], [L.driveL - 4.2, 0.03, kerbZ + 0.9]);
  paint(ap, hsl(0.10, 0.02, 0.56)); beds.push(ap);

  // Mailbox. INFERRED, not measured: the street photograph shows a
  // post-mounted black object at the kerb by the neighbouring lot but our own
  // is out of frame in every shot. Reported as such.
  const mx = L.driveR + 2.2, mz = L.street - 3.2;
  const post = boxAt(0.22, 3.2, 0.22, mx, L.lo, mz);
  paint(post, _c.setHex(0x1d1e20)); props.push(post);
  const arm = boxAt(0.20, 0.20, 1.1, mx, L.lo + 3.0, mz - 0.35);
  paint(arm, _c.setHex(0x1d1e20)); props.push(arm);
  const bxg = boxAt(0.55, 0.58, 1.20, mx, L.lo + 3.2, mz - 0.35);
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

// ---------------------------------------------------------- the driveway car
// The parked SUV is a real GLB now — a black BMW X5 — looked up in the model
// library BY NAME, so the owner can swap the car by re-uploading over that one
// model without touching this file. Three things follow from that:
//
//  - the eight-box primitive below stays as the FALLBACK, for any instance
//    whose library has no such model (a fresh clone, or the model deleted).
//    It is built into its own Group instead of merged into `props`, because
//    the model list arrives asynchronously and the swap has to be able to
//    replace whatever is standing there;
//  - `carSpot` is recorded by addFrontYard while the yard is planted, so the
//    swap knows where the drive is without re-deriving the landmarks;
//  - the model is bottom-seated by models.js getInstance('bottom') and scaled
//    from metres to feet there, so `y` here is the driveway SURFACE and the
//    .glb is expected to be authored at real size in metres. `carSpot.ry` is
//    the heading of the CAR (0 = nose at the garage, -Z, which is how it is
//    parked in every front photograph and what the primitive does natively);
//    CAR_MODEL_RY absorbs whichever way the .glb happens to be authored.
const CAR_MODEL_NAME = 'Driveway Car';
// The uploaded X5 (model 323) has its nose down +Z: its headlamp emissives sit
// at z +1.8..+2.1 m and the red tail cluster at z -2.6 m in model space. A
// half-turn puts the nose at the garage, so the rear window, tailgate and
// rear plate face the street — which is what demo/exterior_night.jpg shows.
const CAR_MODEL_RY = Math.PI;
let carModelId = null;
let carSpot = null;       // { x, y, z, ry } — set while the front yard is built
let carGroup = null;      // whichever of the two is in the yard right now

// main.js hands the model library over once at boot. Fire-and-forget: until it
// lands (or if it never does) the primitive stands on the drive.
export function setYardModels(models) {
  const want = CAR_MODEL_NAME.toLowerCase();
  const hit = (models || []).find((m) => (m.name || '').trim().toLowerCase() === want);
  const id = hit ? hit.id : null;
  if (id === carModelId) return;
  carModelId = id;
  syncCar();
}

// Must run BEFORE buildYard's teardown sweep, which disposes the geometry of
// every mesh under `yard`. That is safe for everything the yard authors itself
// and WRONG for a library model: models.js's getInstance does `scene.clone(true)`,
// which shares BufferGeometry with the cached model — disposing it here would
// blank out every later instance of that .glb, in the yard and anywhere else.
// Materials it does clone per instance, so those are ours to release.
function disposeCar() {
  carEnvMats.clear();   // the next car re-registers its own materials
  if (!carGroup) return;
  carGroup.parent?.remove(carGroup);
  carGroup.traverse((o) => {
    if (!o.isMesh) return;
    // ownGeometry is per MESH, not per group: the car group mixes geometry we
    // authored (the primitive, the contact blob) with geometry the model cache
    // owns, and only the former may be disposed.
    if (o.userData.ownGeometry === true) o.geometry.dispose();
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.dispose();
  });
  carGroup = null;
}

// Soft contact-occlusion blob, the same trick the yard already uses to ground
// the house footprint. It is not a stand-in for a real shadow that happens to
// be missing: the sun's shadow map is tuned for the house shell — 2048 px over
// a 280 ft square with a 1 ft normalBias, which is coarser than the whole gap
// between a car's sill and the concrete — so a parked car gets no readable
// ground contact from it at any sun angle, and reads as pasted onto the drive.
// Sized to the car's own footprint with a margin, and sunk just above the
// driveway surface. Deliberately opaque enough to read on bright concrete and
// still soft-edged: a hard ellipse looks worse than none.
// The car's own sky.
//
// scene.environment is three.js's RoomEnvironment — a small white box with
// light panels, which is a fine neutral fill for furniture indoors and is the
// wrong world entirely for a car standing outside. Gloss black paint is almost
// nothing BUT reflection: with an indoor box overhead, every panel collapses to
// the same near-black and the only thing left is one or two blown specular
// smears. Four independent critics comparing this render against photographs of
// a real black X5 M named that same defect first — "no sky gradient down the
// shoulder", "parked feet from a white garage door and reflects neither",
// "a flat silhouette, not curved sheetmetal".
//
// So the car gets its own envMap. Per-material `envMap` overrides
// scene.environment in three's shader, so this is scoped to the car alone and
// nothing else in the app changes. What it has to contain is not a pretty sky
// but the three bands a car body actually reflects: sky above, a bright narrow
// horizon, and ground below. The horizon band is the important one — it is what
// draws the hard bright line along the shoulder crease and the sill that says
// "this surface is curved", and it is exactly what was missing.
//
// envMapIntensity is left alone: scene.js applyEnvIntensity() sweeps the whole
// scene with the day/night ramp, so the car dims into the evening with
// everything else.
let carEnvDay = null;    // PMREM'd, built once each, on the first car that needs them
let carEnvNight = null;
const carEnvMats = new Set();   // every car material carrying one of them
let carSkyTicking = false;

// One 512x256 equirect canvas -> PMREM texture. `paint(g)` draws the sky.
function bakeCarSky(paint) {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 256;
  paint(c.getContext('2d'));
  const tex = new THREE.Texture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const out = pmrem.fromEquirectangular(tex).texture;
  pmrem.dispose();
  tex.dispose();
  return out;
}

function makeCarEnvironment() {
  if (carEnvDay || !renderer) return carEnvDay;
  carEnvDay = bakeCarSky(paintCarDaySky);
  return carEnvDay;
}

function paintCarDaySky(g) {
  // The lower hemisphere has to go DARK, and fast. A first pass ran the ground
  // at real driveway value (#b9b7b0 falling to #4c4b48) on the reasoning that
  // that is what is actually under the car — and it rendered the X5 in
  // GUNMETAL with chrome wheels, because a metallic 0.62 body reflecting a
  // uniform mid-grey hemisphere IS mid-grey, and a low-roughness rim reflecting
  // pale concrete is a mirror. What makes a black car read black outdoors is
  // CONTRAST, not average brightness: sky on the horizontal surfaces, one
  // bright horizon band across the flanks at shoulder height, and near-black
  // everywhere the panel faces down.
  const grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0.00, '#5c7ba4');   // zenith, matched to the app's sky
  grad.addColorStop(0.32, '#93aecb');
  grad.addColorStop(0.44, '#dae6f1');   // horizon haze
  grad.addColorStop(0.485, '#ffffff');  // the band that draws the shoulder line
  grad.addColorStop(0.515, '#3c3c3a');  // ...and the cliff straight after it
  grad.addColorStop(0.70, '#232322');
  grad.addColorStop(1.00, '#131313');   // nadir
  g.fillStyle = grad;
  g.fillRect(0, 0, 512, 256);

  // The white garage door.
  //
  // A blind critic comparing this render against a photograph of a real black
  // X5 put it exactly: "a huge white garage door stands directly in front of it
  // and does not appear anywhere on the bonnet or flank, so bonnet, wing and
  // door collapse into one flat black mass separated only by thin drawn
  // shutlines, which is the one cue a real black car never uses." A pure
  // vertical gradient gives the shoulder line but it cannot give that, because
  // there is nothing in it with a horizontal extent.
  //
  // three's equirectUv is u = atan2(dir.z, dir.x)/2pi + 0.5, so the -Z
  // direction — where the garage stands, the car being parked nose-out — is
  // u 0.25, i.e. x 128. The band runs from just above the horizon up to about
  // 40 degrees of elevation, which is roughly what a two-storey garage wall
  // subtends from 12 ft away, and it is feathered at every edge: a hard-edged
  // patch reads as a decal sliding over the paintwork as the camera moves.
  const gx = 128, gw = 78, gy0 = 74, gy1 = 124;   // 124 is just above the horizon
  const wall = g.createLinearGradient(0, gy0, 0, gy1);
  wall.addColorStop(0, 'rgba(255,255,255,0)');
  wall.addColorStop(0.45, 'rgba(246,247,248,0.92)');
  wall.addColorStop(1, 'rgba(246,247,248,0.98)');
  const fade = g.createLinearGradient(gx - gw, 0, gx + gw, 0);
  fade.addColorStop(0.00, 'rgba(0,0,0,0)');
  fade.addColorStop(0.22, 'rgba(0,0,0,1)');
  fade.addColorStop(0.78, 'rgba(0,0,0,1)');
  fade.addColorStop(1.00, 'rgba(0,0,0,0)');
  const m = document.createElement('canvas');
  m.width = 512; m.height = 256;
  const mg = m.getContext('2d');
  mg.fillStyle = wall;
  mg.fillRect(gx - gw, gy0, gw * 2, gy1 - gy0);
  mg.globalCompositeOperation = 'destination-in';
  mg.fillStyle = fade;
  mg.fillRect(gx - gw, gy0, gw * 2, gy1 - gy0);
  g.drawImage(m, 0, 0);
}

// The car's NIGHT sky.
//
// At night the eave LEDs are emissive geometry, not lights, so PBR never sees
// them: the body reflected a near-black sky and a critic read it as "a cut-out
// silhouette under a string of bulbs". What the photo's car actually shows is
// those bulbs, doubled in the paint — a dotted warm streak riding the roof
// rails, the rear-glass edge and the tailgate crease. So the night env bakes
// the house's lit features where they sit RELATIVE TO THE CAR (x 27.7,
// z 65.8, nose at -Z): the string along the porch and garage eaves at ~11 ft
// runs from x -5 to x 46 at z 29.5, which from the car is azimuth ~-135 to
// ~-65 degrees (u 0.13..0.32) at ~14 degrees of elevation; the upper gable
// eaves at ~22 ft sit higher and narrower; the sconce-lit garage door is a
// soft warm patch straight ahead just above the horizon; the two sconces are
// two bright points in it. Everything else is near-black, so the flanks stay
// black and only the crease lines light up — contrast again, as with the day
// sky. Intensity is pinned in applyCarSky, since the scene's night ramp
// takes envMapIntensity to ~0 and would switch all of this off.
function paintCarNightSky(g) {
  // The whole map is read through CAR_NIGHT_ENV_INTENSITY (~8x, since a canvas
  // cannot hold an HDR bulb), so every "ambient" value here is authored at
  // roughly an eighth of what it should look like: the sky is all but black,
  // and only the bulbs and the sconce-lit door are allowed real brightness.
  const grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0.00, '#010102');
  grad.addColorStop(0.46, '#030407');   // faint sky glow at the horizon
  grad.addColorStop(0.50, '#050505');
  grad.addColorStop(0.53, '#020202');
  grad.addColorStop(1.00, '#000000');
  g.fillStyle = grad;
  g.fillRect(0, 0, 512, 256);

  // the garage door, sconce-lit: a soft warm patch, feathered every side
  const door = g.createRadialGradient(140, 118, 4, 140, 118, 36);
  door.addColorStop(0.00, 'rgba(255,222,176,0.30)');
  door.addColorStop(0.55, 'rgba(255,214,160,0.12)');
  door.addColorStop(1.00, 'rgba(255,210,150,0)');
  g.fillStyle = door;
  g.fillRect(90, 96, 100, 34);

  // The bulb strings, as a STREAK. The first pass drew each bulb as a hot
  // 1.5 px point, and on the paint that came back as "uniform white specks —
  // a noise map, not clearcoat": the PMREM mip the gloss paint samples still
  // resolved the individual dots, and a black car doubles a bulb string as a
  // blurred bright line, not as pinpricks (the photo's tailgate and rear
  // glass show exactly that line). So the run is a smooth warm band with only
  // a mild dotted modulation on top, and the whole map is blurred ~3 px
  // below before it goes to PMREM.
  const string = (x0, x1, y, step, h) => {
    const band = g.createLinearGradient(0, y - h * 2.2, 0, y + h * 2.2);
    band.addColorStop(0.00, 'rgba(255,196,128,0)');
    band.addColorStop(0.35, 'rgba(255,214,150,0.72)');
    band.addColorStop(0.50, 'rgba(255,238,205,1.0)');
    band.addColorStop(0.65, 'rgba(255,214,150,0.72)');
    band.addColorStop(1.00, 'rgba(255,196,128,0)');
    g.fillStyle = band;
    g.fillRect(x0 - h * 2, y - h * 2.2, x1 - x0 + h * 4, h * 4.4);
    g.fillStyle = 'rgba(255,248,230,0.6)';    // the modulation: bulbs, faintly
    for (let x = x0; x <= x1; x += step) {
      g.beginPath(); g.arc(x, y, h * 0.9, 0, Math.PI * 2); g.fill();
    }
  };
  string(66, 168, 108, 3, 1.6);    // porch + garage eave, the long run
  string(84, 132, 92, 4, 1.3);     // upper gable eaves, higher and shorter
  // the two garage sconces: brighter points flanking the door
  for (const sx of [116, 164]) {
    const s = g.createRadialGradient(sx, 114, 0, sx, 114, 9);
    s.addColorStop(0, 'rgba(255,236,200,1)');
    s.addColorStop(0.3, 'rgba(255,220,160,0.6)');
    s.addColorStop(1, 'rgba(255,200,140,0)');
    g.fillStyle = s;
    g.fillRect(sx - 9, 105, 18, 18);
  }
  // soften everything: a copy blurred back over itself
  const src = g.canvas;
  const cp = document.createElement('canvas');
  cp.width = src.width; cp.height = src.height;
  cp.getContext('2d').drawImage(src, 0, 0);
  g.filter = 'blur(3px)';
  g.drawImage(cp, 0, 0);
  g.filter = 'none';
}

// Why so high: black paint reflects almost nothing. three's F0 for this body
// is mix(0.04, base 0.01, metalness 0.62) ~ 0.02, plus the clearcoat's 0.04,
// so a bulb painted at canvas-white 1.0 comes back at ~0.06 x intensity —
// and 1.6 or 2.6 gave the roof rails a highlight you had to look for. A real
// bulb is a hundred times brighter than the siding it hangs on; this is the
// HDR headroom a canvas cannot hold, with the sky above authored near-black
// to compensate. (8 with pinpoint bulbs sparkled; the streak below reads at 5.)
const CAR_NIGHT_ENV_INTENSITY = 2;   // round 9: a faint rim on roofline and shoulders, no more

// Picks day or night sky for every car material. Runs every frame once a car
// exists (a few dozen uniform writes): daylight.js re-sweeps the whole scene's
// envMapIntensity from its own frame tick during a ramp, and this must land
// AFTER that sweep to pin the night value. The env swap itself is gated, not
// eased — two env maps cannot be lerped per material — and flips at the
// midpoint of the night factor, when the sky is already dark enough that the
// day sky's reflection has nothing left to show.
function applyCarSky() {
  if (!carEnvMats.size) return;
  const night = getNightFactor() > 0.5;
  const env = night ? carEnvNight : carEnvDay;
  if (!env) return;
  const intensity = night ? CAR_NIGHT_ENV_INTENSITY : getEnvIntensity();
  for (const m of carEnvMats) {
    const u = m.userData;
    if (u.plate) {
      // The plate is RETRO-reflective: it throws the sconce light straight
      // back at the camera, which is why in the photo it is a blown white
      // slab with the characters all but washed out — the brightest small
      // thing on the car. No sky for it; at night it simply emits its
      // washed-out face, by day it is the plain decal lit by the scene.
      m.emissiveIntensity = night ? PLATE_NIGHT_EMIT : 0;
      continue;
    }
    if (u.plateRim) { m.envMapIntensity = 0; continue; }
    if (u.plateGlow) { m.opacity = 0; continue; }   // round 9: no fill on the rear at all
    if (m.envMap !== env) { m.envMap = env; m.needsUpdate = true; }
    // polishCar marks what must NOT take the full night sky: chrome and
    // wheels reflect it at 5x as the brightest things on the car, which the
    // photo flatly contradicts — its tips and rims are lost in the dark.
    m.envMapIntensity = intensity * (night && u.nightEnvScale != null ? u.nightEnvScale : 1);
    if (u.dayColor) {
      if (night && u.nightAlbedo != null) m.color.copy(u.dayColor).multiplyScalar(u.nightAlbedo);
      else m.color.copy(u.dayColor);
    }
    if (u.dayMetalness != null) m.metalness = night ? u.nightMetalness : u.dayMetalness;
    if (u.dayRoughness != null) m.roughness = night ? u.nightRoughness : Math.max(u.dayRoughness, u.nightEnvScale === 0.02 ? 0.7 : 0.45);
    if (u.flatAtNight) {
      if (u.dayNormalScale) m.normalScale.copy(u.dayNormalScale).multiplyScalar(night ? 0 : 1);
      if (u.dayBumpScale != null) m.bumpScale = night ? 0 : u.dayBumpScale;
    }
  }
}

function giveCarItsOwnSky(root) {
  if (!renderer) return;
  if (!carEnvDay) carEnvDay = bakeCarSky(paintCarDaySky);
  if (!carEnvNight) carEnvNight = bakeCarSky(paintCarNightSky);
  root.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (!m || !('envMap' in m)) continue;
      carEnvMats.add(m);
    }
  });
  applyCarSky();   // the shader gains an ENVMAP define on the first apply
  if (!carSkyTicking) { carSkyTicking = true; onFrame(applyCarSky); }
}

// A parked car shows no light. The uploaded X5 ships with its lamp clusters
// as emissive materials (warm-white DRL/headlamp rings at emissiveStrength 3-4,
// a red tail bar at 3) — the way a showroom model is authored — and at night
// they read as a car pulling IN with its lights on, which is not the photo:
// there every lamp is dark and the body is lit only by the eave lights.
// Emissive is killed outright rather than dimmed; a faint glow still reads as
// "on" against a black car. The lens glass keeps its base colour, so the
// clusters are still visible as fittings by day.
function parkCar(root) {
  root.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (!m || !m.emissive) continue;
      m.emissiveIntensity = 0;
      m.emissive.setHex(0x000000);
      if (m.emissiveMap) { m.emissiveMap = null; m.needsUpdate = true; }
    }
  });
}

// What a black car shows at night is almost entirely specular: the eave and
// sconce lights drawn as sharp highlights along the roof rails, the rear-glass
// edge and the tailgate crease. Those only appear on LOW-roughness surfaces —
// a point light's highlight on roughness 0.44 is a smear too faint to read
// against near-black paint. The X5's authored paint is already gloss
// (roughness 0.13 + clearcoat), but its brightwork and trim ("blestashka",
// "serebristenkaya", RS chrome — the roof rails, window surrounds, grille
// surround) ship at 0.35-0.45 and the tinted glass at 0.05. Everything dark
// and metallic is pulled down to trim gloss and the glass to a true polish.
// Authored colours are never touched; this is finish, not paint.
// "desirefx" is the wheel asset's own prefix in this model: every wheel part
// — tyre, rim, brake, caliper AND the chrome lip ("..._chrome_13_...") — is
// a "Desirefx_me_*" node. The lip was the striped bright drum in round 5's
// crop: its material is a black metal that the paint rule polished to 0.22.
const CAR_WHEEL_RE = /tire|tyre|wheel|brake|caliper|rim|disc|desirefx/i;
function polishCar(root) {
  root.traverse((o) => {
    if (!o.isMesh) return;
    // wheels are identified by NODE name (the model names them "..._tire_01_",
    // "..._brakes_02_", "..._caliper_01_"); their materials are shared with
    // nothing else on the body
    const wheel = CAR_WHEEL_RE.test(o.name) || CAR_WHEEL_RE.test(o.parent?.name || '');
    // the quad tips are nodes "x5g05_exhaust_L/R" wearing a WHEEL material
    // ("etk_wheel_03a", dark metal) that neither name test caught -- a night
    // audit found them unflagged at metalness 0.35 / roughness 0.3, which is
    // exactly the gleam every critic named. Classified by node name.
    const exhaust = /exhaust|muffler|tailpipe/i.test(o.name) || /exhaust|muffler|tailpipe/i.test(o.parent?.name || '');
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (!m || !m.color || m.roughness === undefined) continue;
      const lum = m.color.r * 0.3 + m.color.g * 0.59 + m.color.b * 0.11;
      const red = m.color.r > 0.3 && m.color.g < 0.15 && m.color.b < 0.15;
      const chrome = exhaust || /chrome|mirror/i.test(m.name) || (lum > 0.3 && m.metalness >= 0.7);
      if (wheel || chrome) {
        // Night exceptions. Wheels: barely any sky, and the albedo cut to a
        // third so the tread does not render as a bright striped drum — in
        // the photo the rubber is the blackest thing in frame. Chrome (the
        // quad exhaust tips, mirror caps, window brights): a whisper of the
        // sky, or the tips become four lamps. applyCarSky reads these.
        m.userData.dayColor = m.color.clone();
        m.userData.nightEnvScale = wheel ? 0.02 : 0.03;
        m.userData.nightAlbedo = wheel ? 0.15 : 0.3;
        // and at night the metal goes dielectric: a rim at metalness 0.75
        // still draws the drive spot as a bright striped drum however rough
        // it is made, because a metal's specular IS its colour at full F0.
        // At 0 it is a 4% dielectric gloss on near-black rubber — gone.
        m.userData.dayMetalness = m.metalness;
        m.userData.nightMetalness = 0;   // both: a 4% dielectric under the lights, nothing gleams
        m.userData.dayRoughness = m.roughness;
        m.userData.nightRoughness = 0.85;
        m.roughness = Math.max(m.roughness, wheel ? 0.7 : 0.45);
        if (wheel) {
          // and no relief: a ribbed sidewall under the drive spot is the
          // second most obvious tell, so any normal/bump map is flattened
          // at night (the ribs that are geometry stay; they are dark now)
          m.userData.flatAtNight = true;
          if (m.normalScale) m.userData.dayNormalScale = m.normalScale.clone();
          m.userData.dayBumpScale = m.bumpScale;
        }
        continue;
      }
      if (m.transparent && m.opacity < 1) {          // glass
        // roughness 0 and 2.5x the night sky: the rear glass was a uniform
        // black; in the photo it carries the bulb string and the lit door
        m.roughness = 0;
        m.opacity = Math.min(m.opacity, 0.6);   // tinted, not opaque: headrests and the door read through
        m.userData.nightEnvScale = 2.5;
      } else if (red) {                              // tail-lamp lenses
        // round 9: the polished lens drew a "taillight-bar highlight" off
        // the drive wash; the photo's tail cluster is dark. Satin, and a
        // whisper of sky.
        m.roughness = Math.max(m.roughness, 0.35);
        m.userData.nightEnvScale = 0.15;
      } else if (lum < 0.08 && m.metalness >= 0.5) { // paint, trim, brightwork
        // 0.22 / 0.06 drew the bulb band as a hard stripe; a touch rougher
        // and the streak diffuses along the panel the way the photo's does
        m.roughness = Math.min(Math.max(m.roughness, 0.35), 0.4);
        if ('clearcoat' in m && m.clearcoat > 0) m.clearcoatRoughness = 0.25;
      }
    }
  });
}

// Its own falloff, not the yard's makeShadowTexture: that one is a linear
// radial fade meant to ground a whole house footprint, and under a car it
// reads as a grey halo. A car's underside is nearly solid dark to well past
// the sills and only then lets go — dense core, short skirt.
let carShadowTex = null;
function makeCarShadowTexture() {
  if (carShadowTex) return carShadowTex;
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 10, 128, 128, 128);
  grad.addColorStop(0.00, 'rgba(0,0,0,1)');
  grad.addColorStop(0.55, 'rgba(0,0,0,0.92)');
  grad.addColorStop(0.78, 'rgba(0,0,0,0.45)');
  grad.addColorStop(1.00, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  carShadowTex = new THREE.CanvasTexture(c);
  return carShadowTex;
}

function carContactShadow(w, d, opacity = 0.85) {
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(w, d),
    // 0.34 vanished at night — on concrete that is already dark, a third of
    // black is nothing, and the tyres read as hovering. Now that the drive
    // is lit to ~15% around the car it has to read against THAT, so it is
    // nearly opaque at the core; the short skirt keeps it from becoming a
    // hard puddle by day.
    new THREE.MeshBasicMaterial({
      map: makeCarShadowTexture(), color: 0x000000, transparent: true,
      opacity, depthWrite: false }));
  m.userData.ownGeometry = true;
  m.rotation.x = -Math.PI / 2;
  m.renderOrder = 1;   // after the opaque drive, so it never z-fights it away
  return m;
}

// ------------------------------------------------------- the licence plates
// New Jersey plates, front and rear, reading R53-PNS (asked for on
// 2026-09-01). The .glb is not touched: the plates are two small textured
// boxes hung on the loaded car at runtime, so re-uploading a different car
// over the "Driveway Car" library entry keeps the plates — and the owner's
// number — without anyone editing a model.
//
// Where a plate goes is FOUND, not hard-coded. A plate sits on the bodywork,
// and the bodywork of whatever car is in the library is not known here, so
// each end fires a ray down the car's centreline at plate height and hangs
// the plate on the first panel it hits, facing along that panel's normal. A
// few heights are tried in order of preference (a real X5 carries its rear
// plate in the tailgate recess at ~3 ft and its front plate in the bumper at
// ~2 ft) and the first hit that is a near-vertical, opaque panel within reach
// of the car's end wins — grille slats let a ray through into the engine bay,
// and the tinted glass is a BLEND material, which is what the two filters are
// for. Everything here is in the car group's OWN frame, where +Z is always
// the nose (CAR_MODEL_RY has already turned the .glb to agree with that), so
// the +Z end takes the front plate and the -Z end the rear one, whichever way
// the car is parked in the world.
const PLATE_TEXT = 'R53-PNS';
const PLATE_W = 1.0, PLATE_H = 0.5;   // 12 x 6 in, the North American plate
let plateTex = null;                  // one canvas, shared by every instance
let nightPlateTex = null;             // the retro-reflective, washed-out face
// 2.2 blew it to a text-less white slab, which no camera exposing for the
// eave bulbs would do; 0.6 keeps the face at ~150-180/255 warm-white, under
// the bloom threshold, with the characters clearly dark.
// Round 8: NO emissive at all. Even 0.6 read as "a uniformly lit lightbox";
// the real plate is a dim warm-grey slab lit only by its lamp's spill, its
// characters dark, its frame visible. Kept as a constant so the retro-
// reflective look can be dialled back in if a lit driveway ever calls for it.
// ...but 0 with the sconces dimmed left the plate unreadable (~50/255). The
// plate LAMP lights it, and since that lamp is faked, its light on the face
// is carried as a texture-modulated emissive: the day decal itself as the
// emissive map at 0.35, so the face lands ~110/255 warm-grey and the
// characters and frame stay as dark as they are printed. Not a lightbox.
// Round 9: back to 0. With the lighting builder's wash pulled off the car's
// rear there is no source for a lit plate; the photo's is a dim grey
// rectangle at ~40-60/255, and that is what an unlit neutral face gives.
// ...and at 0 the round-9 shot metered the plate at 10/255 against a
// 40-60 target: with every wash off the car's rear there is NOTHING lighting
// it, and a plate that vanishes is as wrong as one that glows. A car's own
// plate lamp is the one real source there is, so it is carried as the
// smallest neutral texture-modulated emissive that puts the face at ~45/255
// -- characters still dark, no amber, nowhere near the bloom threshold.
const PLATE_NIGHT_EMIT = 0.12;

// The plate as the camera sees it at night: retro-reflective sheeting throws
// the sconce light back along the line of sight, so the face goes to white
// and the printed characters survive only as faint grey shapes.
function makeNightPlateTexture() {
  if (nightPlateTex) return nightPlateTex;
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#efe6cf';   // warm: the sheeting returns the sconces' colour
  g.fillRect(0, 0, 1024, 512);
  // the sheeting's hot centre: a soft bloom that fades toward the rim
  const bloom = g.createRadialGradient(512, 256, 60, 512, 256, 620);
  bloom.addColorStop(0, 'rgba(255,249,236,1)');
  bloom.addColorStop(1, 'rgba(226,216,192,1)');
  g.fillStyle = bloom;
  g.fillRect(0, 0, 1024, 512);
  g.strokeStyle = 'rgba(0,0,0,0.10)';
  g.lineWidth = 12;
  g.strokeRect(6, 6, 1012, 500);
  g.fillStyle = '#3f3b34';   // the characters: ~25% grey, clearly legible
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = '700 236px "Arial Narrow", "Helvetica Neue", Arial, sans-serif';
  if ('letterSpacing' in g) g.letterSpacing = '14px';
  g.fillText(PLATE_TEXT, 512, 258);
  // blur, as the day face is: retro-reflection blooms past the letter edges
  const s = document.createElement('canvas');
  s.width = 256; s.height = 128;
  s.getContext('2d').drawImage(c, 0, 0, 256, 128);
  g.imageSmoothingEnabled = true;
  g.imageSmoothingQuality = 'high';
  g.drawImage(s, 0, 0, 1024, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  if (renderer) tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  nightPlateTex = tex;
  return tex;
}

// The plate lamp's spill: a small warm pool on the bumper around the plate.
// Faked as an additive quad rather than a PointLight -- adding a light after
// boot recompiles every shader in the scene -- and driven night-only by
// applyCarSky through `plateGlow`.
let plateGlowTex = null;
function makePlateGlowTexture() {
  if (plateGlowTex) return plateGlowTex;
  const c = document.createElement('canvas');
  c.width = 256; c.height = 128;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 44, 6, 128, 44, 120);
  grad.addColorStop(0.00, 'rgba(255,220,170,0.9)');
  grad.addColorStop(0.35, 'rgba(255,205,150,0.35)');
  grad.addColorStop(1.00, 'rgba(255,190,130,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 128);
  plateGlowTex = new THREE.CanvasTexture(c);
  return plateGlowTex;
}

function makePlateTexture() {
  if (plateTex) return plateTex;
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 512;
  const g = c.getContext('2d');
  // NJ's straw-to-cream fade, top to bottom. Kept PALE and low-chroma on
  // purpose: the first pass used a saturated #f0cb45 top and a critic read
  // it at night as "a self-luminous yellow block" — under a warm sconce a
  // strong yellow albedo comes back brighter than the white siding beside it.
  // Real NJ plates are a washed straw that photographs near-white; the
  // photo's plate is the brightest thing on the car but it is not yellow.
  // Albedo ~0.5, well under the white siding: a plate is retro-reflective
  // only to a light at the camera, and there is none here, so under the
  // sconces it should sit a step DARKER than the door behind it.
  // (Round 5 took it down another ~1.5 stops: nothing on the car's rear may
  // be brighter than the house lights, and under the sconces it still was.)
  // Round 8: a warm grey around 100/255 — the face is REFLECTIVE, not lit,
  // and under the plate lamp alone that is where it sits — with a real
  // frame: a dark outer rim, a light inner bevel line, then the face.
  const grad = g.createLinearGradient(0, 0, 0, 512);   // NEUTRAL grey: "not amber"
  grad.addColorStop(0.00, '#7c7b78');
  grad.addColorStop(0.50, '#868582');
  grad.addColorStop(1.00, '#8b8a87');
  g.fillStyle = grad;
  g.fillRect(0, 0, 1024, 512);
  // the frame: black-plastic surround, then the plate's own rolled bevel
  g.strokeStyle = '#1a1a1a';
  g.lineWidth = 34;
  g.strokeRect(17, 17, 990, 478);
  g.strokeStyle = 'rgba(255,255,255,0.28)';   // bevel catch-light
  g.lineWidth = 6;
  g.strokeRect(40, 40, 944, 432);
  g.strokeStyle = 'rgba(0,0,0,0.35)';         // and its shadow side
  g.lineWidth = 4;
  g.strokeRect(46, 46, 932, 420);
  g.fillStyle = '#1c1b18';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = 'italic 600 78px Georgia, "Times New Roman", serif';
  g.fillText('New Jersey', 512, 76);
  g.font = 'italic 600 64px Georgia, "Times New Roman", serif';
  g.fillText('Garden State', 512, 444);
  g.font = '700 236px "Arial Narrow", "Helvetica Neue", Arial, sans-serif';
  if ('letterSpacing' in g) g.letterSpacing = '14px';
  g.fillText(PLATE_TEXT, 512, 258);
  // the four mounting bolts
  g.fillStyle = '#3a3a3a';
  for (const [bx, by] of [[110, 60], [914, 60], [110, 452], [914, 452]]) {
    g.beginPath(); g.arc(bx, by, 13, 0, Math.PI * 2); g.fill();
  }
  // Soften: at 16 ft a phone camera does not resolve plate lettering to a
  // crisp edge, and a razor-sharp 1024 px decal on a night car read as
  // "emissive and sharp". A down-and-up bounce through a quarter-size canvas
  // is a cheap ~4 px blur that keeps the characters legible as shapes.
  const s = document.createElement('canvas');
  s.width = 256; s.height = 128;
  const sg = s.getContext('2d');
  sg.drawImage(c, 0, 0, 256, 128);
  g.imageSmoothingEnabled = true;
  g.imageSmoothingQuality = 'high';
  g.drawImage(s, 0, 0, 1024, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  if (renderer) tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  plateTex = tex;
  return tex;
}

// Hangs one plate on the `sign` end of the car (+1 = +Z, -1 = -Z). `g` must
// already be in the scene with its matrices current: the ray is cast in world
// space and the hit is mapped back into g's frame, so this is independent of
// however the car group happens to be placed or turned.
function mountPlate(g, pivot, sign, heights, lbox) {
  const ray = new THREE.Raycaster();
  const cx = (lbox.min.x + lbox.max.x) / 2;
  const zEnd = sign > 0 ? lbox.max.z : lbox.min.z;
  const inv = new THREE.Matrix4().copy(g.matrixWorld).invert();
  const qInv = g.getWorldQuaternion(new THREE.Quaternion()).invert();
  const dir = new THREE.Vector3(0, 0, -sign);
  for (const h of heights) {
    const origin = g.localToWorld(new THREE.Vector3(cx, h, zEnd + sign * 3));
    ray.set(origin, dir.clone().transformDirection(g.matrixWorld));
    const hits = ray.intersectObject(pivot, true);
    for (const hit of hits) {
      if (!hit.object.isMesh || !hit.face) continue;
      const mats = Array.isArray(hit.object.material) ? hit.object.material : [hit.object.material];
      if (mats.some((m) => m && m.transparent)) continue;         // glass
      const p = hit.point.clone().applyMatrix4(inv);
      if (Math.abs(p.z - zEnd) > 1.6) continue;                    // through a grille
      const n = hit.face.normal.clone()
        .transformDirection(hit.object.matrixWorld).applyQuaternion(qInv);
      if (n.z * sign < 0.7) continue;                              // not a facing panel
      const geo = new THREE.BoxGeometry(PLATE_W, PLATE_H, 0.02);
      // Lit by the scene only: no metalness (a metallic plate reflected the
      // car env's white horizon band straight back at the camera), and it is
      // deliberately NOT given the car's own sky below — that sky exists to
      // draw the shoulder line on gloss paint, and on a matte plate it only
      // added a flat glow that read as emissive.
      const rim = new THREE.MeshStandardMaterial({ color: 0xa8a28c, roughness: 0.8, metalness: 0 });
      rim.userData.plateRim = true;
      // emissiveMap is wired from the start (a null -> texture flip would
      // recompile the shader); applyCarSky drives emissiveIntensity 0 by day
      // and PLATE_NIGHT_EMIT at night, and swaps `map` to the washed face.
      const face = new THREE.MeshStandardMaterial({
        map: makePlateTexture(), roughness: 0.75, metalness: 0,
        emissive: 0xffffff, emissiveMap: makePlateTexture(), emissiveIntensity: 0 });
      face.userData.plate = true;
      carEnvMats.add(face);
      carEnvMats.add(rim);
      // BoxGeometry material order: +x -x +y -y +z -z — the text is on +z
      const plate = new THREE.Mesh(geo, [rim, rim, rim, rim, face, rim.clone()]);
      plate.userData.ownGeometry = true;
      plate.castShadow = true;
      plate.position.copy(p).addScaledVector(n, 0.015);
      const m = new THREE.Matrix4().lookAt(
        p.clone().add(n), p, new THREE.Vector3(0, 1, 0));   // +z of the box = n
      plate.quaternion.setFromRotationMatrix(m);
      g.add(plate);
      // the lamp's pool, centred a little above the plate, riding just off
      // the panel so it never z-fights the plate or the bumper
      const glow = new THREE.Mesh(
        new THREE.PlaneGeometry(PLATE_W * 1.9, PLATE_H * 2.2),   // a SMALL lamp's pool, not a floodlit tailgate
        new THREE.MeshBasicMaterial({
          map: makePlateGlowTexture(), color: 0xffc990, transparent: true, opacity: 0,
          blending: THREE.AdditiveBlending, depthWrite: false }));
      glow.userData.ownGeometry = true;
      glow.material.userData.plateGlow = true;
      glow.position.copy(p).addScaledVector(n, 0.05).add(new THREE.Vector3(0, PLATE_H * 0.55, 0));
      glow.quaternion.copy(plate.quaternion);
      glow.renderOrder = 3;
      g.add(glow);
      carEnvMats.add(glow.material);
      return true;
    }
  }
  console.warn(`yard: no panel found for the ${sign > 0 ? 'front' : 'rear'} plate`);
  return false;
}

function addLicensePlates(g, pivot) {
  g.updateWorldMatrix(true, true);
  const lbox = new THREE.Box3().setFromObject(pivot)
    .applyMatrix4(new THREE.Matrix4().copy(g.matrixWorld).invert());
  mountPlate(g, pivot, -1, [3.1, 2.9, 2.7, 3.3, 2.5, 2.3], lbox);   // rear, tailgate
  mountPlate(g, pivot, +1, [2.0, 1.8, 2.2, 1.6, 2.4, 1.4], lbox);   // front, bumper
}

// Puts the tyres ON the slab. carSpot.y is a guess at the drive surface made
// while the yard is planted, and the drive has been re-laid more than once
// since (lo + 0.02, then lo + 0.05): a guess 0.03 ft high floats the car over
// its own shadow and a guess 0.03 ft low sinks the rubber and z-fights the
// contact blobs into the concrete — both of which a critic called
// "levitating". So the car is seated by measurement: one ray straight down
// from above each wheel, against everything in the scene that is not the car
// itself, and the group's origin (the model's bbox bottom, i.e. the tyre
// contact) goes to the highest hit. The blobs ride 0.02-0.03 ft above that,
// which is enough to clear the slab's depth without visibly hovering.
function seatCar(g, wheels) {
  const ray = new THREE.Raycaster();
  const down = new THREE.Vector3(0, -1, 0);
  const isCar = (o) => { for (let p = o; p; p = p.parent) if (p === g) return true; return false; };
  let top = -Infinity;
  for (const [lx, lz] of wheels) {
    const w = g.localToWorld(new THREE.Vector3(lx, 0, lz));
    ray.set(new THREE.Vector3(w.x, w.y + 8, w.z), down);
    for (const hit of ray.intersectObjects(scene.children, true)) {
      if (!hit.object.isMesh || isCar(hit.object)) continue;
      const mats = Array.isArray(hit.object.material) ? hit.object.material : [hit.object.material];
      if (mats.some((m) => m && m.transparent)) continue;   // fog, glass, blobs
      top = Math.max(top, hit.point.y);
      break;   // hits come nearest-first, so the first opaque one is the slab
    }
  }
  if (Number.isFinite(top)) {
    g.position.y = top + 0.005;
    g.updateWorldMatrix(true, true);
  }
}

// Idempotent: called at the end of every yard build and again whenever the
// model id changes. The GLB load is async, so it captures the yard it was
// started for and drops the result if a rebuild has since replaced it.
function syncCar() {
  disposeCar();
  if (!carSpot || !yard) return;
  const { x, y, z, ry } = carSpot;
  if (carModelId == null) {
    carGroup = buildCarPrimitive(x, y, z, ry);
    yard.add(carGroup);
    return;
  }
  const forYard = yard;
  getInstance(carModelId, 'bottom').then((pivot) => {
    if (forYard !== yard) return;   // a rebuild beat us to it
    disposeCar();
    const g = new THREE.Group();
    g.userData.kind = 'driveway-car';   // how a screenshot harness finds it
    g.position.set(x, y, z);
    g.rotation.y = ry + CAR_MODEL_RY;
    pivot.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    giveCarItsOwnSky(pivot);   // models.js already cloned every material
    parkCar(pivot);            // lamps off: it is parked, not arriving
    polishCar(pivot);          // paint/glass/brightwork glossy enough to catch lights
    g.add(pivot);
    // measured off the loaded model, so the blob follows whatever car is in the
    // library rather than a hard-coded X5 footprint. `g` is not in the scene
    // yet, so the box comes back in g's own frame — the pivot is bbox-centred
    // in x/z by models.js, so the centre is ~0 and is used as-is (an earlier
    // pass subtracted the world x from it and put the blob out on the lawn).
    const box = new THREE.Box3().setFromObject(pivot);
    const size = box.getSize(new THREE.Vector3());
    const ctr = box.getCenter(new THREE.Vector3());
    // Tight to the footprint: a wide soft halo reads as ambient murk, a blob
    // just proud of the tyres reads as the car pressing on the concrete.
    const blob = carContactShadow(size.x * 1.25, size.z * 1.1, 0.9);
    blob.position.set(ctr.x, 0.02, ctr.z);
    g.add(blob);
    // and a hard core under each tyre — the one place a parked car's shadow
    // is truly black. Wheel positions are taken off the bbox in proportion
    // (an X5's track is ~0.8 of its mirror-to-mirror width, its wheelbase
    // ~0.6 of its length), so they follow whatever car is in the library.
    // (0.39 x width put the core's outer edge a foot proud of the tyre by
    // day — the bbox width includes the mirrors — so it sits at 0.34.)
    // Each core runs a little past the contact patch on every side: the
    // shadow a tyre casts on the slab is wider than the rubber touching it.
    const wheels = [];
    for (const sx of [-0.34, 0.34]) {
      for (const sz of [-0.30, 0.30]) {
        const wx = ctr.x + sx * size.x, wz = ctr.z + sz * size.z;
        wheels.push([wx, wz]);
        const tyre = carContactShadow(1.9, 3.0, 1.0);
        tyre.position.set(wx, 0.03, wz);
        tyre.renderOrder = 2;
        g.add(tyre);
      }
    }
    carGroup = g;
    yard.add(g);
    seatCar(g, wheels);           // after add: the seating rays need world matrices
    addLicensePlates(g, pivot);   // likewise for the plate mount rays
  }).catch((err) => {
    console.warn(`yard: car model ${carModelId} failed to load:`, err);
    if (forYard !== yard || carGroup) return;
    carGroup = buildCarPrimitive(x, y, z, ry);
    yard.add(carGroup);
  });
}

// Fallback: dark SUV parked nose-in on the driveway (facing -Z, at the garage).
// Read from behind, which is the front-photo angle: wide body, narrower
// greenhouse with a dark glass band, taillights, bumper, tyres proud of the sides.
function buildCarPrimitive(x, y, z, ry) {
  const props = [];
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
  const g = new THREE.Group();
  g.userData.kind = 'driveway-car';   // same tag as the model path, so anything
                                      // looking for the car finds either one
  const mesh = new THREE.Mesh(
    BufferGeometryUtils.mergeGeometries(
      props.map((q) => (q.index ? q.toNonIndexed() : q)), false),
    new THREE.MeshStandardMaterial({
      vertexColors: true, roughness: 0.45, metalness: 0.15, flatShading: true }));
  mesh.userData.ownGeometry = true;
  mesh.castShadow = true;
  // the boxes above are authored in WORLD x/z, so the group sits at the origin
  // and only the heading is applied — about the car, not about the world
  g.add(mesh);
  if (ry) { g.position.set(x, 0, z); mesh.position.set(-x, 0, -z); g.rotation.y = ry; }
  g.position.y += y;
  return g;
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
    // 95.4. Was R.z1 + 34 (75.4), the end of the shell GLB's own driveway
    // strip — but that strip is where the Sketchup model stops, not where the
    // drive does. demo/exterior_night.jpg is shot from the drive itself with
    // concrete filling the bottom of the frame edge to edge, and its
    // photo-matched pose (tools/roomkit/poses.json night_front) stands at
    // z 90; with the street at 75.4 that camera stood in the carriageway and
    // the bottom 300 px of the render were asphalt and a kerb. The lot is
    // 20 ft deeper than the shell's strip; everything street-keyed (sidewalk,
    // kerb, apron, mailbox, lamp-post bed, woodland) moves with it.
    street: R.z1 + 54,
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
  // Subdivided at ~3.5 ft. slab()'s segment arguments default to 1, so round 1
  // laid every lawn patch as a SINGLE QUAD — the whole yard's lawn merged to
  // 30 triangles. That was invisible while the lawn was flat colour; the
  // moment the mown-patch tint went into vertex colours (see buildYard) it
  // meant the field was being sampled at four corners per patch and almost
  // none of it reached the screen.
  const g = (x0, z0, x1, z1, y) => lawns.push(slab(
    x0, z0, x1, z1, y,
    Math.min(90, Math.max(2, Math.round((x1 - x0) / 3.5))),
    Math.min(90, Math.max(2, Math.round((z1 - z0) / 3.5)))));
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
  g(L.padW - 45, L.yardN - 45, L.padE + 45, L.street + 1.0, L.lo);
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
  g(L.padW - 9, L.padF, L.driveL + 0.4, L.street + 1.0, L.lo);
  g(L.driveR - 0.4, L.houseF - 1, L.padE + 9, L.street + 1.0, L.lo);
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
  //    Transverse joints are counted back from the street end now: the night
  //    photograph shows one crossing the drive about 21 ft short of the kerb
  //    and plain concrete from there to the camera's feet, so the last joint
  //    sits at street - 21.4 and the rest step back 12.5 ft from it.
  //    ROUND 7: three transverse joints -- 10 ft off the garage, mid-drive,
  //    and the one 21.4 ft short of the kerb the night photo shows.
  const joints = [];
  for (const z of [L.houseF + 10, L.houseF + 29, L.street - 21.4]) {
    joints.push([L.driveL, z, L.driveR - L.driveL, 0.16]);
  }
  joints.push([(L.driveL + L.driveR) / 2 - 0.08, L.houseF, 0.16, L.street - L.houseF]);
  // two faint tyre-worn lanes into the west bay (the car's track, 5.2 ft)
  const laneX = (L.driveL + L.driveR) / 2 - 5.9;
  const lanes = [[laneX - 2.6, L.houseF + 0.5, L.street - 22, 1.5],
                 [laneX + 2.6, L.houseF + 0.5, L.street - 22, 1.5]];
  // lo + 0.05: above the sidewalk (lo + 0.03) it crosses at the street end,
  // so the crossing reads as driveway, and above the rock beds' gravel
  // (lo + 0.045) that abut its west edge.
  const CONC_Y = L.lo + 0.05;
  addConcrete(L.driveL, L.houseF, L.driveR, L.street - 7.6, CONC_Y, joints, beds, lanes, rng);
  //    The walk. Not a rectangle in front of the steps: demo/exterior_night.jpg
  //    (projected through the night_front pose) shows the concrete west of
  //    the drive as a long FAN — from the steps' full width at the pad face
  //    its west edge runs diagonally from the steps' west corner down to meet
  //    the drive's west edge about 25 ft further out, with the river-rock
  //    strip and its flagstone steppers laid along that diagonal. So: one
  //    flat quad, steps-wide at the top, tapering to nothing at (driveL, walkEnd).
  //    ROUND 6: the fan no longer tapers to a needle at z 70 — the critic
  //    read that as "a narrow straight ribbon". It is a LANDING (steps-wide
  //    at the pad, west edge angling out from the steps' west corner to
  //    x 15.6 at z 58) and then a 4.4 ft band beside the drive that meets it
  //    at a shallow angle (cut from z 63.5 to 68). fanX(z) is the landing's
  //    west edge, which the rock strip, steppers and planter hug.
  //    ROUND 10: the band-and-cut ending of round 6 "dead-ended into lawn
  //    with a hard step-off". The west edge is ONE straight diagonal again,
  //    from the steps' west corner all the way to the drive edge at z 72.5
  //    (the same slope the landing had), so the slab merges into the drive
  //    with no lawn between throat and drive, at the drive's own height,
  //    with a control joint scored along the seam at x = driveL.
  const walkW = L.stepW - 0.4;                   // x 11.6: the slab's west corner
  const walkTopZ = L.stepF + 0.3;                // z 44.8: just off the bottom step
  const bandW = 4.4, bandTop = L.stepF + 13.5;   // (x 15.6 at z 58) fixes the diagonal's slope
  const fanSlope = (L.driveL - bandW - walkW) / (bandTop - walkTopZ);
  const walkEnd = walkTopZ + (L.driveL - walkW) / fanSlope;   // z 72.5: where the edge meets the drive
  const fanX = (z) => Math.min(L.driveL, walkW + fanSlope * Math.max(0, z - walkTopZ));
  concretePoly([
    [walkW, L.padF + 0.4], [L.driveL, L.padF + 0.4], [L.driveL, walkEnd], [walkW, walkTopZ],
  ], CONC_Y, beds);                              // same pour as the drive
  addJoint([L.driveL - 0.08, L.padF + 0.4, 0.16, walkEnd - L.padF - 0.4], CONC_Y, beds);
  // A broad TWO-RISER platform in front of the shell's own narrow steps
  // (x 11..19.5): lower tread top at lo + 0.86, upper at lo + 1.66, the
  // porch edge at 2.13 making the last lip. Both boxes enclose the shell's
  // treads rather than sitting on them, so nothing coplanar z-fights.
  // (tops at 0.92 / 1.72: at 0.86 / 1.66 the shell's own tread edges sat
  // within a hair of the platform tops and drew as faint bands across them)
  // Into `masses`, not `beds`: the beds bucket's grit map is UV'd from world
  // X/Z, so a riser face samples one line of it and streaks top to bottom.
  // Round 9: the TREAD is a separate, lighter top plate (L 0.68 over the
  // riser box's 0.54) so tread and riser read as two planes under a wash.
  // Round 10: treads at L 0.74, risers at 0.58, and a dark nosing shadow
  // line (0.14 ft, L 0.30) along the foot of each riser, so the front reads
  // as two risers and three lit treads rather than one slab.
  for (const [zc, zd, h] of [[L.stepF + 0.7, 3.2, 0.92], [L.stepF - 2.0, 2.4, 1.72]]) {
    const cx = (L.stepW + L.stepE) / 2 - 0.5;
    const step = boxAt(8.6, h, zd, cx, L.lo, zc);
    paintNoisy(step, hsl(0.60, 0.012, 0.58), rng, 0.06); masses.push(step);
    const tread = slab(cx - 4.3, zc - zd / 2, cx + 4.3, zc + zd / 2, L.lo + h + 0.004);
    paintNoisy(tread, hsl(0.60, 0.012, 0.74), rng, 0.04); masses.push(tread);
  }
  {
    const cx = (L.stepW + L.stepE) / 2 - 0.5;
    // foot of the lower riser, on the walk; foot of the upper riser, on the lower tread
    for (const [z, yy] of [[L.stepF + 2.3, CONC_Y + 0.006], [L.stepF - 0.8, L.lo + 0.92 + 0.008]]) {
      const sh = slab(cx - 4.3, z, cx + 4.3, z + 0.14, yy);
      paint(sh, hsl(0.60, 0.012, 0.30)); masses.push(sh);
    }
  }
  // and the same joint treatment: scored across the fan every ~5.5 ft, so
  // that once the path light and porch pools land on it the walk reads as
  // concrete with a shape, not a grey wedge
  for (let z = walkTopZ + 4.5; z < walkEnd - 3; z += 5.5) {
    const jx = fanX(z) + 0.15;
    addJoint([jx, z, L.driveL - 0.2 - jx, 0.16], CONC_Y, beds);
  }

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
  //    NIGHT ROUND (demo/exterior_night.jpg): the drive-side border is no
  //    longer three stacked rectangles. It is ONE polygon strip (addBedPoly)
  //    whose inner edge is the walk fan's diagonal and then the drive's west
  //    edge down to the sidewalk, and whose outer edge is widest beside the
  //    flagstone steppers and tapers toward the street. The front bed's
  //    slate wall now stops at x ~6 where that strip begins, since the
  //    photograph shows the rock running flat past the steps, not walled.
  //    ROUND 4 (blind critic on round 3): the strip is SHORT and FLAT now.
  //    Round 3 ran it 35 ft down the drive to the sidewalk in addBed-sized
  //    stones with a rim of 0.5 ft cobbles, and from the camera that was "a
  //    pile of faceted boulders the size of basketballs running in a straight
  //    diagonal toward the camera, stacked above grade". The photograph has
  //    a ~2 ft band of fist-sized river rock lying at grade between the walk
  //    and the shrub bed for about 10 ft, with two flat steppers crossing
  //    it; the lawn runs to the drive edge beyond. "Front of the house.jpg"
  //    agrees: a low band along the walk/bed edge, and a separate band on
  //    the EAST drive edge (section 5).
  const bedF0 = L.padF + 0.5, bedF1 = L.padF + 6.6;
  const rockY = L.lo + 0.045;
  // ROUND 6: the front bed is a dark MULCH slab with its own edge (the
  // critic: "porch-side plants float on lawn with no mulch or bed edge"),
  // 0.2 ft proud of the lawn; everything planted in it stands on mulchY.
  const mulchY = L.lo + 0.2;
  addMulchBed(rng, L.houseW - 1.4, bedF0, L.stepW - 0.8, bedF1, L.lo, 0.2, beds);
  // ROUND 7: the rock is a BAND now, not a patch -- constant 3 ft width,
  // measured square to the landing's west edge, running with that edge from
  // the foot of the steps (z 47.4) to z 57.5 where the landing meets the
  // drive-side band. Inner edge = the concrete; outer edge = a raised cobble
  // rim against the lawn, so the shape reads when only half of it is lit.
  // Two 18 in round pale steppers sit on its centreline at thirds.
  const stripEnd = L.stepF + 13.0;                        // z 57.5
  const bandTopZ = bedF1 - 0.2;                           // z 47.4
  const ex = L.driveL - bandW - walkW, ez = bandTop - walkTopZ;  // edge direction
  const eL = Math.hypot(ex, ez), nx = -ez / eL, nz = ex / eL;    // unit normal, west
  const BAND_W = 3.0;
  const stepDiscs = addSteppers(rng, [1 / 3, 2 / 3].map((t) => {
    const z = bandTopZ + (stripEnd - bandTopZ) * t;
    return [fanX(z) + nx * BAND_W * 0.5, z + nz * BAND_W * 0.5];
  }), rockY, beds);
  const bandOuter = [[fanX(bandTopZ) + nx * BAND_W, bandTopZ + nz * BAND_W],
                     [fanX(stripEnd) + nx * BAND_W, stripEnd + nz * BAND_W]];
  addBedPoly(rng, [
    [fanX(bandTopZ), bandTopZ], [fanX(stripEnd), stripEnd],
    bandOuter[1], bandOuter[0],
  ], rockY, beds, 13, stepDiscs, 0.17, true);
  // The lawn-side edge: a dark 0.3 ft trench line under a run of SMALL flat
  // stones (sc 0.42). Round 8's rim stones were 0.5 ft cobbles and the
  // band's near end read as "a single rock pile"; the band must stay flat
  // at grade with two parallel edges, and the dark line is what draws the
  // outer edge straight.
  {
    const [[ax, az], [bx, bz]] = bandOuter;
    const L2 = Math.hypot(bx - ax, bz - az), ang = Math.atan2(-(bz - az), bx - ax);
    const trench = boxAt(L2, 0.03, 0.32, (ax + bx) / 2, rockY - 0.01, (az + bz) / 2, ang);
    paint(trench, hsl(0.07, 0.25, 0.20)); beds.push(trench);
  }
  addCobbleRun(rng, [bandOuter[0], bandOuter[1]], rockY, beds, 0.42);
  // the uplight at the strip's far end, lighting the shrubs above it. The
  // fixture body only — eavelights.js puts the light here: x 11.6, z 57.0,
  // base y lo + 0.045 (0.235), 0.42 ft tall.
  addUplightCan(L.stepW - 0.4, L.stepF + 12.5, rockY, props);
  // ONE scalloped stone edge along the raised front bed, ending where the
  // flat rock strip takes over
  addStoneEdge(rng, [
    [L.houseW - 1.6, bedF0 - 0.6], [L.houseW - 1.7, bedF1 - 1.2],
    [L.houseW + 3.0, bedF1 + 0.15], [L.stepW - 3.5, bedF1 + 0.2],
  ], L.lo, 0.62, beds);

  // A mixed row, not nine copies of one boxwood ball: four species, sizes
  // from 0.9 to 2.1 ft, and a salvia drift in front of them — on the WEST
  // two-thirds of the bed. The east end, beside the steps, is hand-placed
  // from the night photograph (left to right): a big pale rounded shrub, the
  // lit ORANGE mum, a dark-red mum, a low boxwood, a straw-coloured
  // ornamental grass, then the dark-red mum PLANTER hard against the steps.
  // ROUND 8: the porch's WEST half is a long low bed of DRIED hydrangea and
  // mum clumps (muted rust / straw / cream, the night photograph's November
  // bed), not the July boxwood-and-salvia row -- five varied clumps with
  // straw tufts between, and a scatter of irregular cobbles along the
  // mulch's front edge.
  const SP = ['boxwood', 'boxwood', 'euonymus', 'juniper', 'yew'];   // still used by the east bed
  const DRIED = ['cream', 'straw', 'rust', 'straw', 'cream', 'rust'];
  let di = 0;
  for (let x = L.houseW - 0.2; x < L.stepW - 10.5; x += 2.6 + rng() * 1.2) {
    addDriedClump(rng, x, bedF0 + 1.4 + rng() * 2.2, 1.05 + rng() * 0.55, mulchY,
                  leaves, DRIED[di++ % DRIED.length]);
    if (rng() < 0.6) addGrassClump(rng, x + 1.3, bedF0 + 0.9 + rng() * 1.2, mulchY, leaves, true);
  }
  for (let x = L.houseW - 0.8; x < L.stepW - 1.5; x += 0.9 + rng() * 0.9) {
    const r = 0.16 + rng() * 0.16;
    const c = new THREE.IcosahedronGeometry(r, 0);
    c.scale(1 + rng() * 0.5, 0.55, 1 + rng() * 0.5);
    c.rotateY(rng() * 6.283);
    c.translate(x, mulchY + r * 0.2, bedF1 - 0.35 - rng() * 0.5);
    paint(c, hsl(0.58 + rng() * 0.05, 0.05, 0.36 + rng() * 0.3)); beds.push(c);
  }
  // (round 4: all lumpy clusters, not smooth spheres; mums rust and gold)
  addBoxwood(rng, L.stepW - 9.0, bedF0 + 2.6, 1.6, mulchY, leaves, 'euonymus', true);
  addMum(rng, L.stepW - 6.4, bedF0 + 3.4, 1.2, mulchY, leaves, 0.075, 0.62, 0.40); // burnt orange
  addMum(rng, L.stepW - 4.3, bedF0 + 2.6, 1.1, mulchY, leaves, 0.045, 0.55, 0.32); // rust
  // and green low shrubs mixed through the dried clumps, so the bed is not a
  // row of one thing
  addBoxwood(rng, L.houseW + 3.2, bedF0 + 3.6, 0.85, mulchY, leaves, 'boxwood', true);
  addBoxwood(rng, L.houseW + 8.4, bedF0 + 1.6, 0.95, mulchY, leaves, 'juniper', true);
  addBoxwood(rng, L.stepW - 2.5, bedF0 + 3.4, 0.9, mulchY, leaves, 'boxwood', true);
  addGrassClump(rng, L.stepW - 1.2, bedF0 + 1.9, mulchY, leaves, true);
  // and four dry tufts between and behind the mums, so the bed is a mass
  // of clumps rather than three balls in a row
  for (const [tx, tz] of [[L.stepW - 7.6, bedF0 + 1.5], [L.stepW - 5.4, bedF0 + 1.3],
                          [L.stepW - 3.4, bedF0 + 1.7], [L.stepW - 5.3, bedF0 + 4.4]]) {
    addGrassClump(rng, tx, tz, mulchY, leaves, true);
  }
  {
    // the planter at the foot of the steps, on the lawn just west of the
    // landing (clear of the new step platform, which reaches z 46.8):
    // a LOW pot, knee-high with its mum (round 1's 0.95 ft pot under a 0.7 ft
    // ball stood 2.4 ft and read as a lollipop)
    const px = fanX(L.stepF + 2.8) - 0.9, pz = L.stepF + 2.8;
    const pot = cylAt(0.5, 0.38, 0.55, 10, px, L.lo + 0.02, pz);
    paint(pot, _c.setHex(0x2a2320)); props.push(pot);
    addMum(rng, px, pz, 0.62, L.lo + 0.47, leaves, 0.04, 0.50, 0.30);
  }
  // Lawn, not rock, between the strip's end and the street: the drive-side
  // border the earlier rounds ran to the sidewalk is in neither photograph.
  // (the two cast geese are gone from the night frame: with the pot beside
  // them they read as "three identical candle lanterns" from 40 ft)
  // Leaf litter and dead grass on the lawn between the bed, the strip and
  // the drive, and along the drive's west edge toward the street — so the
  // lawn has something to catch the fixture spill instead of being a void.
  // (round 7: ~100 flecks in five drifts against the bed edge and the
  // band's lawn side; the 260-fleck field read as a brown plane with a
  // hard edge along the drive)
  addLeafLitter(rng, [
    [L.houseW + 6, bedF1 + 2.2, 3.6, 24], [L.houseW - 0.5, bedF1 + 1.8, 3.0, 16],
    [L.stepW - 4.2, L.stepF + 7.5, 2.6, 22], [L.stepW - 1.5, L.stepF + 13.5, 2.6, 20],
    [L.stepW - 6.5, L.stepF + 12, 2.2, 14],
  ], (x, z) => {
    if (z < bedF1 + 0.3 && x < L.stepW - 0.6) return false;       // the mulch bed
    if (z < stripEnd + 1.4 && x > fanX(z) + nx * (BAND_W + 0.4)) return false; // the band
    return x < fanX(z) - 0.3;                                     // never the walk
  }, L.lo + 0.02, beds);

  // 5. The EAST bed: the rock border down the far side of the drive, running
  //    the whole way to the street, with the salvia mass, the low hedge
  //    behind it and the small tree of "Front of the house.jpg" x 1230-1560.
  addBed(rng, L.driveR + 0.6, L.houseF + 3, L.driveR + 10.5, L.street - 19,
         L.lo + 0.04, beds, BED_DENSITY, false, 0.22);
  addStoneEdge(rng, [[L.driveR + 10.8, L.houseF + 3], [L.driveR + 11.0, L.apronF],
                     [L.driveR + 10.4, L.street - 19]], L.lo, 0.40, beds);
  // The corner group by the garage — the night photograph's right-hand bed
  // of low shrubs with two warm uplights, hard against the drive's east edge
  // at the garage corner. Cans only here; the lights are eavelights.js's.
  addBoxwood(rng, L.driveR + 1.9, L.houseF + 4.4, 1.05, L.lo + 0.04, leaves, 'juniper', true);
  addBoxwood(rng, L.driveR + 3.4, L.houseF + 7.6, 1.2, L.lo + 0.04, leaves, 'boxwood', true);
  addBoxwood(rng, L.driveR + 1.7, L.houseF + 10.4, 0.9, L.lo + 0.04, leaves, 'euonymus', true);
  // (no fixture cans here: the only can in the yard is the one at the rock
  // band's end -- repeated identical fixtures were the round-7 tell)
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
  // the squat black path light stands on the rock right at the walk fan's
  // west edge, a step or two out from the bottom step (night photograph)
  addPathLight(fanX(L.stepF + 3.2) - 0.7, L.stepF + 3.2, rockY, props);  // clear of the first stepper

  // 6. The lamp-post bed, at the street end and EAST of the drive, between
  //    the drive and the sidewalk — which is where "Front of the house, a
  //    little bit of the garage and car pointing to a different house.jpg"
  //    puts it: a black lantern on a slim post standing in a sheet of green
  //    groundcover with ornamental grasses behind, edged in river rock.
  //    (Round 2's critic said this bed appears in no photograph; that
  //    photograph is the evidence it does — what was wrong was its SITE.)
  // Ends at street - 12.4: the sidewalk starts at street - 12, and the old
  // street - 8.0 ran the cobble field 4 ft under it.
  addBed(rng, L.driveR + 1.2, L.street - 19, L.driveR + 12.5, L.street - 12.4,
         L.lo + 0.03, beds, BED_DENSITY, false);
  addStoneEdge(rng, [[L.driveR + 12.7, L.street - 19], [L.driveR + 12.4, L.street - 15],
                     [L.driveR + 11.8, L.street - 12.5]], L.lo, 0.38, beds);
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
  // Recorded, not built: syncCar() puts either the GLB or the primitive here
  // once the yard is complete. The drive runs x 20.8..47.1; the car sits in
  // the west bay, nose at the garage, as it does in the front photographs.
  // Sited from demo/exterior_night.jpg through the photo-matched
  // "night_front" pose (eye at [27,4,90], fov 92): the tailgate is ~16 ft
  // from the lens, so the rear sits at z ~74 and the 16 ft X5 noses to z ~58
  // — nearly 30 ft of open concrete between it and the garage door, which is
  // what the photo shows once the house is scaled right. Solved by projecting
  // the car's rear plate and body width through the pose against the photo
  // (plate x 604/900, body 254 px wide incl. mirrors), not by eye: x 27.7
  // centres it on the west bay, z 65.8 sizes it. Earlier rounds sited it
  // against a pose whose house was ~10% too large and 50 px right, which put
  // the car 4 ft too far west and 5 ft too close — re-solve if the pose moves.
  // Round 7 re-measured the dark silhouette row by row against the photo at
  // 900x1200: rear width 230 vs 216 px (6.5% wide), roof top 7 px high --
  // i.e. ~1.1 ft too close. z 64.7 now; x unchanged (left edges agreed).
  carSpot = { x: L.driveL + 6.9, y: L.lo + 0.02,
              z: L.houseF + 35.2, ry: 0 };
  // The bin stands just past the garage's EAST corner ("Front of the house"
  // x 1195), not in front of the door.
  addBin(L.driveR + 0.9, L.houseF + 0.9, props);
  // Black urns at the two garage corners. The two used to stand within a
  // foot of each other at the west corner; the day photograph has one at
  // each jamb, and the night one shows the west urn full of ORANGE mums.
  for (const [ux, uz] of [[L.driveL + 1.0, L.houseF + 2.2], [L.driveR - 0.9, L.houseF + 1.5]]) {
    const urn = cylAt(0.85, 0.55, 1.25, 10, ux, L.lo, uz);
    paint(urn, _c.setHex(0x24252a)); props.push(urn);
  }
  addMum(rng, L.driveL + 1.0, L.houseF + 2.2, 0.95, L.lo + 1.05, leaves, 0.075, 0.65, 0.42);

  // 8. Framing trees. The front photograph is framed top-left and top-right by
  //    mature canopies overhanging the drive; without them the house reads as
  //    standing in an open field.
  // This one also stands over the Sketchup scale FIGURE baked into the shell's
  // merged Root_Node mesh at x -16.5, z 44.7 — it cannot be hidden separately.
  addShadeTree(rng, L.driveL - 37, L.apronF - 5.6, 1.8, trunks, leaves);
  addShadeTree(rng, L.driveR + 22, L.apronF + 2, 1.35, trunks, leaves);
  addShadeTree(rng, L.driveR + 26, L.houseF + 4, 1.2, trunks, leaves);
  // 8b. BARE silhouettes at both edges of the night frame. demo/exterior_
  //     night.jpg has leafless canopies against the sky at far left and far
  //     right, and the blue landscape light at the far left lands on a
  //     tree/shrub mass there. Planted explicitly (not through PLANT_TREES,
  //     which stays false for the day-lit yard), as a mass west of the
  //     porch's west return and one beyond the garage. Heights 26-36 ft:
  //     from night_front (pos [27,4,90]) a 30 ft crown 55 ft out breaks the
  //     skyline ~380 px above the horizon. Two lumpy shrubs sit under the
  //     west mass for the blue light to find.
  addBareTree(rng, L.houseW - 12.5, L.houseF + 3.5, 34, trunks);
  addBareTree(rng, L.houseW - 7.5, L.houseF + 11.0, 29, trunks);
  addBareTree(rng, L.houseW - 11.0, L.houseF + 15.5, 26, trunks);
  // and a dark undergrowth mass beneath and among those trunks (r 3-5 ft
  // blobs), so the blue landscape light lands on a mass, not on sticks
  addUndergrowth(rng, [
    [L.houseW - 15.0, L.houseF + 1.5, 4.6], [L.houseW - 10.0, L.houseF + 6.0, 3.8],
    [L.houseW - 13.5, L.houseF + 10.5, 4.2], [L.houseW - 7.0, L.houseF + 14.0, 3.4],
    [L.houseW - 12.0, L.houseF + 17.5, 3.6], [L.houseW - 4.5, L.houseF + 9.0, 3.0],
  ], leaves);
  addBareTree(rng, L.padE + 6.0, L.houseF + 4.5, 31, trunks);
  addBareTree(rng, L.padE + 11.0, L.houseF + 13.0, 27, trunks);
  addBoxwood(rng, L.houseW - 8.0, L.padF + 2.5, 1.6, L.lo, leaves, 'euonymus', true);
  addBoxwood(rng, L.houseW - 5.0, L.padF + 4.5, 1.3, L.lo, leaves, 'juniper', true);
  // 8d. The BACKGROUND tree line: bare crowns behind and beside the house
  //     that show above the garage ridge (18.2 ft) at right and behind the
  //     porch roof at left from night_front -- the photograph's sky is not
  //     a void, it has silhouettes bleeding into a low glow. An irregular
  //     row: beside the house (x outside the block) at z -12..-30, behind
  //     it (x across the block) at z -32..-44 so nothing stands in a room;
  //     30-45 ft tall, 9-14 ft apart, plus two big crowns east of the
  //     garage. About 1,500 five-sided cylinders in the one bark draw call.
  //     Behind the GARAGE wing they stand closer (z -14..-24, right behind
  //     its rear wall) and taller: at z -38 a 40 ft crown 128 ft out sits
  //     only ~60 px above the garage ridge and vanished into the roofline.
  for (let x = L.houseW - 24; x < L.padE + 26; x += 9 + rng() * 5) {
    const inMain = x > L.houseW - 3 && x < L.blockE + 1;
    const inWing = x >= L.blockE + 1 && x < L.padE + 3;
    const z = inMain ? L.blockN - 8 - rng() * 12
            : inWing ? L.wingN - 3 - rng() * 10 : L.wingN - 1 - rng() * 18;
    const h = inWing ? 38 + rng() * 8 : 30 + rng() * 15;
    addBareTree(rng, x + (rng() - 0.5) * 3, z, h, trunks);
  }
  addBareTree(rng, L.padE + 11.5, L.houseF + 6.5, 42, trunks);
  addBareTree(rng, L.padE + 19.5, L.houseF - 5.5, 38, trunks);
  // 8c. Dark hedge masses that BURY the horizon at both frame edges (the
  //     whole-frame critic: "no flat ground plane meets a flat sky"). From
  //     night_front the eye is 4 ft up, so anything under ~5 ft cannot cross
  //     the horizon line; these are 6.5-8 ft. West: a diagonal run on the
  //     lawn beyond the bed; east: a line up the garage's east flank.
  addHedgeMass(rng, [[L.houseW - 4.0, L.padF + 11], [L.houseW - 13.0, L.padF + 22]], 6.5, leaves);
  addHedgeMass(rng, [[L.padE + 4.0, L.houseF + 3.5], [L.padE + 9.5, L.houseF - 11]], 8.0, leaves);

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
  // straddles the pad's rear edge, which is where "Backyard v3 5" puts the
  // mulch border: on the far edge of the lawn, not out beyond it
  addBed(rng, L.padW - 2, yN - 2.6, L.padE + 2, yN + 2.6, L.lo + 0.04, beds, 4.4);
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
    addGrassClump(rng, x, yN - 0.4 + (rng() - 0.5) * 3, L.lo + 0.04, leaves);
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
// ===========================================================================
// EDITABLE YARD
//
// The exterior is not stored piece by piece. Every tree, bed, slab and prop
// above is drawn by this file from one fixed seed, identically on every load.
// That is what makes it cheap, and it is also what made it uneditable: by the
// time the yard reaches the screen it is six merged meshes, and a tree has no
// more identity in them than a vertex does.
//
// So editing works by DELTA. While the yard builds, every geometry it produces
// is attributed to an "item" — one tree, one shrub, one slab of driveway — and
// each item gets a key derived from what it is and where the builder put it
// (see itemKey). The backend stores nothing but the changes made against those
// keys: a nudge, a spin, a scale, an erase, a duplicate. On the next load the
// yard is generated exactly as before and the deltas are laid on top, so an
// untouched yard is identical to the one this file drew before any of this
// existed, and an edited one is that yard plus the edits.
//
// Item boundaries come from two rules:
//   * a call to one of the factories in ITEM_FACTORIES opens an item and
//     everything it pushes belongs to it. Nested factory calls stay inside the
//     outer item, so a shrub built out of three lumps is one shrub;
//   * geometry pushed with no factory open joins a RUN: consecutive loose
//     pushes form a single item. That is what keeps a hand-built step platform
//     or a scattered row of cobbles as one thing you can grab.
// ===========================================================================

// A geometry bucket that also records which item each geometry came from.
// Drop-in for the plain arrays the yard builders push into — they only ever
// call .push() and read .length.
class Bucket {
  constructor(name) {
    this.name = name;
    this.geos = [];
    this.own = [];        // parallel to geos: owning item index
  }

  push(...gs) {
    for (const g of gs) {
      const owner = ownerForPush();
      items[owner].geos.push({ bucket: this.name, i: this.geos.length });
      this.geos.push(g);
      this.own.push(owner);
    }
    return this.geos.length;
  }

  get length() { return this.geos.length; }
}

let items = [];        // rebuilt from scratch by every buildYard
let itemsByKey = new Map();
let curItem = -1;      // the open factory item, -1 for none
let looseRun = -1;     // the open run of unscoped pushes, -1 for none

function newItem(kind, label) {
  items.push({ kind, label, geos: [], key: '', pivot: [0, 0, 0], edit: null });
  return items.length - 1;
}

// Who owns the geometry being pushed right now: inside a factory, that
// factory's item; outside, the current loose run, opening one if this is the
// first loose push since the last factory closed.
function ownerForPush() {
  if (curItem >= 0) return curItem;
  if (looseRun < 0) looseRun = newItem('piece', 'Yard piece');
  return looseRun;
}

// Wrap a yard factory so everything it pushes is attributed to one item.
// Reassigning the function declaration is deliberate: every call site above
// resolves the binding at call time — including the
// `(cond ? addConifer : addDeciduous)(...)` dispatch — so no call site changes.
function scoped(kind, label, fn) {
  return function (...args) {
    if (curItem >= 0) return fn.apply(this, args);   // nested: stay in the outer item
    looseRun = -1;                                   // a factory ends any loose run
    curItem = newItem(kind, label);
    try {
      return fn.apply(this, args);
    } finally {
      curItem = -1;
    }
  };
}

// What counts as one grabbable piece of the yard. Everything that draws a
// discrete object is here; the pure helpers (slab, boxAt, paint…) are not,
// because they are the material these are built out of, not things in
// themselves. Getter/setter pairs rather than names because a module binding
// cannot be reached by string without eval.
const ITEM_FACTORIES = [
  ['lawn', 'Lawn', () => addGroundCover, (f) => (addGroundCover = f)],
  ['tree', 'Shade tree', () => addShadeTree, (f) => (addShadeTree = f)],
  ['tree', 'Bare tree', () => addBareTree, (f) => (addBareTree = f)],
  ['tree', 'Conifer', () => addConifer, (f) => (addConifer = f)],
  ['tree', 'Deciduous tree', () => addDeciduous, (f) => (addDeciduous = f)],
  ['tree', 'Weeping tree', () => addWeeper, (f) => (addWeeper = f)],
  ['shrub', 'Bush', () => addBush, (f) => (addBush = f)],
  ['shrub', 'Shrub', () => addBoxwood, (f) => (addBoxwood = f)],
  ['shrub', 'Photinia', () => addPhotinia, (f) => (addPhotinia = f)],
  ['shrub', 'Shrub mound', () => addMound, (f) => (addMound = f)],
  ['shrub', 'Hedge', () => addHedgeMass, (f) => (addHedgeMass = f)],
  ['shrub', 'Undergrowth', () => addUndergrowth, (f) => (addUndergrowth = f)],
  ['plant', 'Mum', () => addMum, (f) => (addMum = f)],
  ['plant', 'Dried clump', () => addDriedClump, (f) => (addDriedClump = f)],
  ['plant', 'Perennials', () => addPerennial, (f) => (addPerennial = f)],
  ['plant', 'Grass clump', () => addGrassClump, (f) => (addGrassClump = f)],
  ['plant', 'Ground cover', () => addGroundCoverMass, (f) => (addGroundCoverMass = f)],
  ['bed', 'Planting bed', () => addBed, (f) => (addBed = f)],
  ['bed', 'Rock bed', () => addBedPoly, (f) => (addBedPoly = f)],
  ['bed', 'Mulch bed', () => addMulchBed, (f) => (addMulchBed = f)],
  ['bed', 'Leaf litter', () => addLeafLitter, (f) => (addLeafLitter = f)],
  ['edge', 'Cobble rim', () => addCobbleRim, (f) => (addCobbleRim = f)],
  ['edge', 'Cobble run', () => addCobbleRun, (f) => (addCobbleRun = f)],
  ['edge', 'Stone edge', () => addStoneEdge, (f) => (addStoneEdge = f)],
  ['edge', 'Retaining slate', () => addSlate, (f) => (addSlate = f)],
  ['paving', 'Concrete', () => addConcrete, (f) => (addConcrete = f)],
  ['paving', 'Concrete pour', () => concretePoly, (f) => (concretePoly = f)],
  ['paving', 'Flagstones', () => addFlagstones, (f) => (addFlagstones = f)],
  ['paving', 'Stepping stones', () => addSteppers, (f) => (addSteppers = f)],
  ['paving', 'Control joint', () => addJoint, (f) => (addJoint = f)],
  ['prop', 'Uplight', () => addUplightCan, (f) => (addUplightCan = f)],
  ['prop', 'Path light', () => addPathLight, (f) => (addPathLight = f)],
  ['prop', 'Wheelie bin', () => addBin, (f) => (addBin = f)],
  ['prop', 'Bird feeder', () => addFeeder, (f) => (addFeeder = f)],
  ['prop', 'Goose', () => addGoose, (f) => (addGoose = f)],
  ['building', 'Neighbour', () => addNeighbour, (f) => (addNeighbour = f)],
  ['street', 'Street', () => addStreet, (f) => (addStreet = f)],
];

let scopesInstalled = false;

function installItemScopes() {
  if (scopesInstalled) return;
  scopesInstalled = true;
  for (const [kind, label, get, set] of ITEM_FACTORIES) set(scoped(kind, label, get()));
}

// ---- identity --------------------------------------------------------------
//
// A key has to survive a rebuild, and ideally survive an edit to this file that
// leaves the piece itself alone. Ordinals fail the second test — insert one
// tree and every key after it shifts by one — so a key is the piece's KIND plus
// the position the builder gave it, in tenths of a foot. Two pieces of one kind
// at the same spot get a disambiguating suffix, only ever reached by coincident
// geometry.
function itemKey(item, used) {
  const [cx, , cz] = item.pivot;
  let key = `${item.kind}:${Math.round(cx * 10)}:${Math.round(cz * 10)}`;
  if (used.has(key)) {
    let n = 2;
    while (used.has(`${key}#${n}`)) n++;
    key = `${key}#${n}`;
  }
  used.add(key);
  return key;
}

const _ibox = new THREE.Box3();
const _ivec = new THREE.Vector3();

// An item's pivot: the centre of its footprint at its lowest point, so a tree
// turns about its trunk and grows up from the ground rather than out of it.
function measureItem(item, buckets) {
  _ibox.makeEmpty();
  for (const { bucket, i } of item.geos) {
    const g = buckets[bucket].geos[i];
    if (!g.boundingBox) g.computeBoundingBox();
    _ibox.union(g.boundingBox);
  }
  if (_ibox.isEmpty()) return [0, 0, 0];
  _ibox.getCenter(_ivec);
  return [_ivec.x, _ibox.min.y, _ivec.z];
}

// ---- the stored edits ------------------------------------------------------

let yardEdits = [];        // rows straight from the backend
let yardEditing = false;   // is the Outside editor open?

// house.yard from GET /api/house, or the standalone GET /api/house/yard.
export function setYardEdits(rows) {
  yardEdits = Array.isArray(rows) ? rows : [];
}

export function getYardEdits() {
  return yardEdits;
}

// The editor draws the yard one mesh per item so each piece can be picked and
// dragged; the viewer keeps the six merged meshes. Returns true if the mode
// actually changed, so callers know whether a rebuild is owed.
export function setYardEditing(on) {
  if (yardEditing === !!on) return false;
  yardEditing = !!on;
  applyYardVisibility();
  buildYard();
  return true;
}

export function isYardEditing() {
  return yardEditing;
}

// Every item in the yard as it currently stands, for the editor's list and
// for restoring erased pieces.
export function getYardItems() {
  return items;
}

export function getYardItem(key) {
  return itemsByKey.get(key) || null;
}

// The per-item groups the editor raycasts against. Empty unless the editor is
// open — in view mode there are no per-item meshes to hit.
// Re-run the whole build. Needed only when the item SET changes (a duplicate,
// a reset-everything); a move/turn/scale is live on the group already and an
// erase is a visibility flip, so neither pays for this.
export function rebuildYard() {
  buildYard();
}

// Fold one saved override into the local copy of the edits, so the next
// rebuild sees it without re-fetching the house.
export function applyYardEdit(key, patch) {
  const row = yardEdits.find((e) => e.key === key);
  if (row) Object.assign(row, patch);
  else yardEdits.push({ key, ...IDENTITY_EDIT, ...patch });
  const item = itemsByKey.get(key);
  if (item) item.edit = yardEdits.find((e) => e.key === key);
}

export function dropYardEdit(key) {
  yardEdits = yardEdits.filter((e) => e.key !== key);
  const item = itemsByKey.get(key);
  if (item) item.edit = null;
}

// Kinds that are GROUND rather than something standing on it. The lawn is one
// item covering the whole lot, so left clickable it swallows every click on
// open grass -- you could never deselect, and never reach anything lying flat
// on it. Same rule objects.js applies to room-wide floors and ceilings, for the
// same reason. It stays an item and still takes edits; it just is not what a
// click on the yard means.
const SURFACE_KINDS = new Set(['lawn']);

// Every per-item group in the yard. Empty unless the editor is open -- in view
// mode the yard is six merged meshes and there is nothing per-piece to hit.
export function getYardPickables() {
  if (!yardEditing || !yard) return [];
  return yard.children.filter((o) => o.userData?.kind === 'yard');
}

// What a CLICK may land on: the pickables minus the ground.
export function getYardClickTargets() {
  return getYardPickables().filter((o) => !SURFACE_KINDS.has(o.userData.yardKind));
}

const IDENTITY_EDIT = { dx: 0, dy: 0, dz: 0, rot_y: 0, scale: 1, deleted: 0 };

function editFor(key) {
  return yardEdits.find((e) => e.key === key && !e.src) || null;
}

// T(pivot + d) · Ry · S · T(-pivot): turn and scale a piece about its own base,
// then move it. Returns null for an untouched piece so the common path costs
// nothing.
function editMatrix(pivot, edit) {
  if (!edit) return null;
  const dx = edit.dx || 0, dy = edit.dy || 0, dz = edit.dz || 0;
  const ry = edit.rot_y || 0, s = edit.scale ?? 1;
  if (!dx && !dy && !dz && !ry && s === 1) return null;
  const [px, py, pz] = pivot;
  return new THREE.Matrix4()
    .makeTranslation(px + dx, py + dy, pz + dz)
    .multiply(new THREE.Matrix4().makeRotationY(ry))
    .multiply(new THREE.Matrix4().makeScale(s, s, s))
    .multiply(new THREE.Matrix4().makeTranslation(-px, -py, -pz));
}

export function setEnvironmentData(house) {
  lastHouse = house;
  setYardEdits(house?.yard);   // overrides on the generated exterior
  remeasureShell();
  buildYard();
  settleShellAnchors();
}

// The shell has not finished settling the moment main() hands us the house.
// Measured on this machine: the roofRect this build sees is z0 -25.43 / z1
// 41.36, and one frame later the same measurement gives -25.77 / 41.70. The
// entire yard is laid out from that rect, so the yard drawn at boot was NOT the
// yard any later rebuild produced -- open the planner, hit undo, or sync, and
// the whole exterior quietly shifted and reshuffled. Nothing noticed while the
// yard was anonymous geometry; the Outside editor made it visible, because a
// piece has to still be the same piece across a rebuild to be editable at all.
//
// So: re-measure a few times over the first half second and rebuild only if the
// anchors really moved. The guard is the one levelChanged has always used, and
// a settled shell makes every check after the first a no-op. setTimeout rather
// than requestAnimationFrame on purpose -- rAF is paused in a backgrounded or
// occluded tab, and the yard must settle whether or not anyone is watching.
const ANCHOR_SETTLE_MS = [0, 120, 500];

function settleShellAnchors() {
  for (const ms of ANCHOR_SETTLE_MS) {
    setTimeout(() => { if (lastHouse && remeasureShell()) buildYard(); }, ms);
  }
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

  // Before the teardown sweep below, not after: see disposeCar().
  disposeCar();
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
  carSpot = null;       // re-recorded by addFrontYard, if there is a shell
  // Recording buckets, not plain arrays: they file every geometry under the
  // item that pushed it, which is what makes an individual tree editable
  // afterwards. The builders below only ever .push() and read .length, so
  // nothing about how the yard is drawn changes. See "EDITABLE YARD" above.
  installItemScopes();
  items = [];
  curItem = -1;
  looseRun = -1;
  const trunks = new Bucket('trunks'), leaves = new Bucket('leaves');
  const beds = new Bucket('beds'), props = new Bucket('props');
  const lawns = new Bucket('lawns'), masses = new Bucket('masses');
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

  // ---- resolve items, apply the stored edits, emit ------------------------
  //
  // Everything above pushed geometry in WORLD coordinates and, along the way,
  // told each Bucket which item it belonged to. Now the items get their
  // identity (a key derived from where the builder put them), the user's saved
  // deltas are laid on top, and the result is drawn — six merged meshes for the
  // viewer, one mesh per item while the Outside editor is open so each piece
  // can be picked and dragged.
  const buckets = { lawns, beds, props, masses, trunks, leaves };

  // Drop the items that drew nothing, BEFORE keys are handed out. A factory
  // gated off by a build flag — PLANT_TREES and BUILD_NEIGHBOURS are both
  // false — still opens an item and then pushes no geometry, and there are 108
  // of those here. They are unselectable, and worse, an item with no geometry
  // measures at the origin, so every one of them keys to 0,0 and takes a
  // collision suffix: 106 keys whose identity would shift the day either flag
  // moves. Nothing can own geometry through a dropped item, so compacting the
  // list only has to renumber the survivors.
  const remap = new Int32Array(items.length).fill(-1);
  const kept = [];
  for (let i = 0; i < items.length; i++) {
    if (!items[i].geos.length) continue;
    remap[i] = kept.length;
    kept.push(items[i]);
  }
  for (const b of Object.values(buckets)) {
    for (let i = 0; i < b.own.length; i++) b.own[i] = remap[b.own[i]];
  }
  items = kept;

  const used = new Set();
  itemsByKey = new Map();
  for (const item of items) {
    item.pivot = measureItem(item, buckets);
    item.key = itemKey(item, used);
    item.edit = editFor(item.key);
    itemsByKey.set(item.key, item);
  }

  // Clones: an extra copy of a piece that already exists, with its own key and
  // its own delta measured from the ORIGINAL's pivot — so "duplicate, then drag
  // it 10 ft east" is exactly dx: 10. Cloned from the source's geometry before
  // any deletion filtering, so a piece can be erased and still have copies.
  for (const row of yardEdits) {
    if (!row.src) continue;
    const src = itemsByKey.get(row.src);
    if (!src) continue;   // the source no longer exists in the build
    const idx = newItem(src.kind, src.label);
    const clone = items[idx];
    clone.key = row.key;
    clone.pivot = src.pivot.slice();
    clone.edit = row;
    clone.isClone = true;
    for (const { bucket, i } of src.geos) {
      const b = buckets[bucket];
      clone.geos.push({ bucket, i: b.geos.length });
      b.geos.push(b.geos[i].clone());
      b.own.push(idx);
    }
    itemsByKey.set(row.key, clone);
  }

  // World-space surface detail, derived per geometry rather than per merged
  // mesh so it survives being split into per-item meshes. Same maths as before:
  // the lawn re-derives its UVs the way the 1200 ft grass disc does and carries
  // the large-scale mown patchiness in vertex colours (three octaves at
  // 54 / 19 / 7 ft, sampled in world feet, so it never repeats and interpolates
  // smoothly across slab()'s cells); the hardscape takes one grain scale
  // across slabs of very different sizes. Read from the position the BUILDER
  // gave the geometry, so an untouched yard is pixel-identical to before and a
  // moved slab carries its own grain with it.
  for (const g of lawns.geos) {
    const pos = g.attributes.position, uv = g.attributes.uv;
    const col = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), z = pos.getZ(i);
      uv.setXY(i, x / 2400 + 0.5, -z / 2400 + 0.5);
      const f = 1 + (worldNoise(x, z, 54) - 0.5) * 0.14
                  + (worldNoise(x + 313, z + 129, 19) - 0.5) * 0.19
                  + (worldNoise(x + 91, z - 47, 7) - 0.5) * 0.11;
      col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = f;
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    uv.needsUpdate = true;
  }
  for (const g of beds.geos) {
    const pos = g.attributes.position, uv = g.attributes.uv;
    for (let i = 0; i < pos.count; i++) uv.setXY(i, pos.getX(i) / 6, -pos.getZ(i) / 6);
    uv.needsUpdate = true;
  }

  // One material per bucket, shared by every mesh drawn from it. Created here
  // rather than at the merge sites because the per-item path needs the same
  // six, and because the yard disposes its own materials on rebuild (which is
  // why the lawn cannot simply reuse grassMat).
  const lawnMat = new THREE.MeshStandardMaterial({
    color: grassMat.color.clone(), map: grassMat.map, roughness: 1,
    vertexColors: true });
  // registered so weather.js's wet/snow tint still reaches the yard's lawn;
  // skipped when there is no lawn, or the list would collect a material no
  // mesh owns and the rebuild teardown would never dispose it
  if (lawns.length) yardGrassMats.push(lawnMat);
  const MATS = {
    lawns: lawnMat,
    // Fine grain on the hardscape. Vertex colours alone gave the driveway
    // sd 3.7 / mean|Δ| 0.30 against the photograph's 10.8 / 6.3 — the right
    // average value and no texture at the scale the eye reads, which is the
    // "sd is scale-blind" trap. A near-white 4 ft noise tile multiplies into
    // the same vertex colours for every bed, wall and slab in both yards.
    beds: new THREE.MeshStandardMaterial({
      vertexColors: true, map: makeGritTexture(), roughness: 1, flatShading: true }),
    props: new THREE.MeshStandardMaterial({
      vertexColors: true, roughness: 0.45, metalness: 0.15, flatShading: true }),
    // Background BUILDING massing (the neighbours) must be matte and
    // UNTEXTURED: the beds bucket's UVs come from world X/Z, so a wall face
    // samples one line of the grit tile and streaks eave to grade, and props'
    // semi-gloss metal is equally wrong for painted siding.
    masses: new THREE.MeshStandardMaterial({
      vertexColors: true, roughness: 0.9, metalness: 0.0, flatShading: true }),
    // Near-black bark (albedo ~0.03). Every tree in this bucket is a bare
    // winter silhouette now (PLANT_TREES is off), and at 0x6d4c33 the west
    // group rendered as "bare white stick geometry lit blue".
    trunks: new THREE.MeshStandardMaterial({ color: 0x0c0b0a, roughness: 1 }),
    leaves: new THREE.MeshStandardMaterial({
      vertexColors: true, roughness: 1, flatShading: true }),
  };
  const CASTS = { props: true, masses: true };   // props: the car needs to sit on the drive
  const RECEIVES = { lawns: true, beds: true };

  // mergeGeometries refuses to mix indexed (cylinder/cone) with non-indexed
  // (icosahedron) geometry — normalize everything to non-indexed first
  const flat = (geos) => geos.map((g) => (g.index ? g.toNonIndexed() : g));

  function bucketMesh(name, geos) {
    if (!geos.length) return null;
    const m = new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(geos), false), MATS[name]);
    m.castShadow = !!CASTS[name];
    m.receiveShadow = !!RECEIVES[name];
    return m;
  }

  if (yardEditing) {
    // EDITOR: one group per item, sitting at its own pivot with its geometry
    // re-centred there, so TransformControls can move/turn/scale it directly
    // and the gesture reads straight back out as the delta to save.
    for (const item of items) {
      const byBucket = new Map();
      for (const { bucket, i } of item.geos) {
        if (!byBucket.has(bucket)) byBucket.set(bucket, []);
        byBucket.get(bucket).push(buckets[bucket].geos[i].clone());
      }
      const [px, py, pz] = item.pivot;
      const group = new THREE.Group();
      for (const [name, geos] of byBucket) {
        for (const g of geos) g.translate(-px, -py, -pz);
        const mesh = bucketMesh(name, geos);
        if (mesh) { mesh.userData.ownGeometry = true; group.add(mesh); }
      }
      const e = item.edit;
      group.position.set(px + (e?.dx || 0), py + (e?.dy || 0), pz + (e?.dz || 0));
      group.rotation.y = e?.rot_y || 0;
      group.scale.setScalar(e?.scale ?? 1);
      // An erased piece is BUILT and hidden, not skipped: un-erasing it is then
      // a visibility flip instead of a rebuild, and the panel's erased list has
      // something to name.
      group.visible = !e?.deleted;
      group.userData = {
        kind: 'yard',
        yardKey: item.key,
        name: item.label,
        yardKind: item.kind,
        // the untouched pivot: drag.js subtracts it to recover dx/dy/dz
        pivot: item.pivot,
        isClone: !!item.isClone,
        userScale: e?.scale ?? 1,
      };
      yard.add(group);
    }
  } else {
    // VIEWER: the original six merged meshes. Deleted items drop out and every
    // other item's delta is baked into its geometry here, so the merged path
    // costs exactly what it always did.
    for (const [name, bucket] of Object.entries(buckets)) {
      const keep = [];
      for (let i = 0; i < bucket.geos.length; i++) {
        const item = items[bucket.own[i]];
        if (item?.edit?.deleted) continue;
        const g = bucket.geos[i];
        const m = editMatrix(item.pivot, item.edit);
        if (m) g.applyMatrix4(m);
        keep.push(g);
      }
      const mesh = bucketMesh(name, keep);
      if (mesh) yard.add(mesh);
    }
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

  syncCar();

  // yard.js holds references into the groups this build just replaced, and
  // undo/redo and a house reload both land here without going through it.
  window.dispatchEvent(new CustomEvent('yardRebuilt'));
}
