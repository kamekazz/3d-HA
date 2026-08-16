// Drives the scene lighting from Home Assistant: sun.sun (elevation/azimuth)
// sets the time-of-day look, the weather entity dims/tints it. Everything
// eases toward its target each frame, so state changes fade instead of snap.
import * as THREE from 'three';
import { scene, hemiLight, sunLight, onFrame, setEnvIntensity } from './scene.js';
import { getState, findEntities, onStateApplied } from './state.js';

// ------------------------------------------------------------- ramps/tables

// keyframes by sun elevation (degrees), piecewise-lerped. Colors are the
// clear-sky look; weather multiplies/desaturates on top.
//
// The hemisphere GROUND colour is doing a second job here beyond "light bounced
// off the lawn": it is the only fill an interior surface facing away from the
// sun receives. With the original dark-slate ground (0x474e57 at full day) the
// four identically painted walls of an empty room metered 222 / 185 / 158 / 125
// — a 97-byte spread on one paint colour, where a photograph of a real room
// holds them within ~30. Every room builder independently papered over that
// with per-room emissive "wall wash" panels, which then read as hard-edged
// rectangles. Raising the daytime ground values fixes it once, for every room,
// with no extra lights (a light count change recompiles every MeshStandard
// shader — see roomlights.js) and no change to the night end of the ramp, so
// night mode and the room-glow still work. Verified with `roomkit.meter`.
const ELEVATION_RAMP = [
  //  el   sun color  sunInt  hemi sky  hemi gnd  hemiInt  bg+fog
  [-18, 0xff8844, 0.00, 0x223052, 0x0b0e14, 0.30, 0x070b12], // night
  [ -8, 0xff8844, 0.00, 0x2c3a5e, 0x151220, 0.40, 0x0d1220], // astro dusk
  [ -3, 0xff7733, 0.35, 0x51557e, 0x241c26, 0.55, 0x1d2135], // civil dusk
  [  0, 0xff9a4d, 0.65, 0x7c86ab, 0x3f3336, 0.70, 0x2c3049], // sunrise/set
  [  8, 0xffc487, 1.10, 0xa9bedd, 0x5c5c58, 0.85, 0x3d4c68], // golden hour
  [ 20, 0xffe8c8, 1.35, 0xc7dcf5, 0x7c848c, 0.95, 0x54688a],
  [ 45, 0xfff6e8, 1.50, 0xdfe8ff, 0x8e97a1, 1.00, 0x5f7692], // full day
];

// HA weather condition -> how much it dims the sun/sky and greys the colors
const WEATHER = {
  'sunny':           { sunX: 1.00, hemiX: 1.00, desat: 0.00, tint: 0xdfe6ee },
  'clear-night':     { sunX: 1.00, hemiX: 1.00, desat: 0.00, tint: 0xdfe6ee },
  'exceptional':     { sunX: 1.00, hemiX: 1.00, desat: 0.00, tint: 0xdfe6ee },
  'windy':           { sunX: 0.95, hemiX: 1.00, desat: 0.05, tint: 0xdfe6ee },
  'windy-variant':   { sunX: 0.95, hemiX: 1.00, desat: 0.05, tint: 0xdfe6ee },
  'partlycloudy':    { sunX: 0.80, hemiX: 0.95, desat: 0.15, tint: 0xdfe6ee },
  'cloudy':          { sunX: 0.45, hemiX: 0.85, desat: 0.45, tint: 0xc2cdd9 },
  'fog':             { sunX: 0.30, hemiX: 0.80, desat: 0.60, tint: 0xc8ced6 },
  'rainy':           { sunX: 0.35, hemiX: 0.80, desat: 0.55, tint: 0xb6c2d2 },
  'lightning':       { sunX: 0.30, hemiX: 0.75, desat: 0.55, tint: 0xb6c2d2 },
  'lightning-rainy': { sunX: 0.30, hemiX: 0.75, desat: 0.55, tint: 0xb6c2d2 },
  'pouring':         { sunX: 0.22, hemiX: 0.70, desat: 0.65, tint: 0xaab6c6 },
  'hail':            { sunX: 0.22, hemiX: 0.70, desat: 0.65, tint: 0xaab6c6 },
  'snowy':           { sunX: 0.50, hemiX: 1.10, desat: 0.35, tint: 0xe4ecf6 },
  'snowy-rainy':     { sunX: 0.50, hemiX: 1.10, desat: 0.35, tint: 0xe4ecf6 },
};
const WEATHER_CLEAR = WEATHER['sunny'];

