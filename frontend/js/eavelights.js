// The house at night, as the street sees it: permanent warm-white LED strings
// along every roofline, the landscape uplights in the beds, and the one
// upstairs window that is always lit. Bar: demo/exterior_night.jpg.
//
// Everything here is night-only and House-mode-only. The emissive geometry
// (LED dots, their halos, the siding wash, the lit window) is parented to the
// shell GLB's group, so it follows the shell's transform and hides with it in
// the floor views; the handful of real lights live at the scene root, because
// a light under an invisible parent drops out of the frame's light list and
// `lights.point.length` is in three's program cache key -- so hiding them would
// recompile every MeshStandardMaterial on every level switch (see the pool
// comment in roomlights.js). They are created once, in initEaveLights (before
// renderer.compileAsync), and only ever driven by intensity.
//
// No bloom pass exists, so the LEDs are a two-layer fake: a small unlit sphere
// per LED (the fixture, visible by day) under a screen-space halo (THREE.Points
// with a soft radial sprite, additive, clamped to a sane pixel size so flying
// up close does not turn them into beach balls). The wash the LEDs throw down
// the siding is additive vertex-alpha strips hung under each edge -- a strip of
// 300 real point lights is out of the question, and RectAreaLights cost ~30x a
// point light per fragment for every material in the scene, all day, even at
// intensity 0. Real lights are spent only where a flat strip cannot fake it:
// the porch ceiling and columns (3 points), the blue landscape uplight on the
// west treeline (1 spot) and the amber bed uplights (3 points).
//
// Roof edges are MEASURED off the loaded shell's roof meshes (92051 = main
// house + porch, 90809 = garage, 44 + 4 triangles: scratchpad/night/rooftris.py
// dumps them in world feet) and the wall planes off horizontal raycast sweeps
// (wallscan.py / eastscan.py). They are recorded in world feet under the shell
// transform they were measured at (MEASURED_SHELL) and converted to shell-local
// space at build time, so a later shell move in the panel carries them along.
import * as THREE from 'three';
import { scene, camera, renderer, onFrame } from './scene.js';
import { getShellRoot } from './house.js';
import { getNightFactor } from './daylight.js';

// The shell config the numbers below were read under (GET /api/house
// house_shell, 2026-09-02). Only x is non-identity here.
const MEASURED_SHELL = { x: 20.96, y: 0, z: 0, rot_y: 0, scale: 1 };

const LED_SPACING = 1.75;     // ft between LEDs -- counted off the photo's porch run
const LED_DROP = 0.3;         // LEDs hang this far below the roof edge
const LED_OUT = 0.25;         // and this far proud of the fascia face
const LED_COLOR = new THREE.Color(0xffc58f);   // ~2700K amber-white, like the photo's bulbs
const AMBER = new THREE.Color(0xffa040);
const HALO_SIZE = 0.7;        // ft; screen size clamped in the shader
const AMBER_HALO = 0.3;       // the bed fixtures are smaller lamps
const WASH_COLOR = [1.0, 0.56, 0.30];          // linear rgb of the siding wash (~3000K)
const CLAPBOARD = 5 / 12;                      // ft; the siding course spacing
const GLASS_NIGHT = new THREE.Color(0x0c0c0e);  // unlit window glass after dark

