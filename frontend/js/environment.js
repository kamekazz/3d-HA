// Outdoor environment: the generated yard (lawn, beds, trees, props, the
// rear lake) around the house shell. It exists ONLY while the Outside editor
// is open: setYardEditing(true) builds it (one group per piece, ~10 s cold)
// and setYardEditing(false) disposes it again. The viewer draws no exterior at
// all -- the house shell (which ships its own pale site pad and driveway)
// stands on scene.js's dark ground plane, the way edit mode always looked --
// so the ~11 s yard build is off the boot path and nothing outside the house
// is rendered. Placement uses a seeded RNG so the yard never reshuffles
// across builds, which is what lets yard_edits address a piece by position.
// Two things the build does to the SHELL are needed in the viewer too and are
// handled outside the build: hideShellPatioProps (on houseShellLoaded) and the
// rear-pad cut (restored on teardown).
import * as THREE from 'three';
import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';
import { scene } from './scene.js';
import { getShellRoot, isOutdoorRoom, getBuildingBox } from './house.js';
import { getInstance } from './models.js';
import { renderer, getEnvIntensity, onFrame } from './scene.js';   // onFrame: the car's sky tick
import { getNightFactor, getDaylight } from './daylight.js';   // car sky and rear atmosphere
import { objects3d } from './objects.js'; // locate the deferred rear deck instance

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

// Procedural canvases that take no inputs and paint from their own fixed seed
// are painted once per page and reused by every yard rebuild. Only the
// <canvas> is cached — callers still wrap it in a fresh CanvasTexture per
// build, so the yard's own texture disposal is unchanged.
const canvasMemo = new Map();
function memoCanvas(key, paint) {
  let c = canvasMemo.get(key);
  if (!c) { c = paint(); canvasMemo.set(key, c); }
  return c;
}

// A growable Float32Array with a push interface. The lake woodland writes
// ~26 M vertices per build; pushing them through JS number arrays and then
// copying into Float32Arrays was most of addRearLakeDetail's 14 s. Writing
// the float32 directly rounds each double exactly as the copy did, so the
// buffers are bit-identical to the array path (see leafCloud).
class F32Buf {
  constructor(cap = 1 << 18) { this.a = new Float32Array(cap); this.n = 0; }
  get length() { return this.n; }
  grow(min) {
    let c = this.a.length * 2; while (c < min) c *= 2;
    const b = new Float32Array(c); b.set(this.a.subarray(0, this.n)); this.a = b;
  }
  push3(x, y, z) {
    const n = this.n; if (n + 3 > this.a.length) this.grow(n + 3);
    const a = this.a; a[n] = x; a[n + 1] = y; a[n + 2] = z; this.n = n + 3;
  }
  push2(u, v) {
    const n = this.n; if (n + 2 > this.a.length) this.grow(n + 2);
    const a = this.a; a[n] = u; a[n + 1] = v; this.n = n + 2;
  }
  reset() { this.n = 0; }
  // a compact copy the BufferAttribute owns; the accumulator is reused after
  attr(itemSize) { return new THREE.BufferAttribute(this.a.slice(0, this.n), itemSize); }
}
// position / colour / normal / uv accumulators for one leaf geometry
function leafStore() { return { pos: new F32Buf(), col: new F32Buf(), nrm: new F32Buf(), uv: new F32Buf(1 << 17) }; }