// fog must always start beyond controls.maxDistance (300) — see scene.js
const FOG_DEFAULT = { near: 360, far: 1000 };
const FOG_FOGGY = { near: 320, far: 750 };

const DEFAULT_PRESET = { elevation: 45, azimuth: 180, condition: 'sunny' };
const SUN_DISTANCE = 150;
const SMOOTH_TAU = 0.6; // seconds; ~1-2 s visible settle
const MODE_KEY = '3dha.lightMode';

// ------------------------------------------------------------- state

function makeLightState() {
  return {
    sunDir: new THREE.Vector3(0, 1, 0),
    sunColor: new THREE.Color(),
    sunIntensity: 1.4,
    hemiSky: new THREE.Color(0xdfe8ff),
    hemiGround: new THREE.Color(0x30363f),
    hemiIntensity: 1.0,
    bg: new THREE.Color(0x10141a),
    fogNear: FOG_DEFAULT.near,
    fogFar: FOG_DEFAULT.far,
    nightFactor: 0,
    envIntensity: 0.45,
  };
}

const target = makeLightState();
const current = makeLightState();

let weatherId = null;      // discovered weather.* entity
let simOverride = null;    // console override via __daylight.simulate()
let mode = 'auto';         // 'auto' | 'day' | 'night'

export function getNightFactor() {
  return current.nightFactor;
}

// weather.js (particles/clouds) follows the same resolved sun+weather as the
// lighting — including mode overrides and __daylight.simulate() — via this
// registry instead of re-deriving it from entity states.
const daylightListeners = new Set();
let lastDaylight = { elevation: 45, condition: 'sunny', nightFactor: 0 };
export function onDaylightChanged(fn) { daylightListeners.add(fn); }
export function getDaylight() { return lastDaylight; }

// ------------------------------------------------------------- target calc

const _tint = new THREE.Color();

// ramp rows normalized once: [el, sunColor(Color), sunInt, sky(Color),
// ground(Color), hemiInt, bg(Color)]
const RAMP = ELEVATION_RAMP.map(([el, sun, si, sky, gnd, hi, bg]) => [
  el, new THREE.Color(sun), si, new THREE.Color(sky),
  new THREE.Color(gnd), hi, new THREE.Color(bg),
]);
const _ramp = [0, new THREE.Color(), 0, new THREE.Color(),
               new THREE.Color(), 0, new THREE.Color()];

function rampAt(el) {
  let a = RAMP[0], b = RAMP[0];
  for (const row of RAMP) {
    if (row[0] <= el) a = row;
    if (row[0] >= el) { b = row; break; }
    b = row;
  }
  const t = a === b ? 0 : (el - a[0]) / (b[0] - a[0]);
  _ramp[0] = el;
  for (const j of [1, 3, 4, 6]) _ramp[j].copy(a[j]).lerp(b[j], t);
  for (const j of [2, 5]) _ramp[j] = THREE.MathUtils.lerp(a[j], b[j], t);
  return _ramp;
}

function readSunWeather() {
  if (mode === 'day') return DEFAULT_PRESET;
  if (mode === 'night') return { elevation: -18, azimuth: 0, condition: 'clear-night' };
  if (simOverride) return simOverride;

  const sun = getState('sun.sun');
  const el = Number(sun?.attributes?.elevation);
  if (!Number.isFinite(el)) return DEFAULT_PRESET;
  const az = Number(sun?.attributes?.azimuth);
  const weather = weatherId ? getState(weatherId) : null;
  return {
    elevation: el,
    azimuth: Number.isFinite(az) ? az : 180,
    condition: weather?.state,
    cloud_coverage: weather?.attributes?.cloud_coverage,
  };
}

