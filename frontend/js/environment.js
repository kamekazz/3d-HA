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

// Slightly olive and desaturated against the old pure green: the reference
// photo's lawn is a muted summer turf, and the daytime IBL was raised in
// daylight.js (interior wall fix), which lifted this too.
const GRASS_BASE = new THREE.Color(0x53703c);
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

// near-white speckle so grassMat.color tints it (same pattern as textures.js)
function makeGrassTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff';
  g.fillRect(0, 0, 128, 128);
  for (let i = 0; i < 2400; i++) {
    const v = 195 + Math.floor(Math.random() * 60);
    g.fillStyle = `rgb(${v - 12},${v},${v - 18})`;
    g.fillRect(Math.random() * 128, Math.random() * 128, 1.5, 1.5);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(280, 280);
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
    paint(blob, _leaf.setHSL(hue, 0.45 + rng() * 0.16, 0.19 + rng() * 0.09,
                             THREE.SRGBColorSpace));
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
    paint(cone, _leaf);
    leaves.push(cone);
    y += tierH * 0.62;
  }
}

function addBush(rng, x, z, leaves) {
  const r = 1.1 + rng() * 1.2;
  const bush = new THREE.IcosahedronGeometry(r, 1);
  bush.scale(1, 0.65, 1);
  bush.translate(x, r * 0.45, z);
  paint(bush, _leaf.setHSL(0.3 + rng() * 0.06, 0.46, 0.18 + rng() * 0.07,
                           THREE.SRGBColorSpace));
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
const ROCK = new THREE.Color(0x76777b);
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

// A rock-mulch bed: gravel plane, a thin edge strip, and cobbles scattered
// over the whole bed — in the photo the rock reads the same brightness as the
// concrete, so it is the lumpiness, not the tone, that tells them apart.
function addBed(rng, x0, z0, x1, z1, y, beds) {
  const g = slab(x0, z0, x1, z1, y, Math.max(2, Math.round((x1 - x0) / 2)),
                 Math.max(2, Math.round((z1 - z0) / 2)));
  speckle(g, ROCK, rng, 0.5);
  beds.push(g);
  const edge = boxAt(x1 - x0, 0.16, 0.4, (x0 + x1) / 2, y - 0.06, z1 - 0.2);
  paint(edge, _c.setHex(0x3c3b34));
  beds.push(edge);
  // one cobble per 2 sq ft, not per 3.2: the photographed rock meters
  // mean|d1| 15.8 and sd 46.9, i.e. a dense field of individually lit
  // stones, and a sparse scatter over a flat plane cannot reach either.
  const n = Math.round((x1 - x0) * (z1 - z0) / 2.0);
  for (let i = 0; i < n; i++) {
    const r = 0.2 + rng() * 0.28;
    const s = new THREE.IcosahedronGeometry(r, 0);
    s.scale(1, 0.55, 1);
    s.translate(x0 + rng() * (x1 - x0), y + r * 0.2, z0 + rng() * (z1 - z0));
    paint(s, hsl(0.09, 0.06, 0.22 + rng() * 0.42));
    beds.push(s);
  }
}

// clipped boxwood — rounder and more uniform than addBush's wild shrubs
function addBoxwood(rng, x, z, r, y, leaves) {
  const g = new THREE.IcosahedronGeometry(r, 1);
  g.scale(1, 0.92, 1);
  g.translate(x, y + r * 0.82, z);
  paint(g, hsl(0.30, 0.45, 0.27 + rng() * 0.06));
  leaves.push(g);
}

// mound of purple flowering perennials (the salvia/catmint drifts in the photo)
function addPerennial(rng, x, z, y, leaves) {
  for (let i = 0; i < 3; i++) {
    const r = 0.38 + rng() * 0.24;
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(1.15, 0.8, 1.05);
    g.translate(x + (rng() - 0.5) * 1.6, y + r * 0.55, z + (rng() - 0.5) * 1.3);
    paint(g, hsl(0.74, 0.48, 0.42 + rng() * 0.08));
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
    paint(g, _c);
    leaves.push(g);
  }
}

// Big clipped mound — the standalone specimen shrubs standing free on the back
// lawn in Backyard v3 5/7: near-hemispherical, 4-9 ft across, one of them the
// red-purple photinia beside the deck. Much larger and rounder than addBush.
function addMound(rng, x, z, r, y, hue, leaves) {
  const g = new THREE.IcosahedronGeometry(r, 2);
  g.scale(1.05, 0.72, 1.0);
  g.translate(x, y + r * 0.60, z);
  paint(g, hue === 'red'
    ? hsl(0.98, 0.30, 0.24 + rng() * 0.05)     // photinia / loropetalum
    : hsl(0.29 + rng() * 0.05, 0.42, 0.20 + rng() * 0.05));
  leaves.push(g);
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
    paint(blob, _leaf.setHSL(hue, 0.42 + rng() * 0.14, 0.15 + rng() * 0.07,
                             THREE.SRGBColorSpace));
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

// Neighbouring house, as pure massing. Both the front and the back photographs
// have one in frame on each side — without them the house stands in an empty
// field, which is the loudest thing wrong with the whole-house view. Kept
// deliberately plain and slightly desaturated: it must read as background.
function addNeighbour(x, z, w, d, h, ry, doors, props) {
  const wall = hsl(0.10, 0.04, 0.86);
  const roof = hsl(0.08, 0.03, 0.54);
  const push = (g, c) => { paint(g, c); props.push(g); };
  push(boxAt(w, h, d, x, 0, z, ry), wall);
  // gable prism sitting on the walls, ridge along the local X axis
  const rise = 5.5;
  const pr = new THREE.BufferGeometry();
  const hw = w / 2 + 0.7, hd = d / 2 + 0.7;
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
  pr.rotateY(ry); pr.translate(x, h, z);
  push(pr, roof);
  const dd = d / 2 + 0.15, cr = Math.cos(ry), sr = Math.sin(ry);
  for (let i = 0; i < doors; i++) {
    const off = (i - (doors - 1) / 2) * 9.5;
    push(boxAt(8.4, 7.2, 0.4, x + off * cr + dd * sr, 0.2,
               z - off * sr + dd * cr, ry), hsl(0.10, 0.02, 0.86));
  }
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
  //     4 ft PAST the pad's own front edge: anything short of it leaves a
  //     white sliver of the GLB's slab reading as a kerb across the lawn.
  g(L.padW - 2, L.padF, L.driveL + 0.2, L.apronF + 4, L.lo);
  g(L.driveR - 0.2, L.houseF - 1, L.padE + 2, L.apronF + 4, L.lo);
  g(L.porchE, L.houseF, L.driveL, L.padF, L.hi);
  lawns.push(quadAt([L.padW, L.hi, L.padF], [L.driveL, L.hi, L.padF],
                    [L.driveL, L.lo, L.padF + 2.2], [L.padW, L.lo, L.padF + 2.2]));
}

function addFrontYard(L, rng, leaves, beds, props, lawns, trunks) {
  // 1. Driveway and the walk to the porch steps, scored with control joints.
  //    ("Front of the house.jpg": one longitudinal joint down the middle and
  //    transverse ones roughly every 12 ft.)
  const joints = [];
  for (let z = L.houseF + 12; z < L.street; z += 12.5) {
    joints.push([L.driveL, z, L.driveR - L.driveL, 0.16]);
  }
  joints.push([(L.driveL + L.driveR) / 2 - 0.08, L.houseF, 0.16, L.street - L.houseF]);
  addConcrete(L.driveL, L.houseF, L.driveR, L.street, L.lo + 0.02, joints, beds);
  addConcrete(L.stepW - 0.6, L.padF + 0.4, L.driveL + 0.2, L.stepF + 1.6,
              L.lo + 0.03, [], beds);

  // 2. The slate retaining course. The shell pad's front face is a bare 2 ft
  //    white cliff running the width of the house; in the photographs it is a
  //    dry-stacked thin-slab stone wall, which is also what holds the front
  //    bed up. The same wall turns the west corner.
  addSlate(rng, 'x', L.houseW - 1.2, L.stepW - 0.9, L.padF + 0.1, L.lo, L.hi + 0.1, beds);
  addSlate(rng, 'z', L.wingN + 6, L.padF, L.houseW - 1.1, L.lo, L.hi + 0.1, beds);

  // 3. Front bed: river rock at the foot of the slate, clipped boxwood in a
  //    near-continuous row with drifts of purple perennials in front, and
  //    flagstones stepping through it from the drive up to the porch steps.
  const bedF0 = L.padF + 0.5, bedF1 = L.padF + 6.4;
  addBed(rng, L.houseW - 1.4, bedF0, L.stepW - 0.8, bedF1, L.lo + 0.05, beds);
  for (let x = L.houseW - 0.6; x < L.stepW - 1.4; x += 1.9 + rng() * 0.9) {
    addBoxwood(rng, x, bedF0 + 1.5 + rng() * 1.1, 1.15 + rng() * 0.7, L.lo + 0.05, leaves);
  }
  for (let x = L.houseW + 1.5; x < L.stepW - 2.6; x += 4.2 + rng() * 3.0) {
    addPerennial(rng, x, bedF1 - 1.5 - rng() * 0.9, L.lo + 0.05, leaves);
  }
  addFlagstones(rng, [[L.stepW - 2.2, bedF1 - 0.7], [L.stepW - 3.4, bedF1 - 2.1],
                      [L.stepW - 2.0, bedF1 - 3.4], [L.stepW - 3.2, bedF1 - 4.7]],
                L.lo + 0.06, beds);

  // 4. Bed east of the driveway, at the property line: rock, purple drifts and
  //    a pair of squat path lights (second and third front photos).
  addBed(rng, L.driveR + 0.6, L.houseF + 4, L.driveR + 9.5, L.apronF + 6, L.lo + 0.04, beds);
  for (let z = L.houseF + 6; z < L.apronF + 4; z += 3.2 + rng() * 2.0) {
    const x = L.driveR + 2.4 + rng() * 4.4;
    if (rng() < 0.55) addBoxwood(rng, x, z, 1.15 + rng() * 0.8, L.lo + 0.04, leaves);
    else addPerennial(rng, x, z, L.lo + 0.04, leaves);
  }
  addPathLight(L.driveR + 1.4, L.houseF + 9, L.lo + 0.04, props);
  addPathLight(L.driveR + 2.0, L.houseF + 19, L.lo + 0.04, props);
  addPathLight(L.stepW - 5.0, bedF1 - 0.8, L.lo + 0.05, props);

  // 5. Island bed at the street end of the drive, with the lamp post
  addBed(rng, L.driveL - 10, L.apronF + 2.5, L.driveL - 0.6, L.apronF + 13, L.lo + 0.03, beds);
  for (let i = 0; i < 6; i++) {
    addBoxwood(rng, L.driveL - 8 + rng() * 6.5, L.apronF + 4 + rng() * 7.5,
               1.1 + rng() * 0.8, L.lo + 0.03, leaves);
  }
  const lx = L.driveL - 5.2, lz = L.apronF + 9.0;
  const post = cylAt(0.12, 0.16, 6.2, 8, lx, L.lo, lz);
  paint(post, _c.setHex(0x191a1c)); props.push(post);
  const lamp = boxAt(0.8, 1.1, 0.8, lx, L.lo + 6.2, lz);
  paint(lamp, _c.setHex(0xd8cda4)); props.push(lamp);
  const lcap = cylAt(0.02, 0.62, 0.42, 4, lx, L.lo + 7.3, lz);
  paint(lcap, _c.setHex(0x191a1c)); props.push(lcap);
  addGrassClump(rng, lx - 2.2, lz - 1.0, L.lo, leaves);
  addGrassClump(rng, lx + 2.0, lz + 1.2, L.lo, leaves);
  addGrassClump(rng, lx - 0.4, lz + 2.6, L.lo, leaves);

  // 6. Vehicles and hardware. The bin is BLUE with a black lid - the v3 front
  //    shots were taken at dusk and it reads black there, but "Side of the
  //    house.jpg" shows it in daylight against the garage flank.
  addCar((L.driveL + L.driveR) / 2 - 1.4, L.houseF + 13, props);
  addBin(L.driveR - 1.4, L.houseF + 1.9, props);
  // black urns standing against the wall where the porch meets the garage
  for (const [ux, uz] of [[L.porchE + 0.9, L.houseF + 1.4], [L.driveL + 1.1, L.houseF + 1.4]]) {
    const urn = cylAt(0.85, 0.55, 1.25, 10, ux, L.lo, uz);
    paint(urn, _c.setHex(0x24252a)); props.push(urn);
  }

  // 7. Framing trees. The front photograph is framed top-left and top-right by
  //    mature canopies overhanging the drive; without them the house reads as
  //    standing in an open field.
  // This one also stands over the Sketchup scale FIGURE baked into the shell's
  // merged Root_Node mesh at x -16.5, z 44.7 — it cannot be hidden separately.
  addShadeTree(rng, L.driveL - 37, L.apronF - 5.6, 1.8, trunks, leaves);
  addShadeTree(rng, L.driveR + 22, L.apronF + 2, 1.35, trunks, leaves);
  addShadeTree(rng, L.driveR + 26, L.houseF + 4, 1.2, trunks, leaves);

  // 8. The neighbouring house at the west, two garage doors facing the street
  addNeighbour(L.driveL - 78, L.houseF + 7, 26, 30, 18, 0, 2, beds);

  // 9. Woodland across the far side of the street. Both yards' fly-to poses
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
function addBackYard(L, rng, leaves, beds, props, lawns, trunks) {
  const yN = L.padN;            // where the raised lawn ends
  // The deck (a placed object on room 3) occupies world x 2.7..29.9,
  // z -44.5..-24.3. Nothing below may grow inside it.
  // 1. Rock beds edging the lawn. NARROW: the photographs are lawn-dominated
  //    with the rock confined to a border at the foot of the treeline and one
  //    wider apron beside the deck steps.
  addBed(rng, L.padW - 2, yN - 6.5, L.padE + 2, yN - 1.5, L.lo + 0.04, beds);
  addBed(rng, L.padW - 1.5, -46, L.padW + 3.0, L.wingN - 6, L.hi + 0.04, beds);
  addBed(rng, L.padE - 7.5, -47, L.padE + 2, -28, L.lo + 0.04, beds);
  // stepping stones running away from the deck's east flight, as in the aerial
  addFlagstones(rng, [[L.padE - 5.5, -33], [L.padE - 4.4, -35.4], [L.padE - 5.4, -37.8],
                      [L.padE - 4.2, -40.2], [L.padE - 5.3, -42.6]], L.lo + 0.06, beds);

  // 2. The big clipped mounds standing free on the lawn. Dark green ones across
  //    the middle of the lawn and the red-purple one beside the deck steps.
  addMound(rng, L.padW + 3.5, L.blockN - 6, 4.2, L.hi, 'green', leaves);
  addMound(rng, L.padW + 2, L.blockN - 22, 3.4, L.hi, 'green', leaves);
  addMound(rng, L.padW + 13, -50, 3.8, L.hi, 'green', leaves);
  // The big red-purple photinia beyond the deck rail (v3 9). Sized and sited
  // to also swallow the shell GLB's leftover parasol RIBS: hiding the
  // terrace lounge set takes its canopy with it, but the frame is merged
  // into mesh_11 along with the siding and the boundary fence and cannot be
  // hidden separately, so it was left standing as bare white spokes.
  addMound(rng, L.padE - 11.5, -36.5, 6.0, L.lo, 'red', leaves);
  addMound(rng, L.lowE + 9, -25, 3.0, L.hi, 'green', leaves);
  addMound(rng, L.padE - 4, -45, 3.2, L.lo, 'green', leaves);
  addMound(rng, L.padE - 8, -39, 4.8, L.lo, 'green', leaves);
  addMound(rng, L.padE - 14, -41.5, 4.2, L.lo, 'green', leaves);

  // 3. Ornamental grasses and low shrubs along the bed edges
  for (let x = L.padW; x < L.padE; x += 5 + rng() * 5) {
    addGrassClump(rng, x, yN - 4.5 + (rng() - 0.5) * 3, L.lo + 0.04, leaves);
  }
  for (let z = -46; z < L.wingN - 7; z += 5 + rng() * 4) {
    if (rng() < 0.6) addGrassClump(rng, L.padW + 0.8 + rng() * 1.6, z, L.hi + 0.04, leaves);
    else addBoxwood(rng, L.padW + 1.0 + rng() * 1.6, z, 1.3 + rng() * 0.7, L.hi + 0.04, leaves);
  }
  for (let z = -46; z < -29; z += 4 + rng() * 3) {
    addGrassClump(rng, L.padE - 1.2 - rng() * 4, z, L.lo + 0.04, leaves);
  }

  // 4. Dense mature treeline round the boundary - the back photographs are
  //    closed off by woodland on all three sides, well above roof height.
  //    Planted ON the lot lines (past the site pad's own edges), not just
  //    outside the lawn: the app's exterior fly-to for this yard stands the
  //    camera at (-18.5, -77.9), and a treeline hugging the lawn edge put a
  //    30 ft canopy over the lens.
  for (let x = L.padW - 22; x < L.padE + 26; x += 8 + rng() * 5) {
    addShadeTree(rng, x + (rng() - 0.5) * 4, L.yardN - 7 - rng() * 14,
                 1.0 + rng() * 0.5, trunks, leaves);
  }
  for (let z = L.yardN + 2; z < L.wingN - 4; z += 9 + rng() * 6) {
    addShadeTree(rng, L.padW - 24 - rng() * 10, z, 0.95 + rng() * 0.5, trunks, leaves);
  }
  for (let z = L.yardN + 4; z < -22; z += 10 + rng() * 6) {
    addShadeTree(rng, L.padE + 16 + rng() * 10, z, 0.9 + rng() * 0.5, trunks, leaves);
  }

  // 4b. Understory. Without it the treeline is bare trunks over open lawn and
  //     the boundary reads as a park; every back photograph has a dense mass of
  //     shrub and small tree under the canopy right down to the grass.
  for (let x = L.padW - 22; x < L.padE + 24; x += 4 + rng() * 4) {
    addMound(rng, x + (rng() - 0.5) * 3, L.yardN - 4 - rng() * 9,
             3.0 + rng() * 2.4, L.lo, rng() < 0.12 ? 'red' : 'green', leaves);
  }
  for (let z = L.yardN + 4; z < L.wingN; z += 5 + rng() * 4) {
    addMound(rng, L.padW - 12 - rng() * 8, z, 2.8 + rng() * 2.2,
             L.hi, 'green', leaves);
    addMound(rng, L.padE + 10 + rng() * 8, z, 2.8 + rng() * 2.2,
             L.lo, 'green', leaves);
  }

  // 5. A neighbouring house each side, as in "Backyard v3 7"
  addNeighbour(L.padW - 46, L.blockN - 14, 26, 28, 17, 0, 0, beds);
  addNeighbour(L.padE + 40, L.blockN - 18, 26, 28, 17, 0, 0, beds);
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
// siding, roof, fence or terrain — the terrace slab itself, the fence and the
// rear elevation all stay. Set HIDE_TERRACE_PROPS to null to restore them.
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
  const trunks = [], leaves = [], beds = [], props = [], lawns = [];
  const onPad = (x, z, m = 3) =>
    pads.some((p) => x > p.x0 - m && x < p.x1 + m && z > p.z0 - m && z < p.z1 + m);
  // frontmost pad edge at this x — puts foundation beds in front of the porch
  const frontZ = (x) => pads.reduce(
    (m, p) => (x >= p.x0 && x <= p.x1 ? Math.max(m, p.z1) : m), -Infinity);
  const tree = (x, z, s) => {
    if (onPad(x, z, 4)) return;
    (rng() < 0.28 ? addConifer : addDeciduous)(rng, x, z, s, trunks, leaves);
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

  // shrub clusters flanking the driveway entrance near the street
  const dLeft = garage ? garage.x : center.x - 8;
  const dRight = garage ? garage.x + garage.width : center.x + 8;
  for (let i = 0; i < 4; i++) {
    addBush(rng, dLeft - 6 - rng() * 7, bz1 + 12 + rng() * 10, leaves);
  }
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
    addFrontYard(L, rng, leaves, beds, props, lawns, trunks);
    addBackYard(L, rng, leaves, beds, props, lawns, trunks);
    hideShellPatioProps();
  }

  // mergeGeometries refuses to mix indexed (cylinder/cone) with non-indexed
  // (icosahedron) geometry — normalize everything to non-indexed first
  const flat = (geos) => geos.map((g) => (g.index ? g.toNonIndexed() : g));
  if (lawns.length) {
    // own material (not grassMat) because the yard disposes its materials on
    // rebuild; registered so weather.js's wet/snow tint still reaches it
    const mat = new THREE.MeshStandardMaterial({
      color: grassMat.color.clone(), map: grassMat.map, roughness: 1 });
    yardGrassMats.push(mat);
    const geo = BufferGeometryUtils.mergeGeometries(flat(lawns), false);
    // re-derive UVs from world position exactly as the 1200-radius grass disc
    // does, so the shared speckle map keeps the same scale across the seam
    const pos = geo.attributes.position, uv = geo.attributes.uv;
    for (let i = 0; i < pos.count; i++) {
      uv.setXY(i, pos.getX(i) / 2400 + 0.5, -pos.getZ(i) / 2400 + 0.5);
    }
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