// Where a yard build spends its time, per builder, for the last build:
// window.__environment.timings(). Wall-clock, main thread, ms. yardLap(label)
// records the time since the previous lap; builders may call it for sub-steps.
let yardTimings = [], yardLapT = 0;
function yardLap(label) {
  const t = performance.now();
  yardTimings.push([label, +(t - yardLapT).toFixed(1)]);
  yardLapT = t;
}

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

  // debug handle (console): where the last yard build spent its time
  window.__environment = {
    timings: () => { console.table(yardTimings.map(([stage, ms]) => ({ stage, ms }))); return yardTimings; },
    // every item of the last build (empty unless the Outside editor is open)
    items: () => items.map((i) => ({ key: i.key, kind: i.kind, label: i.label,
      pivot: i.pivot, deleted: !!i.edit?.deleted })),
  };

  // The exterior shows only while the Outside editor is open, and only on the
  // whole-house level (single-floor view shows floorview.js's studio backdrop).
  // yard.js closes the editor on leaving edit mode, so no appModeChanged
  // listener is needed here.
  let onHouseLevel = true;
  const applyVisibility = () => {
    root.visible = yardEditing && onHouseLevel;
  };
  applyYardVisibility = applyVisibility;
  applyVisibility();   // root holds the grass disc: hidden until the editor opens

  // The whole-house shell GLB loads async and its real footprint is far
  // bigger than the traced room rects; setLevel fires levelChanged once it
  // lands — while editing, measure it and replant the yard around the true bounds.
  window.addEventListener('levelChanged', (e) => {
    onHouseLevel = e.detail.level === 'all';
    applyVisibility();
    if (yardEditing && lastHouse && remeasureShell()) buildYard();
  });

  // The shell's own terrace lounge set is hidden for every shell instance
  // (boot and every reloadHouse hands out a fresh clone with all meshes
  // visible). This used to happen inside the yard build, which the viewer no
  // longer runs; the placed Backyard objects are the real furniture.
  window.addEventListener('houseShellLoaded', () => hideShellPatioProps());
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
  // Rear turf is seated at the photographed low grade by addRearGroundDetail.
  // The shared low sheet above remains intact; no front or side slab changes.
  // --- side yards, west and east of the house
  g(L.padW, L.wingN, L.houseW, L.houseF, L.hi);
  g(L.driveL - 0.4, L.wingN, L.padE, L.houseF - 0.2, L.lo);
  // --- front: the apron in front of the porch, west of the driveway. Runs
  //     PAST the pad's own front edge and all the way to the street, so no
  //     sliver of the GLB's slab is left to read as a kerb across the lawn.
  g(L.padW - 9, L.padF, L.driveL + 0.4, L.street + 1.0, L.lo);
  g(L.driveR - 0.4, L.houseF - 1, L.padE + 9, L.street + 1.0, L.lo);
  g(L.porchE, L.houseF, L.driveL, L.padF, L.hi);
  // The front pad transition remains at its original grade.
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
// Rear lake only. The broadleaf trunks, open water gaps, low opposite bank and
// curved gravel boundary come from backyard4k reference photographs 05/06/11/12/13.
// North is -Z. Its private seed never advances the front yard's generator.
// Water is an opaque surface over submerged ground, with an actual rising bank;
// no photograph, camera-facing plane or global lighting adjustment is involved.
function addRearLakeDetail(L, leaves, beds, props, lawns, trunks, masses) {
  const rng = mulberry32(0x4c414b45);
  const mid = (L.padW + L.padE) * 0.5;
  const waterY = L.lo + 0.018;
  const bedY = L.lo + 0.72;
  const lawnEdge = x => L.yardN + 6.8 + 2.8 * Math.sin((x - mid) / 13)
    + 1.6 * Math.cos((x - mid) / 6.8);
  const shore = x => lawnEdge(x) - 9.3 - 2.0 * Math.sin((x - mid) / 17);
  // Photo 05/06/11/13 show a small, unresolved opposite-bank vegetation band.
  // This visual depth estimate is about 260 ft across, not a surveyed distance.
  const far = x => L.yardN - 260 + 13 * Math.sin((x - mid) / 43)
    + 4.2*Math.sin((x-mid)/9.4)+1.3*Math.sin((x-mid)/3.1);
  const nearX0 = L.padW - 31, nearX1 = L.padE + 31;
  const lakeX0 = mid - 245, lakeX1 = mid + 245;
  const localItem = (kind, label, fn) => scoped(kind, label, fn)();
  const color = hex => new THREE.Color(hex);
  // A gridded, non-facing ribbon, with UVs compatible with the normal yard
  // buckets. Subdivision retains organic curves from every orbit direction.
  const ribbon = (x0, x1, f0, f1, y0, y1, segments = 100) => {
    const pos = [], uv = [];
    for (let i = 0; i < segments; i++) {
      const a = x0 + (x1 - x0) * i / segments;
      const b = x0 + (x1 - x0) * (i + 1) / segments;
      for (const p of [[a,y0,f0(a)],[b,y0,f0(b)],[b,y1,f1(b)],
                       [a,y0,f0(a)],[b,y1,f1(b)],[a,y1,f1(a)]]) {
        pos.push(...p); uv.push(p[0] / 6, -p[2] / 6);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.computeVertexNormals();
    // f0 is the southern boundary and f1 the northern boundary, so +Y winding.
    return g;
  };
  localItem('shore', 'Rear curved gravel shore', () => {
    const edgePts = [], backPts = [];
    for (let i = 0; i <= 64; i++) {
      const x = nearX0 + (nearX1 - nearX0) * i / 64;
      edgePts.push([x, lawnEdge(x)]); backPts.push([x, shore(x) + 2.6]);
    }
    // Fine mixed aggregate has its own repeating material; the front gravel
    // material and its UV scale are untouched. Raised individual pebbles catch
    // light over a dense, shaded stone matrix at approximately one-inch scale.
    const canvas=document.createElement('canvas'); canvas.width=canvas.height=1024;
    const ctx=canvas.getContext('2d'); ctx.fillStyle='#696964';ctx.fillRect(0,0,1024,1024);
    for(let i=0;i<29000;i++) {
      const x=rng()*1024,z=rng()*1024,r=1.4+rng()*4.5,shade=90+rng()*88;
      ctx.fillStyle=`rgb(${shade+4},${shade+3},${shade})`;
      ctx.beginPath();ctx.ellipse(x,z,r,r*(.45+rng()*.4),rng()*6.28,0,Math.PI*2);ctx.fill();
      ctx.strokeStyle='rgba(45,44,38,.35)';ctx.lineWidth=.8;ctx.stroke();
    }
    const aggregate=new THREE.CanvasTexture(canvas); aggregate.colorSpace=THREE.SRGBColorSpace;
    aggregate.wrapS=aggregate.wrapT=THREE.RepeatWrapping; aggregate.anisotropy=8;
    const mat=new THREE.MeshStandardMaterial({map:aggregate,bumpMap:aggregate,bumpScale:.025,roughness:1,color:0xb8b6af});
    mat.addEventListener('dispose',()=>aggregate.dispose());
    const gravel=new THREE.Mesh(ribbon(nearX0,nearX1,lawnEdge,x=>shore(x)+2.6,bedY,bedY-.18,180),mat);
    gravel.name='rear-shore-fine-gravel';gravel.receiveShadow=true;gravel.userData.ownGeometry=true;yard.add(gravel);
    for(let x=nearX0;x<nearX1;x+=.24+rng()*.16)for(let row=0;row<2;row++) {
      const r=.10+rng()*.13,g=new THREE.IcosahedronGeometry(r,1);
      g.scale(.8+rng()*.6,.45+rng()*.3,.75+rng()*.45);
      g.rotateY(rng()*6.28);g.translate(x+(rng()-.5)*.2,bedY-.02,lawnEdge(x)-row*.29+(rng()-.5)*.24);
      const tint=new THREE.Color().setHSL(.08+rng()*.09,.04+rng()*.17,.32+rng()*.27,THREE.SRGBColorSpace);
      paintNoisy(g,tint,rng,.17);beds.push(g);
    }
    const apron = ribbon(nearX0, nearX1, x => lawnEdge(x) + 2.6, lawnEdge,
      L.lo + 0.012, bedY - 0.035, 120);
    lawns.push(apron);
    yardLap('    lake: gravel + apron');
    const soil = ribbon(lakeX0, lakeX1, x => shore(x) + 2.7, shore,
      bedY - 0.08, waterY + 0.012, 160);
    paintNoisy(soil, color(0x514d3b), rng, 0.45); beds.push(soil);
  });

  // The water is a genuine horizontal 3D mesh. Its small normal ripples and
  // Fresnel sky reflection follow scene.background on every render (including
  // sun/weather simulations and night); the standard light model remains in
  // charge of its diffuse term. No emissive floor and no additional lights.
  const waterGeo = ribbon(lakeX0, lakeX1, shore, far, waterY, waterY, 200);
  const waterMat = new THREE.MeshStandardMaterial({
    color: 0x69786a, roughness: 0.24, metalness: 0.08,
    side: THREE.DoubleSide,
  });
  const waterUniforms = {
    rearLakeSky: { value: new THREE.Color(0x9aaeb5) },
    rearLakeTime: { value: 0 },
    rearLakeReflection: { value: null },
    rearLakeProjection: { value: new THREE.Matrix4() },
  };
  waterMat.onBeforeCompile = shader => {
    Object.assign(shader.uniforms, waterUniforms);
    shader.vertexShader = 'varying vec3 vRearLakeWorld;\nvarying vec4 vRearLakeReflect;\nuniform mat4 rearLakeProjection;\n' + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace('#include <worldpos_vertex>',
      '#include <worldpos_vertex>\nvRearLakeWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;\nvRearLakeReflect = rearLakeProjection * vec4(vRearLakeWorld, 1.0);');
    shader.fragmentShader = 'varying vec3 vRearLakeWorld;\nvarying vec4 vRearLakeReflect;\nuniform sampler2D rearLakeReflection;\nuniform vec3 rearLakeSky;\nuniform float rearLakeTime;\n'
      + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace('#include <normal_fragment_maps>',
      '#include <normal_fragment_maps>\n'
      + 'float lakeWave = sin(vRearLakeWorld.x * 3.7 + vRearLakeWorld.z * 7.1 + rearLakeTime * 0.32);\n'
      + 'normal = normalize(normal + vec3(lakeWave * 0.024, cos(vRearLakeWorld.z * 9.3 - rearLakeTime * 0.21) * 0.017, 0.0));');
    shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>',
      'float lakeFresnel = pow(1.0 - abs(dot(normalize(vViewPosition), normal)), 3.0);\n'
      + 'float lakeDistance=length(cameraPosition-vRearLakeWorld);\n'
      + 'float lakeRoughness=smoothstep(25.0,270.0,lakeDistance);\n'
      + 'float lakeCrossWave=sin(vRearLakeWorld.x*1.37+vRearLakeWorld.z*4.83-rearLakeTime*.19);\n'
      + 'vec2 reflectedUV=vRearLakeReflect.xy/vRearLakeReflect.w+vec2((lakeWave+lakeCrossWave*.6)*(.0014+lakeRoughness*.0018),cos(vRearLakeWorld.z*7.9+rearLakeTime*.18)*.0006);\n'
      + 'vec2 roughFootprint=vec2(.0012+lakeRoughness*.0026,.00035+lakeRoughness*.00055);\n'
      + 'vec3 reflectedTrees=texture2D(rearLakeReflection,reflectedUV).rgb*.40;\n'
      + 'reflectedTrees+=(texture2D(rearLakeReflection,reflectedUV+vec2(roughFootprint.x,0.0)).rgb+texture2D(rearLakeReflection,reflectedUV-vec2(roughFootprint.x,0.0)).rgb)*.20;\n'
      + 'reflectedTrees+=(texture2D(rearLakeReflection,reflectedUV+roughFootprint).rgb+texture2D(rearLakeReflection,reflectedUV-roughFootprint).rgb)*.10;\n'
      + 'float reflectedLuma=dot(reflectedTrees,vec3(.2126,.7152,.0722));\n'
      + 'reflectedTrees=mix(reflectedTrees,vec3(reflectedLuma),lakeRoughness*.22);\n'
      + 'float reflectAmount=(.27+lakeFresnel*.34)*(1.0-lakeRoughness*.25);\n'
      + 'outgoingLight=mix(outgoingLight,reflectedTrees*(.85+lakeCrossWave*.026),reflectAmount);\n'
      + '#include <opaque_fragment>');
  };
  waterMat.customProgramCacheKey = () => 'rear-lake-water-v3';
  const water = new THREE.Mesh(waterGeo, waterMat);
  yardLap('    lake: water');
  water.name = 'rear-lake-surface';
  water.userData.ownGeometry = true;
  water.userData.rearLake = true;
  water.receiveShadow = true;
  // A local planar reflection renders the real scene from a mirrored camera.
  // Oblique clipping keeps submerged terrain out. It owns its render target and
  // updates only when this mesh renders; there is no global frame subscription.
  const reflectionTarget=new THREE.WebGLRenderTarget(1024,768,{type:THREE.HalfFloatType});
  waterUniforms.rearLakeReflection.value=reflectionTarget.texture;
  const mirrorCamera=new THREE.PerspectiveCamera(),plane=new THREE.Plane(),clip=new THREE.Vector4(),q=new THREE.Vector4();
  const bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1);
  const lastCamera=new THREE.Matrix4(); let reflecting=false,lastReflect=-Infinity;
  waterMat.addEventListener('dispose',()=>reflectionTarget.dispose());
  water.onBeforeRender = (activeRenderer,activeScene,camera) => {
    if (scene.background?.isColor) waterUniforms.rearLakeSky.value.copy(scene.background);
    waterUniforms.rearLakeTime.value = performance.now() * 0.001;
    if(reflecting||camera.position.y<=waterY||camera.userData.rearLakeMirror)return;
    const now=performance.now();
    if(now-lastReflect<160 || (camera.matrixWorld.equals(lastCamera)&&now-lastReflect<2000))return;
    reflecting=true;lastReflect=now;lastCamera.copy(camera.matrixWorld);
    const direction=new THREE.Vector3();camera.getWorldDirection(direction);direction.y*=-1;
    mirrorCamera.position.copy(camera.position);mirrorCamera.position.y=2*waterY-camera.position.y;
    mirrorCamera.up.copy(camera.up);mirrorCamera.up.y*=-1;
    mirrorCamera.lookAt(mirrorCamera.position.clone().add(direction));
    mirrorCamera.near=camera.near;mirrorCamera.far=camera.far;
    mirrorCamera.projectionMatrix.copy(camera.projectionMatrix);
    mirrorCamera.updateMatrixWorld();mirrorCamera.matrixWorldInverse.copy(mirrorCamera.matrixWorld).invert();
    mirrorCamera.userData.rearLakeMirror=true;
    waterUniforms.rearLakeProjection.value.copy(bias).multiply(mirrorCamera.projectionMatrix).multiply(mirrorCamera.matrixWorldInverse);
    plane.set(new THREE.Vector3(0,1,0),-waterY-.015).applyMatrix4(mirrorCamera.matrixWorldInverse);
    clip.set(plane.normal.x,plane.normal.y,plane.normal.z,plane.constant);
    const projection=mirrorCamera.projectionMatrix.elements;
    q.set((Math.sign(clip.x)+projection[8])/projection[0],(Math.sign(clip.y)+projection[9])/projection[5],-1,(1+projection[10])/projection[14]);
    clip.multiplyScalar(2/clip.dot(q));projection[2]=clip.x;projection[6]=clip.y;projection[10]=clip.z+1;projection[14]=clip.w;
    mirrorCamera.projectionMatrixInverse.copy(mirrorCamera.projectionMatrix).invert();
    const previousTarget=activeRenderer.getRenderTarget(),previousXR=activeRenderer.xr.enabled;
    const previousShadow=activeRenderer.shadowMap.autoUpdate;
    const previousViewport=new THREE.Vector4();activeRenderer.getViewport(previousViewport);
    water.visible=false;
    try {
      activeRenderer.xr.enabled=false;activeRenderer.shadowMap.autoUpdate=false;
      activeRenderer.setRenderTarget(reflectionTarget);activeRenderer.clear();activeRenderer.render(activeScene,mirrorCamera);
    } finally {
      water.visible=true;activeRenderer.xr.enabled=previousXR;activeRenderer.shadowMap.autoUpdate=previousShadow;
      activeRenderer.setRenderTarget(previousTarget);activeRenderer.setViewport(previousViewport);reflecting=false;
    }
  };
  yard.add(water);

  // Real swept bark surfaces retain their UVs through the editable buckets.
  // One physical tile is 1 x 2 metres; circumference and length are in feet.
  const branch = (points, r0, r1, bucket, tint = 0xffffff) => {
    const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
    const length=curve.getLength(), rings=Math.max(5,Math.ceil(length*2.6));
    const sides=r0>.3?28:10,frames=curve.computeFrenetFrames(rings,false),p=[],uv=[],idx=[];
    const phase=rng()*6.28;
    for(let i=0;i<=rings;i++) {
      const t=i/rings,c=curve.getPointAt(t),base=r0*Math.pow(1-t,.88)+r1*t;
      for(let j=0;j<=sides;j++) {
        const a=j/sides*Math.PI*2;
        const ridges=1+.065*Math.sin(a*7+t*4+phase)+.028*Math.sin(a*17-t*7);
        const flare=1+Math.exp(-t*length*2)*Math.max(0,Math.sin(a*5+phase))*.20;
        const r=base*ridges*flare,n=frames.normals[i],bn=frames.binormals[i];
        p.push(c.x+r*(Math.cos(a)*n.x+Math.sin(a)*bn.x),c.y+r*(Math.cos(a)*n.y+Math.sin(a)*bn.y),c.z+r*(Math.cos(a)*n.z+Math.sin(a)*bn.z));
        uv.push(j/sides*Math.PI*2*r0/3.28084,t*length/6.56168);
        if(i<rings&&j<sides){const k=i*(sides+1)+j;idx.push(k,k+1,k+sides+1,k+1,k+sides+2,k+sides+1);}
      }
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(idx);g.computeVertexNormals();
    paint(g,color(tint));if(bucket===masses)g.userData.rearBark=true;bucket.push(g);
  };
  const limb=(a,b,r0,r1,tint,bucket)=>branch([a,b],r0,r1,bucket,bucket===masses?0xffffff:tint);
  // Individual scanned oak leaves curve along their central vein. These are
  // four-triangle surfaces, not whole-crown billboards; the photograph's alpha
  // supplies the natural lobes while its normal map supplies the small veins.
  // ~2.2 M leaves per build (26 M vertices), so this loop is the yard's single
  // biggest CPU cost. It is scalar on purpose: the SAME arithmetic three's
  // Vector3.applyQuaternion / normalize (multiply by 1/length) / addScaledVector
  // and Quaternion.setFromEuler('XYZ') perform, in the SAME order, so the output
  // is bit-identical to the object-per-leaf version it replaced (verified by
  // hashing the position buffers: rear-distant-oak-leaves 914aad08,
  // rear-scanned-oak-leaves 4ac95656) — measured 3.1 µs/leaf through the
  // Vector3/Quaternion methods in situ, ~1 µs/leaf here. Keep the rng() call
  // order exactly as it is: every later plant in the lake draws from the same
  // stream, and the r160 formulas are copied verbatim because a mathematically
  // equal rearrangement rounds differently.
  const _lcUV=[0,0,1,0,0,.5,1,.5,0,1,1,1], _lcIndices=[0,1,2,1,3,2,2,3,4,3,5,4];
  const _lcVX=new Float64Array(6),_lcVY=new Float64Array(6),_lcVZ=new Float64Array(6);
  const _lcNX=new Float64Array(6),_lcNY=new Float64Array(6),_lcNZ=new Float64Array(6);
  let leafCloudMs = 0, leafCloudLeaves = 0;   // reported into yardTimings below
  const leafCloud = (cx, cy, cz, rx, ry, rz, count, store, scale = 1) => {
    const lcT0 = performance.now();
    if(scale<=1)count=Math.ceil(count*1.45);
    leafCloudLeaves += count;
    const clusterCount=Math.ceil(count/28);
    const positions=store.pos, colors=store.col, normals=store.nrm, uvs=store.uv;
    const VX=_lcVX,VY=_lcVY,VZ=_lcVZ,NX=_lcNX,NY=_lcNY,NZ=_lcNZ;
    for(let cl=0;cl<clusterCount;cl++) {
      let dx,dy,dz;do {dx=rng()*2-1;dy=rng()*2-1;dz=rng()*2-1;}while(dx*dx+dy*dy+dz*dz>1);
      const ccx=cx+dx*rx, ccy=cy+dy*ry, ccz=cz+dz*rz;
      const depth=Math.sqrt(dx*dx+dy*dy+dz*dz);
      const shade=.42+depth*.26+rng()*.19;
      // Vector3.set(...).normalize(): divideScalar(length || 1) is multiplyScalar(1/len)
      let ax=rng()-.5, ay=.2+rng()*.4, az=rng()-.5;
      { const inv=1/(Math.sqrt(ax*ax+ay*ay+az*az)||1); ax*=inv; ay*=inv; az*=inv; }
      for(let n=0;n<28&&cl*28+n<count;n++) {
        // c = center.addScaledVector(axis, s)  then  c.add(jitter)
        const s1=(rng()-.5)*1.6;
        let px=ccx+ax*s1, py=ccy+ay*s1, pz=ccz+az*s1;
        const jx=(rng()-.5)*1.15, jy=(rng()-.5)*.8, jz=(rng()-.5)*1.15;
        px+=jx; py+=jy; pz+=jz;
        const halfLength=(.19+rng()*.115)*scale,halfWidth=halfLength*.586;
        const bend=halfLength*(.11+rng()*.17);
        // Quaternion.setFromEuler(Euler(x, y, z, 'XYZ'))
        const ex=(rng()-.5)*2.1, ey=rng()*6.28, ez=(rng()-.5)*1.9;
        const c1=Math.cos(ex/2), c2=Math.cos(ey/2), c3=Math.cos(ez/2);
        const s1e=Math.sin(ex/2), s2=Math.sin(ey/2), s3=Math.sin(ez/2);
        const qx=s1e*c2*c3+c1*s2*s3, qy=c1*s2*c3-s1e*c2*s3, qz=c1*c2*s3+s1e*s2*c3, qw=c1*c2*c3-s1e*s2*s3;
        for(let i=0;i<6;i++){
          // the six local corners: (-L,0,-W) (-L,0,W) (0,b,-W) (0,b,W) (L,-.35b,-W) (L,-.35b,W)
          const lx=i<2?-halfLength:i<4?0:halfLength;
          const ly=i<2?0:i<4?bend:-bend*.35;
          const lz=(i&1)?halfWidth:-halfWidth;
          // Vector3.applyQuaternion (r160): t = 2 cross(q.xyz, v); v + w t + cross(q.xyz, t)
          {
            const tx=2*(qy*lz-qz*ly), ty=2*(qz*lx-qx*lz), tz=2*(qx*ly-qy*lx);
            VX[i]=(lx+qw*tx+qy*tz-qz*ty)+px;
            VY[i]=(ly+qw*ty+qz*tx-qx*tz)+py;
            VZ[i]=(lz+qw*tz+qx*ty-qy*tx)+pz;
          }
          // normal: set(lx/L*.24, 1, lz/W*.1).normalize().applyQuaternion(q)
          {
            let nx=lx/halfLength*.24, ny=1, nz=lz/halfWidth*.1;
            const inv=1/(Math.sqrt(nx*nx+ny*ny+nz*nz)||1); nx*=inv; ny*=inv; nz*=inv;
            const tx=2*(qy*nz-qz*ny), ty=2*(qz*nx-qx*nz), tz=2*(qx*ny-qy*nx);
            NX[i]=nx+qw*tx+qy*tz-qz*ty;
            NY[i]=ny+qw*ty+qz*tx-qx*tz;
            NZ[i]=nz+qw*tz+qx*ty-qy*tx;
          }
        }
        const brightness=shade*(.9+rng()*.2),warm=.96+rng()*.08;
        for(let j=0;j<12;j++) {
          const k=_lcIndices[j];
          normals.push3(NX[k],NY[k],NZ[k]);positions.push3(VX[k],VY[k],VZ[k]);
          uvs.push2(_lcUV[k*2],_lcUV[k*2+1]);colors.push3(brightness*warm,brightness,brightness*(.96+rng()*.035));
        }
      }
    }
    leafCloudMs += performance.now() - lcT0;
  };
  const matureTree = (x, z, radius, height, lean, authoredPivot) => localItem('tree', 'Rear mature broadleaf', () => {
    items[curItem].authoredPivot=authoredPivot;
    const y=bedY-.20,store=leafStore(),phase=rng()*6.28;
    const spine=Array.from({length:7},(_,i)=>[x+lean*i/6+Math.sin(i*1.25+phase)*radius*.30,y+height*i/6,z+Math.sin(i*.85)*radius*.5]);
    spine[0]=[x,y,z];branch(spine,radius,radius*.045,masses);
    for(let i=0;i<5;i++) {
      const a=phase+i*1.256+(rng()-.5)*.5,r=radius*(1.7+rng());
      branch([[x,y+.52,z],[x+Math.cos(a)*r*.5,y+.06,z+Math.sin(a)*r*.5],[x+Math.cos(a)*r,y-.09,z+Math.sin(a)*r]],radius*.32,.013,masses);
    }
    const lowJoin=radius>.4?(.17+rng()*.12):(.34+rng()*.10);
    for(let b=0;b<9;b++) {
      const angle=phase+b*2.399+(rng()-.5)*.6,join=lowJoin+b*.060;
      const origin=[x+lean*join,y+height*join,z+Math.sin(join*5)*radius*.4];
      const reach=(radius>.4?6:4)+rng()*5, rise=2.8+rng()*6;
      const tip=[origin[0]+Math.cos(angle)*reach,origin[1]+rise,origin[2]+Math.sin(angle)*reach];
      const bend=[origin[0]+Math.cos(angle)*reach*.42,origin[1]+rise*.22,origin[2]+Math.sin(angle)*reach*.40];
      branch([origin,bend,tip],radius*(b<2?.46:.32),.035,masses);
      for(let t=0;t<5;t++) {
        const ta=angle+(t-2)*.50,j=.42+t*.13;
        const from=origin.map((v,i)=>v+(tip[i]-v)*j);
        const end=[from[0]+Math.cos(ta)*(2+rng()*3),from[1]+.7+rng()*2.7,from[2]+Math.sin(ta)*(2+rng()*3)];
        branch([from,[(from[0]+end[0])*.5,from[1]+.35,(from[2]+end[2])*.5],end],.075,.009,masses);
        leafCloud(...end,2.3+rng(),1.4+rng(),2.2+rng(),280,store,.95);
      }
    }
    // Interlocking crown tiers enclose the site from ground and aerial views.
    // They continue the existing trunks upward, rather than forming a screen.
    for(let b=0;b<5;b++) {
      const a=phase+b*2.399,reach=3.5+rng()*4;
      const end=[x+lean+Math.cos(a)*reach,y+height*(.77+rng()*.20),z+Math.sin(a)*reach];
      const from=[x+lean*.65,y+height*.61,z];
      branch([from,[(from[0]+end[0])*.5,end[1]-3,(z+end[2])*.5],end],radius*.26,.025,masses);
      leafCloud(...end,4.6+rng()*1.8,3.5+rng()*1.4,4.4+rng()*1.4,1650,store,1);
    }
    // North-reaching secondary boughs create several depths at the water
    // window, with drooping tips below the main crown's higher scallops.
    if(radius>.58)for(let b=0;b<2;b++) {
      const end=[x+(b?1:-1)*(4+rng()*3),y+8.3+rng()*2.6,z-6-rng()*4];
      const origin=[x+lean*.4,y+height*.40,z];
      branch([origin,[(x+end[0])*.5,end[1]+3.5,z-4],end],radius*.26,.018,masses);
      leafCloud(...end,4.4,3.3,3.5,1700,store,.86);
    }
    // The western side has low branches and a thick shaded understory; the
    // center/eastern water window remains below the spreading upper branches.
    for(let b=0;b<3;b++) {
      const end=[x+(b-1)*4.8+(rng()-.5)*3,y+9+rng()*5,z-1+(rng()-.5)*5];
      const origin=[x+lean*.27,y+height*(.20+rng()*.10),z];
      branch([origin,[(origin[0]+end[0])*.5,end[1]+1,(z+end[2])*.5],end],radius*.22,.025,masses);
      leafCloud(...end,4.6+rng(),2.5+rng(),3.4+rng(),1300,store,.9);
    }
    if(x<mid-9)for(let b=0;b<3;b++) {
      const end=[x-2+rng()*5,y+3+rng()*4,z-1-rng()*4];
      branch([[x,y+height*.27,z],[x-1,y+7,z-3],end],radius*.16,.012,masses);
      leafCloud(...end,3.7,2.6,3,1000,store,.8);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',store.pos.attr(3));
    g.setAttribute('color',store.col.attr(3));
    g.setAttribute('uv',store.uv.attr(2));
    g.setAttribute('normal',store.nrm.attr(3));
    g.userData.rearFoliage=true;g.userData.rearOakLeaf=true;g.userData.rearSingleLeafSurface=true;props.push(g);
  });
  // Unequal gaps, diameters, lean and bank offsets follow the multiple reference
  // views: old trunks west, a thin central group, and two larger eastern trees.
  // These measured R3 pivots are the saved Outside-editor identities. Crown
  // growth must not move their keys or the centers of existing transforms.
  const rearTreePivots=[
    [-28.117618560791016, 0.6063904166221619, -92.55056381225586],
    [-16.470466375350952, 0.5850999355316162, -90.79825210571289],
    [-7.611598014831543, 0.6067643761634827, -98.65209197998047],
    [1.168381690979004, 0.6015253663063049, -95.57381439208984],
    [8.806659936904907, 0.6062871217727661, -93.73613739013672],
    [13.858349561691284, 0.6075313687324524, -96.21585083007812],
    [20.048478364944458, 0.6083599925041199, -91.35988235473633],
    [22.090208530426025, 0.6093277931213379, -91.2473030090332],
    [29.252517700195312, 0.6072371602058411, -92.38594055175781],
    [36.730207443237305, 0.6034967303276062, -91.51291275024414],
    [42.09299659729004, 0.6068471074104309, -96.19887924194336],
    [49.8985538482666, 0.5973221659660339, -93.12164688110352],
    [65.29949378967285, 0.6003846526145935, -96.26172256469727],
  ];
  let treeOrdinal=0;
  for(const [offset,r,h,lean,dz] of [[-48,.65,30,-1.2,-1],[-36,.85,31,.8,1],[-27,.50,29,-1.1,-2],
      [-19,.72,33,-1.7,2.5],[-13,.62,31,-.8,2],[-7,.33,30,.7,-1],[-1,.18,28,.2,1],
      [2,.16,29,-.5,.5],[8,.35,31,.9,-.4],[16,.67,35,1.5,1.4],[21,.5,33,1.7,-1.5],
      [31,.75,34,-.8,.4],[44,.7,31,.4,-2]]) {
    const x=mid+offset;matureTree(x,shore(x)+2.5+dz,r,h,lean,rearTreePivots[treeOrdinal++]);
  }
  yardLap('    lake: mature trees');

  // Visible daytime housings and the hanging feeder in reference 11. They
  // introduce no light source and do not override HA fixture state.
  for(const offset of [-7,13]) localItem('prop','Rear shore path-light housing',()=>{
    const x=mid+offset,z=lawnEdge(x)-.85;
    limb([x,bedY,z],[x,bedY+1.35,z],.065,.075,0x202326,props);
    const head=new THREE.CylinderGeometry(.14,.13,.26,16);head.translate(x,bedY+1.40,z);
    paint(head,color(0x181d20));props.push(head);
    const cap=new THREE.CylinderGeometry(.165,.165,.045,18);cap.translate(x,bedY+1.55,z);
    paint(cap,color(0x292c2c));props.push(cap);
  });
  localItem('prop','Rear hanging bird feeder',()=>{
    const x=mid-8,z=shore(x)+4;
    const curve=new THREE.CatmullRomCurve3([[x,bedY,z],[x,bedY+4.5,z],[x+.15,bedY+4.9,z],[x+.65,bedY+4.9,z],[x+.85,bedY+4.5,z]].map(p=>new THREE.Vector3(...p)));
    const hook=new THREE.TubeGeometry(curve,30,.018,6,false);paint(hook,color(0x333832));props.push(hook);
    limb([x+.85,bedY+4.5,z],[x+.85,bedY+3.7,z],.01,.01,0x30362c,props);
    const body=new THREE.CylinderGeometry(.15,.15,.65,12);body.translate(x+.85,bedY+3.4,z);paint(body,color(0xb0b5a1));props.push(body);
    for(const yy of [bedY+3.02,bedY+3.76]){const tray=new THREE.CylinderGeometry(.26,.26,.06,14);tray.translate(x+.85,yy,z);paint(tray,color(0x384638));props.push(tray);}
  });
  localItem('shore','Rear gravel fallen leaves',()=>{
    for(let i=0;i<200;i++) {
      const x=nearX0+rng()*(nearX1-nearX0),z=lawnEdge(x)-rng()*(lawnEdge(x)-shore(x)-3),size=.10+rng()*.14;
      const g=new THREE.CircleGeometry(size,5);g.rotateX(-Math.PI/2);g.scale(1,.5,.55);g.rotateY(rng()*6.28);g.translate(x,bedY+.008,z);
      paint(g,color(rng()<.5?0x796349:0x9c885e));beds.push(g);
    }
  });
  localItem('shore', 'Rear far bank and woodland', () => {
    const bankHeight=x=>L.lo+.55+1.4*worldNoise(x,-210,9)+.55*Math.sin(x*.37);
    const bank = ribbon(lakeX0, lakeX1, far, x=>far(x)-10,
      waterY+.012, L.lo+1.4, 360);
    const bp=bank.attributes.position;
    for(let i=0;i<bp.count;i++) {
      const x=bp.getX(i),t=Math.max(0,Math.min(1,(far(x)-bp.getZ(i))/10));
      bp.setY(i,waterY+.012+(bankHeight(x)-waterY)*t);
    }
    bank.computeVertexNormals();paintNoisy(bank,color(0x939277),rng,.29);beds.push(bank);
    const terrain = ribbon(lakeX0, lakeX1, x=>far(x)-10, x=>far(x)-95,L.lo+1.5,L.lo+3,200);
    lawns.push(terrain);
    yardLap('    lake: trees + bank + terrain');
    const farStore=leafStore();
    // Release temporary JS Number arrays after each plant. Typed geometry
    // chunks preserve exact vertex order and are merged by the existing bucket;
    // one huge forest accumulator otherwise exceeds the browser's memory peak.
    const flushFarLeaves=()=>{
      if(!farStore.pos.length)return;
      const woodland = new THREE.BufferGeometry();
      woodland.setAttribute('position',farStore.pos.attr(3));
      woodland.setAttribute('color',farStore.col.attr(3));
      woodland.setAttribute('uv',farStore.uv.attr(2));
      woodland.setAttribute('normal',farStore.nrm.attr(3));
      woodland.userData.rearFoliage=true;woodland.userData.rearOakLeaf=true;woodland.userData.rearFarLeaf=true;woodland.userData.rearSingleLeafSurface=true;props.push(woodland);
      farStore.pos.reset();farStore.col.reset();farStore.uv.reset();farStore.nrm.reset();
    };
    // Low, broken water-edge scrub hides the bank in places and leaves mud,
    // reeds and short grass visible between clusters. Nothing forms a rail.
    for(let x=lakeX0;x<lakeX1;x+=2.5+rng()*3.7) {
      flushFarLeaves();
      const z=far(x)-1.4-rng()*4,height=1.2+rng()*4.3;
      if(rng()<.67) {
        branch([[x,waterY,z],[x+.3,height*.7+L.lo,z-.4],[x-.5,height+L.lo,z-.7]],.05,.009,masses);
        leafCloud(x,L.lo+height*.70,z,2.1+rng()*1.7,height*.5,1.8+rng(),1100,farStore,.95);
      }
      for(let j=0;j<8;j++) {
        const xx=x+(rng()-.5)*3,zz=far(xx)-rng()*2.2,h=.4+rng()*1.5;
        const g=new THREE.PlaneGeometry(.025+rng()*.045,h);g.rotateY(rng()*6.28);g.rotateZ((rng()-.5)*.45);g.translate(xx,waterY+h*.5,zz);
        paint(g,color(rng()<.4?0x898367:0x707b53));leaves.push(g);
      }
    }
    yardLap('    lake: bank scrub');
    for(let x=lakeX0;x<lakeX1;x+=4+rng()*5) {
      flushFarLeaves();
      const z=far(x)-8-rng()*16,h=3+rng()*6;
      branch([[x,L.lo+1,z],[x-.3,L.lo+h*.6,z-1],[x+1,L.lo+h,z-.4]],.07,.01,masses);
      leafCloud(x,L.lo+h*.62,z,3.4+rng()*2,h*.6,3+rng()*2,1400,farStore,1.1);
    }
    // Three unequal ranks overlap in depth: low pioneer trees on the bank,
    // broad middle crowns and taller crowns receding behind those gaps.
    yardLap('    lake: mid trees');
    for(let rank=0;rank<3;rank++)for(let x=lakeX0-12;x<lakeX1+12;x+=7+rng()*7) {
      flushFarLeaves();
      const xx=x+(rng()-.5)*5,z=far(xx)-8-rank*20-rng()*13;
      const height=rank===0?7+rng()*10:rank===1?16+rng()*14:23+rng()*21;
      const width=(rank===0?4.8:7)+rng()*4,lean=(rng()-.5)*4;
      branch([[xx,L.lo+1,z],[xx+lean*.35,L.lo+height*.48,z-1],[xx+lean,L.lo+height,z-2]],.19+rank*.09,.02,masses);
      for(let b=0;b<4;b++) {
        const a=rng()*6.28,r=width*(.25+rng()*.5);
        const tip=[xx+lean+Math.cos(a)*r,L.lo+height*(.50+b*.115),z+Math.sin(a)*r];
        branch([[xx+lean*.4,L.lo+height*.4,z],[(xx+tip[0])*.5,tip[1]-1.7,(z+tip[2])*.5],tip],.095,.012,masses);
        const crownY=2.8+rank+rng()*2;
        leafCloud(...tip,width*.64,crownY,width*.58,rank===0?1600:2400,farStore,rank===0?1.0:1.3);
      }
    }
    flushFarLeaves();
    yardLap('    lake: far ranks');
    yardTimings.push([`    (of which leafCloud, ${leafCloudLeaves} leaves)`, +leafCloudMs.toFixed(1)]);
  });
}

function addBackYard(L, rng, leaves, beds, props, lawns, trunks, masses) {
  const yN = L.padN;            // where the raised lawn ends
  // The rear deck has adjacent upper and lower platforms: x3..20.6,
  // z-42.2..-24.43 and x20.6..42.2,z-42.2..-10.91. Its north stair
  // landing is x8..12.6,z-46.4..-42.2; planting clears both flights.
  // 1. Rock beds edging the lawn. NARROW: the photographs are lawn-dominated
  //    with the rock confined to a border at the foot of the treeline and one
  //    wider apron beside the deck steps.
  // straddles the pad's rear edge, which is where "Backyard v3 5" puts the
  // mulch border: on the far edge of the lawn, not out beyond it
  // The north border is the curved shore built below, beyond the open lawn.
  addBed(rng, L.padW - 1.5, -46, L.padW + 3.0, L.wingN - 6, L.lo + 0.04, beds, 4.4);
  addBed(rng, L.padE - 7.5, -47, L.padE + 2, -28, L.lo + 0.04, beds, 4.4);
  // stepping stones running away from the deck's east flight, as in the aerial
  addFlagstones(rng, [[L.padE - 5.5, -33], [L.padE - 4.4, -35.4], [L.padE - 5.4, -37.8],
                      [L.padE - 4.2, -40.2], [L.padE - 5.3, -42.6]], L.lo + 0.06, beds);

  // Photo 03/08/09/10: clipped evergreen specimens frame the porch; the
  // central lawn is open. The rear-only detail builder owns its fixed RNG.
  yardLap('  back: beds + flagstones');
  addRearPlantingDetail(L, leaves, beds, props);
  yardLap('  back: addRearPlantingDetail');

  // The reference lake replaces the old opaque boundary ranks and north houses.
  // Keep the rear lawn spacious: the shoreline and its trees stand another
  // 20 feet north of the imported site-pad boundary. Front anchors stay fixed.
  const rearSite = { ...L, yardN: L.yardN - 20 };
  addRearLakeDetail(rearSite, leaves, beds, props, lawns, trunks, masses);
  yardLap('  back: addRearLakeDetail');
  lowerRearShellPad();
  yardLap('  back: lowerRearShellPad');
  addRearGroundDetail(rearSite, { lowGrade: true });
  yardLap('  back: addRearGroundDetail');
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
  ['building', 'Rear deck detail', () => addRearDeckDetail, (f) => (addRearDeckDetail = f)],
  ['building', 'Rear porch detail', () => addRearPorchDetail, (f) => (addRearPorchDetail = f)],
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
  if(item.authoredPivot)return item.authoredPivot.slice();
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

// Opening the editor is what BUILDS the yard (one mesh per item so each piece
// can be picked and dragged); closing it disposes the yard again. The viewer
// never has one. Returns true if the mode actually changed.
export function setYardEditing(on) {
  if (yardEditing === !!on) return false;
  yardEditing = !!on;
  applyYardVisibility();
  if (yardEditing) {
    remeasureShell();
    buildYard();
    settleShellAnchors();
  } else {
    teardownYard();
  }
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
  if (yardEditing) buildYard();
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
  measureHouse(house);         // keeps getEnvironmentCenter() right for weather.js
  hideShellPatioProps();       // idempotent; the shell is already loaded at boot
  // The yard itself is built only while the Outside editor is open.
  if (yardEditing) {
    buildYard();
    settleShellAnchors();
  }
}

// A safety net for the anchors moving under the first build. It used to fire
// on EVERY boot: the roofRect the boot build saw was z0 -25.43 / z1 41.36 and
// "one frame later" it was -25.77 / 41.70, so the whole yard (13-15 s of main
// thread) was built twice. The cause was never a settling shell -- it was
// eavelights.js adding its group (LED strips, siding wash, lit window) INTO
// the shell after the yard had measured it, and house.js getBuildingBox()
// counting those meshes as roof. main.js now runs initEaveLights() before
// setEnvironmentData(), so the first measurement is the final one and these
// ticks are no-ops. Kept because anything else that grows the shell later
// would otherwise leave the yard silently offset from every later rebuild
// (which is what made saved yard edits drift: a piece has to be the same
// piece across rebuilds to be editable at all). setTimeout rather than
// requestAnimationFrame on purpose -- rAF is paused in a backgrounded or
// occluded tab, and the yard must settle whether or not anyone is watching.
const ANCHOR_SETTLE_MS = [0, 120, 500];

function settleShellAnchors() {
  for (const ms of ANCHOR_SETTLE_MS) {
    setTimeout(() => { if (yardEditing && lastHouse && remeasureShell()) buildYard(); }, ms);
  }
}

// The house's traced footprint: the building bbox (excluding the outdoor
// pseudo-rooms, Frontyard/Backyard = porch and deck rects — plants anchor to
// the building but must dodge every pad), every room rect, and the garage.
// Also writes `center`, which weather.js reads every tick to place rain, snow
// and clouds — so this runs on every setEnvironmentData, yard or no yard.
function measureHouse(house) {
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
  return { minX, minZ, maxX, maxZ, pads, garage };
}

// Remove and dispose the yard, and undo everything the build did OUTSIDE the
// yard group: the deck re-parenting, the car, the retry timers, and the cut
// in the shell's rear pad. Run at the top of every build and when the Outside
// editor closes -- after this the scene holds no exterior at all.
function teardownYard() {
  if (rearDeckInstanceTimer) { clearTimeout(rearDeckInstanceTimer); rearDeckInstanceTimer = null; }
  if (rearLightTimer) { clearTimeout(rearLightTimer); rearLightTimer = null; }
  // Before the dispose sweep below, not after: see disposeCar().
  if (rearDeckInstanceCleanup) {
    rearDeckInstanceCleanup();
    rearDeckInstanceCleanup = null;
  }
  disposeCar();
  carSpot = null;
  restoreRearShellPad();
  if (yard) {
    root.remove(yard);
    // ownGeometry per MESH, the same rule disposeCar uses and for the same
    // reason: the yard mixes geometry it authored itself (the buckets, the
    // contact blob) with library models, whose getInstance does
    // `scene.clone(true)` and SHARES BufferGeometry with the model cache.
    // Disposing that would blank out every later instance of the .glb -- in the
    // yard, in the rooms, everywhere. Materials are cloned per instance, so
    // those are always ours to release.
    yard.traverse((o) => {
      if (!o.isMesh) return;
      if (o.userData.ownGeometry === true) o.geometry.dispose();
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.dispose();
    });
    yardGrassMats.length = 0; // those materials were just disposed with the yard
    yard = null;
  }
  items = [];
  itemsByKey = new Map();
}

function buildYard() {
  const house = lastHouse;
  const { minX, minZ, maxX, maxZ, pads, garage } = measureHouse(house);

  // the shell GLB's measured footprint wins over the traced room rects —
  // trees anchor to what the eye sees, and nothing may grow inside it
  if (shellRect) pads.push(shellRect);
  const bx0 = shellRect ? shellRect.x0 : minX;
  const bz0 = shellRect ? shellRect.z0 : minZ;
  const bx1 = shellRect ? shellRect.x1 : maxX;
  const bz1 = shellRect ? shellRect.z1 : maxZ;

  teardownYard();
  yard = new THREE.Group();
  root.add(yard);

  const rng = mulberry32(1337);
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
  // Consume the original rear scatter seed, but let the measured rear planting
  // own this area. Discarded geometry cannot shift any subsequent front item.
  const rearScatterSink = { push: (g) => g.dispose() };
  for (let i = 0; i < 5; i++) {
    addBush(rng, bx1 + 14 + rng() * 16, bz0 - 8 - rng() * 14, roofRect ? rearScatterSink : leaves);
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
  const buildT0 = performance.now();
  yardTimings = [];
  yardLapT = buildT0;
  if (roofRect) {
    const L = landmarks(roofRect);
    addGroundCover(L, lawns); yardLap('addGroundCover');
    addFrontYard(L, rng, leaves, beds, props, lawns, trunks, masses); yardLap('addFrontYard');
    addBackYard(L, rng, leaves, beds, props, lawns, trunks, masses); yardLap('addBackYard');
    addRearPorchDetail(L, props, masses); yardLap('addRearPorchDetail');
    addRearDeckDetail(L, props, masses); yardLap('addRearDeckDetail');
    addRearSidingDetail(); yardLap('addRearSidingDetail');
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

  // Library models standing in the yard: a bench, a grill, a lamp -- anything
  // in the model library, placed outside as its own piece. They own no bucket
  // geometry, so they are items purely for IDENTITY: the editor panel, the
  // erased list, drag and undo all reach a piece through getYardItem, and this
  // is what puts one there. Their pivot is the origin, so the dx/dy/dz stored
  // against them is simply where they stand -- there is no generated piece
  // underneath to be an offset from. The geometry arrives later, in
  // addYardModels, because a .glb load is async.
  const modelItems = [];
  for (const row of yardEdits) {
    if (!row.model_id) continue;
    const item = {
      kind: 'model', label: row.label || 'Model', geos: [], key: row.key,
      pivot: [0, 0, 0], edit: row, isModel: true, modelId: row.model_id,
    };
    items.push(item);
    itemsByKey.set(row.key, item);
    modelItems.push(item);
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
  let rearFoliageMat = null, rearBarkMat = null, rearOakLeafMat = null, rearFarOakMat = null, rearConiferSprayMat = null;

  function bucketMesh(name, geos) {
    if (!geos.length) return null;
    // Only the new rear bark uses the photographed CC0 oak PBR material.
    // Split within the buckets so every tree retains its existing edit group.
    if(name==='masses'&&geos.some(g=>g.userData?.rearBark)) {
      const group=new THREE.Group(),ordinary=geos.filter(g=>!g.userData?.rearBark);
      if(ordinary.length)group.add(bucketMesh(name,ordinary));
      if(!rearBarkMat) {
        const loader=new THREE.TextureLoader(),albedo=loader.load('/textures/backyard/oak-bark-albedo.webp');
        const normal=loader.load('/textures/backyard/oak-bark-normal.webp');
        albedo.colorSpace=THREE.SRGBColorSpace;
        for(const tex of [albedo,normal]){tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.anisotropy=8;}
        rearBarkMat=new THREE.MeshStandardMaterial({map:albedo,normalMap:normal,normalScale:new THREE.Vector2(.85,.85),vertexColors:true,roughness:.97});
        rearBarkMat.addEventListener('dispose',()=>{albedo.dispose();normal.dispose();});
      }
      const barkMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(geos.filter(g=>g.userData?.rearBark)),false),rearBarkMat);
      barkMesh.name='rear-lake-bark';barkMesh.castShadow=barkMesh.receiveShadow=true;
      barkMesh.userData.ownGeometry=true;group.add(barkMesh);return group;
    }
    // Only these leaf surfaces carry photographic leaf UVs. Other rear plants
    // keep their existing foliage material and the front bypasses this branch.
    if(name==='props'&&geos.some(g=>g.userData?.rearOakLeaf)) {
      const group=new THREE.Group(),ordinary=geos.filter(g=>!g.userData?.rearOakLeaf);
      if(ordinary.length)group.add(bucketMesh(name,ordinary));
      if(!rearOakLeafMat) {
        const loader=new THREE.TextureLoader(),map=loader.load('/textures/backyard/oak-leaf-albedo.webp');
        const normal=loader.load('/textures/backyard/oak-leaf-normal-dx.webp');
        map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=8;normal.anisotropy=8;
        rearOakLeafMat=new THREE.MeshStandardMaterial({map,normalMap:normal,normalScale:new THREE.Vector2(.4,-.4),
          vertexColors:true,alphaTest:.45,side:THREE.DoubleSide,roughness:.91,metalness:0});
        rearOakLeafMat.addEventListener('dispose',()=>{map.dispose();normal.dispose();});
      }
      for(const distant of [false,true]) {
        const selected=geos.filter(g=>g.userData?.rearOakLeaf&&!!g.userData?.rearFarLeaf===distant);
        if(!selected.length)continue;
        if(distant&&!rearFarOakMat) {
          rearFarOakMat=rearOakLeafMat.clone();
          // Far foliage can remain when every editable near tree is deleted.
          // It therefore also owns disposal of the shared leaf textures.
          rearFarOakMat.addEventListener('dispose',()=>{rearFarOakMat.map?.dispose();rearFarOakMat.normalMap?.dispose();});
          const atmosphere={rearFarSky:{value:new THREE.Color()},rearFarDay:{value:1}};
          rearFarOakMat.userData.rearAtmosphere=atmosphere;
          rearFarOakMat.onBeforeCompile=shader=>{
            Object.assign(shader.uniforms,atmosphere);
            shader.fragmentShader='uniform vec3 rearFarSky;\nuniform float rearFarDay;\n'+shader.fragmentShader;
            shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',
              '#include <color_fragment>\nfloat farLeafLuma=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));\ndiffuseColor.rgb=mix(vec3(farLeafLuma),diffuseColor.rgb,.40)*1.23;');
            shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',
              'float farAir=clamp(1.0-exp(-length(vViewPosition)*.00050),0.0,.24);\n'+
              'vec3 farAirColor=mix(rearFarSky,vec3(dot(rearFarSky,vec3(.2126,.7152,.0722))),.36);\n'+
              'outgoingLight=mix(outgoingLight,farAirColor*(1.0+rearFarDay*.08),farAir);\n#include <opaque_fragment>');
          };
          rearFarOakMat.customProgramCacheKey=()=> 'rear-distant-oak-atmosphere-v1';
        }
        const mat=distant?rearFarOakMat:rearOakLeafMat;
        const leafMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(selected),false),mat);
        leafMesh.name=distant?'rear-distant-oak-leaves':'rear-scanned-oak-leaves';
        leafMesh.castShadow=leafMesh.receiveShadow=true;leafMesh.userData.ownGeometry=true;
        if(distant)leafMesh.onBeforeRender=()=>{
          const uniforms=rearFarOakMat.userData.rearAtmosphere;
          if(scene.background?.isColor)uniforms.rearFarSky.value.copy(scene.background);
          uniforms.rearFarDay.value=1-getNightFactor();
        };
        group.add(leafMesh);
      }
      return group;
    }
    // Only the appended rear conifer uses small fixed twig-spray alpha planes.
    // Split before the common foliage path so no existing shrub is retextured.
    if(name==='props'&&geos.some(g=>g.userData?.rearConiferSprays)){
      const group=new THREE.Group(),sprays=geos.filter(g=>g.userData?.rearConiferSprays);
      const ordinary=geos.filter(g=>!g.userData?.rearConiferSprays);
      if(ordinary.length)group.add(bucketMesh(name,ordinary));
      if(!rearConiferSprayMat){
        const map=new THREE.TextureLoader().load('/textures/rear-conifer-spray.png',undefined,undefined,()=>{
          // Keep the real twig/needle geometry if the optional atlas is absent.
          if(rearConiferSprayMat)rearConiferSprayMat.visible=false;
        });
        map.colorSpace=THREE.SRGBColorSpace;
        rearConiferSprayMat=new THREE.MeshStandardMaterial({map,vertexColors:true,
          alphaTest:.38,roughness:.98,side:THREE.DoubleSide});
        rearConiferSprayMat.addEventListener('dispose',()=>map.dispose());
      }
      const mesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(sprays),false),rearConiferSprayMat);
      // Three's shadow depth pass inherits map + alphaTest from this material,
      // so only the needle mask casts; the transparent corners never cast quads.
      mesh.castShadow=mesh.receiveShadow=true;mesh.userData.ownGeometry=true;group.add(mesh);
      return group;
    }
    // Rear leaf surfaces keep normal per-item editing but use a matte material.
    // The front's original props and their material pass through unchanged.
    if (name === 'props' && geos.some(g => g.userData?.rearFoliage)) {
      const group = new THREE.Group();
      const ordinary = geos.filter(g => !g.userData?.rearFoliage);
      const foliage = geos.filter(g => g.userData?.rearFoliage);
      if (ordinary.length) group.add(bucketMesh(name, ordinary));
      if(!rearFoliageMat) {
        rearFoliageMat=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,metalness:0,side:THREE.DoubleSide});
        // A thin leaf transmits part of incident light from its opposite face.
        // Both terms use the actual shadowed sun / hemisphere irradiance;
        // no emissive constant, normal bias or extra light is introduced.
        rearFoliageMat.onBeforeCompile=shader=>{
          const marker='reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );';
          const physical=THREE.ShaderChunk.lights_physical_pars_fragment.replace(marker,marker+
            '\nreflectedLight.directDiffuse += max(-dot(geometryNormal,directLight.direction),0.0) * directLight.color * BRDF_Lambert(material.diffuseColor) * 0.22;');
          shader.fragmentShader=shader.fragmentShader.replace('#include <lights_physical_pars_fragment>',physical);
          shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_end>','#include <lights_fragment_end>\n'+
            '#if NUM_HEMI_LIGHTS > 0\nvec3 rearLeafBackIrradiance=vec3(0.0);\n'+
            '#pragma unroll_loop_start\nfor(int i=0;i<NUM_HEMI_LIGHTS;i++){rearLeafBackIrradiance += getHemisphereLightIrradiance(hemisphereLights[i],-geometryNormal); }\n#pragma unroll_loop_end\n'+
            'reflectedLight.indirectDiffuse += rearLeafBackIrradiance * BRDF_Lambert(material.diffuseColor) * 0.28;\n#endif');
        };
        rearFoliageMat.customProgramCacheKey=()=> 'rear-thin-leaf-v1';
      }
      const leafMesh = new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(foliage), false), rearFoliageMat);
      leafMesh.castShadow = leafMesh.receiveShadow = true;
      leafMesh.userData.ownGeometry = true;
      group.add(leafMesh);
      return group;
    }
    const m = new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(geos), false), MATS[name]);
    m.castShadow = !!CASTS[name];
    m.receiveShadow = !!RECEIVES[name];
    m.userData.ownGeometry = true;   // merged here, so ours to dispose
    return m;
  }

  if (yardEditing) {
    // EDITOR: one group per item, sitting at its own pivot with its geometry
    // re-centred there, so TransformControls can move/turn/scale it directly
    // and the gesture reads straight back out as the delta to save.
    for (const item of items) {
      // A library model owns no bucket geometry -- addYardModels below builds
      // its group from the .glb instead. Without this it also gets an EMPTY
      // group here, under the same yardKey, and that phantom is what
      // getYardPickables hands back to a selection first.
      if (item.isModel) continue;
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
        if (mesh) group.add(mesh);
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
    // MERGED: the original six merged meshes. Unreachable since the viewer
    // stopped building the yard (buildYard only runs while yardEditing), kept
    // as the cheap draw path should a "show the yard in the viewer" toggle
    // ever come back. Deleted items drop out and every other item's delta is
    // baked into its geometry here.
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
  shadow.userData.ownGeometry = true;
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set((bx0 + bx1) / 2, -0.03, (bz0 + bz1) / 2);
  yard.add(shadow);

  yardLap('resolve items + merge');
  addRearLightDetail(buckets);
  addRearAtmosphereDetail();
  configureRearDeckInstances();
  syncCar();
  addYardModels(modelItems);
  yardLap('rear light/atmosphere/deck/car');
  yardTimings.push(['TOTAL', +(performance.now() - buildT0).toFixed(1)]);

  // yard.js holds references into the groups this build just replaced, and
  // undo/redo and a house reload both land here without going through it.
  window.dispatchEvent(new CustomEvent('yardRebuilt'));
}

// One group per library model in the yard, in BOTH draw modes -- a .glb cannot
// be merged into the six bucket meshes, so unlike every other yard piece it is
// its own object even in the viewer. Shaped like a per-item editor group
// (kind 'yard', a key, a pivot) so picking, the gizmo and the panel need no
// special case; drag.js subtracts the pivot, which here is the origin.
//
// The load is async, so each captures the yard it was started for and drops the
// result if a rebuild has already replaced it -- the same guard syncCar uses.
// When the last one lands, `yardRebuilt` fires a second time: yard.js is
// holding group references and its selection has to find one that did not exist
// when the build finished.
function addYardModels(list) {
  if (!list.length) return;
  const forYard = yard;
  let pending = list.length;
  let landed = 0;
  const done = () => {
    if (forYard !== yard || --pending > 0 || !landed) return;
    window.dispatchEvent(new CustomEvent('yardRebuilt'));
  };
  for (const item of list) {
    const e = item.edit || {};
    getInstance(item.modelId, 'bottom').then((pivot) => {
      if (forYard !== yard) return;
      const g = new THREE.Group();
      g.position.set(e.dx || 0, e.dy || 0, e.dz || 0);
      g.rotation.y = e.rot_y || 0;
      g.scale.setScalar(e.scale ?? 1);
      // built and hidden, never skipped: un-erasing is a visibility flip and
      // the editor's Erased list has something to name. Same as every other
      // yard piece.
      g.visible = !e.deleted;
      g.userData = {
        kind: 'yard', yardKey: item.key, name: item.label, yardKind: 'model',
        pivot: item.pivot, isModel: true, userScale: e.scale ?? 1,
      };
      pivot.traverse((o) => {
        if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
      });
      g.add(pivot);
      yard.add(g);
      landed += 1;
    }).catch((err) => {
      console.warn('yard model %s failed to load:', item.modelId, err);
    }).then(done, done);
  }
}

// Rear porch finish, measured in the live shell (porch_probe.json, 2026-09-12).
// Glass skins sit ahead of the original blue glass, with physical grille bars.
// Only the two rear door leaves are touched. Photos 14 / 02 fix the details.
function addRearPorchDetail(L, props, masses) {
  const dx = L.blockE - 20.0, dz = L.blockN + 24.5;
  const put = (bucket, w, h, d, x, y, z, color) => {
    const g = boxAt(w, h, d, x + dx, y, z + dz);
    paint(g, new THREE.Color(color));
    bucket.push(g);
  };
  // Restrained nonemissive value field, not an invented interior picture.
  for (const [x0, x1, z] of [[9.5793, 12.6804, -24.3478],
                            [13.0083, 16.1094, -24.2480]]) {
    const y0 = 2.2966, y1 = 11.1080;
    const g = new THREE.PlaneGeometry(x1 - x0, y1 - y0, 8, 18);
    g.rotateY(Math.PI);
    g.translate((x0 + x1) / 2 + dx, (y0 + y1) / 2, z + dz);
    const a = g.attributes.position, colors = new Float32Array(a.count * 3);
    for (let i = 0; i < a.count; i++) {
      const u = (a.getX(i) - dx - x0) / (x1 - x0);
      const v = (a.getY(i) - y0) / (y1 - y0);
      const f = 0.90 + v * 0.38 + 0.06 * Math.sin(u * 9 + v * 4);
      const c = new THREE.Color(0x272e2d).multiplyScalar(f);
      colors.set([c.r, c.g, c.b], i * 3);
    }
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    props.push(g);
  }
  // The source's fine grille is part of its glass appearance; reproduce its
  // three-column/six-row divisions in front of the neutral glazing skin.
  for (const [x0, x1, z] of [[9.5793, 12.6804, -24.390],
                            [13.0083, 16.1094, -24.290]]) {
    for (let i = 1; i < 3; i++)
      put(masses, 0.034, 8.81, 0.026, x0 + (x1 - x0) * i / 3,
        2.2966, z, 0xc3c6bd);
    for (let i = 1; i < 6; i++)
      put(masses, x1 - x0, 0.034, 0.026, (x0 + x1) / 2,
        2.2966 + 8.8114 * i / 6, z, 0xc3c6bd);
  }
  for (const [x0, x1, z] of [[9.5793, 12.6804, -24.360],
                            [13.0083, 16.1094, -24.260]]) {
    for (const x of [x0 + 0.018, x1 - 0.018])
      put(masses, 0.036, 8.78, 0.018, x, 2.31, z, 0x282b2a);
    for (const y of [2.315, 11.075])
      put(masses, x1 - x0, 0.038, 0.018, (x0 + x1) / 2, y, z, 0x282b2a);
  }
  // Recessed charcoal handle: backplate, two stand-offs and the pull.
  put(props, 0.125, 0.64, 0.040, 12.843, 5.42, -24.430, 0x252728);
  for (const y of [5.46, 5.94])
    put(props, 0.090, 0.070, 0.100, 12.843, y, -24.490, 0x1d2020);
  put(props, 0.070, 0.52, 0.068, 12.843, 5.475, -24.555, 0x343838);
  // Sill and parallel sliding tracks sit above the existing deck boards.
  put(masses, 7.03, 0.095, 0.43, 12.844, 2.73, -24.58, 0x9a9b96);
  for (const z of [-24.72, -24.51])
    put(props, 6.64, 0.030, 0.037, 12.844, 2.825, z, 0xb4b7b1);
  put(masses, 6.62, 0.014, 0.068, 12.844, 2.829, -24.62, 0x373c3b);

  // These are owned optical surfaces over the measured source door leaves.
  // A live planar reflection supplies the actual yard, rail and foliage; no
  // photograph, interior tableau or change to the shared shell material.
  const glassGroup=new THREE.Group();glassGroup.name='rear-porch-glazing';
  yard.add(glassGroup);
  const glassMaterial=new THREE.MeshStandardMaterial({color:0x19201e,roughness:.13,metalness:0});
  const reflectionTarget=new THREE.WebGLRenderTarget(1024,1024,{type:THREE.HalfFloatType});
  const uniforms={porchReflection:{value:reflectionTarget.texture},porchProjection:{value:new THREE.Matrix4()}};
  glassMaterial.onBeforeCompile=shader=>{
    Object.assign(shader.uniforms,uniforms);
    shader.vertexShader='uniform mat4 porchProjection;\nvarying vec4 porchReflect;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>',
      '#include <worldpos_vertex>\nporchReflect=porchProjection*modelMatrix*vec4(transformed,1.0);');
    shader.fragmentShader='uniform sampler2D porchReflection;\nvarying vec4 porchReflect;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',
      'float porchFresnel=pow(1.0-abs(dot(normalize(vViewPosition),normal)),5.0);\n'
      +'vec3 porchReflected=texture2D(porchReflection,porchReflect.xy/porchReflect.w).rgb;\n'
      +'outgoingLight=mix(outgoingLight,porchReflected,0.10+0.72*porchFresnel);\n#include <opaque_fragment>');
  };
  glassMaterial.customProgramCacheKey=()=> 'rear-porch-scene-glass-v1';
  let disposed=false,reflecting=false,lastReflect=-Infinity;
  glassMaterial.addEventListener('dispose',()=>{disposed=true;reflectionTarget.dispose();});
  const mirror=new THREE.PerspectiveCamera(),plane=new THREE.Plane(),clip=new THREE.Vector4(),q=new THREE.Vector4();
  const lastCamera=new THREE.Matrix4(),lastProjection=new THREE.Matrix4();
  const bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1);
  const planeZ=-24.36+dz;
  for(const [x0,x1,z] of [[9.5793,12.6804,-24.365],[13.0083,16.1094,-24.265]]){
    const geometry=new THREE.PlaneGeometry(x1-x0,8.8114);
    geometry.rotateY(Math.PI);geometry.translate((x0+x1)/2+dx,6.7023,z+dz);
    const glass=new THREE.Mesh(geometry,glassMaterial);glass.name='rear-slider-reflective-pane';
    glass.userData.ownGeometry=true;glassGroup.add(glass);
    glass.onBeforeRender=(activeRenderer,activeScene,camera)=>{
      // A lake mirror may render this door; retain its last reflection rather
      // than nesting another scene render. The reciprocal tag is understood by
      // the lake helper, so reflection cameras cannot recurse through each other.
      const surfacePlane=new THREE.Plane(new THREE.Vector3(0,0,-1),planeZ).applyMatrix4(glassGroup.matrixWorld);
      if(disposed||reflecting||camera.userData.rearLakeMirror||camera.userData.rearPorchMirror||surfacePlane.distanceToPoint(camera.position)<=0)return;
      const now=performance.now();
      if(now-lastReflect<100 || (camera.matrixWorld.equals(lastCamera)&&camera.projectionMatrix.equals(lastProjection)&&now-lastReflect<1500))return;
      reflecting=true;lastReflect=now;lastCamera.copy(camera.matrixWorld);lastProjection.copy(camera.projectionMatrix);
      const direction=new THREE.Vector3();camera.getWorldDirection(direction);direction.reflect(surfacePlane.normal);
      mirror.position.copy(camera.position).addScaledVector(surfacePlane.normal,-2*surfacePlane.distanceToPoint(camera.position));
      mirror.up.copy(camera.up).reflect(surfacePlane.normal);mirror.lookAt(mirror.position.clone().add(direction));
      mirror.near=camera.near;mirror.far=camera.far;mirror.projectionMatrix.copy(camera.projectionMatrix);
      mirror.updateMatrixWorld();mirror.matrixWorldInverse.copy(mirror.matrixWorld).invert();
      mirror.userData.rearLakeMirror=true;mirror.userData.rearPorchMirror=true;
      uniforms.porchProjection.value.copy(bias).multiply(mirror.projectionMatrix).multiply(mirror.matrixWorldInverse);
      plane.copy(surfacePlane);plane.constant-=.012;plane.applyMatrix4(mirror.matrixWorldInverse);
      clip.set(plane.normal.x,plane.normal.y,plane.normal.z,plane.constant);
      const p=mirror.projectionMatrix.elements;
      q.set((Math.sign(clip.x)+p[8])/p[0],(Math.sign(clip.y)+p[9])/p[5],-1,(1+p[10])/p[14]);
      clip.multiplyScalar(2/clip.dot(q));p[2]=clip.x;p[6]=clip.y;p[10]=clip.z+1;p[14]=clip.w;
      mirror.projectionMatrixInverse.copy(mirror.projectionMatrix).invert();
      const target=activeRenderer.getRenderTarget(),xr=activeRenderer.xr.enabled,shadow=activeRenderer.shadowMap.autoUpdate;
      const viewport=new THREE.Vector4();activeRenderer.getViewport(viewport);
      const visible=glassGroup.visible;glassGroup.visible=false;
      try{
        activeRenderer.xr.enabled=false;activeRenderer.shadowMap.autoUpdate=false;
        activeRenderer.setRenderTarget(reflectionTarget);activeRenderer.clear();activeRenderer.render(activeScene,mirror);
      }finally{
        glassGroup.visible=visible;activeRenderer.xr.enabled=xr;activeRenderer.shadowMap.autoUpdate=shadow;
        activeRenderer.setRenderTarget(target);activeRenderer.setViewport(viewport);reflecting=false;
      }
    };
  }

  // The overhead reference fixes the workstation along the WEST deck edge,
  // perpendicular to the slider wall; photo14 shows its east-facing panels.
  // Preserve the 6.1 x 1.55 x 3.39 ft envelope, rotating the authored -Z front
  // to +X. Wall-mounted accessories stay in the outer porch detail group.
  // The photographed body hangs above exposed slender legs; it is not a deep
  // floor-standing cupboard. No photograph or baked reflection is mapped here.
  const cabinet=new THREE.Group();cabinet.name='rear-porch-stainless-cabinet';yard.add(cabinet);
  const workstation=new THREE.Group();workstation.name='rear-porch-workstation';cabinet.add(workstation);
  workstation.rotation.y=-Math.PI/2;
  const workstationPivot=new THREE.Vector3(6.10+dx,0,-25.19+dz);
  workstation.position.copy(workstationPivot).applyEuler(workstation.rotation).negate()
    .add(new THREE.Vector3(3.90+dx,0,-28.00+dz));
  let detailGroup=workstation;
  const brushCanvas=document.createElement('canvas');brushCanvas.width=brushCanvas.height=256;
  const brushContext=brushCanvas.getContext('2d'),brushPixels=brushContext.createImageData(256,256),brushRng=mulberry32(0x53544545);
  for(let y=0;y<256;y++){
    const line=(brushRng()-.5)*20;
    for(let x=0;x<256;x++){
      const k=(y*256+x)*4,v=128+line+(brushRng()-.5)*5;
      brushPixels.data[k]=brushPixels.data[k+1]=brushPixels.data[k+2]=v;brushPixels.data[k+3]=255;
    }
  }
  brushContext.putImageData(brushPixels,0,0);const brush=new THREE.CanvasTexture(brushCanvas);
  brush.wrapS=brush.wrapT=THREE.RepeatWrapping;brush.repeat.set(2,8);brush.anisotropy=16;
  const steel=new THREE.MeshPhysicalMaterial({color:0xa9aea9,metalness:.94,roughness:.29,
    anisotropy:.58,anisotropyRotation:Math.PI/2,bumpMap:brush,bumpScale:.004});
  steel.addEventListener('dispose',()=>brush.dispose());
  const dark=new THREE.MeshStandardMaterial({color:0x666c67,metalness:.82,roughness:.38});
  const part=(name,w,h,d,x,y,z,mat=steel)=>{
    const m=new THREE.Mesh(boxAt(w,h,d,x+dx,y,z+dz),mat);m.name=name;
    m.userData.ownGeometry=true;m.castShadow=true;m.receiveShadow=true;detailGroup.add(m);return m;
  };
  part('workstation-recessed-body',5.80,2.30,1.28,6.10,3.45,-25.17,dark);
  part('workstation-left-folded-end',.045,2.39,1.41,3.14,3.42,-25.20);
  part('workstation-right-folded-end',.045,2.39,1.41,9.06,3.42,-25.20);
  part('workstation-continuous-counter',6.10,.105,1.55,6.10,5.87,-25.19);
  part('workstation-raised-rear-lip',6.04,.16,.045,6.10,5.975,-24.44);
  part('workstation-folded-counter-edge',6.10,.12,.055,6.10,5.80,-25.955);
  for(const [x,width] of [[4.63,2.88],[7.57,2.88]]){
    // Thin rolled sheet has slight physical bowing between its folded edges.
    // This changes real reflected rays into broad vertical steel highlights;
    // the fine directional texture above supplies only the brush scratches.
    const g=new THREE.PlaneGeometry(width,2.28,48,4);g.rotateY(Math.PI);
    const p=g.attributes.position;
    for(let i=0;i<p.count;i++){
      const u=(p.getX(i)+width/2)/width,v=(p.getY(i)+1.14)/2.28;
      const buckle=Math.sin(u*Math.PI)*Math.sin(v*Math.PI)*(.022*Math.sin(u*15)+.011*Math.sin(u*6+1.2));
      p.setZ(i,p.getZ(i)+buckle);
    }
    g.computeVertexNormals();g.translate(x+dx,4.61,-25.926+dz);
    const sheet=new THREE.Mesh(g,steel);sheet.name='workstation-brushed-sliding-panel';sheet.userData.ownGeometry=true;
    sheet.castShadow=true;sheet.receiveShadow=true;workstation.add(sheet);
    part('workstation-recessed-stainless-pull',.055,1.82,.032,x+(x<6.1?-1.34:1.34),3.71,-25.95,dark);
    part('workstation-pull-folded-edge',.025,1.82,.055,x+(x<6.1?-1.30:1.30),3.71,-25.98);
  }
  part('workstation-lower-panel-track',5.96,.07,.075,6.10,3.39,-25.96);
  for(const x of [3.23,8.97])for(const z of [-24.65,-25.76]){
    part('workstation-exposed-square-leg',.072,.89,.072,x,2.744,z);
    part('workstation-adjustable-foot',.12,.06,.12,x,2.744,z,dark);
  }
  for(const z of [-24.65,-25.76])part('workstation-underframe-rail',5.74,.045,.045,6.10,3.23,z);
  // The photograph shows two small pale plant pots on the work surface and
  // a raised weatherproof wall box above its west end. The wall box is not
  // a tap: keep that photographed distinction in the actual geometry.
  const pale=new THREE.MeshStandardMaterial({color:0xd5d6c8,roughness:.71});
  part('workstation-counter-container',.26,.39,.23,8.11,5.975,-24.86,pale);
  part('workstation-counter-container-west',.30,.31,.27,3.76,5.975,-24.96,pale);
  const plantStem=new THREE.MeshStandardMaterial({color:0x72745a,roughness:1});
  for(const x of [3.76,8.11])for(const [ox,height] of [[-.05,.67],[.065,.96]]){
    part('workstation-fine-plant-stem',.017,height,.017,x+ox,6.25,-24.91,plantStem);
    for(const y of [6.60,6.82]){
      const leaf=new THREE.Mesh(new THREE.SphereGeometry(.047,5,3),plantStem);
      leaf.position.set(x+ox+.036+dx,y,-24.91+dz);leaf.scale.set(1.6,.40,1);
      leaf.userData.ownGeometry=true;workstation.add(leaf);
    }
  }
  // These pieces are house-mounted; rotating the workstation must not move them.
  detailGroup=cabinet;
  part('rear-porch-weatherproof-wall-box',.41,.76,.22,4.29,6.94,-24.56,pale);
  part('rear-porch-wall-box-raised-hood',.49,.075,.29,4.29,7.70,-24.58,pale);
  part('rear-porch-wall-box-recess',.17,.39,.035,4.29,7.13,-24.69,dark);

  // Observed porch lantern and angled weatherproof speaker housings. They are
  // nonemissive geometry; the exterior lighting state/contract is unchanged.
  const hardware=new THREE.MeshStandardMaterial({color:0x323734,metalness:.24,roughness:.64});
  const lens=new THREE.MeshStandardMaterial({color:0xaeb5a7,roughness:.34,metalness:.12});
  part('rear-porch-lantern-wall-plate',.23,.59,.065,8.66,8.40,-24.51,hardware);
  part('rear-porch-lantern-arm',.055,.075,.28,8.66,8.84,-24.66,hardware);
  part('rear-porch-lantern-lens',.29,.46,.25,8.66,8.40,-24.82,lens);
  for(const x of [8.49,8.83])part('rear-porch-lantern-stile',.033,.49,.28,x,8.38,-24.82,hardware);
  for(const y of [8.36,8.87])part('rear-porch-lantern-cap',.40,.075,.35,8.66,y,-24.82,hardware);
  const speakerGeometry=new THREE.CapsuleGeometry(.20,.28,4,8);
  speakerGeometry.scale(1,1,.875);speakerGeometry.rotateX(-.24);speakerGeometry.rotateZ(-.15);
  speakerGeometry.translate(6.47+dx,9.49,-24.75+dz);
  const speaker=new THREE.Mesh(speakerGeometry,hardware);speaker.name='rear-porch-rounded-angled-speaker';
  speaker.userData.ownGeometry=true;speaker.castShadow=true;cabinet.add(speaker);
  // A local cube probe gives the steel outdoor reflections rather than the
  // renderer's generic indoor IBL. Capture only the real scene from in front
  // of this cabinet; its target is released by the owning material.
  const cabinetTarget=new THREE.WebGLCubeRenderTarget(128,{type:THREE.HalfFloatType,generateMipmaps:true,minFilter:THREE.LinearMipmapLinearFilter});
  steel.envMap=cabinetTarget.texture;dark.envMap=cabinetTarget.texture;
  const cabinetProbe=new THREE.CubeCamera(.15,300,cabinetTarget);
  for(const camera of cabinetProbe.children){camera.userData.rearLakeMirror=true;camera.userData.rearPorchMirror=true;}
  let probing=false,probeDisposed=false,lastProbe=-Infinity,lastProbeState='';
  steel.addEventListener('dispose',()=>{probeDisposed=true;cabinetTarget.dispose();});
  workstation.children[0].onBeforeRender=(activeRenderer,activeScene,camera)=>{
    if(probing||probeDisposed||camera.userData.rearLakeMirror||camera.userData.rearPorchMirror||performance.now()-lastProbe<5000)return;
    lastProbe=performance.now();
    const probeState=[activeScene.background?.getHex?.(),activeRenderer.toneMappingExposure,wetF,snowF,
      ...cabinet.matrixWorld.elements,...[...objects3d.values()].flatMap(o=>[o.children.length,o.visible,...o.matrixWorld.elements])].join(',');
    if(probeState===lastProbeState)return;lastProbeState=probeState;probing=true;
    cabinetProbe.position.set(5.78+dx,4.9,-27.1+dz).applyMatrix4(workstation.matrixWorld);
    const visible=cabinet.visible,xr=activeRenderer.xr.enabled,shadows=activeRenderer.shadowMap.autoUpdate;
    const viewport=new THREE.Vector4();activeRenderer.getViewport(viewport);cabinet.visible=false;
    try{activeRenderer.xr.enabled=false;activeRenderer.shadowMap.autoUpdate=false;cabinetProbe.update(activeRenderer,activeScene);}
    finally{cabinet.visible=visible;activeRenderer.xr.enabled=xr;activeRenderer.shadowMap.autoUpdate=shadows;activeRenderer.setViewport(viewport);probing=false;}
  };
}

