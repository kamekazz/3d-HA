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
const HALO_SIZE = 0.8;        // ft; the SPRITE -- the hot core is ~1/5 of it
const BLEED_SIZE = 7.0;       // ft; the faint atmospheric bleed round every bulb
const AMBER_HALO = 1.0;       // the bed fixtures are smaller lamps
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
  // (no string on the garage's east gable rakes: seen end-on from the street
  // they merged into one sourceless flare at the corner)
  { pts: [[20.602, 13.046, 30.66], [48.016, 13.046, 30.66]], out: [0, -LED_DROP, LED_OUT],
    spacing: 1.5, gain: 1.25 },
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
  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 7.5, alpha: 0.36, clampY: 24.2, clap: true, band: 2.6 },
  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 7.5, alpha: 0.36, clampY: 24.2, clap: true, band: 2.6 },
  // main gable rakes (field z 26.9, trim z 27.7)
  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 7.5, alpha: 0.28, clap: true, band: 1.8 },
  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 7.5, alpha: 0.28, clampY: 23.8, clap: true, band: 1.8 },
  // the second-floor walls above the porch roof: a faint lift, no pools
  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 7, alpha: 0.25, scallop: false, clap: true },
  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 7, alpha: 0.25, scallop: false, clap: true },
  // garage front wall (z 29.8) under its eave
  // (kept well under scene.js's bloom threshold: with the sconce floods and the
  // soffit strip on top of it, this face went nova and fogged the frame)
  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 4.5, alpha: 0.32, clap: true, spacing: 1.5 },
  // east wall of the main house (x 20.6-20.9) under the side eave
  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 5, alpha: 0.6, clap: true },
  // the porch fascia board itself, lit by its own string
  { a: [-7.6, 12.95, 41.42], b: [20.9, 12.95, 41.42], down: [0, -1, 0], width: 0.55, alpha: 0.5 },
  // ---- soffits: the underside of every overhang, lit from the bulbs hanging
  // just below it -- the "lit interior" of the gables. Strips run inward from
  // the fascia edge, a hair under the roof sheet, and pool under each bulb.
  { a: [-8.2, 26.27, 30.7], b: [1.74, 36.38, 30.7], down: [0, 0, -1], width: 1.3, alpha: 0.85, soffit: true },
  { a: [1.74, 36.38, 30.7], b: [11.67, 26.27, 30.7], down: [0, 0, -1], width: 1.3, alpha: 0.85, soffit: true },
  { a: [2.3, 36.95, 27.9], b: [6.656, 41.39, 27.9], down: [0, 0, -1], width: 1.2, alpha: 0.75, soffit: true },
  { a: [6.656, 41.39, 27.9], b: [21.519, 26.27, 27.9], down: [0, 0, -1], width: 1.2, alpha: 0.75, soffit: true },
  { a: [20.6, 13.0, 30.68], b: [48.0, 13.0, 30.68], down: [0, 0, -1], width: 0.9, alpha: 0.38, soffit: true, spacing: 1.5 },
  { a: [21.55, 26.27, 27.9], b: [21.55, 26.27, -12.0], down: [-1, 0, 0], width: 0.95, alpha: 0.8, soffit: true },
  // the porch ceiling's front band (the ceiling plane is at y 12.6)
  { a: [-7.615, 12.55, 41.3], b: [20.928, 12.55, 41.3], down: [0, 0, -1], width: 1.6, alpha: 0.6, soffit: true },
];

// ----------------------------------------------------------- real lights
// Candela under r160's physical falloff with the foot as the unit, like
// roomlights.js: illuminance = intensity / d^2.
const PORCH_POINTS = [[-2.5, 11.0, 38.5], [8, 11.0, 38.5], [17, 11.0, 38.5]];
const PORCH_INTENSITY = 48;
const PORCH_RANGE = 16;
// Stands west of the house and fires north-east at its west wall: the photo's
// blue is on the treeline west of the house (environment.js does not plant it
// yet, PLANT_TREES), with only a tinge reaching the porch's west column. From
// the street it shows as the blue pool on the lawn and that tinge -- it must
// NOT wash the facade, which reads purple the moment it does.
const BLUE_SPOT = { pos: [-34, 1, 52], target: [-10, 6, 34], intensity: 4500,
                    angle: 0.6, penumbra: 0.5, range: 80, color: 0x2040ff };