// ----------------------------------------------------------- roof edge runs
// [x, y, z] polylines along the roof edges the LEDs follow, plus the offset
// direction (unit-ish, ft) that pushes the dots off the fascia. `dedupe`
// against the previous run's last point keeps one dot at a shared corner.
const RUNS = [
  // front gable (the small one, front face z 30.695): up the left rake, down the right
  { pts: [[-8.202, 26.322, 30.695], [1.736, 36.431, 30.695], [11.674, 26.322, 30.695]],
    out: [0, -LED_DROP, LED_OUT] },
  // main gable front face (z 27.887). Its left rake is coplanar with the front
  // gable's left rake up to that gable's apex (same eave, same 45 degree
  // pitch), so it starts where it emerges above the small gable.
  { pts: [[2.3, 37.005, 27.887], [6.656, 41.437, 27.887], [21.519, 26.322, 27.887]],
    out: [0, -LED_DROP, LED_OUT] },
  // main roof side eaves, front corner to back corner
  { pts: [[21.519, 26.322, 27.887], [21.519, 26.322, -25.426]], out: [LED_OUT, -LED_DROP, 0] },
  { pts: [[-8.198, 26.322, 27.887], [-8.198, 26.322, -25.426]], out: [-LED_OUT, -LED_DROP, 0] },
  // main gable, back face
  { pts: [[-8.198, 26.322, -25.426], [6.656, 41.437, -25.426], [21.519, 26.322, -25.426]],
    out: [0, -LED_DROP, -LED_OUT] },
  // porch roof: west sloped edge down to the front corner, then the fascia
  { pts: [[-7.615, 16.302, 29.55], [-7.615, 12.959, 41.359], [20.928, 12.959, 41.359]],
    out: [0, -LED_DROP, LED_OUT], outFirst: [-LED_OUT, -LED_DROP, 0] },
  // garage: front eave, up and over the east gable end, back eave
  { pts: [[20.602, 13.046, 30.66], [48.016, 13.046, 30.66]], out: [0, -LED_DROP, LED_OUT] },
  { pts: [[48.016, 13.046, 30.66], [48.016, 23.324, 9.288], [48.016, 13.046, -12.086]],
    out: [LED_OUT, -LED_DROP, 0] },
  { pts: [[48.016, 13.046, -12.086], [20.602, 13.046, -12.086]], out: [0, -LED_DROP, -LED_OUT] },
];

// ----------------------------------------------------------- siding wash
// A strip hung under an edge: from a->b along the edge, `down` is the in-face
// direction the light falls off along, `width` how far it reaches, `clampY`
// keeps a gable strip from spilling past the pediment onto the wall below.
// Planes sit ~0.1 ft proud of the surface they wash (rake trims stand ~1 ft in
// front of the gable fields, so a gable strip sits in front of the trim).
const R2 = Math.SQRT1_2;
const WASHES = [
  // ---- walls. Lit siding: a bright band in the first foot under the bulbs,
  // then a cubic decay, scalloped into a pool under each bulb and cut by the
  // clapboard shadow lines (the shader does all of that -- see makeWashMaterial).
  // front gable rakes (field z 29.6, rake trim z 30.53)
  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 5.5, alpha: 0.68, clampY: 24.2, clap: true },
  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 5.5, alpha: 0.68, clampY: 24.2, clap: true },
  // main gable rakes (field z 26.9, trim z 27.7)
  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 5.5, alpha: 0.5, clap: true },
  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 5.5, alpha: 0.5, clampY: 23.8, clap: true },
  // the second-floor walls above the porch roof: a faint lift, no pools
  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 2, alpha: 0.1, scallop: false, clap: true },
  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 2, alpha: 0.1, scallop: false, clap: true },
  // garage front wall (z 29.8) under its eave
  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 6, alpha: 0.75, clap: true },
  // east wall of the main house (x 20.6-20.9) under the side eave
  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 5, alpha: 0.6, clap: true },
  // the porch fascia board itself, lit by its own string
  { a: [-7.6, 12.95, 41.42], b: [20.9, 12.95, 41.42], down: [0, -1, 0], width: 0.55, alpha: 0.5 },
  // ---- soffits: the underside of every overhang, lit from the bulbs hanging
  // just below it -- the "lit interior" of the gables. Strips run inward from
  // the fascia edge, a hair under the roof sheet, and pool under each bulb.
  { a: [-8.2, 26.27, 30.7], b: [1.74, 36.38, 30.7], down: [0, 0, -1], width: 1.1, alpha: 0.9, soffit: true },
  { a: [1.74, 36.38, 30.7], b: [11.67, 26.27, 30.7], down: [0, 0, -1], width: 1.1, alpha: 0.9, soffit: true },
  { a: [2.3, 36.95, 27.9], b: [6.656, 41.39, 27.9], down: [0, 0, -1], width: 1.0, alpha: 0.8, soffit: true },
  { a: [6.656, 41.39, 27.9], b: [21.519, 26.27, 27.9], down: [0, 0, -1], width: 1.0, alpha: 0.8, soffit: true },
  { a: [20.6, 13.0, 30.68], b: [48.0, 13.0, 30.68], down: [0, 0, -1], width: 0.9, alpha: 0.9, soffit: true },
  { a: [21.55, 26.27, 27.9], b: [21.55, 26.27, -12.0], down: [-1, 0, 0], width: 0.95, alpha: 0.8, soffit: true },
  // the porch ceiling's front band (the ceiling plane is at y 12.6)
  { a: [-7.615, 12.55, 41.3], b: [20.928, 12.55, 41.3], down: [0, 0, -1], width: 1.6, alpha: 0.6, soffit: true },
];