// Rear deck finish and steps, isolated from the lake/ground helpers. Photos
// 02/14 show weathered grey composite, independent diagonal board fields, and
// continuous white rail tops. Photo09 fixes the four north stair risers.
function addRearDeckDetail(L, props, masses) {
  const rng = mulberry32(0x4445434b);
  // The drone and photos02/09 establish two SIDE-BY-SIDE platforms: the
  // open slider landing is west, and the lounge wraps east to the wing wall.
  // Keep every component together so the named placed deck can drive it.
  const deckGroup = new THREE.Group();
  deckGroup.name = 'rear-deck-layout-detail';
  deckGroup.userData.rearDeck = true;
  yard.add(deckGroup);
  // Unlike landscape landmarks, this is an overlay on a placed GLB whose
  // measured world coordinates are fixed by b_deck.py and its placement row.
  const dx = 0, dz = 0;
  // Five individual scanned plank interiors form an atlas. The UVs below
  // select just one interior per physical board, never the scan's joints.
  // Its 1.5 m span combines broken chalk wear with scanned scuffs and grit.
  const loader=new THREE.TextureLoader();
  const map=loader.load('/textures/backyard/deck-grain-albedo.webp');
  const normalMap=loader.load('/textures/backyard/deck-wood-normal.webp');
  const roughnessMap=loader.load('/textures/backyard/deck-roughness.webp');
  for(const texture of [map,normalMap,roughnessMap]) {
    texture.wrapS=THREE.ClampToEdgeWrapping;texture.wrapT=THREE.RepeatWrapping;
    texture.anisotropy=16;
  }
  map.colorSpace=THREE.SRGBColorSpace;
  const material=new THREE.MeshStandardMaterial({
    color:0xffffff,vertexColors:true,map,roughness:1,roughnessMap,metalness:0,
    normalMap,normalScale:new THREE.Vector2(.15,.15),
  });
  material.addEventListener('dispose',()=>{map.dispose();normalMap.dispose();roughnessMap.dispose();});
  const positions=[],normals=[],uvs=[],colors=[];
  const tri=(a,b,d,normal,tint,uv) => {
    for(const p of [a,b,d]) {
      positions.push(p[0]+dx,p[1],p[2]+dz); normals.push(...normal);
      uvs.push(...uv(p)); colors.push(tint.r,tint.g,tint.b);
    }
  };
  const clip=(poly,nx,nz,limit,keepLess) => {
    const out=[];
    for(let i=0;i<poly.length;i++) {
      const a=poly[i],b=poly[(i+1)%poly.length];
      const da=a[0]*nx+a[1]*nz-limit, db=b[0]*nx+b[1]*nz-limit;
      const ina=keepLess?da<=0:da>=0, inb=keepLess?db<=0:db>=0;
      if(ina) out.push(a);
      if(ina!==inb) { const t=da/(da-db); out.push([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]); }
    }
    return out;
  };
  const platform=(x0,z0,x1,z1,y,angle) => {
    const acrossX=Math.cos(angle),acrossZ=Math.sin(angle);
    const alongX=-acrossZ,alongZ=acrossX;
    const rect=[[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
    const edges=rect.map(([x,z])=>x*acrossX+z*acrossZ);
    const pitch=0.48, half=0.231, bevel=.006;
    for(let id=Math.floor(Math.min(...edges)/pitch);id<=Math.ceil(Math.max(...edges)/pitch);id++) {
      const center=id*pitch;
      let poly=clip(rect,acrossX,acrossZ,center-half,false);
      if(poly.length<3) continue;
      poly=clip(poly,acrossX,acrossZ,center+half,true);
      if(poly.length<3) continue;
      const light=0.945+rng()*0.050;
      const tint=new THREE.Color().setRGB(light,light,light,THREE.SRGBColorSpace);
      const shift=rng()*7;
      const scan=[[8,197],[211,402],[419,605],[624,810],[834,1014]][Math.floor(rng()*5)];
      const uv=p=>[(scan[0]+((p[0]*acrossX+p[2]*acrossZ-center)/(half*2)+.5)*(scan[1]-scan[0]))/1024,
        (p[0]*alongX+p[2]*alongZ)/4.92126+shift];
      const edgeHeight=(x,z)=>y-.006*Math.max(0,(Math.abs(x*acrossX+z*acrossZ-center)-(half-bevel))/bevel);
      // Three strips give each plank a physical eased edge. The top remains
      // planar; the bevel and the dark substrate reveal a recessed joint from
      // every camera instead of relying on an albedo stripe to imply a seam.
      for(const [lo,hi,side] of [[-half,-half+bevel,-1],[-half+bevel,half-bevel,0],[half-bevel,half,1]]) {
        let band=clip(poly,acrossX,acrossZ,center+lo,false);
        band=clip(band,acrossX,acrossZ,center+hi,true);if(band.length<3)continue;
        const surface=band.map(([x,z])=>[x,edgeHeight(x,z),z]);
        const normal=new THREE.Vector3(acrossX*side*1.1,1,acrossZ*side*1.1).normalize().toArray();
        const bandTint=tint.clone().multiplyScalar(side?.95:1);
        for(let i=1;i<surface.length-1;i++)tri(surface[0],surface[i+1],surface[i],normal,bandTint,uv);
      }
      const top=poly.map(([x,z])=>[x,edgeHeight(x,z),z]);
      const edgeTint=tint.clone().multiplyScalar(0.40);
      for(let i=0;i<top.length;i++) {
        const a=top[i],b=top[(i+1)%top.length], ax=[a[0],y-0.025,a[2]], bx=[b[0],y-0.025,b[2]];
        const len=Math.hypot(b[0]-a[0],b[2]-a[2]);
        if(len<0.0001) continue;
        const n=[(b[2]-a[2])/len,0,(a[0]-b[0])/len];
        tri(a,b,bx,n,edgeTint,uv); tri(a,bx,ax,n,edgeTint,uv);
      }
    }
  };
  // Both overhead references: upper runs east/west; lower southwest/northeast.
  // The angle is ACROSS the boards, perpendicular to their visible grain.
  platform(3.0,-42.2,20.60,-24.43,2.744,Math.PI/2);
  platform(20.60,-42.2,42.20,-10.91,2.424,Math.PI/4);
  const meshGeometry=new THREE.BufferGeometry();
  meshGeometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  meshGeometry.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
  meshGeometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
  meshGeometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  const finish=new THREE.Mesh(meshGeometry,material);
  finish.name='rear-deck-weathered-boards'; finish.userData.ownGeometry=true;
  finish.userData.rearDeck=true; finish.receiveShadow=true;
  deckGroup.add(finish);

  const detailGeometries=[];
  const put=(w,h,d,x,y,z,hex) => {
    const g=boxAt(w,h,d,x+dx,y,z+dz); paint(g,new THREE.Color(hex)); detailGeometries.push(g);
  };
  // Solid substrate keeps the narrow board seams dark; perimeter fascia and
  // posts are real geometry, including the exposed north and east elevations.
  for(const [x0,z0,x1,z1,y] of [[3,-42.2,20.60,-24.43,2.744],[20.60,-42.2,42.20,-10.91,2.424]]) {
    put(x1-x0,0.13,z1-z0,(x0+x1)/2,y-0.165,(z0+z1)/2,0x202628);
    for(const z of [z0,z1]) put(x1-x0+.20,.58,.20,(x0+x1)/2,y-.60,z,0x686b6c);
    for(const x of [x0,x1]) put(.20,.58,z1-z0,x,y-.60,(z0+z1)/2,0x686b6c);
    for(let x=x0+.35;x<x1;x+=6) for(const z of [z0+.35,z1-.35])
      put(.36,y-.62-L.lo,.36,x,L.lo,z,0x565c59);
  }
  // A single north/south nosing marks the shallow step between platforms.
  // Use the same worn composite on its top, darkened by the exposed edge's
  // wear; a solid color here reads like a painted metal strip at close range.
  const noseGeometry=boxAt(.31,.05,17.80,20.59+dx,2.720,-33.315+dz);
  paint(noseGeometry,new THREE.Color(0xb8b8b8));
  const nosePosition=noseGeometry.attributes.position,noseUV=noseGeometry.attributes.uv;
  for(let i=0;i<nosePosition.count;i++) {
    noseUV.setXY(i,.211+(nosePosition.getX(i)-dx-20.435)/.31*.181,
      (nosePosition.getZ(i)-dz)/4.92126);
  }
  const nosing=new THREE.Mesh(noseGeometry,material);
  nosing.name='rear-deck-weathered-step-nosing';
  nosing.userData.ownGeometry=true;nosing.userData.rearDeck=true;
  nosing.receiveShadow=true;deckGroup.add(nosing);
  put(.032,.29,17.80,20.76,2.424,-33.315,0x2d3133);
  const rail=(x0,z0,x1,z1,y)=>{
    const len=Math.hypot(x1-x0,z1-z0), n=Math.max(1,Math.ceil(len/5.8));
    for(let j=0;j<=n;j++) {
      const f=j/n,x=x0+(x1-x0)*f,z=z0+(z1-z0)*f;
      put(.29,3.00,.29,x,y,z,0xe2e3dd); put(.40,.10,.40,x,y+3,z,0xebebe5);
    }
    for(const [h,w,d] of [[2.80,.28,.28],[.24,.17,.17]])
      put(Math.abs(x1-x0)+w,.14,Math.abs(z1-z0)+d,(x0+x1)/2,y+h,(z0+z1)/2,0xe3e4de);
    const count=Math.floor(len/.40);
    for(let j=1;j<count;j++) {const f=j/count;
      put(.105,2.43,.105,x0+(x1-x0)*f,y+.37,z0+(z1-z0)*f,0xe7e8e2);
    }
  };
  rail(3,-42.2,3,-24.78,2.744);
  rail(3,-42.2,8,-42.2,2.744);
  rail(12.6,-42.2,20.60,-42.2,2.744);
  rail(20.60,-42.2,42.20,-42.2,2.424);
  rail(42.20,-42.2,42.20,-19.0,2.424);
  rail(42.20,-14.4,42.20,-11.1,2.424);
  // Four uniform risers from the UPPER landing to the restored low lawn.
  const topY=2.744, groundY=L.lo+0.027, rise=(topY-groundY)/4;
  for(let i=0;i<4;i++) {
    const z=-42.2-i*1.05;
    const treadY=topY-(i+1)*rise;
    put(4.60,0.13,1.08,10.30,treadY-0.13,z-0.525,0x686c70);
    put(4.50,rise,0.09,10.30,treadY,z-0.025,0x5f6366);
    put(4.62,0.045,0.065,10.30,treadY-0.03,z-1.05,0x7a7d80);
    // Dark recessed step-light housings only, matching the unlit photo forms.
    for(const x of [9.05,11.55]) put(0.15,0.105,0.015,x,treadY+rise*0.48,z-0.078,0x292c2d);
  }
  for(const x of [7.86,12.74]) {
    // Closed grey stringer stepped under the treads, and white stair rails.
    for(let i=0;i<4;i++) put(0.16,topY-(i+1)*rise-groundY+0.16,1.06,x,groundY,-42.725-i*1.05,0x686b6d);
    for(const [z,y] of [[-42.18,topY],[-46.34,groundY]]) {
      put(0.26,2.9,0.26,x,y,z,0xe0e0d9); put(0.37,0.09,0.37,x,y+2.9,z,0xe5e5df);
    }
    const a=new THREE.Vector3(x+dx,topY+2.65,-42.18+dz), b=new THREE.Vector3(x+dx,groundY+2.65,-46.34+dz);
    const rail=new THREE.BoxGeometry(0.19,0.17,a.distanceTo(b));
    const dir=b.clone().sub(a).normalize();
    rail.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),dir));
    rail.translate(...a.add(b).multiplyScalar(0.5).toArray()); paint(rail,new THREE.Color(0xdfdfd9)); detailGeometries.push(rail);
  }
  // East steps descend from the lounge onto the gravel, with no stair or
  // railing through the join between the two usable deck platforms.
  const eastRise=(2.424-groundY)/4;
  for(let i=0;i<4;i++) {
    const x=42.2+i*1.05,y=2.424-(i+1)*eastRise;
    put(1.08,.13,4.6,x+.525,y-.13,-16.7,0x686c70);
    put(.09,eastRise,4.5,x+.025,y,-16.7,0x5f6366);
    for(const z of [-19.05,-14.35]) put(1.06,y-groundY+.14,.16,x+.525,groundY,z,0x686b6d);
  }
  for(const z of [-19.13,-14.27]) {
    for(const [x,y] of [[42.18,2.424],[46.34,groundY]]) {
      put(.26,2.9,.26,x,y,z,0xe0e0d9);put(.37,.09,.37,x,y+2.9,z,0xe5e5df);
    }
    const a=new THREE.Vector3(42.18,5.074,z),b=new THREE.Vector3(46.34,groundY+2.65,z);
    const g=new THREE.BoxGeometry(.19,.17,a.distanceTo(b));
    g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,0,1),b.clone().sub(a).normalize()));
    g.translate(...a.add(b).multiplyScalar(.5).toArray());paint(g,new THREE.Color(0xdfdfd9));detailGeometries.push(g);
  }
  const detailsGeo=BufferGeometryUtils.mergeGeometries(detailGeometries,false);
  detailGeometries.forEach(g=>g.dispose());
  const details=new THREE.Mesh(detailsGeo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.82}));
  details.name='rear-deck-rails-frame-stairs';details.userData.ownGeometry=true;
  details.castShadow=true;details.receiveShadow=true;deckGroup.add(details);
}