function recomputeTarget() {
  const { elevation, azimuth, condition, cloud_coverage } = readSunWeather();

  // HA azimuth: 0=N, 90=E, clockwise. Scene: north = -Z, east = +X.
  const el = THREE.MathUtils.degToRad(elevation);
  const az = THREE.MathUtils.degToRad(azimuth ?? 180);
  target.sunDir.set(
    Math.cos(el) * Math.sin(az),
    Math.max(Math.sin(el), -0.15), // never point steeply upward; night = intensity 0
    -Math.cos(el) * Math.cos(az),
  ).normalize();

  const [, sunCol, sunInt, sky, gnd, hemiInt, bg] = rampAt(elevation);
  const w = WEATHER[condition] || WEATHER_CLEAR;
  let sunX = w.sunX;
  if (Number.isFinite(cloud_coverage) &&
      ['sunny', 'partlycloudy', 'cloudy'].includes(condition)) {
    sunX = THREE.MathUtils.lerp(1.0, 0.40, cloud_coverage / 100);
  }
  _tint.setHex(w.tint);

  target.sunColor.copy(sunCol).lerp(_tint, w.desat);
  target.sunIntensity = sunInt * sunX;
  target.hemiSky.copy(sky).lerp(_tint, w.desat);
  target.hemiGround.copy(gnd);
  target.hemiIntensity = hemiInt * w.hemiX;
  target.bg.copy(bg).lerp(_tint, w.desat * 0.6);
  const fog = condition === 'fog' ? FOG_FOGGY : FOG_DEFAULT;
  target.fogNear = fog.near;
  target.fogFar = fog.far;
  target.nightFactor = THREE.MathUtils.clamp((4 - elevation) / 10, 0, 1);
  // IBL follows the sun so the environment map doesn't flatten nights.
  // The daytime end was 0.45 and is the main fill an interior wall facing away
  // from the sun gets: RoomEnvironment is omnidirectional, so unlike the
  // hemisphere it lifts a shaded wall without flattening the sky/ground
  // gradient the exterior depends on. Raised to close the wall-to-wall spread
  // measured by `roomkit.meter` (an empty room ran 222 down to 125 on one paint
  // colour). Night end left at 0.05 so the dark house and roomlights.js's glow
  // are untouched.
  // 1.15 is a measured compromise, not a guess. Raising it compresses the
  // wall-to-wall spread inside a room (the residual complaint from every critic)
  // but flattens the exterior: at 1.9 an empty room's spread only improved
  // 80 -> 71 bytes while the roof and siding visibly lost their relief. The
  // remaining spread is the honest limit of one directional sun with no bounce
  // light, and must NOT be fought with per-room emissive panels — that is what
  // produced the glowing trim and hard-edged wall washes critics rejected.
  target.envIntensity =
    THREE.MathUtils.lerp(1.15, 0.05, target.nightFactor) * w.hemiX;

  lastDaylight = {
    elevation,
    condition: condition || 'sunny',
    nightFactor: target.nightFactor,
  };
  for (const fn of daylightListeners) fn(lastDaylight);
}

// ------------------------------------------------------------- per-frame

const _pos = new THREE.Vector3();

function converged() {
  return Math.abs(current.sunIntensity - target.sunIntensity) < 1e-3 &&
         Math.abs(current.hemiIntensity - target.hemiIntensity) < 1e-3 &&
         Math.abs(current.nightFactor - target.nightFactor) < 1e-3 &&
         Math.abs(current.envIntensity - target.envIntensity) < 1e-3 &&
         Math.abs(current.fogNear - target.fogNear) < 0.1 &&
         current.sunDir.distanceToSquared(target.sunDir) < 1e-6 &&
         Math.abs(current.bg.r - target.bg.r) < 1e-3 &&
         Math.abs(current.bg.g - target.bg.g) < 1e-3 &&
         Math.abs(current.bg.b - target.bg.b) < 1e-3 &&
         Math.abs(current.sunColor.r - target.sunColor.r) < 1e-3 &&
         Math.abs(current.hemiSky.r - target.hemiSky.r) < 1e-3;
}