// ----------------------------------------------------------- real lights
// Candela under r160's physical falloff with the foot as the unit, like
// roomlights.js: illuminance = intensity / d^2.
const PORCH_POINTS = [[-2.5, 11.0, 38.5], [8, 11.0, 38.5], [17, 11.0, 38.5]];
const PORCH_INTENSITY = 36;
const PORCH_RANGE = 16;
// Stands west of the house and fires north-east at its west wall: the photo's
// blue is on the treeline west of the house (environment.js does not plant it
// yet, PLANT_TREES), with only a tinge reaching the porch's west column. From
// the street it shows as the blue pool on the lawn and that tinge -- it must
// NOT wash the facade, which reads purple the moment it does.
const BLUE_SPOT = { pos: [-30, 0.5, 55], target: [-18, 8, 38], intensity: 1600,
                    angle: 0.45, penumbra: 0.5, range: 70, color: 0x2040ff };
// amber bed uplights: two in the walkway bed, one at the driveway's east edge
const AMBER_POINTS = [[5.3, 0.3, 49.0], [8.6, 0.3, 48.8], [48.5, 0.3, 37.5]];
const AMBER_INTENSITY = 5;
const AMBER_RANGE = 7;
// a tight warm pool over the walk and the bottom porch step (the photo's walk
// is lit to ~40% grey right at the steps and black ten feet out)
// Sits over the rock strip so the cobbles and steppers beside the walk read
// (x 3..12, z 44..58 at ~60/255) and the walk at the steps stays ~100.
const STEP_POOL = { pos: [10.5, 6.0, 49.0], intensity: 95, range: 18, color: 0xffb46b };
// The concrete is the brightest ground surface in the photo: warm grey ~35%
// under the garage string, ~15% at the car, black by the street.
// Higher and further back with a wider, softer cone: the same total on the
// concrete without the hot ellipse round the car that a tight cone drew.
const DRIVE_SPOT = { pos: [33, 16, 26], target: [33, 0, 66], intensity: 2600,
                     angle: 0.95, penumbra: 0.8, range: 66, color: 0xffbe80 };

// the lit upstairs window (glass at z 26.50 in a recess of the z 26.74 wall)
// (mesh_8 in the shell: lower sash z 26.50, upper 26.66, in the z 26.74 wall)
const WINDOW = { x0: 14.55, x1: 17.15, y0: 18.3, y1: 24.0, z: 26.70 };

// ----------------------------------------------------------- state

let group = null;          // everything emissive, child of the shell group
let halos = null;          // THREE.Points
let haloMat = null;
let ledMat = null;         // the fixture spheres' material
let washMat = null;
let windowMat = null;
let glass = [];            // [{m, orig}] the shell's transparent (window) materials
const lights = [];         // [{light, local: Vector3, base}] at scene root
let spot = null;           // the blue uplight (also in `lights`)
let spotTargetLocal = null;
let driveSpot = null;
let driveTargetLocal = null;
let sky = null;            // night sky dome (scene root, follows the camera)
let skyMat = null;
let suspended = false;
let lastApplied = -1;