// Runtime-only correction for the named rear objects. Corrections sit BELOW
// object roots, so saved root moves/rotation/scale, visibility, and selection
// retain their normal single writer. Cached GLB geometry is never mutated.
// Measured source placement snapshot (world feet), before this photo refit.
// Fixed baselines, rather than first-seen root matrices, preserve subsequently
// saved editor offsets through a full object/page reload as well as a rebuild.
function makeRearGrillCover() {
  const group=new THREE.Group();group.name='rear-grill-cloth-cover';group.userData.rearGrillCover=true;
  const positions=[],uv=[],indices=[],segments=96,rows=38;
  // Rounded rectangular cross sections follow the covered lid/side shelves.
  // The unsupported skirt gathers into irregular vertical folds; upper cloth
  // is pulled taut across the lid, with no hard box corners left exposed.
  const profile=[
    [0.07,2.15,1.16],[.22,2.19,1.19],[1.15,2.13,1.17],
    [2.18,2.19,1.20],[2.75,2.34,1.27],[3.02,2.40,1.28],
    [3.28,2.31,1.20],[3.65,1.82,1.09],[4.03,1.74,.85],
    [4.14,1.59,.67],[4.19,.02,.02],
  ];
  for(let row=0;row<=rows;row++){
    const y=.07+(4.19-.07)*row/rows;
    let at=1;while(at<profile.length-1&&profile[at][0]<y)at++;
    const a=profile[at-1],b=profile[at],t=(y-a[0])/(b[0]-a[0]);
    const width=THREE.MathUtils.lerp(a[1],b[1],t),depth=THREE.MathUtils.lerp(a[2],b[2],t);
    for(let i=0;i<=segments;i++){
      const theta=i/segments*Math.PI*2,c=Math.cos(theta),s=Math.sin(theta);
      const lower=Math.max(0,1-y/3.2);
      const fold=(Math.sin(theta*13+.38*Math.sin(y*2+theta*3))*.052
        +Math.sin(theta*23+y*.37)*.026)*(.25+lower*.9);
      const x=Math.sign(c)*Math.pow(Math.abs(c),.34)*(width+fold);
      const z=Math.sign(s)*Math.pow(Math.abs(s),.34)*(depth+fold);
      const hem=Math.sin(theta*7+.8)*.065*lower*lower;
      positions.push(x,y+hem,z);uv.push(i/segments*4,row/rows*3);
      if(row<rows&&i<segments){
        const n=row*(segments+1)+i;
        indices.push(n,n+segments+1,n+1,n+1,n+segments+1,n+segments+2);
      }
    }
  }
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geometry.setIndex(indices);geometry.computeVertexNormals();
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;
  const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(128,128),rng=mulberry32(0x434c4f54);
  for(let y=0;y<128;y++)for(let x=0;x<128;x++){
    const p=(y*128+x)*4,v=128+(rng()-.5)*34+(x%2-y%2)*11;
    pixels.data[p]=pixels.data[p+1]=pixels.data[p+2]=v;pixels.data[p+3]=255;
  }
  ctx.putImageData(pixels,0,0);const weave=new THREE.CanvasTexture(canvas);
  weave.wrapS=weave.wrapT=THREE.RepeatWrapping;weave.repeat.set(6,6);weave.anisotropy=8;
  const material=new THREE.MeshStandardMaterial({color:0x252726,roughness:.96,metalness:0,bumpMap:weave,bumpScale:.013,side:THREE.DoubleSide});
  material.addEventListener('dispose',()=>weave.dispose());
  const mesh=new THREE.Mesh(geometry,material);mesh.name='rear-grill-gathered-cloth';
  mesh.userData.ownGeometry=true;mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);
  // A sewn edge is geometry and therefore follows the cloth under every view.
  const hemPoints=[];
  for(let i=0;i<=segments;i++)hemPoints.push(new THREE.Vector3(positions[i*3],positions[i*3+1]+.055,positions[i*3+2]));
  const seamGeo=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(hemPoints),segments,.009,4,false);
  const seamMat=new THREE.MeshStandardMaterial({color:0x323432,roughness:1});
  const seam=new THREE.Mesh(seamGeo,seamMat);seam.name='rear-grill-sewn-hem';seam.userData.ownGeometry=true;group.add(seam);
  return group;
}
const REAR_DECK_SOURCE_POSES = new Map([
  ['Backyard Deck',[17.305,-.4,-33.83,0]],
  ['Backyard Grill',[7.01,2.77,-27.2,3.1067]],
  ['Backyard Sofa',[18.13,2.72,-30.4,4.6775]],
  ['Backyard Lounge',[11.022265930499458,2.4,-36.625,0]],
  ['Backyard Parasol',[25.516368632576242,2.4,-39.130784325773035,3.490658503988659]],
  ['Backyard Chaise',[21,2.4,-38.2,4.747295565424577]],
  ['Backyard Planter',[25.8,2.4,-34.4,0]],
  ['Backyard Planter Two',[4.8,2.4,-41.2,0]],
]);
let rearDeckInstanceTimer = null;
let rearDeckInstanceCleanup = null;
function configureRearDeckInstances() {
  if (rearDeckInstanceTimer) clearTimeout(rearDeckInstanceTimer);
  if (rearDeckInstanceCleanup) rearDeckInstanceCleanup();
  rearDeckInstanceCleanup = null;
  const owner=yard, replacement=owner?.getObjectByName('rear-deck-layout-detail');
  if(!replacement)return;
  // Keep added porch surfaces with the existing procedural porch item's
  // saved transform and deletion. Its original bounds/key stay unchanged.
  const porchItem=items.find(item=>item.label==='Rear porch detail'&&!item.isClone);
  if(porchItem)for(const name of ['rear-porch-glazing','rear-porch-stainless-cabinet']){
    const detail=owner.getObjectByName(name);if(!detail)continue;
    const itemGroup=yardEditing&&owner.children.find(o=>o.userData.yardKey===porchItem.key);
    if(itemGroup){itemGroup.add(detail);detail.position.set(...porchItem.pivot.map(v=>-v));}
    else{detail.matrixAutoUpdate=false;detail.matrix.copy(editMatrix(porchItem.pivot,porchItem.edit)||new THREE.Matrix4());detail.visible=!porchItem.edit?.deleted;}
  }
  const layout=new Map([
    // Both overhead references put the long grill axis along the west rail.
    ['Backyard Grill',[4.55,2.744,-38.50,270]],
    ['Backyard Sofa',[28.00,2.424,-40.15,0]],
    ['Backyard Lounge',[33.00,2.424,-31.60,0]],
    ['Backyard Chaise',[40.15,2.424,-33.00,0]],
    ['Backyard Parasol',[40.10,2.424,-39.50,200]],
    ['Backyard Planter',[40.50,2.424,-13.10,0]],
    ['Backyard Planter Two',[4.90,2.744,-32.80,0]],
  ]);
  const restores=[],applied=new WeakSet();
  // Parent calls this cleanup before the yard disposal sweep, moving the
  // replacement back under its owner so normal resource cleanup still owns it.
  rearDeckInstanceCleanup=()=>{
    for(const restore of restores)restore();
    if(replacement.parent!==owner)owner.add(replacement);
    replacement.matrixAutoUpdate=true;replacement.position.set(0,0,0);
    replacement.quaternion.identity();replacement.scale.set(1,1,1);
  };
  const settle=remaining=>{
    rearDeckInstanceTimer=null;if(yard!==owner)return;
    let found=0;
    for(const object of objects3d.values()) {
      const name=object.userData.name;
      if(!object.userData.outdoor || (name!=='Backyard Deck'&&!layout.has(name)))continue;
      const model=object.children.find(c=>c!==replacement);
      if(!model)continue;
      found++;if(applied.has(model))continue;
      object.updateWorldMatrix(true,true);model.updateMatrix();
      const [bx,by,bz,angle]=REAR_DECK_SOURCE_POSES.get(name);
      const base=new THREE.Matrix4().compose(new THREE.Vector3(bx,by,bz),
        new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),angle),new THREE.Vector3(1,1,1));
      const inverse=base.clone().invert();
      if(name==='Backyard Deck') {
        const visible=model.visible;model.visible=false;
        restores.push(()=>{model.visible=visible;});
        // Actual child of the placed deck: its editor transforms and normal
        // object visibility automatically carry the replacement with them.
        object.add(replacement);replacement.matrixAutoUpdate=false;
        replacement.matrix.copy(inverse);replacement.matrixWorldNeedsUpdate=true;
      } else {
        const old=model.matrix.clone(),auto=model.matrixAutoUpdate;
        const [x,y,z,degrees]=layout.get(name),scale=new THREE.Vector3();
        base.decompose(new THREE.Vector3(),new THREE.Quaternion(),scale);
        const target=new THREE.Matrix4().compose(new THREE.Vector3(x,y,z),
          new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),degrees*Math.PI/180),scale);
        model.matrixAutoUpdate=false;model.matrix.copy(inverse).multiply(target).multiply(old);
        model.matrixWorldNeedsUpdate=true;
        restores.push(()=>{model.matrix.copy(old);model.matrix.decompose(model.position,model.quaternion,model.scale);model.matrixAutoUpdate=auto;model.matrixWorldNeedsUpdate=true;});
        if(name==='Backyard Grill'){
          const cover=makeRearGrillCover(),visible=model.visible;
          model.visible=false;object.add(cover);cover.matrixAutoUpdate=false;
          cover.matrix.copy(inverse).multiply(target);cover.matrixWorldNeedsUpdate=true;
          // Restore source visibility and return owned meshes to the teardown
          // owner. The actual placed root remains the editor/visibility owner.
          restores.push(()=>{model.visible=visible;owner.add(cover);});
        }
      }
      applied.add(model);
    }
    owner.userData.rearDeckLayout={applied:found,upper:[3,-42.2,20.6,-24.43,2.744],lower:[20.6,-42.2,42.2,-10.91,2.424]};
    if(found<8&&remaining)rearDeckInstanceTimer=setTimeout(()=>settle(remaining-1),250);
  };
  settle(120);


}
// Rear-only mown turf. All texture marks are generated blade/albedo structure,
// never sampled from the photographs. A private RNG keeps front items identical.
// lowGrade is enabled only once the imported raised rear site pad is clipped.
function addRearGroundDetail(L, { lowGrade = false } = {}) {
  const rng = mulberry32(0x47524f55);
  const mid = (L.padW + L.padE) / 2;
  const edge = x => L.yardN + 6.8 + 2.8 * Math.sin((x - mid) / 13)
    + 1.6 * Math.cos((x - mid) / 6.8);
  const smooth = t => { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); };
  const grade = (x, z) => {
    if (lowGrade) return L.lo;
    const north = Math.max(0, Math.min(1, (z - (L.padN - 2.6)) / 2.6));
    const east = Math.max(0, Math.min(1, (L.lowE + 2.6 - x) / 2.6));
    const wing = Math.max(0, Math.min(1, (z + 32.4) / 1.8));
    const side = smooth((x - (L.padW - 2)) / 2) * smooth((L.padE + 2.4 - x) / 2.4);
    return L.lo + (L.hi - L.lo) * Math.max(north * east, wing) * side;
  };
  const height = (x, z) => {
    // Match the lake apron exactly; an eased ramp intersects its straight slope.
    const shoreRamp = Math.max(0, Math.min(1, (edge(x) + 2.6 - z) / 2.6)) * 0.685;
    return grade(x, z) + 0.027 + shoreRamp
      + 0.018 * Math.sin(x * 0.8 + z * 0.47) * Math.sin(z * 0.69 - x * 0.37);
  };

  // The rear turf is the FRONT lawn's material, deliberately: the same base
  // colour, the same procedural near-white tile at the same 8.57 ft repeat,
  // the same three-octave mono vertex noise the lawn buckets get (see the
  // colour pass in buildYard), and the same wet/snow tint through
  // repaintGrass(). Only the geometry is rear-specific: the lowered grade, the
  // gentle undulation and the ramp up to the lake apron. It used to be its own
  // photo-textured system -- a CC0 albedo + normal map, a lavender base under
  // a 4x sun / 2% ambient / x1.425 blue override, 160,000 shadow-casting blade
  // tufts and 2,400 clover -- which read as a different, blue-grey lawn behind
  // the house and cost ~10 s of every yard build. Not pushed into the lawns
  // bucket on purpose: a bucket geometry becomes a grabbable "piece" item in
  // the Outside editor, and a lot-sized clickable turf would swallow every
  // click behind the house (the reason SURFACE_KINDS excludes the lawn).
  const owner = yard, loader = new THREE.TextureLoader();
  const anisotropy = Math.min(16, renderer.capabilities.getMaxAnisotropy());
  const mat = new THREE.MeshStandardMaterial({
    color: grassMat.color.clone(), map: grassMat.map, roughness: 1, vertexColors: true });
  yardGrassMats.push(mat);
  const pos = [], uv = [], col = [];
  const x0 = L.padW - 29, x1 = L.padE + 29;
  const xs = Array.from({length: 181}, (_, i) => x0 + (x1 - x0) * i / 180);
  const zs = Array.from({length: 121}, (_, i) => L.yardN - 0.5 + (L.wingN - L.yardN + 0.5) * i / 120);
  xs.push(L.padW, L.padW - 2, L.lowE, L.lowE + 2.6, L.padE, L.padE + 2.4);
  zs.push(L.padN, L.padN - 2.6, -32.4, -30.6); xs.sort((a,b)=>a-b); zs.sort((a,b)=>a-b);
  const vertex = (x,z) => {
    z = Math.max(z, edge(x) + 0.1 + 0.06 * Math.sin(x * 7));
    pos.push(x, height(x,z), z);
    // the lawn tile's UV convention: world feet over the 2400 ft disc
    uv.push(x / 2400 + 0.5, -z / 2400 + 0.5);
    const f = 1 + (worldNoise(x, z, 54) - 0.5) * 0.14
                + (worldNoise(x + 313, z + 129, 19) - 0.5) * 0.19
                + (worldNoise(x + 91, z - 47, 7) - 0.5) * 0.11;
    col.push(f, f, f);
  };
  for (let ix=0;ix<xs.length-1;ix++) for(let iz=0;iz<zs.length-1;iz++) {
    const a=xs[ix],b=xs[ix+1],c=zs[iz],d=zs[iz+1];
    if (d < Math.min(edge(a),edge(b))) continue;
    for(const [x,z] of [[a,c],[a,d],[b,d],[a,c],[b,d],[b,c]]) vertex(x,z);
  }
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3)); geo.computeVertexNormals();
  const turf=new THREE.Mesh(geo,mat); turf.name='rear-mown-turf';
  turf.userData.ownGeometry=true; turf.receiveShadow=true;
  yard.add(turf);

  // Scanned oak contours and veins on individually curved eight-triangle leaves.
  // Their autumn pigments, burial and curl vary independently of the camera.
  const lp=[],lc=[],luv=[];
  const palette=[0x9c7644,0xb59058,0x8b704a,0xbba575,0x746344];
  for(let i=0;i<1350;i++) {
    const x=x0+rng()*(x1-x0), z=edge(x)+0.55+Math.pow(rng(),1.75)*24;
    if(z>L.padN-1)continue;
    const length=.35+rng()*.34,width=length*(.48+rng()*.17),angle=rng()*Math.PI*2,ca=Math.cos(angle),sa=Math.sin(angle);
    const y=height(x,z)+.065+rng()*.15, tone=new THREE.Color(palette[Math.floor(rng()*palette.length)]);
    const curlAcross=(rng()-.3)*.16,curlTip=(rng()-.35)*.18,twist=(rng()-.5)*.09;
    const put=(u,v)=>{const a=u*2-1,b=v*2-1,px=a*width*.5,pz=b*length*.5;
      lp.push(x+px*ca-pz*sa,y+a*a*curlAcross+b*b*curlTip+a*b*twist+.012*(1-Math.abs(a)),z+px*sa+pz*ca);
      lc.push(tone.r,tone.g,tone.b);luv.push(u,v);};
    for(let ux=0;ux<2;ux++)for(let vz=0;vz<2;vz++) {
      const u=ux*.5,v=vz*.5;
      for(const [a,b] of [[u,v],[u,v+.5],[u+.5,v+.5],[u,v],[u+.5,v+.5],[u+.5,v]])put(a,b);
    }
  }
  const leafGeo=new THREE.BufferGeometry();
  leafGeo.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));
  leafGeo.setAttribute('uv',new THREE.Float32BufferAttribute(luv,2));
  leafGeo.setAttribute('color',new THREE.Float32BufferAttribute(lc,3)); leafGeo.computeVertexNormals();
  const fallbackCanvas=document.createElement('canvas');fallbackCanvas.width=64;fallbackCanvas.height=112;
  const fallbackCtx=fallbackCanvas.getContext('2d');fallbackCtx.fillStyle='#606060';fallbackCtx.beginPath();
  for(let i=0;i<=72;i++){const a=i/72*Math.PI*2,r=1+.13*Math.sin(a*10),x=32+Math.sin(a)*25*r,y=55+Math.cos(a)*49; if(i)fallbackCtx.lineTo(x,y);else fallbackCtx.moveTo(x,y);}
  fallbackCtx.closePath();fallbackCtx.fill();
  const leafFallback=new THREE.CanvasTexture(fallbackCanvas);leafFallback.colorSpace=THREE.SRGBColorSpace;
  const leafMat=new THREE.MeshStandardMaterial({map:leafFallback,vertexColors:true,alphaTest:.45,
    normalScale:new THREE.Vector2(.3,-.3),roughness:.95,side:THREE.DoubleSide});
  const litterWeather={leafWet:{value:wetF},leafSnow:{value:snowF},leafSnowColor:{value:GRASS_SNOW}};
  leafMat.onBeforeCompile=shader=>{
    Object.assign(shader.uniforms,litterWeather);
    shader.fragmentShader='uniform float leafWet;\nuniform float leafSnow;\nuniform vec3 leafSnowColor;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>',
      '#include <map_fragment>\nfloat leafDetail=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));\ndiffuseColor.rgb=vec3(clamp(pow(max(leafDetail,.001)/.111,.8),.35,1.5));');
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',
      '#include <color_fragment>\ndiffuseColor.rgb*=1.0-.30*leafWet;\ndiffuseColor.rgb=mix(diffuseColor.rgb,leafSnowColor,leafSnow);');
  };
  leafMat.customProgramCacheKey=()=> 'rear-fallen-oak-autumn-v1';
  const litterMaps=[];let litterDisposed=false;
  for(const isNormal of [false,true]) {
    const map=loader.load('/textures/backyard/'+(isNormal?'oak-leaf-normal-dx.webp':'oak-leaf-albedo.webp'),loaded=>{
      if(litterDisposed||yard!==owner){loaded.dispose();return;}
      if(isNormal)leafMat.normalMap=loaded;else leafMat.map=loaded;leafMat.needsUpdate=true;
    },undefined,()=>{if(!litterDisposed)leafMat.userData[isNormal?'normalLoadFailed':'albedoLoadFailed']=true;});
    map.colorSpace=isNormal?THREE.NoColorSpace:THREE.SRGBColorSpace;map.anisotropy=anisotropy;litterMaps.push(map);
  }
  leafMat.addEventListener('dispose',()=>{litterDisposed=true;leafFallback.dispose();for(const map of litterMaps)map.dispose();});
  const fallen=new THREE.Mesh(leafGeo,leafMat);fallen.name='rear-fallen-leaves';
  fallen.userData.ownGeometry=true;fallen.castShadow=true;fallen.receiveShadow=true;
  fallen.onBeforeRender=()=>{litterWeather.leafWet.value=wetF;litterWeather.leafSnow.value=snowF;leafMat.roughness=.95-.25*wetF;};
  yard.add(fallen);
}