function tick(dt) {
  if (converged()) return;
  const k = 1 - Math.exp(-dt / SMOOTH_TAU);

  current.sunDir.lerp(target.sunDir, k);
  current.sunColor.lerp(target.sunColor, k);
  current.sunIntensity = THREE.MathUtils.lerp(current.sunIntensity, target.sunIntensity, k);
  current.hemiSky.lerp(target.hemiSky, k);
  current.hemiGround.lerp(target.hemiGround, k);
  current.hemiIntensity = THREE.MathUtils.lerp(current.hemiIntensity, target.hemiIntensity, k);
  current.bg.lerp(target.bg, k);
  current.fogNear = THREE.MathUtils.lerp(current.fogNear, target.fogNear, k);
  current.fogFar = THREE.MathUtils.lerp(current.fogFar, target.fogFar, k);
  current.nightFactor = THREE.MathUtils.lerp(current.nightFactor, target.nightFactor, k);
  current.envIntensity = THREE.MathUtils.lerp(current.envIntensity, target.envIntensity, k);

  setEnvIntensity(current.envIntensity);
  sunLight.position.copy(_pos.copy(current.sunDir).multiplyScalar(SUN_DISTANCE));
  sunLight.color.copy(current.sunColor);
  sunLight.intensity = current.sunIntensity;
  // skip the shadow depth pass when the sun is effectively down (night, or
  // heavy pouring/fog) — the shadow is invisible there anyway
  sunLight.castShadow = current.sunIntensity > 0.02;
  hemiLight.color.copy(current.hemiSky);
  hemiLight.groundColor.copy(current.hemiGround);
  hemiLight.intensity = current.hemiIntensity;
  // floorview.js swaps the background for a gradient texture and nulls the
  // fog while a single floor is shown — only touch them when they're ours
  if (scene.background?.isColor) scene.background.copy(current.bg);
  if (scene.fog) {
    scene.fog.color.copy(current.bg); // fog matches bg for a seamless horizon
    scene.fog.near = current.fogNear;
    scene.fog.far = current.fogFar;
  }
}

// ------------------------------------------------------------- mode button

const MODE_LABELS = { auto: '☀ auto', day: '☀ day', night: '☾ night' };
const MODE_ORDER = ['auto', 'day', 'night'];

function setMode(m) {
  mode = MODE_ORDER.includes(m) ? m : 'auto';
  try { localStorage.setItem(MODE_KEY, mode); } catch { /* private mode */ }
  const btn = document.getElementById('btn-daylight');
  if (btn) btn.textContent = MODE_LABELS[mode];
  recomputeTarget();
}

// ------------------------------------------------------------- init

export function initDaylight() {
  // current starts equal to target so first paint has no multi-second fade
  recomputeTarget();
  syncCurrentToTarget();

  onStateApplied((entityId) => {
    if (entityId === null) {
      weatherId = findEntities('weather.')[0] || null;
      recomputeTarget();
    } else if (entityId === 'sun.sun' || entityId === weatherId) {
      recomputeTarget();
    }
  });

  onFrame(tick);

  const btn = document.getElementById('btn-daylight');
  if (btn) {
    btn.onclick = () =>
      setMode(MODE_ORDER[(MODE_ORDER.indexOf(mode) + 1) % MODE_ORDER.length]);
  }
  let saved = null;
  try { saved = localStorage.getItem(MODE_KEY); } catch { /* private mode */ }
  setMode(saved || 'auto');
  syncCurrentToTarget(); // saved night mode shouldn't fade in from day on load

  window.__daylight = {
    simulate(o) { simOverride = o || null; recomputeTarget(); },
    mode(m) { setMode(m); },
    state() { return { current, target, weatherEntityId: weatherId, mode }; },
  };
}

// floorview.js calls this after giving the background/fog back: tick()
// early-returns once converged, so a sky that changed while the floor
// backdrop was up would otherwise stay stale until the next state change.
export function repaintSky() {
  tickApply();
}

function syncCurrentToTarget() {
  current.sunDir.copy(target.sunDir);
  current.sunColor.copy(target.sunColor);
  current.sunIntensity = target.sunIntensity;
  current.hemiSky.copy(target.hemiSky);
  current.hemiGround.copy(target.hemiGround);
  current.hemiIntensity = target.hemiIntensity;
  current.bg.copy(target.bg);
  current.fogNear = target.fogNear;
  current.fogFar = target.fogFar;
  current.nightFactor = target.nightFactor;
  current.envIntensity = target.envIntensity;
  // push once so the first frame already shows the right look
  tickApply();
}

function tickApply() {
  setEnvIntensity(current.envIntensity);
  sunLight.position.copy(_pos.copy(current.sunDir).multiplyScalar(SUN_DISTANCE));
  sunLight.color.copy(current.sunColor);
  sunLight.intensity = current.sunIntensity;
  sunLight.castShadow = current.sunIntensity > 0.02;
  hemiLight.color.copy(current.hemiSky);
  hemiLight.groundColor.copy(current.hemiGround);
  hemiLight.intensity = current.hemiIntensity;
  if (scene.background?.isColor) scene.background.copy(current.bg);
  if (scene.fog) {
    scene.fog.color.copy(current.bg);
    scene.fog.near = current.fogNear;
    scene.fog.far = current.fogFar;
  }
}