const _m = new THREE.Matrix4();
const _v = new THREE.Vector3();

// world (as measured) -> shell-local
function measuredToLocal() {
  const m = new THREE.Matrix4();
  m.compose(
    new THREE.Vector3(MEASURED_SHELL.x, MEASURED_SHELL.y, MEASURED_SHELL.z),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), MEASURED_SHELL.rot_y),
    new THREE.Vector3().setScalar(MEASURED_SHELL.scale || 1));
  return m.invert();
}

// ----------------------------------------------------------- init

export function initEaveLights() {
  // The lights, once, before the boot compile (see the header).
  for (const p of PORCH_POINTS) {
    const light = new THREE.PointLight(0xffb46b, 0, PORCH_RANGE, 2);
    light.name = 'eaveLight:porch';
    scene.add(light);
    lights.push({ light, local: new THREE.Vector3(...p), base: PORCH_INTENSITY });
  }
  for (const p of AMBER_POINTS) {
    const light = new THREE.PointLight(AMBER, 0, AMBER_RANGE, 2);
    light.name = 'eaveLight:amber';
    scene.add(light);
    lights.push({ light, local: new THREE.Vector3(...p), base: AMBER_INTENSITY });
  }
  {
    const light = new THREE.PointLight(STEP_POOL.color, 0, STEP_POOL.range, 2);
    light.name = 'eaveLight:step';
    scene.add(light);
    lights.push({ light, local: new THREE.Vector3(...STEP_POOL.pos), base: STEP_POOL.intensity });
  }
  driveSpot = new THREE.SpotLight(DRIVE_SPOT.color, 0, DRIVE_SPOT.range, DRIVE_SPOT.angle,
                                  DRIVE_SPOT.penumbra, 2);
  driveSpot.name = 'eaveLight:drive';
  scene.add(driveSpot);
  scene.add(driveSpot.target);
  lights.push({ light: driveSpot, local: new THREE.Vector3(...DRIVE_SPOT.pos), base: DRIVE_SPOT.intensity });
  driveTargetLocal = new THREE.Vector3(...DRIVE_SPOT.target);
  spot = new THREE.SpotLight(BLUE_SPOT.color, 0, BLUE_SPOT.range, BLUE_SPOT.angle,
                             BLUE_SPOT.penumbra, 2);
  spot.name = 'eaveLight:blue';
  scene.add(spot);
  scene.add(spot.target);
  lights.push({ light: spot, local: new THREE.Vector3(...BLUE_SPOT.pos), base: BLUE_SPOT.intensity });
  spotTargetLocal = new THREE.Vector3(...BLUE_SPOT.target);
  // the measured numbers are world feet; the lights are placed relative to the
  // shell, so express them in its local space like the geometry
  const toLocal = measuredToLocal();
  for (const l of lights) l.local.applyMatrix4(toLocal);
  spotTargetLocal.applyMatrix4(toLocal);
  driveTargetLocal.applyMatrix4(toLocal);

  // The night sky: the photo's black has faint sensor grain and a lift at the
  // horizon, and a clipped flat colour reads as a void. A big BackSide sphere
  // around the camera with a tiny tiled noise texture, night-only, fog off
  // (it sits past fog-far on purpose so nothing in the yard ever reaches it).
  skyMat = new THREE.MeshBasicMaterial({
    map: makeSkyTexture(), side: THREE.BackSide, fog: false, toneMapped: false,
    transparent: true, opacity: 0, depthWrite: false,
  });
  sky = new THREE.Mesh(new THREE.SphereGeometry(1200, 24, 12), skyMat);
  sky.name = 'nightSky';
  sky.renderOrder = -10;
  sky.frustumCulled = false;
  sky.visible = false;
  scene.add(sky);

  window.addEventListener('houseShellLoaded', (e) => build(e.detail.shell));
  const existing = getShellRoot();
  if (existing) build(existing);

  onFrame(tick);

  window.__eavelights = {
    debug: () => ({ built: !!group, dots: halos?.geometry.attributes.position.count,
      night: getNightFactor(), applied: lastApplied,
      lights: lights.map((l) => ({ name: l.light.name, intensity: l.light.intensity })) }),
  };
}