// Photo-derived rear planting arrangement. Geometric leaves are roughly one
// inch long; no photographic planes, giant low-poly mounds or shared RNG use.
// Each specimen stays an editable shrub item. Its bark and folded leaf faces
// join props, whose existing material path casts actual directional shadows.
function addRearPlantingDetail(L, leaves, beds, props) {
  const rng = mulberry32(0x504c414e);
  const tone = h => new THREE.Color(h);
  const leafPalette = [0x2d402e, 0x3c5134, 0x465b39, 0x344a31, 0x536342];
  const leafPositions = [], leafColors = [], leafUVs = [];
  // Preserve the pre-refit Outside-editor anchors as the crowns grow outward.
  const specimenPivots = [
    [47.4973239899,.1344256699,-41.2042770386],[-2.0937818289,.1358322799,-38.4869632721],
    [46.1022090912,.1651925743,-30.2025556564],[47.513999939,.1673579514,-23.1960716248],
    [51.0037460327,.1411488354,-15.9901437759],[19.0027084351,.1222221926,-45.3964042664],
    [21.9888420105,.1311081797,-45.213760376],[24.9989175797,.1228073686,-44.909954071],
    [28.0164308548,.1339447647,-43.4938659668],[-4.6885583401,.1226787269,-45.9995193481],
    [3.0034079552,.1160103306,-45.8008804321],
  ];
  let specimenIndex = 0;
  const putTriangle = (a,b,c,color) => {
    for (const p of [a,b,c]) {
      leafPositions.push(p.x,p.y,p.z);
      leafColors.push(color.r,color.g,color.b);
      leafUVs.push(0,0);
    }
  };
  const branch = (a,b,r0,r1) => {
    const d = new THREE.Vector3().subVectors(b,a);
    const g = new THREE.CylinderGeometry(r1,r0,d.length(),8);
    g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize()));
    g.translate(...a.clone().add(b).multiplyScalar(0.5).toArray());
    paint(g,tone(0x4b4538)); props.push(g);
  };
  const spreadingShrub = (x,z,rx,ry,rz,y,tint) => {
    // The rail planting grows as interlocking woody sprays, with actual gaps
    // between leaves. A closed ellipsoid would fill those gaps with smooth paint.
    const random=mulberry32(0x53485242+Math.round(x*101));
    const positions=[],colors=[],uvs=[];
    const height=ry*2.65, spreadX=rx*1.18, spreadZ=rz*1.08;
    const origin=new THREE.Vector3(x,y+.16,z);
    const emit=(a,b,c,color)=>{
      for(const p of [a,b,c]){
        positions.push(p.x,Math.max(y+.18,p.y),Math.min(-42.42,p.z));
        colors.push(color.r,color.g,color.b);uvs.push(0,0);
      }
    };
    const twig=(a,b,r)=>{
      const direction=b.clone().sub(a).normalize();
      const side=new THREE.Vector3().crossVectors(direction,new THREE.Vector3(0,1,0)).normalize().multiplyScalar(r);
      const across=new THREE.Vector3().crossVectors(direction,side).normalize().multiplyScalar(r);
      const color=tone(0x494633);
      emit(a.clone().add(side),a.clone().sub(side),b,color);
      emit(a.clone().add(across),a.clone().sub(across),b,color);
    };
    // Each spray has a different height and reach. Neighbouring shrubs overlap
    // across their existing item boundaries, while each still moves as one item.
    for(let shoot=0;shoot<28;shoot++){
      const angle=shoot*2.399963+random()*.65;
      const reach=.38+.62*Math.sqrt(random());
      const tall=(shoot%6===0?1:shoot%4===1?.32+random()*.25:.60+random()*.32);
      const root=origin.clone().add(new THREE.Vector3((random()-.5)*spreadX*.32,0,(random()-.5)*spreadZ*.25));
      const fork=root.clone().add(new THREE.Vector3(Math.cos(angle)*spreadX*.20,height*.08,Math.sin(angle)*spreadZ*.18));
      const tip=new THREE.Vector3(x+Math.cos(angle)*spreadX*reach,y+height*tall,z+Math.sin(angle)*spreadZ*reach);
      twig(root,fork,.024);twig(fork,tip,.017);
      const palette=tone(shoot%5===0?0x34472f:shoot%4===0?0x748057:tint);
      for(let leaf=0;leaf<31;leaf++){
        const t=.04+.96*random();
        const p=fork.clone().lerp(tip,t);
        const a=angle+leaf*2.399963;
        const reachLeaf=(.16+random()*.32)*Math.sin(t*Math.PI*.84);
        p.add(new THREE.Vector3(Math.cos(a)*reachLeaf,(random()-.5)*.27,Math.sin(a)*reachLeaf));
        if(leaf%7===0)twig(fork.clone().lerp(tip,Math.max(.05,t-.16)),p,.012);
        const axis=new THREE.Vector3(Math.cos(a),.18+random()*.9,Math.sin(a)).normalize();
        const across=new THREE.Vector3(-Math.sin(a),.1*(random()-.5),Math.cos(a)).normalize();
        const length=.14+random()*.12,width=length*(.38+random()*.20);
        const top=p.clone().addScaledVector(axis,length),bottom=p.clone().addScaledVector(axis,-length);
        const left=p.clone().addScaledVector(across,width),right=p.clone().addScaledVector(across,-width);
        left.y-=.025;right.y-=.025;
        const color=palette.clone().multiplyScalar(.70+random()*.48);
        emit(top,left,bottom,color);emit(bottom,right,top,color);
      }
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
    geometry.computeVertexNormals();geometry.userData.rearFoliage=true;
    props.push(geometry);
  };
  const specimen = scoped('shrub','Clipped evergreen', (x,z,rx,ry,rz,y,form='round',tint=null) => {
    items[curItem].authoredPivot=specimenPivots[specimenIndex++];
    if(form==='spreading'){
      spreadingShrub(x,z,rx,ry,rz,y,tint);
      // Keep the shared generator at its previous position, so later accents
      // retain their exact geometry, colouring and authored editor transforms.
      const area=4*Math.PI*Math.pow((Math.pow(rx*ry,1.6075)+Math.pow(rx*rz,1.6075)+Math.pow(ry*rz,1.6075))/3,1/1.6075);
      for(let i=0;i<Math.round(area*56)*6;i++)rng();
      return;
    }
    // Elliptical clipped crowns retain a slightly irregular leaf silhouette,
    // with the bare lower branching visible as in photographs 09 and 10.
    const lift = ry < 1.7 ? 0.12 : form==='upright' ? 0.10 : 1.05;
    const centre = new THREE.Vector3(x,y+ry+lift,z);
    const shapePoint = (nx,ny,nz) => {
      if(form==='upright') {
        const radial=Math.sqrt(nx*nx+nz*nz);
        const side=(0.64+0.30*(ny+1)*0.5)*Math.sqrt(Math.max(0,1-Math.pow(Math.abs(ny),6)));
        const factor=radial>0.0001?side/radial:0;
        return new THREE.Vector3(x+nx*rx*factor,centre.y+ny*ry,z+nz*rz*factor);
      }
      // Clipped mature holly has broad shoulders and a subtly flattened crown,
      // not a geometric ball. Continuous lobes keep the core and leaves aligned.
      const signedPow=v=>Math.sign(v)*Math.pow(Math.abs(v),.88);
      const ripple=1+.018*Math.sin(nx*9+nz*5)+.013*Math.cos(nz*11-ny*7)+.009*Math.sin(ny*17+nx*4);
      return new THREE.Vector3(x+signedPow(nx)*rx*ripple,
        centre.y+signedPow(ny)*ry*(1+.014*Math.sin(nx*8+nz*7)),z+signedPow(nz)*rz*ripple);
    };
    const core = new THREE.SphereGeometry(1,64,40);
    const cp=core.attributes.position;
    for(let i=0;i<cp.count;i++) {
      const nx=cp.getX(i),ny=cp.getY(i),nz=cp.getZ(i);
      const p=shapePoint(nx*.965,ny*.965,nz*.965);
      cp.setXYZ(i,p.x,p.y,p.z);
    }
    core.computeVertexNormals(); paint(core,tone(tint || 0x263829));
    core.userData.rearFoliage=true; props.push(core);
    const stem=new THREE.Vector3(x,y,z);
    for(let j=0;j<5;j++) {
      const angle=j*Math.PI*2/5+.21;
      const start=stem.clone().add(new THREE.Vector3(Math.cos(angle)*.22,0,Math.sin(angle)*.22));
      const fork=new THREE.Vector3(x+Math.cos(angle)*rx*.17,y+lift*.70+ry*.10,z+Math.sin(angle)*rz*.17);
      const tip=new THREE.Vector3(x+Math.cos(angle+.12)*rx*.59,y+lift+ry*.67,z+Math.sin(angle+.12)*rz*.59);
      branch(start,fork,ry>3?.15:.085,.072);branch(fork,tip,.077,.022);
      for(let k=0;k<2;k++) {
        const a=angle+(k?-.42:.46);
        branch(fork.clone().lerp(tip,.33+k*.19),
          new THREE.Vector3(x+Math.cos(a)*rx*.68,y+lift+ry*(.47+k*.26),z+Math.sin(a)*rz*.68),.043,.013);
      }
    }
    leafPositions.length=leafColors.length=leafUVs.length=0;
    const area=4*Math.PI*Math.pow((Math.pow(rx*ry,1.6075)+Math.pow(rx*rz,1.6075)+Math.pow(ry*rz,1.6075))/3,1/1.6075);
    const count=Math.round(area*56);
    const golden=Math.PI*(3-Math.sqrt(5));
    for(let i=0;i<count;i++) {
      const ny=1-2*(i+.5)/count, radius=Math.sqrt(1-ny*ny),a=i*golden;
      const nx=Math.cos(a)*radius,nz=Math.sin(a)*radius;
      const n=new THREE.Vector3(nx/rx,ny/ry,nz/rz).normalize();
      const p=shapePoint(nx,ny,nz).addScaledVector(n,(rng()-.25)*.14);
      const tangent=new THREE.Vector3().crossVectors(n,Math.abs(n.y)>.9?new THREE.Vector3(1,0,0):new THREE.Vector3(0,1,0)).normalize();
      tangent.applyAxisAngle(n,rng()*Math.PI*2);
      const across=new THREE.Vector3().crossVectors(n,tangent).normalize();
      const length=.078+rng()*.067, width=length*(.38+rng()*.15);
      const tip=p.clone().addScaledVector(tangent,length),bottom=p.clone().addScaledVector(tangent,-length);
      const left=p.clone().addScaledVector(across,width),right=p.clone().addScaledVector(across,-width);
      const ridge=p.clone().addScaledVector(n,.010+rng()*.017);
      const color=tone(tint || leafPalette[Math.floor(rng()*leafPalette.length)]).multiplyScalar(.77+rng()*.40);
      putTriangle(tip,left,ridge,color);putTriangle(left,bottom,ridge,color);
      color.multiplyScalar(.84);
      putTriangle(bottom,right,ridge,color);putTriangle(right,tip,ridge,color);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(leafPositions,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(leafColors,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(leafUVs,2));
    g.computeVertexNormals();g.userData.rearFoliage=true;props.push(g);
  });
  // Scalloped river-gravel beds connect the porch planting. The open middle
  // lawn and the north stair landing stay outside these polygons.
  const bedPivots = [
    [[35.3551387787,.1835728735,-30.1528596878],[35.3296627998,.1884338260,-30.1425476074]],
    [[-1.9727630615,.1842523515,-36.0511617661],[-2.0201001167,.1884332448,-36.0553941727]],
  ];
  let bedIndex=0;
  const bed = points => {
    const curve=new THREE.CatmullRomCurve3(points.map(([x,z])=>new THREE.Vector3(x,0,z)),true,'centripetal');
    const outline=curve.getPoints(60).map(p=>[p.x,p.z]);
    const anchors=bedPivots[bedIndex++];
    const bedItem=items.length;
    addBedPoly(rng,outline,L.lo+.075,beds,8,[],.18,true);
    items[bedItem].authoredPivot=anchors[0];
    const edgeItem=items.length;
    addCobbleRun(rng,outline,L.lo+.075,beds,.45);
    items[edgeItem].authoredPivot=anchors[1];
  };
  bed([[15.7,-43.3],[42.5,-43.3],[42.8,-31],[46.8,-22],[46.8,-13.0],
    [54.5,-12.9],[55,-28],[59,-38],[58.5,-45],[51,-49.3],[25,-48.4],[16.5,-47.2]]);
  bed([[-7.8,-25],[-.3,-25],[1.3,-33.8],[2.2,-41.5],[5.0,-44.4],
    [4.4,-47.7],[-3,-48.0],[-11.5,-45.7],[-12.0,-36.5]]);
  // East (left in photo 09) and west mature specimens: the photo's substantial
  // clipped masses rise above the rails. The outward offsets keep every crown
  // clear of the measured deck x3..20.6 / x20.6..42.2 footprints.
  specimen(50.4,-41.2,7.60,5.35,6.74,L.lo);
  specimen(-4.4,-38.5,6.67,4.81,6.05,L.lo);
  // Upright clipped evergreen pair in the east gravel return (photo 08).
  specimen(46.1,-30.2,1.7,2.60,1.55,L.lo,'upright');
  specimen(47.5,-23.2,1.35,2.15,1.35,L.lo,'upright');
  specimen(51.0,-16.0,3.3,2.65,3.0,L.lo);
  // Low spreading hedge under the north deck rail, leaving the stair landing
  // x10.3..14.9 clear. Small leaf-colour variation follows photograph 10.
  for(const [x,z,rx,ry,rz,c] of [
    [19.0,-45.4,2.25,1.25,1.55,0x606449], [22.0,-45.2,2.3,1.50,1.6,0x5a613f],
    [25.0,-44.9,2.4,1.40,1.55,0x687145], [28.0,-43.5,1.8,1.10,1.4,0x3b5636],
  ]) specimen(x,z,rx,ry,rz,L.lo,'spreading',c);
  // Sparse low evergreen accents at the west bed, never scattered across the
  // middle of the lawn. Shore tree/bank planting belongs to the lake builder.
  specimen(-4.7,-46.0,1.4,.58,1.15,L.lo,'round',0x58664b);
  specimen(3.0,-45.8,1.55,.56,1.1,L.lo,'round',0x4e6440);
  addRearLayeredConifer(L, props);
}

// Photos 09 and 04 show this broad, low evergreen behind the west clipped
// crown, toward the fence: image-right when looking south from the rear lawn.
// Its independently seeded scope is appended after all existing planting items.
function addRearLayeredConifer(L, props) {
  scoped('tree','Rear layered evergreen', () => {
    const x=-20.5,z=-29.5,y=L.lo;
    items[curItem].authoredPivot=[x,y,z];
    const rng=mulberry32(0x50494e45),positions=[],colors=[],uvs=[];
    const sprayPositions=[],sprayColors=[],sprayUVs=[];
    const bark=new THREE.Color(0x514b3c);
    const palette=[0x465940,0x526446,0x5c6e49,0x384f39,0x65764d];
    const emit=(a,b,c,color)=>{
      for(const p of [a,b,c]){
        positions.push(p.x,p.y,p.z);colors.push(color.r,color.g,color.b);uvs.push(0,0);
      }
    };
    // Crossed tapered wood facets keep real branch junctions visible between
    // the needle sprays without filling their gaps with a closed canopy mesh.
    const twig=(a,b,r,color=bark)=>{
      const axis=b.clone().sub(a).normalize();
      const side=new THREE.Vector3().crossVectors(axis,new THREE.Vector3(0,1,0));
      if(side.lengthSq()<.001)side.set(1,0,0);
      side.normalize().multiplyScalar(r);
      const across=new THREE.Vector3().crossVectors(axis,side).normalize().multiplyScalar(r);
      emit(a.clone().add(side),a.clone().sub(side),b,color);
      emit(a.clone().add(across),a.clone().sub(across),b,color);
    };
    const root=new THREE.Vector3(x,y+.08,z);
    const fork=new THREE.Vector3(x+.35,y+5.5,z+.18);
    twig(root,fork,.26);
    twig(fork,new THREE.Vector3(x-.7,y+10.3,z+.45),.13);
    twig(fork,new THREE.Vector3(x+1.3,y+11.6,z-.35),.10);
    // Unequal horizontal shelves, widest in the middle. Angular offsets and
    // missing sectors avoid a rotationally symmetric tiered-cone silhouette.
    const shelves=[{h:6.7,r:5.6,n:5,a:.3},{h:8.3,r:8.0,n:7,a:.86},
      {h:9.9,r:6.9,n:6,a:.04},{h:11.4,r:3.8,n:4,a:1.13}];
    for(const [level,shelf] of shelves.entries())for(let b=0;b<shelf.n;b++){
      const angle=shelf.a+b*Math.PI*2/shelf.n+(rng()-.5)*.37;
      const radius=shelf.r*(.79+rng()*.26);
      const dx=Math.cos(angle),dz=Math.sin(angle);
      const start=new THREE.Vector3(x+.25*(level-1),y+shelf.h-.8,z+.14*level);
      const elbow=start.clone().add(new THREE.Vector3(dx*radius*.47,-.35+rng()*.2,dz*radius*.40));
      const tip=start.clone().add(new THREE.Vector3(dx*radius,.12+rng()*.55,dz*radius*.72));
      twig(start,elbow,.085-level*.012);twig(elbow,tip,.045);
      const tone=new THREE.Color(palette[(b+level)%palette.length]);
      for(let shoot=0;shoot<6;shoot++){
        const t=.22+shoot*.135;
        const base=elbow.clone().lerp(tip,t);
        const sign=shoot%2?1:-1;
        const a=angle+sign*(.52+rng()*.43),length=.9+rng()*.64;
        const axis=new THREE.Vector3(Math.cos(a),.17+rng()*.25,Math.sin(a)).normalize();
        const lateral=new THREE.Vector3(-Math.sin(a),.18,Math.cos(a)).normalize();
        const end=base.clone().addScaledVector(axis,length);
        twig(base,end,.018,tone.clone().multiplyScalar(.65));
        // Two fixed crossing surfaces carry hundreds of sub-inch needles per
        // branchlet. They rotate with the actual shoot, never with the camera.
        for(let plane=0;plane<2;plane++){
          const cross=lateral.clone().applyAxisAngle(axis,plane*Math.PI/2+.23*(shoot%3));
          const bottom=base.clone().addScaledVector(axis,-.35);
          const top=end.clone().addScaledVector(axis,.72);
          const w=.82+rng()*.25;
          const corners=[bottom.clone().addScaledVector(cross,-w),bottom.clone().addScaledVector(cross,w),
            top.clone().addScaledVector(cross,w),top.clone().addScaledVector(cross,-w)];
          const tint=.63+rng()*.25,uv=[[0,0],[1,0],[1,1],[0,1]];
          for(const id of [0,1,2,0,2,3]){
            sprayPositions.push(...corners[id].toArray());sprayColors.push(tint,tint,tint);sprayUVs.push(...uv[id]);
          }
        }
        for(let needle=0;needle<4;needle++){
          const along=(needle+.2)/4,centre=base.clone().lerp(end,along);
          const reach=(.44+rng()*.27)*(1-along*.30),width=.075+rng()*.035;
          const color=tone.clone().multiplyScalar(.74+rng()*.43);
          for(const side of [-1,1]){
            const tipNeedle=centre.clone().addScaledVector(axis,reach*.45)
              .addScaledVector(lateral,side*reach);
            tipNeedle.y+=.07+rng()*.16;
            emit(centre.clone().addScaledVector(axis,-width),
              centre.clone().addScaledVector(axis,width),tipNeedle,color);
          }
        }
      }
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));
    geometry.computeVertexNormals();geometry.userData.rearFoliage=true;
    props.push(geometry);
    const sprays=new THREE.BufferGeometry();
    sprays.setAttribute('position',new THREE.Float32BufferAttribute(sprayPositions,3));
    sprays.setAttribute('color',new THREE.Float32BufferAttribute(sprayColors,3));
    sprays.setAttribute('uv',new THREE.Float32BufferAttribute(sprayUVs,2));
    sprays.computeVertexNormals();sprays.userData.rearFoliage=true;sprays.userData.rearConiferSprays=true;
    props.push(sprays);
  })();
}

// Imported site-pad surgery is restricted to the measured triangle signatures
// below. Index offsets address the already prop-masked live Root_Node geometry.
// A changed/re-exported shell fails closed instead of cutting unknown surfaces.
let rearPadPatch = null;
function lowerRearShellPad() {
  const shell = getShellRoot();
  if (!shell || rearPadPatch?.shell === shell) return;
  if (rearPadPatch) restoreRearShellPad();
  shell.updateWorldMatrix(true, true);
  let mesh = null;
  shell.traverse(o => { if(o.isMesh && o.name==='Root_Node' && o.material?.name==='PaletteMaterial001') mesh=o; });
  if(!mesh) return;
  const source=mesh.geometry, index=source.index, attrs=source.attributes;
  if(!index || !attrs.position || source.groups.length) return;
  const candidates=[[84204,[[-7.2841,0.164,-51.0327],[-7.2841,0.164,-6.4039],[-7.2841,2.1338,-51.0327]]],[84207,[[-7.2841,0.164,-6.4039],[-7.2841,2.1338,-6.4039],[-7.2841,2.1338,-51.0327]]],[84210,[[-7.2841,2.1338,-6.4039],[-7.2841,2.1338,13.8205],[24.6015,2.1338,-51.0327]]],[84213,[[-7.2841,2.1338,13.8205],[10.7579,2.1338,26.7393],[24.6015,2.1338,-51.0327]]],[84216,[[24.6015,2.1338,-51.0327],[10.7579,2.1338,26.7393],[20.5973,2.1338,-10.8983]]],[84219,[[10.7579,2.1338,26.7393],[20.5973,2.1338,26.7393],[20.5973,2.1338,-10.8983]]],[84222,[[47.3597,2.1338,-10.8983],[20.5973,2.1338,-10.8983],[47.3597,0.164,-10.8983]]],[84225,[[47.3597,0.164,-10.8983],[20.5973,2.1338,-10.8983],[20.5973,0.164,-10.8983]]],[84252,[[-7.2841,0.164,-51.0327],[-7.2841,2.1338,-51.0327],[24.6015,0.164,-51.0327]]],[84255,[[20.5973,2.1338,-10.8983],[47.3597,2.1338,-10.8983],[24.6015,2.1338,-29.4951]]],[84258,[[47.3597,2.1338,-10.8983],[47.3597,2.1338,-29.4951],[24.6015,2.1338,-29.4951]]],[84261,[[47.3597,2.1338,-10.8983],[47.3597,0.164,-10.8983],[47.3597,0.164,-29.4951]]],[200775,[[47.3597,0.164,-29.4951],[24.6015,0.164,-29.4951],[24.6015,2.1338,-29.4951]]]];
  const point=i=>new THREE.Vector3().fromBufferAttribute(attrs.position,index.getX(i)).applyMatrix4(mesh.matrixWorld);
  for(const [offset, expected] of candidates) {
    if(offset+2>=index.count) return;
    for(let j=0;j<3;j++) if(point(offset+j).distanceTo(new THREE.Vector3(...expected[j]))>0.004) {
      console.warn('Rear pad signature changed; preserving source geometry.'); return;
    }
  }
  const byOffset=new Map(candidates), output=[], additions=[];
  const names=Object.keys(attrs);
  const vertex=i=>({id:i,world:new THREE.Vector3().fromBufferAttribute(attrs.position,i).applyMatrix4(mesh.matrixWorld),
    data:Object.fromEntries(names.map(n=>[n,Array.from({length:attrs[n].itemSize},(_,j)=>attrs[n].array[i*attrs[n].itemSize+j])]))});
  const interpolate=(a,b,t)=>({id:null,world:a.world.clone().lerp(b.world,t),
    data:Object.fromEntries(names.map(n=>[n,a.data[n].map((v,j)=>v+(b.data[n][j]-v)*t)]))});
  const clip=(poly,axis,limit,less)=>{
    const out=[];for(let i=0;i<poly.length;i++) {
      const a=poly[i],b=poly[(i+1)%poly.length],da=a.world[axis]-limit,db=b.world[axis]-limit;
      const ina=less?da<=0:da>=0,inb=less?db<=0:db>=0;
      if(ina)out.push(a);if(ina!==inb)out.push(interpolate(a,b,da/(da-db)));
    }return out;
  };
  const add=v=>{if(v.id!==null)return v.id;v.id=attrs.position.count+additions.length;additions.push(v);return v.id;};
  let changed=0;
  for(let k=0;k<index.count;k+=3) {
    if(!byOffset.has(k)){output.push(index.getX(k),index.getX(k+1),index.getX(k+2));continue;}
    const triangle=[0,1,2].map(j=>vertex(index.getX(k+j)));
    // Split at the rear elevation's step, retain only the south portion of
    // each resulting polygon. Attributes at cut edges interpolate linearly.
    const parts=[clip(clip(triangle,'x',20.5973,true),'z',-24.5107,false),
      clip(clip(triangle,'x',20.5973,false),'z',-10.9445,false)];
    for(const p of parts) for(let j=1;j<p.length-1;j++) {
      if(new THREE.Vector3().subVectors(p[j].world,p[0].world).cross(new THREE.Vector3().subVectors(p[j+1].world,p[0].world)).lengthSq()<1e-14)continue;
      output.push(add(p[0]),add(p[j]),add(p[j+1]));
    }
    changed++;
  }
  const geo=source.clone();
  for(const name of names) {
    const attr=attrs[name],data=new attr.array.constructor((attr.count+additions.length)*attr.itemSize);
    data.set(attr.array);
    const next=new THREE.BufferAttribute(data,attr.itemSize,attr.normalized);
    additions.forEach((v,i)=>v.data[name].forEach((value,j)=>{data[(attr.count+i)*attr.itemSize+j]=value;}));
    geo.setAttribute(name,next);
  }
  geo.setIndex(output);geo.computeBoundingBox();geo.computeBoundingSphere();
  const legacyRemnants=clearMeasuredRearPadRemnants(geo,mesh.matrixWorld);
  mesh.geometry=geo;
  mesh.userData.rearPadCut={sourceTriangles:index.count/3,resultTriangles:geo.index.count/3,candidates:changed,legacyRemnants};
  rearPadPatch={shell,mesh,source,geometry:geo};
}

// Put the shell's original rear pad back. The cut only makes sense under the
// yard's lowered turf; with the yard gone (editor closed) it is a hole in the
// pad. `source` is the model cache's geometry, shared with every other
// instance of the shell, so it is never disposed here -- only our clipped copy.
function restoreRearShellPad() {
  if (!rearPadPatch) return;
  const { mesh, source, geometry } = rearPadPatch;
  if (mesh.geometry === geometry) mesh.geometry = source;
  delete mesh.userData.rearPadCut;
  geometry.dispose();
  rearPadPatch = null;
}

// North elevation finish. The measured backing triangles carry their real
// openings and gable outline into the courses; no other shell face is changed.
// This is additive and deliberately independent of the rear terrain index cut.
export function addRearSidingDetail() {
  if (!yard || yard.getObjectByName('rear-siding-detail')) return;
  const shell=getShellRoot(); if(!shell)return;
  shell.updateWorldMatrix(true,true);
  const group=new THREE.Group();group.name='rear-siding-detail';
  const course=[], trim=[], glass=[];
  const clip=(poly,y,above)=>{
    const out=[];for(let i=0;i<poly.length;i++){
      const a=poly[i],b=poly[(i+1)%poly.length],da=a.y-y,db=b.y-y;
      const ina=above?da>=-1e-8:da<=1e-8,inb=above?db>=-1e-8:db<=1e-8;
      if(ina)out.push(a.clone());if(ina!==inb)out.push(a.clone().lerp(b,da/(da-db)));
    }return out;
  };
  const clipX=(poly,x,above)=>{
    const out=[];for(let i=0;i<poly.length;i++){
      const a=poly[i],b=poly[(i+1)%poly.length],da=a.x-x,db=b.x-x;
      const ina=above?da>=-1e-8:da<=1e-8,inb=above?db>=-1e-8:db<=1e-8;
      if(ina)out.push(a.clone());if(ina!==inb)out.push(a.clone().lerp(b,da/(da-db)));
    }return out;
  };
  const emit=(arr,poly,offset=0)=>{for(let i=1;i<poly.length-1;i++)
    for(const v of [poly[0],poly[i],poly[i+1]])arr.push(v.x,v.y,v.z-offset);};
  const planes=[{z:-24.436689,x0:-7.285,x1:20.598,y0:2.1338,y1:40.595},
    {z:-10.8983,x0:20.596,x1:47.361,y0:2.14,y1:12.963},
    {z:-8.1702,x0:20.596,x1:40.481,y0:14.849,y1:22.914}];
  let backingTriangles=0,trimTriangles=0,glassTriangles=0;
  shell.traverse(mesh=>{
    if(!mesh.isMesh || !['Root_Node','mesh_8'].includes(mesh.name))return;
    const g=mesh.geometry,p=g.attributes.position,idx=g.index,uv=g.attributes.uv;
    if(!p||!uv)return;
    for(let k=0;k<(idx?.count||p.count);k+=3){
      const ids=[0,1,2].map(j=>idx?idx.getX(k+j):k+j);
      const v=ids.map(i=>new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld));
      if(v.some(p=>!Number.isFinite(p.x)))continue;
      const n=v[1].clone().sub(v[0]).cross(v[2].clone().sub(v[0])).normalize();
      const u=uv.getX(ids[0]);
      if(mesh.name==='Root_Node'&&Math.abs(u-.4609375)<.0001&&n.z<-.99999){
        const plane=planes.find(f=>v.every(p=>Math.abs(p.z-f.z)<.0005&&p.x>=f.x0&&p.x<=f.x1));
        if(plane){
          let poly=clip(clip(v,plane.y0,true),plane.y1,false);if(poly.length<3)continue;
          backingTriangles++;
          const lo=Math.min(...poly.map(p=>p.y)),hi=Math.max(...poly.map(p=>p.y)),pitch=.481;
          for(let row=Math.floor((lo-2.134)/pitch);row<=Math.floor((hi-2.134)/pitch);row++){
            const y0=2.134+row*pitch,y1=y0+pitch;
            const strip=clip(clip(poly,y0,true),y1,false);if(strip.length<3)continue;
            // Rounded half-inch vinyl laps: the underside and face are real
            // facets, so their contrast follows the incident daylight.
            const xlo=Math.floor(Math.min(...strip.map(p=>p.x))/4)*4;
            const xhi=Math.max(...strip.map(p=>p.x));
            const sections=[0,.05,.13,.24,.70,.91,1];
            const depths=[.041,.045,.047,.041,.012,.004,0];
            for(let x=xlo;x<xhi;x+=4)for(let b=0;b<sections.length-1;b++){
              const face=clipX(clipX(clip(clip(strip,y0+pitch*sections[b],true),
                y0+pitch*sections[b+1],false),x,true),x+4,false);
              if(face.length<3)continue;
              for(const p of face){
                const t=(p.y-y0)/pitch;
                const blend=(t-sections[b])/(sections[b+1]-sections[b]);
                const profile=THREE.MathUtils.lerp(depths[b],depths[b+1],blend);
                // Small installation tolerances alter the physical lap angle,
                // without putting a repeated dark line into the paint texture.
                const projection=profile*(1+.17*Math.sin(row*1.71)+.09*Math.sin(p.x*.32+row*.67));
                const bow=.009*Math.sin(p.x*.57+row*.41)*Math.sin(Math.PI*t);
                p.z=plane.z-.095-projection-bow;
              }
              emit(course,face);
            }
          }
        }
      }
      // White north-facing window casings, corner faces, gable fascia and
      // the two recessed wing gutters. Side returns and other elevations stay original.
      if(mesh.name==='Root_Node'&&Math.abs(u-.3203125)<.0001&&n.z<-.8){
        const main=v.every(p=>p.z< -24.26&&p.z> -25.45&&p.x> -8.5&&p.x<21.8&&p.y>2.13);
        const wing=v.every(p=>p.x>=20.59&&p.x<=48.02&&((p.z< -10.97&&p.z> -12.51&&p.y>12.3&&p.y<13.15)||(p.z< -7.95&&p.z> -9.8&&p.y>19&&p.y<23)));
        if(main||wing){emit(trim,v,.10);trimTriangles++;}
      }
      // Four main rear sash panes and the small upper wing window only.
      if(mesh.name==='mesh_8'&&n.z<-.999&&v.every(p=>p.y>18.7)&&
        (v.every(p=>p.z< -24.18&&p.z> -24.37)||v.every(p=>p.z< -7.8&&p.z> -8.3))){
        emit(glass,v,.015);glassTriangles++;
      }
    }
  });
  const make=(positions,material,name)=>{
    if(!positions.length){material.dispose();return;}
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.computeVertexNormals();
    const mesh=new THREE.Mesh(geo,material);mesh.name=name;mesh.userData.ownGeometry=true;mesh.receiveShadow=true;mesh.castShadow=true;group.add(mesh);return mesh;
  };
  // Fine chalking and vinyl grain only. Lap shading belongs to the physical
  // profile above; a painted dark stripe made every course uniformly crisp.
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=256;
  const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(512,256),rng=mulberry32(0x53494445);
  for(let y=0;y<256;y++)for(let x=0;x<512;x++){
    const u=x/512,v=y/256;
    // Chalking follows the extruded vinyl grain.
    const chalk=5.5*Math.sin(u*24+v*2)+2.6*Math.sin(u*61-v*4);
    const grain=1.4*Math.sin(u*300+Math.sin(v*19)*.8);
    const tone=Math.round(238+chalk+grain+(rng()-.5)*3),k=(y*512+x)*4;
    pixels.data[k]=pixels.data[k+1]=pixels.data[k+2]=tone;pixels.data[k+3]=255;
  }
  ctx.putImageData(pixels,0,0);const map=new THREE.CanvasTexture(canvas);
  map.wrapS=map.wrapT=THREE.RepeatWrapping;map.anisotropy=8;map.colorSpace=THREE.SRGBColorSpace;
  const sidingMat=new THREE.MeshStandardMaterial({color:0xb9c1c7,map,roughness:.83,metalness:0});
  sidingMat.addEventListener('dispose',()=>map.dispose());
  const siding=make(course,sidingMat,'rear-lapped-vinyl');
  // Sub-inch laps are below the sun shadow map's texel size. Their tilted
  // faces remain legible without subpixel shadow acne;
  // the retained source shell supplies the building's cast shadow.
  if(siding)siding.castShadow=false;
  if(siding){const p=siding.geometry.attributes.position,colors=[],uv=[];
    for(let i=0;i<p.count;i++){const y=p.getY(i),x=p.getX(i),row=Math.floor((y-2.134+.00001)/.481);
      // Course batches age differently, with broad connected chalk tones.
      const age=worldNoise(x+191,y+617,7)-.5;
      const chalk=worldNoise(x+427,y+83,15)-.5;
      const f=.904+Math.sin(row*2.71)*.016+.16*age+.07*chalk;
      colors.push(f,f,f);uv.push(x/12+Math.sin(row*1.73)*.31,(y-2.134)/.481);}
    siding.geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    siding.geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));sidingMat.vertexColors=true;}
  make(trim,new THREE.MeshStandardMaterial({color:0xe5e8e7,roughness:.67}),'rear-white-fascia-casings');
  make(glass,new THREE.MeshStandardMaterial({color:0x263132,roughness:.18,metalness:.18}),'rear-neutral-upper-glazing');
  group.userData.rearSidingMeasurement={backingTriangles,trimTriangles,glassTriangles,planes,courseTriangles:course.length/9};
  addMeasuredRearRoofFinish(shell,group);
  yard.add(group);
}