// amber bed uplights: two in the walkway bed, one at the driveway's east edge
const AMBER_POINTS = [[5.3, 0.3, 49.0], [8.6, 0.3, 48.8], [48.5, 0.3, 37.5]];
const AMBER_INTENSITY = 2.5;
const AMBER_RANGE = 5;
// a tight warm pool over the walk and the bottom porch step (the photo's walk
// is lit to ~40% grey right at the steps and black ten feet out)
// Sits over the rock strip so the cobbles and steppers beside the walk read
// (x 3..12, z 44..58 at ~60/255) and the walk at the steps stays ~100.
// The walk fan (x 11..20, z 44..70) and the rock band beside it (x 8.6..15.6,
// z 47..58) at ~100/255, the lawn either side dark: two downward spots whose
// penumbra dies before the grass, not a point that spills in every direction.
// A single wide, fully-feathered spot from the porch soffit: the walk fan, the
// rock band, the step treads and the top of the drive in one even wash with no
// pool edge anywhere (two tight 10 ft spots read as 'spotlights in a void').
const WALK_SPOTS = [
  // short and steep: the steps and the upper fan; cone and range end at z ~58
  { pos: [21, 8, 46], target: [19, 0, 64], intensity: 1900, angle: 0.4, penumbra: 1.0, range: 36, color: 0xffb46b },
];
// the low path light at the rock band's end, where the photo's is
const PATH_LIGHT = { pos: [11.6, 1.2, 57], intensity: 3, range: 8, color: 0xffb46b };
// the step treads and risers, from under the porch fascia above them
const STEP_LIGHT = { pos: [15.5, 6, 49], intensity: 60, range: 12, color: 0xffb46b };
// The concrete is the brightest ground surface in the photo: warm grey ~35%
// under the garage string, ~15% at the car, black by the street.
// Higher and further back with a wider, softer cone: the same total on the
// concrete without the hot ellipse round the car that a tight cone drew.
// Two overlapping wide, fully-feathered spots from the garage eave: a broad,
// near-even wash with no cone edge anywhere in frame (a single 0.95 rad cone
// drew a hard grey wedge from the car to the bottom-right), falling to ~2/255
// by the bottom edge on the range cutoff. The first casts the car's shadow.
const DRIVE_SPOTS = [
  // the garage string's throw down the drive: the door apron is the sconces'
  // (roomlights), this carries z 40..60 and the cone/range end at the car's
  // rear, so nothing lights the car's rear face, plate or tyres
  { pos: [33, 13, 30], target: [29, 0, 62], intensity: 950, angle: 0.9, penumbra: 1.0, range: 50, color: 0xfff2e4, shadow: true },
  // the garage door face itself, from the eave (the photo has it as the
  // brightest surface on that wall; the sconces alone leave it at ~70)
  { pos: [33, 12.6, 34], target: [34, 5, 29.8], intensity: 1500, angle: 0.85, penumbra: 0.6, range: 22, color: 0xffe6c8 },
];

// the lit upstairs window (glass at z 26.50 in a recess of the z 26.74 wall)
// (mesh_8 in the shell: lower sash z 26.50, upper 26.66, in the z 26.74 wall)
const WINDOW = { x0: 14.55, x1: 17.15, y0: 18.3, y1: 24.0, z: 26.70 };

// ----------------------------------------------------------- state