// ----------------------------------------------------------- build

function build(shell) {
  dispose();
  // the shell's transparent materials are its window glass (and a pond);
  // collected BEFORE our own transparent meshes are added
  glass = [];
  const seen = new Set();
  shell.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
      if (m && m.transparent && m.color && !seen.has(m)) { seen.add(m); glass.push({ m, orig: m.color.clone() }); }
    }
  });
  const toLocal = measuredToLocal();
  const local = (p) => new THREE.Vector3(p[0], p[1], p[2]).applyMatrix4(toLocal);

  group = new THREE.Group();
  group.name = 'eaveLights';
  group.userData = { kind: 'eave-lights', pickable: false };

  // ---- LED positions along every run
  const dots = [];
  let jseed = 11;
  const jitter = () => { jseed = (jseed * 16807) % 2147483647; return jseed / 2147483647; };
  const pushDot = (v) => {
    for (const d of dots) if (d.distanceToSquared(v) < 0.16) return; // shared corner
    dots.push(v);
  };
  for (const run of RUNS) {
    for (let i = 0; i + 1 < run.pts.length; i++) {
      const a = local(run.pts[i]), b = local(run.pts[i + 1]);
      const off = new THREE.Vector3(...((i === 0 && run.outFirst) || run.out));
      const len = a.distanceTo(b);
      const n = Math.max(1, Math.round(len / LED_SPACING));
      for (let k = 0; k <= n; k++) {
        // a little spacing jitter on the interior bulbs (+-6% of a gap)
        const jit = (k === 0 || k === n) ? 0 : (jitter() - 0.5) * 0.12;
        pushDot(new THREE.Vector3().lerpVectors(a, b, (k + jit) / n).add(off));
      }
    }
  }

  // ---- the fixtures: one small sphere per LED (what you see by day)
  const sphere = new THREE.SphereGeometry(0.11, 6, 5);
  ledMat = new THREE.MeshStandardMaterial({
    color: 0xc9c9c9, roughness: 0.4, metalness: 0.1,
    emissive: LED_COLOR, emissiveIntensity: 0,
  });
  const inst = new THREE.InstancedMesh(sphere, ledMat, dots.length);
  inst.name = 'eaveLEDs';
  dots.forEach((d, i) => inst.setMatrixAt(i, _m.makeTranslation(d.x, d.y, d.z)));
  inst.instanceMatrix.needsUpdate = true;
  inst.computeBoundingBox();
  inst.computeBoundingSphere();
  group.add(inst);

  // ---- the halos: Points, one per LED plus one per amber bed fixture
  const haloPts = [...dots];
  const haloCols = dots.map(() => LED_COLOR);
  const haloSize = dots.map(() => HALO_SIZE);
  // +-10% per-LED brightness, seeded so the string never twinkles between builds
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const haloBright = dots.map(() => 0.9 + 0.2 * rnd());
  for (const p of AMBER_POINTS) {
    haloPts.push(local(p));
    haloCols.push(AMBER);
    haloSize.push(AMBER_HALO);
    haloBright.push(1);
  }
  const hg = new THREE.BufferGeometry();
  hg.setAttribute('position', new THREE.Float32BufferAttribute(haloPts.flatMap((p) => [p.x, p.y, p.z]), 3));
  hg.setAttribute('color', new THREE.Float32BufferAttribute(haloCols.flatMap((c) => [c.r, c.g, c.b]), 3));
  hg.setAttribute('aSize', new THREE.Float32BufferAttribute(haloSize, 1));
  hg.setAttribute('aBright', new THREE.Float32BufferAttribute(haloBright, 1));
  haloMat = makeHaloMaterial();
  halos = new THREE.Points(hg, haloMat);
  halos.name = 'eaveHalos';
  halos.renderOrder = 3;
  halos.frustumCulled = false;
  group.add(halos);

  // ---- the siding wash
  washMat = makeWashMaterial();
  const wash = new THREE.Mesh(buildWashGeometry(local), washMat);
  wash.name = 'eaveWash';
  wash.renderOrder = 2;
  wash.frustumCulled = false;
  group.add(wash);

  // ---- the lit window
  windowMat = new THREE.MeshBasicMaterial({
    map: makeBlindsTexture(), transparent: true, opacity: 0, toneMapped: false,
    depthWrite: false,
  });
  const w = WINDOW;
  const win = new THREE.Mesh(new THREE.PlaneGeometry(w.x1 - w.x0, w.y1 - w.y0), windowMat);
  win.position.copy(local([(w.x0 + w.x1) / 2, (w.y0 + w.y1) / 2, w.z]));
  win.name = 'litWindow';
  win.renderOrder = 2;
  group.add(win);

  shell.add(group);
  lastApplied = -1; // force a repaint at the current night factor
}