// The imported roof material is shared with every elevation. Copy only the
// four measured NORTH-facing wing/dormer triangles, preserving the source
// geometry, UVs and material cache. The long lower slope continues under the
// dormer to its real ridge; its z-positive end is still the north roof plane.
function addMeasuredRearRoofFinish(shell,group) {
  const positions=[],uvs=[],sources=[];
  const patches={
    '90809':{offsets:[6,9],min:[20.601,13.045,-12.087],max:[48.017,23.325,9.289]},
    '92051':{offsets:[33,36],min:[20.153,22.942,-9.516],max:[41.234,27.652,.286]},
  };
  shell.traverse(mesh=>{
    const patch=patches[mesh.name];
    if(!mesh.isMesh||!patch||mesh.material?.name!=='Roofing Shingles Asphalt')return;
    const g=mesh.geometry,p=g.attributes.position,idx=g.index;
    for(const offset of patch.offsets){
      if(offset+2>=(idx?.count||p.count))continue;
      const v=[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,idx?idx.getX(offset+j):offset+j).applyMatrix4(mesh.matrixWorld));
      const n=v[1].clone().sub(v[0]).cross(v[2].clone().sub(v[0])).normalize();
      if(n.z>-.43||n.z<-.44||n.y<.90||Math.abs(n.x)>.001||
        !v.every(p=>p.toArray().every((x,i)=>x>=patch.min[i]&&x<=patch.max[i])))continue;
      for(const p of v){
        uvs.push(p.x/12,p.y/(-n.z*8));
        p.addScaledVector(n,.018);positions.push(p.x,p.y,p.z);
      }
      sources.push({mesh:mesh.name,offset,normal:n.toArray()});
    }
  });
  if(!positions.length)return;
  // Mineral granules and low-contrast irregular shingle courses, in feet.
  // This is a material tile, generated independently of the reference photo.
  // Painted ONCE per page (memoCanvas): a million pixels × two worldNoise calls
  // each, from a fixed seed with no inputs, so every rebuild used to repaint
  // the identical tile. The CanvasTexture is still made fresh per build so the
  // dispose listener below keeps its meaning.
  const canvas=memoCanvas('rear-roof-shingles',()=>{
    const size=1024,canvas=document.createElement('canvas');canvas.width=canvas.height=size;
    const ctx=canvas.getContext('2d'),data=ctx.createImageData(size,size),rng=mulberry32(0x524f4f46);
    const rows=18,cols=12,tones=Array.from({length:rows},()=>Array.from({length:cols},()=>rng()));
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){
      const row=Math.floor(y/size*rows),fy=(y/size*rows)%1;
      const shift=(row%2)*.5+.14*Math.sin(row*1.79),u=x/size*cols+shift;
      const col=((Math.floor(u)%cols)+cols)%cols,fx=u-Math.floor(u);
      // Asphalt aggregates vary at several scales, independently of tab joints.
      const mottling=12*(worldNoise(x+74,y+281,51)-.5)+
        8*(worldNoise(x+391,y+71,17)-.5)+4*Math.sin(x*.021+y*.011);
      const granules=(rng()-.5)*27;
      const lap=fy>.90?(fy-.90)/.10*7:0;
      const joint=fx>.980&&fy>.15?3.5:0;
      const tone=70+(tones[row][col]-.5)*21+mottling+granules-lap-joint,k=(y*size+x)*4;
      data.data[k]=tone*.97;data.data[k+1]=tone;data.data[k+2]=tone*1.035;data.data[k+3]=255;
    }
    ctx.putImageData(data,0,0);
    return canvas;
  });
  const map=new THREE.CanvasTexture(canvas);map.wrapS=map.wrapT=THREE.RepeatWrapping;
  map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=8;
  const material=new THREE.MeshStandardMaterial({map,color:0xffffff,roughness:.96,metalness:0,bumpMap:map,bumpScale:.007});
  material.addEventListener('dispose',()=>map.dispose());
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));geometry.computeVertexNormals();
  const roof=new THREE.Mesh(geometry,material);roof.name='rear-cool-asphalt-roof';
  roof.userData.ownGeometry=true;roof.receiveShadow=true;roof.castShadow=false;
  roof.userData.measuredSources=sources;group.userData.rearRoofMeasurement={triangles:positions.length/9,sources};group.add(roof);
}