let group = null;          // everything emissive, child of the shell group
let halos = null;          // THREE.Points
let haloMat = null;
let bleedMat = null;
let ledMat = null;         // the fixture spheres' material
let washMat = null;
let windowMat = null;
let glowMat = null;
let glass = [];            // [{m, orig}] the shell's transparent (window) materials
const lights = [];         // [{light, local: Vector3, base}] at scene root
const spotTargets = [];    // [{light, local}] every SpotLight's aim point, shell-local
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
  const addPoint = (name, pos, intensity, range, color) => {
    const light = new THREE.PointLight(color, 0, range, 2);
    light.name = name;
    scene.add(light);
    lights.push({ light, local: new THREE.Vector3(...pos), base: intensity });
  };
  const addSpot = (name, cfg) => {
    const light = new THREE.SpotLight(cfg.color, 0, cfg.range, cfg.angle, cfg.penumbra, 2);
    light.name = name;
    if (cfg.shadow) {
      // The one shadow-casting light here: without it the car floats on the lit
      // concrete. Set ONCE at init (a shadow toggle is a program cache-key term,
      // like the light count). The spot's own fov is the shadow frustum, so the
      // car (x ~28, z 58..74) sits inside it; near/far trimmed to the drive.
      light.castShadow = true;
      light.shadow.mapSize.set(2048, 2048);
      light.shadow.camera.near = 4;
      light.shadow.camera.far = 70;
      light.shadow.bias = -0.0004;
      light.shadow.normalBias = 0.3;
    }
    scene.add(light);
    scene.add(light.target);
    lights.push({ light, local: new THREE.Vector3(...cfg.pos), base: cfg.intensity });
    spotTargets.push({ light, local: new THREE.Vector3(...cfg.target) });
  };
  for (const p of PORCH_POINTS) addPoint('eaveLight:porch', p, PORCH_INTENSITY, PORCH_RANGE, 0xffb46b);
  for (const p of AMBER_POINTS) addPoint('eaveLight:amber', p, AMBER_INTENSITY, AMBER_RANGE, AMBER);
  for (const c of WALK_SPOTS) addSpot('eaveLight:walk', c);
  addPoint('eaveLight:path', PATH_LIGHT.pos, PATH_LIGHT.intensity, PATH_LIGHT.range, PATH_LIGHT.color);
  addPoint('eaveLight:steps', STEP_LIGHT.pos, STEP_LIGHT.intensity, STEP_LIGHT.range, STEP_LIGHT.color);
  for (const c of DRIVE_SPOTS) addSpot('eaveLight:drive', c);
  addSpot('eaveLight:blue', BLUE_SPOT);
  // the measured numbers are world feet; the lights are placed relative to the
  // shell, so express them in its local space like the geometry
  const toLocal = measuredToLocal();
  for (const l of lights) l.local.applyMatrix4(toLocal);
  for (const t of spotTargets) t.local.applyMatrix4(toLocal);

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
  const dotGain = [];
  let jseed = 11;
  const jitter = () => { jseed = (jseed * 16807) % 2147483647; return jseed / 2147483647; };
  const pushDot = (v, gain) => {
    for (const d of dots) if (d.distanceToSquared(v) < 0.16) return; // shared corner
    dots.push(v);
    dotGain.push(gain);
  };
  for (const run of RUNS) {
    for (let i = 0; i + 1 < run.pts.length; i++) {
      const a = local(run.pts[i]), b = local(run.pts[i + 1]);
      const off = new THREE.Vector3(...((i === 0 && run.outFirst) || run.out));
      const len = a.distanceTo(b);
      const n = Math.max(1, Math.round(len / (run.spacing || LED_SPACING)));
      for (let k = 0; k <= n; k++) {
        // a little spacing jitter on the interior bulbs (+-6% of a gap)
        const jit = (k === 0 || k === n) ? 0 : (jitter() - 0.5) * 0.12;
        pushDot(new THREE.Vector3().lerpVectors(a, b, (k + jit) / n).add(off), run.gain || 1);
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
  // seeded, so the string never twinkles between builds
  let seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  // +-12% size variance per bulb, +-10% brightness
  const haloSize = dots.map(() => HALO_SIZE * (0.88 + 0.24 * rnd()));
  const haloBright = dots.map((d, i) => (0.85 + 0.3 * rnd()) * (dotGain[i] || 1));
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
  haloMat = makeHaloMaterial(1.0, 1.0, 0);
  halos = new THREE.Points(hg, haloMat);
  halos.name = 'eaveHalos';
  halos.renderOrder = 3;
  halos.frustumCulled = false;
  group.add(halos);
  // the bleed: the same points, a much bigger and dimmer gaussian, so the lit
  // roofline carries a hair of atmosphere against the sky instead of a knife edge
  bleedMat = makeHaloMaterial(BLEED_SIZE / HALO_SIZE, 0.0, 1);
  const bleed = new THREE.Points(hg, bleedMat);
  bleed.name = 'eaveBleed';
  bleed.renderOrder = 2;
  bleed.frustumCulled = false;
  group.add(bleed);
  // scene.js night optics (UnrealBloom + grain + black lift) landed after this
  // layer was written and supplies the atmospheric bleed itself; two bloom
  // systems stacked into fog. Kept, off, so a sole-renderer deploy can re-arm it.
  bleed.visible = false;

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
  // the light it throws onto the siding round the frame
  glowMat = new THREE.MeshBasicMaterial({
    map: makeGlowTexture(), transparent: true, opacity: 0, toneMapped: false,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const glow = new THREE.Mesh(new THREE.PlaneGeometry((w.x1 - w.x0) * 2.4, (w.y1 - w.y0) * 1.7), glowMat);
  glow.position.copy(win.position).add(new THREE.Vector3(0, 0, 0.03));
  glow.name = 'litWindowGlow';
  glow.renderOrder = 2;
  group.add(glow);

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
    const spacing = w.scallop === false ? 0 : len / Math.max(1, Math.round(len / (w.spacing || LED_SPACING)));
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
        float band = soffit ? 0.35 : 2.6;
        float rise = soffit ? 1.0 : smoothstep(0.1, 0.9, d);
        float decay = d < band ? 1.0
          : pow(max(0.0, 1.0 - (d - band) / max(0.01, W - band)), soffit ? 1.6 : 2.4);
        float p = rise * decay;
        if (spacing > 0.0) {
          float a = (fract(vAlong / spacing) - 0.5) * spacing;   // ft to the nearest bulb
          float sigma = soffit ? 0.6 : 0.85;
          float pool = exp(-(a * a) / (2.0 * sigma * sigma));
          p *= soffit ? (0.3 + 0.7 * pool) : (0.68 + 0.32 * pool);
        }
        if (vParams.z > 0.5) {
          float f = fract(vWorldY / uCourse);
          p *= 1.0 - 0.45 * (1.0 - smoothstep(0.0, 0.18, f));
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

// Screen-space bloom for a bulb. The sprite is ~5x the hot core: a gaussian
// white core, an amber mid, and a long gaussian tail that fades into the
// siding -- additive, so the bulbs crowding a gable apex build a hot-spot.
// sizeMul/gain/mode make the same shader serve the wide, faint "bleed" layer.
function makeHaloMaterial(sizeMul, gain, mode) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uScale: { value: 300 },
      uOpacity: { value: 0 },
      uSizeMul: { value: sizeMul },
      uGain: { value: gain },
      uMode: { value: mode },
    },
    vertexShader: `
      uniform float uScale; uniform float uSizeMul;
      attribute float aSize; attribute float aBright;
      varying vec3 vColor; varying float vBright;
      void main() {
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        float ps = aSize * uSizeMul * uScale / max(0.5, -mv.z);
        gl_PointSize = clamp(ps, 5.0 * uSizeMul, 36.0 * uSizeMul);
        gl_Position = projectionMatrix * mv;
        vColor = color; vBright = aBright;
      }`,
    fragmentShader: `
      uniform float uOpacity; uniform float uGain; uniform float uMode;
      varying vec3 vColor; varying float vBright;
      float g(float d, float s) { return exp(-(d * d) / (2.0 * s * s)); }
      void main() {
        float d = length(gl_PointCoord - 0.5) * 2.0;
        if (d > 1.0) discard;
        vec3 c;
        if (uMode > 0.5) {
          c = vColor * (g(d, 0.42) * uGain);          // bleed: one soft gaussian
        } else {
          float core = g(d, 0.09);
          float mid = g(d, 0.24);
          float tail = g(d, 0.5);
          // the core overshoots 1.0 so it still clips on lit siding, but it
          // clips THROUGH the amber -- a 2700K bulb, not a 6500K pinhead
          c = mix(vColor, vec3(1.0), core * 0.6) * (core * 2.0 + mid * 0.22 + tail * 0.03) * uGain;
        }
        gl_FragColor = vec4(c * vBright * uOpacity, 1.0);
        #include <colorspace_fragment>
      }`,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
}

// Tiled grain for the sky dome: near-black, a hair of blue, +-2/255 noise.
function makeSkyTexture() {
  const cv = document.createElement('canvas');
  // 256x256 tiled 8x4 over the dome: ~0.18 degrees per texel both ways. An
  // anisotropic tile (r6: 256x128 tiled 6x1) read as vertical streaks.
  cv.width = 256; cv.height = 256;
  const ctx = cv.getContext('2d');
  const img = ctx.createImageData(256, 256);
  let seed = 3;
  for (let y = 0; y < 256; y++) {
    const base = 2.0;                      // flat: any gradient tiles into bands
    for (let x = 0; x < 256; x++) {
      seed = (seed * 16807) % 2147483647;
      const n = (seed / 2147483647 - 0.5) * 2.0;
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

// warm radial glow for the siding round the lit window
function makeGlowTexture() {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 128;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 6, 64, 64, 64);
  g.addColorStop(0, 'rgba(210, 225, 255, 0.5)');
  g.addColorStop(0.35, 'rgba(200, 215, 255, 0.2)');
  g.addColorStop(1, 'rgba(190, 210, 255, 0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// warm light through a closed venetian blind
function makeBlindsTexture() {
  const cv = document.createElement('canvas');
  cv.width = 32; cv.height = 128;
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#dfe9ff';                 // ~6000K: an LED ceiling light behind the blind
  ctx.fillRect(0, 0, 32, 128);
  ctx.fillStyle = 'rgba(40, 50, 80, 0.6)';
  for (let y = 2; y < 128; y += 7) ctx.fillRect(0, y, 32, 2);
  // a curtain: the lamp is up near the ceiling, the blind's foot is in shadow
  const grad = ctx.createLinearGradient(0, 0, 0, 128);
  grad.addColorStop(0, 'rgba(240,246,255,0.45)');
  grad.addColorStop(0.35, 'rgba(220,230,255,0)');
  grad.addColorStop(1, 'rgba(10,15,30,0.7)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 32, 128);
  // the sash frame
  ctx.strokeStyle = 'rgba(30, 35, 50, 0.9)';
  ctx.lineWidth = 3;
  ctx.strokeRect(1.5, 1.5, 29, 125);
  ctx.fillStyle = 'rgba(30, 35, 50, 0.8)';
  ctx.fillRect(0, 62, 32, 3);                // meeting rail
  ctx.fillRect(15, 0, 2, 128);               // mullion
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
  for (const m of [ledMat, haloMat, bleedMat, washMat, windowMat, glowMat]) {
    if (m?.map) m.map.dispose();
    m?.dispose();
  }
  group = null; halos = null; ledMat = null; haloMat = null; bleedMat = null; washMat = null; windowMat = null; glowMat = null;
}

// ----------------------------------------------------------- per frame

function tick() {
  const shell = getShellRoot();
  const live = !!(shell && group && shell.visible && !suspended);
  const night = live ? getNightFactor() : 0;

  // the lights follow the shell (they are not its children -- see the header)
  if (shell && night > 0) {
    for (const l of lights) l.light.position.copy(l.local).applyMatrix4(shell.matrixWorld);
    for (const t of spotTargets) t.light.target.position.copy(t.local).applyMatrix4(shell.matrixWorld);
  }

  if (haloMat && renderer) {
    // gl_PointSize is in device pixels; scale = drawing-buffer height / 2 is
    // what three's own PointsMaterial uses for sizeAttenuation
    haloMat.uniforms.uScale.value = renderer.domElement.height / 2;
    bleedMat.uniforms.uScale.value = renderer.domElement.height / 2;
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
  bleedMat.uniforms.uOpacity.value = night;
  halos.visible = on;
  ledMat.emissiveIntensity = 6.0 * night;
  washMat.uniforms.uOpacity.value = night;
  washMat.visible = on;
  // unlit glass is near-black after dark: the shell's window material is a
  // sky-blue map that reads as flat cyan panes at night
  for (const g of glass) g.m.color.copy(g.orig).lerp(GLASS_NIGHT, night * 0.92);
  windowMat.opacity = night;
  windowMat.visible = on;
  glowMat.opacity = night;
  glowMat.visible = on;
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