function buildWashGeometry(local) {
  const pos = [], col = [], dist = [], along = [], params = [], idx = [];
  const c = WASH_COLOR;
  for (const w of WASHES) {
    const a = local(w.a), b = local(w.b);
    const down = new THREE.Vector3(...w.down).normalize();
    const len = a.distanceTo(b);
    const segs = Math.max(2, Math.ceil(len / 0.75));
    const rows = 4; // the profile is evaluated per fragment; rows only carry the plane
    const alpha = w.alpha ?? 0.7;
    // pools sit under the bulbs, so the scallop period is the run's real gap
    // (RUNS fits a whole number of gaps into each edge, so it is len / n)
    const spacing = w.scallop === false ? 0 : len / Math.max(1, Math.round(len / LED_SPACING));
    const base = pos.length / 3;
    for (let i = 0; i <= segs; i++) {
      const p = new THREE.Vector3().lerpVectors(a, b, i / segs);
      for (let r = 0; r <= rows; r++) {
        const t = r / rows;
        _v.copy(p).addScaledVector(down, w.width * t);
        if (w.clampY !== undefined && _v.y < w.clampY) _v.y = w.clampY;
        pos.push(_v.x, _v.y, _v.z);
        col.push(c[0], c[1], c[2], alpha);
        dist.push(w.width * t);
        along.push(len * i / segs);
        params.push(w.width, spacing, w.clap ? 1 : 0, w.soffit ? 1 : 0);
      }
    }
    for (let i = 0; i < segs; i++) {
      for (let r = 0; r < rows; r++) {
        const p0 = base + i * (rows + 1) + r;
        const p1 = p0 + rows + 1;
        idx.push(p0, p1, p0 + 1, p0 + 1, p1, p1 + 1);
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4));
  g.setAttribute('aDist', new THREE.Float32BufferAttribute(dist, 1));
  g.setAttribute('aAlong', new THREE.Float32BufferAttribute(along, 1));
  g.setAttribute('aParams', new THREE.Float32BufferAttribute(params, 4));
  g.setIndex(idx);
  return g;
}

// The wash is what the bulbs put on the house. Per fragment, in feet:
//   profile  -- rises over the first half foot under the edge (the fascia's
//               own shadow), holds for a foot, then falls off as a cube, so
//               the wall is dim grey again by mid-height;
//   pools    -- a gaussian under each bulb along the run, so the fascia and
//               soffit read as a chain of warm pools rather than a strip;
//   courses  -- a shadow line at the foot of every 5 in clapboard course, so
//               the band reads as lit siding and not a glow sheet.
// Additive, premultiplied, tone-mapping bypassed like the halos.
function makeWashMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: { uOpacity: { value: 0 }, uCourse: { value: CLAPBOARD } },
    vertexShader: `
      attribute float aDist; attribute float aAlong; attribute vec4 aParams;
      varying vec4 vColor; varying float vDist; varying float vAlong; varying float vWorldY;
      varying vec4 vParams;
      void main() {
        vColor = color; vDist = aDist; vAlong = aAlong; vParams = aParams;
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldY = wp.y;
        gl_Position = projectionMatrix * viewMatrix * wp;
      }`,
    fragmentShader: `
      uniform float uOpacity; uniform float uCourse;
      varying vec4 vColor; varying float vDist; varying float vAlong; varying float vWorldY;
      varying vec4 vParams;
      void main() {
        float W = vParams.x; float spacing = vParams.y;
        bool soffit = vParams.w > 0.5;
        float d = vDist;
        float band = soffit ? 0.35 : 1.0;
        float rise = soffit ? 1.0 : smoothstep(0.0, 0.45, d);
        float decay = d < band ? 1.0
          : pow(max(0.0, 1.0 - (d - band) / max(0.01, W - band)), soffit ? 1.6 : 3.0);
        float p = rise * decay;
        if (spacing > 0.0) {
          float a = (fract(vAlong / spacing) - 0.5) * spacing;   // ft to the nearest bulb
          float sigma = soffit ? 0.6 : 0.85;
          float pool = exp(-(a * a) / (2.0 * sigma * sigma));
          p *= soffit ? (0.3 + 0.7 * pool) : (0.68 + 0.32 * pool);
        }
        if (vParams.z > 0.5) {
          float f = fract(vWorldY / uCourse);
          p *= 1.0 - 0.28 * (1.0 - smoothstep(0.0, 0.12, f));
        }
        vec3 c = vColor.rgb * (vColor.a * p * uOpacity);
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
}

// Screen-space halo: hot white core, soft warm skirt. Size in world feet with
// perspective attenuation, clamped so a close fly-by keeps them dot-sized.
function makeHaloMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: {
      uScale: { value: 300 },
      uOpacity: { value: 0 },
    },
    vertexShader: `
      uniform float uScale;
      attribute float aSize; attribute float aBright;
      varying vec3 vColor;
      void main() {
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        float ps = aSize * uScale / max(0.5, -mv.z);
        gl_PointSize = clamp(ps, 4.0, 24.0);
        gl_Position = projectionMatrix * mv;
        vColor = color * aBright;
      }`,
    fragmentShader: `
      uniform float uOpacity;
      varying vec3 vColor;
      void main() {
        float d = length(gl_PointCoord - 0.5) * 2.0;
        if (d > 1.0) discard;
        float core = smoothstep(0.30, 0.05, d);
        float skirt = pow(max(0.0, 1.0 - d), 1.4) * 0.45;
        // the core overshoots 1.0 on purpose: additive onto lit siding it must
        // still clip, or the dot is just a pinhead riding on the wash -- but
        // it clips through the amber, so the bulb reads 2700K, not 6500K
        vec3 c = mix(vColor, vec3(1.0), core * 0.55) * (core * 1.9 + skirt);
        gl_FragColor = vec4(c * uOpacity, 1.0);
        #include <colorspace_fragment>
      }`,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
}

// Tiled grain for the sky dome: near-black, a hair of blue, +-1/255 noise.
function makeSkyTexture() {
  const cv = document.createElement('canvas');
  // 256x256 tiled 8x4 over the dome: ~0.18 degrees per texel both ways. An
  // anisotropic tile (r6: 256x128 tiled 6x1) read as vertical streaks.
  cv.width = 256; cv.height = 256;
  const ctx = cv.getContext('2d');
  const img = ctx.createImageData(256, 256);
  let seed = 3;
  for (let y = 0; y < 256; y++) {
    const base = 2.6;                      // flat: any gradient tiles into bands
    for (let x = 0; x < 256; x++) {
      seed = (seed * 16807) % 2147483647;
      const n = (seed / 2147483647 - 0.5) * 2.4;
      const v = Math.max(0, base + n);
      const i = (y * 256 + x) * 4;
      img.data[i] = v; img.data[i + 1] = v + 0.5; img.data[i + 2] = v + 1.5; img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const tex = new THREE.CanvasTexture(cv);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(8, 4);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// warm light through a closed venetian blind
function makeBlindsTexture() {
  const cv = document.createElement('canvas');
  cv.width = 32; cv.height = 128;
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#ffe2b0';
  ctx.fillRect(0, 0, 32, 128);
  ctx.fillStyle = 'rgba(110, 70, 30, 0.6)';
  for (let y = 2; y < 128; y += 7) ctx.fillRect(0, y, 32, 2);
  // a curtain: the lamp is up near the ceiling, the blind's foot is in shadow
  const grad = ctx.createLinearGradient(0, 0, 0, 128);
  grad.addColorStop(0, 'rgba(255,250,230,0.45)');
  grad.addColorStop(0.35, 'rgba(255,220,170,0)');
  grad.addColorStop(1, 'rgba(40,20,5,0.7)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 32, 128);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function dispose() {
  for (const g of glass) g.m.color.copy(g.orig); // hand the shell its glass back
  glass = [];
  if (!group) return;
  group.removeFromParent();
  group.traverse((o) => { if (o.geometry) o.geometry.dispose(); });
  for (const m of [ledMat, haloMat, washMat, windowMat]) {
    if (m?.map) m.map.dispose();
    m?.dispose();
  }
  group = null; halos = null; ledMat = null; haloMat = null; washMat = null; windowMat = null;
}

// ----------------------------------------------------------- per frame

function tick() {
  const shell = getShellRoot();
  const live = !!(shell && group && shell.visible && !suspended);
  const night = live ? getNightFactor() : 0;

  // the lights follow the shell (they are not its children -- see the header)
  if (shell && night > 0) {
    for (const l of lights) l.light.position.copy(l.local).applyMatrix4(shell.matrixWorld);
    spot.target.position.copy(spotTargetLocal).applyMatrix4(shell.matrixWorld);
    driveSpot.target.position.copy(driveTargetLocal).applyMatrix4(shell.matrixWorld);
  }

  if (haloMat && renderer) {
    // gl_PointSize is in device pixels; scale = drawing-buffer height / 2 is
    // what three's own PointsMaterial uses for sizeAttenuation
    haloMat.uniforms.uScale.value = renderer.domElement.height / 2;
  }

  if (sky) {
    sky.visible = night > 0.01;
    if (sky.visible) sky.position.copy(camera.position);
  }

  if (Math.abs(night - lastApplied) < 1e-3) return;
  lastApplied = night;
  if (skyMat) skyMat.opacity = night;
  for (const l of lights) l.light.intensity = l.base * night;
  if (!group) return;
  const on = night > 0.01;
  haloMat.uniforms.uOpacity.value = night;
  halos.visible = on;
  ledMat.emissiveIntensity = 6.0 * night;
  washMat.uniforms.uOpacity.value = night;
  washMat.visible = on;
  // unlit glass is near-black after dark: the shell's window material is a
  // sky-blue map that reads as flat cyan panes at night
  for (const g of glass) g.m.color.copy(g.orig).lerp(GLASS_NIGHT, night * 0.92);
  windowMat.opacity = night;
  windowMat.visible = on;
}

// snapshots.js brackets its room-card capture with this: cards persist, and a
// card shot at night would bake the porch lights into the front rooms forever.
// Intensity only, never light.visible (shader recompile -- see the header).
export function suspendEaveLights() {
  suspended = true;
  const saved = lights.map((l) => l.light.intensity);
  for (const l of lights) l.light.intensity = 0;
  const skyWas = sky ? sky.visible : false;
  if (sky) sky.visible = false; // the card's studio backdrop, not our night sky
  return () => {
    suspended = false;
    lights.forEach((l, i) => { l.light.intensity = saved[i]; });
    if (sky) sky.visible = skyWas;
  };
}