// Remaining hollow faces of the imported pad's obsolete north stairs and east
// return strip, exposed only when the lawn is lowered. Exact measured vertices
// guard these 24 rear triangles; no generic low-wall or bounding-box deletion.
function clearMeasuredRearPadRemnants(geo, matrixWorld) {
  const signatures=[[67983,[[26.5712,0.5894,-31.4648],[26.5712,0.5894,-50.6443],[26.5712,0.164,-50.6443]]],[67986,[[26.5712,0.164,-50.6443],[26.5712,0.5894,-50.6443],[27.5515,0.164,-50.6443]]],[67989,[[26.5712,0.5894,-50.6443],[27.5515,0.5894,-50.6443],[27.5515,0.164,-50.6443]]],[67992,[[27.5515,0.164,-50.6443],[27.5515,0.5894,-50.6443],[27.5515,0.164,-32.4543]]],[67995,[[27.5515,0.5894,-50.6443],[27.5515,0.5894,-32.4543],[27.5515,0.164,-32.4543]]],[68007,[[26.5712,0.5894,-31.4648],[26.5712,0.164,-50.6443],[26.5712,0.164,-31.4648]]],[68250,[[3.3228,0.5894,-53.9919],[13.9853,0.5894,-53.9919],[3.3228,0.164,-53.9919]]],[68253,[[13.9853,0.5894,-53.9919],[13.9853,0.164,-53.9919],[3.3228,0.164,-53.9919]]],[68262,[[13.9853,0.164,-53.9919],[13.9853,0.5894,-53.9919],[13.9853,0.164,-53.0024]]],[68265,[[13.9853,0.5894,-53.9919],[13.9853,0.5894,-53.0024],[13.9853,0.164,-53.0024]]],[68268,[[13.9853,0.164,-53.0024],[13.9853,0.5894,-53.0024],[3.3228,0.5894,-53.0024]]],[68271,[[3.3228,0.5894,-53.9919],[3.3228,0.164,-53.9919],[3.3228,0.5894,-53.0024]]],[68274,[[3.3228,0.164,-53.9919],[3.3228,0.164,-53.0024],[3.3228,0.5894,-53.0024]]],[68283,[[13.9853,0.164,-53.0024],[13.9853,1.0796,-53.0024],[13.9853,0.164,-52.0222]]],[68286,[[13.9853,1.0796,-53.0024],[13.9853,1.0796,-52.0222],[13.9853,0.164,-52.0222]]],[68289,[[13.9853,0.164,-52.0222],[13.9853,1.0796,-52.0222],[3.3228,1.0796,-52.0222]]],[68292,[[3.3228,1.0796,-53.0024],[3.3228,0.164,-53.0024],[3.3228,1.0796,-52.0222]]],[68295,[[3.3228,0.164,-53.0024],[3.3228,0.164,-52.0222],[3.3228,1.0796,-52.0222]]],[68298,[[13.9853,1.5789,-52.0222],[13.9853,0.164,-52.0222],[3.3228,0.164,-52.0222]]],[68307,[[13.9853,0.164,-52.0222],[13.9853,1.5789,-52.0222],[13.9853,0.164,-51.0327]]],[68310,[[3.3228,0.164,-52.0222],[3.3228,0.164,-51.0327],[3.3228,1.5789,-51.0327]]],[201471,[[13.9853,0.164,-51.0327],[3.3228,1.5789,-51.0327],[3.3228,0.164,-51.0327]]],[201474,[[13.9853,0.164,-52.0222],[3.3228,1.0796,-52.0222],[3.3228,0.164,-52.0222]]],[201477,[[13.9853,0.164,-53.0024],[3.3228,0.5894,-53.0024],[3.3228,0.164,-53.0024]]]], index=geo.index, pos=geo.attributes.position;
  for(const [offset,expected] of signatures) for(let j=0;j<3;j++) {
    if(offset+j>=index.count)return 0;
    const v=new THREE.Vector3().fromBufferAttribute(pos,index.getX(offset+j)).applyMatrix4(matrixWorld);
    if(v.distanceTo(new THREE.Vector3(...expected[j]))>0.004)return 0;
  }
  const skip=new Set(signatures.map(s=>s[0])),keep=[];
  for(let k=0;k<index.count;k+=3)if(!skip.has(k))keep.push(index.getX(k),index.getX(k+1),index.getX(k+2));
  geo.setIndex(keep);return skip.size;
}

