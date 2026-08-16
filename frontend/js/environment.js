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
import { getShellRoot } from './house.js';

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
    const rr = shell ? rectOfRoof(shell) : null;
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

// The BUILDING footprint, as opposed to rectOfShell's whole-lot bounds: this
// shell is one merged mesh per material, so its lot pad, driveway and fences
// all share a bbox with the house and the union above lands on the lot line.
// The roof masses are the exception — they are separate meshes that start a
// storey up, so "elevated and thick" isolates them, and a roof outline is the
// building outline. Used to anchor the foundation beds/driveway props, which
// have to sit against the real walls rather than the lot edge.
function rectOfRoof(shell) {
  shell.updateWorldMatrix(true, true);
  const box = new THREE.Box3();
  const mb = new THREE.Box3();
  shell.traverse((o) => {
    if (!o.isMesh) return;
    mb.setFromObject(o);
    if (mb.min.y >= 8 && mb.max.y - mb.min.y >= 5) box.union(mb);
  });
  if (box.isEmpty()) return null;
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

const ROCK = new THREE.Color(0x8b857b);
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
  const n = Math.round((x1 - x0) * (z1 - z0) / 3.2);
  for (let i = 0; i < n; i++) {
    const r = 0.2 + rng() * 0.28;
    const s = new THREE.IcosahedronGeometry(r, 0);
    s.scale(1, 0.55, 1);
    s.translate(x0 + rng() * (x1 - x0), y + r * 0.2, z0 + rng() * (z1 - z0));
    paint(s, hsl(0.09, 0.07, 0.52 + rng() * 0.22));
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

function addFrontYard(R, rng, leaves, beds, props, lawns) {
  // Landmarks measured off this shell GLB with a downward ray sweep (feet,
  // world space) and written as offsets from the roof rect so they travel with
  // the shell if it is moved or rescaled. Street is +Z, garage on the +X side.
  const driveL = R.x1 - 27.0;   // driveway edges
  const driveR = R.x1 - 2.0;
  const padL = R.x1 - 54.0;   // the shell's pale site pad, left of the driveway
  const padF = R.z1 + 8.6;   // pad's front edge; lawn beyond it
  const porchF = R.z1 + 3.6;   // porch deck front edge
  const stepL = R.x1 - 36.0;   // porch steps down to the walk
  const garageF = R.z1 - 10.9;   // garage front wall

  // 1. Lawn over the site pad. The GLB's ground plane is one pale concrete-ish
  //    slab across the whole lot, so without this the house sits on a huge
  //    apron where the photo has grass. The walk from the porch steps to the
  //    driveway is left uncovered — that part really is concrete.
  lawns.push(slab(padL, R.z1 - 12, stepL - 0.5, padF + 0.5, 0.25));
  lawns.push(slab(stepL - 0.5, padF - 2.0, driveL + 0.4, padF + 0.5, 0.25));

  // 2. Foundation beds: across the front of the porch, up the west wall, and
  //    down the far side of the driveway (all three read in the front photo).
  const bedF0 = porchF + 0.4, bedF1 = porchF + 5.8;
  addBed(rng, R.x0 - 2.0, bedF0, stepL - 1.0, bedF1, 0.34, beds);
  addBed(rng, R.x0 - 3.0, R.z1 - 13, R.x0 + 0.4, bedF0, 0.34, beds);
  addBed(rng, driveR + 0.4, garageF + 2.5, driveR + 8.5, padF + 6, 0.34, beds);
  // small bed at the street end of the driveway, where the lamp post stands
  addBed(rng, driveL - 9, padF + 2, driveL - 0.4, padF + 12, 0.3, beds);

  // 3. Planting: a near-continuous row of clipped shrubs against the siding
  //    with drifts of purple perennials in front of them, as in the photo
  for (let x = R.x0 - 1.4; x < stepL - 1.6; x += 1.9 + rng() * 0.9) {
    addBoxwood(rng, x, bedF0 + 1.5 + rng() * 1.2, 1.15 + rng() * 0.7, 0.34, leaves);
  }
  for (let x = R.x0 + 1.5; x < stepL - 3.0; x += 4.5 + rng() * 3.5) {
    addPerennial(rng, x, bedF1 - 1.4 - rng() * 0.9, 0.34, leaves);
  }
  for (let z = R.z1 - 13; z < bedF0 - 1; z += 2.4 + rng() * 1.2) {
    addBoxwood(rng, R.x0 - 1.5 + rng() * 0.9, z, 1.05 + rng() * 0.6, 0.34, leaves);
  }
  for (let z = garageF + 4; z < padF + 5; z += 3.2 + rng() * 2.0) {
    const x = driveR + 2.4 + rng() * 3.6;
    if (rng() < 0.6) addBoxwood(rng, x, z, 1.15 + rng() * 0.8, 0.34, leaves);
    else addPerennial(rng, x, z, 0.34, leaves);
  }
  for (let i = 0; i < 6; i++) {
    addBoxwood(rng, driveL - 7.5 + rng() * 6.5, padF + 3.5 + rng() * 7, 1.1 + rng() * 0.8, 0.3, leaves);
  }

  // 4. Flagstones stepping through the front bed toward the porch steps
  for (let i = 0; i < 4; i++) {
    const g = boxAt(2.1, 0.14, 1.7, stepL - 3.2 - i * 2.6, 0.36,
                    bedF0 + 1.4 + (i % 2) * 0.7, (rng() - 0.5) * 0.3);
    paint(g, hsl(0.33, 0.05, 0.44 + rng() * 0.07));
    beds.push(g);
  }

  // 5. Vehicles and hardware
  addCar((driveL + driveR) / 2 - 0.6, garageF + 11, props);
  addBin(driveR + 1.4, garageF + 1.6, props);
  addPathLight(driveR + 1.6, garageF + 8, 0.34, props);
  addPathLight(driveR + 2.2, garageF + 16, 0.34, props);
  addPathLight(stepL - 5.5, bedF0 + 0.9, 0.34, props);
  // the black urns standing against the wall where the porch meets the garage
  for (const [ux, uz] of [[driveL + 0.7, porchF - 0.6], [driveL + 1.3, garageF + 1.4]]) {
    const urn = cylAt(0.85, 0.55, 1.25, 10, ux, 0.22, uz);
    paint(urn, _c.setHex(0x24252a)); props.push(urn);
  }

  // 6. Porch: white planters with topiary flanking the steps, bench to the side
  // (its own Color, not the shared _c scratch — addBoxwood below overwrites that)
  const white = new THREE.Color(0xeeece7);
  const deckY = 2.15;
  for (const px of [stepL - 1.6, stepL - 7.5]) {
    const pot = cylAt(0.78, 0.6, 1.5, 10, px, deckY, porchF - 1.5);
    paint(pot, white); props.push(pot);
    addBoxwood(rng, px, porchF - 1.5, 0.72, deckY + 1.4, leaves);
    addBoxwood(rng, px, porchF - 1.5, 0.52, deckY + 2.7, leaves);
  }
  // kept clear of the porch's own left-hand stair, which the shell models
  const bx = stepL - 13.0, bz = porchF - 2.6;
  const bench = [boxAt(4.2, 0.28, 1.6, bx, deckY + 1.25, bz),
                 boxAt(4.2, 1.35, 0.22, bx, deckY + 1.5, bz - 0.7),
                 boxAt(0.28, 1.25, 1.5, bx - 1.95, deckY, bz),
                 boxAt(0.28, 1.25, 1.5, bx + 1.95, deckY, bz)];
  for (const g of bench) { paint(g, white); props.push(g); }

  // 7. Street lamp post in the island bed by the driveway, flanked by the
  //    ornamental grasses (second photo, looking down the drive to the road)
  const lx = driveL - 5.0, lz = padF + 8.5;
  const post = cylAt(0.12, 0.16, 6.2, 8, lx, 0.3, lz);
  paint(post, _c.setHex(0x191a1c)); props.push(post);
  const lamp = boxAt(0.8, 1.1, 0.8, lx, 6.5, lz);
  paint(lamp, _c.setHex(0xd8cda4)); props.push(lamp);
  const cap = cylAt(0.02, 0.62, 0.42, 4, lx, 7.6, lz);
  paint(cap, _c.setHex(0x191a1c)); props.push(cap);
  addGrassClump(rng, lx - 2.2, lz - 1.0, 0.3, leaves);
  addGrassClump(rng, lx + 2.0, lz + 1.2, 0.3, leaves);
  addGrassClump(rng, lx - 0.4, lz + 2.6, 0.3, leaves);
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
  roofRect = shell ? rectOfRoof(shell) : null;
  buildYard();
}

function buildYard() {
  const house = lastHouse;
  // building bbox excludes outdoor pseudo-rooms (Frontyard/Backyard = porch
  // and deck rects) — plants anchor to the building but must dodge every pad
  const OUTDOOR = /yard|patio|deck|outdoor|garden/i;
  let minX = Infinity, minZ = Infinity, maxX = -Infinity, maxZ = -Infinity;
  const pads = []; // every room rect (incl. outdoor) — nothing grows on one
  let garage = null;
  for (const floor of house?.floors || []) {
    for (const room of floor.rooms || []) {
      const fp = room.footprint;
      pads.push({ x0: fp.x, z0: fp.z, x1: fp.x + fp.width, z1: fp.z + fp.depth });
      if (!garage && /garage/i.test(room.name || '')) garage = fp;
      if (OUTDOOR.test(room.name || '')) continue;
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

  // Everything the shell GLB leaves out between the siding and the street:
  // planting beds, the SUV, the bin, porch pieces (see addFrontYard). Anchored
  // to the shell's roof outline, so it only runs when a shell is loaded — the
  // generated-geometry fallback keeps its own bushes above.
  if (roofRect) addFrontYard(roofRect, rng, leaves, beds, props, lawns);

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
    const m = new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(flat(beds), false),
      new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, flatShading: true }));
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