// Rear-view atmospheric artwork, deliberately not a global physical sky.
// The closed background-depth field is wholly north of Z=0. Its directional
// gradient and wind-stretched wisps have no image asset, panel border,
// shadow, lighting contribution or renderer-state writes.
// A fragment-level camera gate also makes front/side/interior views unchanged.
function addRearAtmosphereDetail() {
  if (!yard || yard.getObjectByName('rear-atmosphere-detail')) return;
  const group = new THREE.Group(); group.name = 'rear-atmosphere-detail';
  const daylightWhite = new THREE.Color(0xf8fafb);
  const scatterLift = new THREE.Color(2.45,2.9,3.1);
  const clearWeather = {sunny:1,exceptional:1,'clear-night':1,windy:0.9,'windy-variant':0.8,partlycloudy:0.45};
  const vertexShader = `
    varying vec3 vCloudWorld;
    void main() {
      vCloudWorld = (modelMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      // Background depth lets every real surface occlude the private sky.
      gl_Position.z = gl_Position.w * 0.99999;
    }`;
  const fragmentShader = `
    uniform vec3 cloudColor;
    uniform vec3 skyColor;
    uniform float cloudDay;
    uniform float cloudWet;
    varying vec3 vCloudWorld;
    float hashCloud(vec2 p) {
      return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
    }
    float noiseCloud(vec2 p) {
      vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
      return mix(mix(hashCloud(i),hashCloud(i+vec2(1,0)),f.x),
                 mix(hashCloud(i+vec2(0,1)),hashCloud(i+vec2(1,1)),f.x),f.y);
    }
    float fbmCloud(vec2 p) {
      float n=0.0, a=0.5;
      for(int i=0;i<5;i++){n+=a*noiseCloud(p);p=p*2.07+vec2(9.3,4.7);a*=0.5;}
      return n;
    }
    void main() {
      // South/front, primary side elevations and the interior cannot see it.
      float north=-cameraPosition.z;
      if(north<24.5 || abs(cameraPosition.x-16.0)>max(28.0,(north-10.0)*1.4)) discard;
      vec3 ray=normalize(vCloudWorld-cameraPosition);
      // A continuous directional projection has no longitude seam at west.
      vec2 p=vec2(dot(ray.xz,vec2(5.2,3.8))+3.7,ray.y*18.0);
      float curl=fbmCloud(p*0.38);
      vec2 wind=vec2(p.x*0.60-p.y*0.24,(p.y+p.x*0.35)*4.0+curl*3.0);
      float body=fbmCloud(wind);
      float streak=fbmCloud(wind*vec2(0.55,2.8)+vec2(31.1,18.4));
      float banks=smoothstep(0.40,0.68,fbmCloud(p*0.8+vec2(8.0,2.0)));
      float density=smoothstep(0.43,0.73,body)*mix(0.3,1.0,streak)*banks;
      float horizon=pow(1.0-smoothstep(0.0,0.7,max(0.0,ray.y)),2.0);
      vec3 atmosphere=mix(skyColor,cloudColor,horizon*0.58);
      atmosphere=mix(atmosphere,cloudColor,density*0.85);
      float alpha=cloudDay*(1.0-cloudWet)*0.94;
      if(alpha<0.001) discard;
      gl_FragColor=vec4(atmosphere,alpha);
      #include <colorspace_fragment>
    }`;
  const makeField = () => {
    const uniforms = {cloudColor:{value:new THREE.Color()},skyColor:{value:new THREE.Color()},cloudDay:{value:0},
      cloudWet:{value:0}};
    const material = new THREE.ShaderMaterial({uniforms,vertexShader,fragmentShader,
      transparent:true,depthWrite:false,depthTest:true,side:THREE.BackSide,
      toneMapped:false,fog:false});
    const geometry = new THREE.SphereGeometry(300,48,24);
    geometry.translate(16,0,-301);
    const mesh = new THREE.Mesh(geometry,material); mesh.name='rear-atmosphere-dome';
    mesh.renderOrder=-1000;
    mesh.userData.ownGeometry=true;
    mesh.onBeforeRender=()=>{
      const day=1-getNightFactor();
      const daylight=getDaylight();
      const clear=clearWeather[daylight.condition] || 0;
      const highSun=THREE.MathUtils.smoothstep(daylight.elevation,6,26);
      uniforms.cloudDay.value=scene.background?.isColor?day*day*clear*highSun:0;
      uniforms.cloudWet.value=wetF;
      if(scene.background?.isColor) {
        uniforms.cloudColor.value.copy(scene.background).lerp(daylightWhite,0.93*day);
        // The existing HA sky remains the color source; this local directional
        // scattering lift follows it and disappears in overcast/night states.
        uniforms.skyColor.value.copy(scene.background).multiply(scatterLift);
      }
    };
    group.add(mesh);
  };
  // A closed field avoids panel edges from oblique porch and lake views.
  // Every vertex remains north (Z=-601..-1); only its background-depth
  // fragments are drawn, so the field cannot cover any building geometry.
  makeField();
  group.userData.scope='rear-camera-only, north geometry, no global sky changes';
  yard.add(group);
}

let rearLightTimer = null;
// Rear contact occlusion follows the actual deck and clipped crown transforms.
// It attenuates indirect irradiance only; existing modules still own the sun,
// HA light pools, weather and exposure.
export function addRearLightDetail(buckets) {
  if (!yard || yard.userData.rearLightDetail) return;
  const owner = yard;
  // Measure the current foliage instead of retaining obsolete crown sizes.
  // Editor geometry is still authored here; viewer geometry includes edits.
  const centers = [], radii = [], contacts=[];
  for (const item of items) {
    if(item.label!=='Clipped evergreen'||contacts.length>=32)continue;
    const box=new THREE.Box3();
    for(const ref of item.geos){
      const g=buckets?.[ref.bucket]?.geos?.[ref.i];
      if(!g?.userData?.rearFoliage)continue;
      if(!g.boundingBox)g.computeBoundingBox();box.union(g.boundingBox);
    }
    if(box.isEmpty())continue;
    const point=box.getCenter(new THREE.Vector3());point.y=box.min.y;
    const radius=box.getSize(new THREE.Vector3()).multiplyScalar(.5);
    const group=yardEditing?yard.children.find(o=>o.userData.yardKey===item.key):null;
    if(group)point.sub(new THREE.Vector3(...item.pivot));
    contacts.push({item,point,radius,group});
    centers.push(new THREE.Vector4());radii.push(new THREE.Vector4());
  }
  const count=centers.length;
  while(centers.length<32){centers.push(new THREE.Vector4());radii.push(new THREE.Vector4(1,1,1,0));}
  const deckToLocal=new THREE.Matrix4(),deckVisible={value:1};
  const deckGroup=owner.getObjectByName('rear-deck-layout-detail');
  const point=new THREE.Vector3(),scale=new THREE.Vector3();
  const visibleInTree=o=>{for(let n=o;n;n=n.parent)if(!n.visible)return false;return true;};
  const refreshContacts=()=>{
    contacts.forEach((c,i)=>{
      point.copy(c.point);let s=1,angle=0,visible=!c.item.edit?.deleted;
      if(c.group){c.group.updateWorldMatrix(true,false);point.applyMatrix4(c.group.matrixWorld);
        c.group.getWorldScale(scale);s=Math.abs(scale.x);angle=c.group.rotation.y;visible=visibleInTree(c.group);}
      centers[i].set(point.x,point.y,point.z,angle);
      radii[i].set(c.radius.x*s,c.radius.y*s,c.radius.z*s,visible?1:0);
    });
    if(deckGroup){deckGroup.updateWorldMatrix(true,false);deckToLocal.copy(deckGroup.matrixWorld).invert();
      deckVisible.value=visibleInTree(deckGroup)?1:0;}
    else deckVisible.value=0;
  };
  refreshContacts();
  const uniforms={rearContactCenters:{value:centers},rearContactRadii:{value:radii},rearContactCount:{value:count},
    rearDeckToLocal:{value:deckToLocal},rearDeckVisible:deckVisible};
  // Woodland receives the renderer's actual foliage shadows. A spherical
  // canopy AO approximation suppressed the same ambient sky repeatedly and
  // failed matched-camera validation, so no additional turf sky term is used.
  const materials=new Set();
  yard.traverse(mesh=>{
    if(!mesh.isMesh || mesh.userData.rearLake || mesh.name.startsWith('rear-lapped') ||
      mesh.name.startsWith('rear-white') || mesh.name.startsWith('rear-neutral'))return;
    const renderBefore=mesh.onBeforeRender;
    mesh.onBeforeRender=function(...args){refreshContacts();renderBefore.apply(this,args);};
    for(const material of Array.isArray(mesh.material)?mesh.material:[mesh.material]) {
      if(!material.isMeshStandardMaterial || materials.has(material))continue;
      materials.add(material);
      const before=material.onBeforeCompile, cache=material.customProgramCacheKey.bind(material);
      const previousKey=cache();
      material.onBeforeCompile=(shader,renderer)=>{
        before.call(material,shader,renderer); Object.assign(shader.uniforms,uniforms);
        shader.vertexShader='varying vec3 vRearContactWorld;\n'+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>',
          `#include <worldpos_vertex>
vec4 rearContactPosition=vec4(transformed,1.0);
#ifdef USE_BATCHING
  rearContactPosition=batchingMatrix*rearContactPosition;
#endif
#ifdef USE_INSTANCING
  rearContactPosition=instanceMatrix*rearContactPosition;
#endif
vRearContactWorld=(modelMatrix*rearContactPosition).xyz;`);
        shader.fragmentShader=`varying vec3 vRearContactWorld;
uniform vec4 rearContactCenters[32];
uniform vec4 rearContactRadii[32];
uniform int rearContactCount;
uniform mat4 rearDeckToLocal;
uniform float rearDeckVisible;
float rearDeckContact(vec3 p,vec4 box,float top){
  vec2 edge=min(p.xz-box.xy,box.zw-p.xz);
  float coverage=smoothstep(-0.35,1.65,min(edge.x,edge.y));
  return coverage*(1.0-smoothstep(top-0.18,top,p.y));
}
`+shader.fragmentShader;
        shader.fragmentShader=shader.fragmentShader.replace('#include <aomap_fragment>',`#include <aomap_fragment>
// Outside this measured rear region the original shader arithmetic is untouched.
if(vRearContactWorld.z < -0.01 && vRearContactWorld.y < 8.0){
  vec3 p=vRearContactWorld;
  float rearAO=1.0;
  vec3 deckPoint=(rearDeckToLocal*vec4(p,1.0)).xyz;
  float deck=rearDeckVisible*max(rearDeckContact(deckPoint,vec4(3.0,-42.2,20.6,-24.43),2.72),
                 rearDeckContact(deckPoint,vec4(20.6,-42.2,42.2,-10.91),2.40));
  rearAO*=1.0-0.72*deck;
  for(int i=0;i<32;i++){
    if(i>=rearContactCount)break;
    if(rearContactRadii[i].w<0.5)continue;
    vec3 d=p-rearContactCenters[i].xyz;
    float a=rearContactCenters[i].w;
    vec2 local=mat2(cos(a),-sin(a),sin(a),cos(a))*d.xz;
    vec3 r=rearContactRadii[i].xyz;
    float radial=length(local/(r.xz+vec2(0.38)));
    float contact=(1.0-smoothstep(0.15,1.2,radial))*(1.0-smoothstep(0.1,r.y*1.4+0.35,d.y));
    rearAO*=1.0-0.48*contact;
  }
  reflectedLight.indirectDiffuse*=max(0.18,rearAO);
  reflectedLight.indirectSpecular*=max(0.35,rearAO);
}`);
      };
      material.customProgramCacheKey=()=>previousKey+'|rear-contact-v4';
      material.needsUpdate=true;
    }
  });
  owner.userData.rearLightDetail={indirectMaterials:materials.size,crowns:count,deckMeshes:0,
    contacts:{centers,radii,deckToLocal,deckVisible}};
  // Existing placed furniture does not opt into shadows globally. Only this
  // named outdoor deck gets the physical sun response that its boards need.
  if(rearLightTimer)clearTimeout(rearLightTimer);
  const settle=remaining=>{
    rearLightTimer=null;if(yard!==owner)return;
    const deck=[...objects3d.values()].find(o=>o.userData.name==='Backyard Deck'&&o.userData.outdoor);
    if(!deck?.children.length){if(remaining)rearLightTimer=setTimeout(()=>settle(remaining-1),250);return;}
    let meshes=0;deck.traverse(m=>{if(m.isMesh){m.castShadow=true;m.receiveShadow=true;meshes++;}});
    owner.userData.rearLightDetail.deckMeshes=meshes;
  };
  settle(120);
}

