// "Sims day": the lighting and colour grade the outside gets whenever the
// generated yard is on screen, and ONLY then. Since 2026-10-11 that is the
// viewer's House level too (view and edit mode), not just the Outside editor:
// environment.js calls setYardGrade(true, root) when the yard becomes visible
// (applyVisibility -- a yard is standing and the level is 'all') and
// setYardGrade(false) when it stops being visible (a single floor, room focus);
// every global this touches is put back exactly then, so floor views and every
// interior render as they always have. snapshots.js brackets its room-card
// render with suspendYardGrade().
//
// What it changes, and why each is cheap enough for a phone:
//   - daylight.js's resolved target (sun colour/intensity, hemisphere sky and
//     ground, background+fog colour and distance, IBL), via setDaylightGrade.
//     All uniforms, no light added or removed, so no shader recompiles.
//   - the resting tone-mapping exposure (scene.js setExposureBase), a uniform.
//   - a gradient sky dome with soft cumulus, parented to the environment root
//     (so it shows exactly when the yard does), drawn at background depth so
//     every surface occludes it. One draw call; the fbm runs only on sky pixels.
//   - the viewer's dark ground plane and the edit grid are hidden through
//     their MATERIAL's visible flag, not the object's, so this never fights
//     the appModeChanged / snapshots.js writers of object.visible.
//
// The grade is weighted by how high the sun is and how clear HA says it is:
// a rainy evening in the editor is still a rainy evening, only a clear day is
// pushed all the way to the bright, saturated build-mode midday.
import * as THREE from 'three';
import { scene, renderer, onFrame, setExposureBase, camera, sunLight } from './scene.js';
import { setDaylightGrade, getGradeWeight } from './daylight.js';

// Target values at full weight. Picked against the Sims 4 bar shots through
// this renderer's ACES + exposure, not by eye on the hex.
const G = {
  // A golden, strong key against a cool, weaker fill is what gives the Sims
  // midday its contrast: sun-kissed roofs and paving, and cast shadows that
  // read blue-violet because the only light reaching them is the blue sky.
  // Near-white with a warm cast: white siding must stay white with warm
  // highlights (0xffe4b8 read it as tan).
  // ~5200 K: warm enough for yellow-green sunlit canopies, not so warm the
  // siding turns tan.
  sunColor: new THREE.Color(0xffe8cc),
  sunIntensity: 4.6,   // stronger key, lower fill ratio (~0.25): sun vs shade must differ
  // Blue-violet sky fill at ~0.35-0.4 of the key: shade must stay a coloured
  // mid-tone (shaded hedges and the car's shadow were crushing to black at
  // 0.8). Shadow SHAPES stay crisp -- they come from the map, not the fill.
  hemiSky: new THREE.Color(0xa6bdf6),   // clean light-blue shade, not murky grey
  hemiGround: new THREE.Color(0x8f8c55), // warm yellow-green bounce under canopies
  hemiIntensity: 1.3,
  // Light sky-blue horizon = fog = background (warm pale/white read as milky
  // overcast). The fog is the distance haze: clear across the lot and its tree
  // ring, then the far ground melts into the horizon by the 1200 ft disc edge,
  // so there is no hard green-against-sky line.
  bg: new THREE.Color(0x9fcaf2),
  fogNear: 650,   // haze is a thin band at the horizon only; trees keep their colour
  fogFar: 1300,
  envIntensity: 0.25,   // RoomEnvironment is grey: it is what made shade murky
  exposure: 1.0,
  // A raking key: the sun is lowered to at most this elevation and swung this
  // far round, so shadows run long and diagonal across the lot instead of
  // pooling under things at a clinical noon. HA's sun still decides which side
  // of the house is lit; this only biases the angle.
  maxElevationDeg: 33,
  azimuthSwingDeg: 50,   // ~75 deg off the front/back camera axes for side light; deck stays out of the north treeline's shade (raycast-checked)
};
const ZENITH = new THREE.Color(0x2763cc);
// Crisper sun shadows while graded: the same 2048 map over a tighter ortho
// frustum (the lot, not the 280 ft the viewer covers) -- ~0.1 ft per texel
// instead of ~0.14. No define changes, so no recompile; restored on close.
const SHADOW_HALF = 100;
const BASE_EXPOSURE = 1.15;   // scene.js default; restored on close

// The grade's tone curve: three's own ACES (so the exposure response is the one
// every number above was tuned through) followed by a saturation lift and a
// small toe lift. ACES pulls everything toward grey as it rolls off; the Sims
// look is the opposite, clean and saturated with no murky blacks. It is
// installed as three's CustomToneMapping, which nothing else in the app uses,
// so swapping renderer.toneMapping to it while the editor is open is the gate.
// That swap changes every visible material's program key -- a one-time compile
// on open and on close, never a per-frame cost -- and it is only made by day:
// at night the optics composer's OutputPass knows nothing of a custom curve.
// 1.32 overcooked the lawn into fluorescent lime and clipped its shadows to
// pure green paint (blind critic, lawn round 1); 1.12 keeps the clean read.
const CONTRAST = 0.38;                 // 0 = plain ACES, 1 = full smoothstep S-curve
const WB = [1.035, 1.0, 0.94];         // display-linear white balance multiplier
const SATURATION = 1.12;
const TOE_LIFT = 0.003;   // linear; small: the Sims bar's lawn shade measures ~[15,45,5], blue near 0
{
  const stock = 'vec3 CustomToneMapping( vec3 color ) { return color; }';
  const chunk = THREE.ShaderChunk.tonemapping_pars_fragment;
  if (chunk.includes(stock)) {
    THREE.ShaderChunk.tonemapping_pars_fragment = chunk.replace(stock, `
vec3 CustomToneMapping( vec3 color ) {
  // A NEGATIVE exposure means "plain ACES at -exposure" (suspendYardGrade,
  // for snapshots.js's room cards): ACES multiplies by the exposure uniform,
  // so negating the colour too lands exactly on stock ACES -- without the
  // renderer.toneMapping swap that would recompile every program twice.
  if ( toneMappingExposure < 0.0 ) return ACESFilmicToneMapping( -color );
  vec3 c = ACESFilmicToneMapping( color );
  // Contrast S-curve on LUMINANCE only, in display (~gamma 2.2) space: ACES
  // leaves the frame in one mid-value band, Sims is punchy sRGB. Scaling rgb
  // by the luminance ratio keeps hue and saturation exactly where they were,
  // so SATURATION and TOE_LIFT below mean what they meant before this.
  float l0 = max( dot( c, vec3( 0.2126, 0.7152, 0.0722 ) ), 1e-5 );
  float g = pow( l0, 1.0 / 2.2 );
  g = mix( g, g * g * ( 3.0 - 2.0 * g ), ${CONTRAST.toFixed(3)} );
  c *= pow( g, 2.2 ) / l0;
  // warm white balance: whites go cream, not cold
  c *= vec3( ${WB.map((v) => v.toFixed(3)).join(', ')} );
  float l = dot( c, vec3( 0.2126, 0.7152, 0.0722 ) );
  c = max( mix( vec3( l ), c, ${SATURATION.toFixed(3)} ), 0.0 );
  c = ${TOE_LIFT.toFixed(4)} + ( 1.0 - ${TOE_LIFT.toFixed(4)} ) * c;
  return saturate( c );
}`);
  }
}

let active = false;
let dome = null;
let lastWeight = -1;
let groundMat = null, gridMat = null;
let groundWas = true, gridWas = true;
let shadowWas = null;

function setShadowFrustum(on) {
  const cam = sunLight?.shadow?.camera;
  if (!cam) return;
  if (on) {
    if (!shadowWas) shadowWas = { l: cam.left, r: cam.right, t: cam.top, b: cam.bottom };
    cam.left = cam.bottom = -SHADOW_HALF; cam.right = cam.top = SHADOW_HALF;
  } else if (shadowWas) {
    cam.left = shadowWas.l; cam.right = shadowWas.r; cam.top = shadowWas.t; cam.bottom = shadowWas.b;
    shadowWas = null;
  } else return;
  cam.updateProjectionMatrix();
}

function grade(t, { elevation, sunX }) {
  const day = THREE.MathUtils.smoothstep(elevation, 3, 22);
  const clear = THREE.MathUtils.clamp((sunX - 0.3) / 0.7, 0, 1);
  const k = day * clear;
  if (k <= 0) return 0;
  const L = THREE.MathUtils.lerp;
  const d = t.sunDir, h = Math.hypot(d.x, d.z);
  if (h > 1e-4) {
    const el = Math.asin(THREE.MathUtils.clamp(d.y, -1, 1));
    const el2 = L(el, Math.min(el, THREE.MathUtils.degToRad(G.maxElevationDeg)), k);
    const az = Math.atan2(d.x, d.z) + THREE.MathUtils.degToRad(G.azimuthSwingDeg) * k;
    d.set(Math.cos(el2) * Math.sin(az), Math.sin(el2), Math.cos(el2) * Math.cos(az)).normalize();
  }
  t.sunColor.lerp(G.sunColor, k);
  t.sunIntensity = L(t.sunIntensity, G.sunIntensity, k);
  t.hemiSky.lerp(G.hemiSky, k);
  t.hemiGround.lerp(G.hemiGround, k);
  t.hemiIntensity = L(t.hemiIntensity, G.hemiIntensity, k);
  t.bg.lerp(G.bg, k);
  t.fogNear = L(t.fogNear, G.fogNear, k);
  t.fogFar = L(t.fogFar, G.fogFar, k);
  t.envIntensity = L(t.envIntensity, G.envIntensity, k);
  return k;
}

const vertexShader = `
  varying vec3 vDir;
  void main() {
    vDir = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    gl_Position.z = gl_Position.w * 0.99999;   // background depth
  }`;
const fragmentShader = `
  uniform vec3 zenith;
  uniform vec3 horizon;
  uniform float cloudAmt;
  varying vec3 vDir;
  float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float n2(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x),
               mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
  }
  float fbm(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) { s += a * n2(p); p = p * 2.03 + vec2(7.1, 3.3); a *= 0.5; }
    return s;
  }
  void main() {
    vec3 d = normalize(vDir);
    float h = max(d.y, 0.0);
    vec3 col = mix(horizon, zenith, pow(smoothstep(0.0, 0.16, h), 0.6));
    if (cloudAmt > 0.001 && d.y > 0.0) {
      vec2 p = d.xz / (d.y + 0.25) * 4.5;
      float n = fbm(p + vec2(3.0, 11.0));
      float c = smoothstep(0.55, 0.64, n) * smoothstep(0.0, 0.05, d.y) * cloudAmt * 0.9;
      // lit tops, slightly blue-grey bellies: read as puffy, not as fog
      float top = smoothstep(0.5, 0.8, fbm(p * 1.3 + vec2(0.4, 1.9)));
      vec3 cloud = mix(horizon * 0.92 + vec3(0.02, 0.03, 0.06), vec3(1.0), 0.55 + 0.45 * top);
      col = mix(col, cloud, c);
    }
    gl_FragColor = vec4(col, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
  }`;

function makeDome() {
  const uniforms = {
    zenith: { value: new THREE.Color() },
    horizon: { value: new THREE.Color() },
    cloudAmt: { value: 0 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms, vertexShader, fragmentShader,
    side: THREE.BackSide, depthWrite: false, depthTest: true, fog: false,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(1000, 32, 16), mat);
  m.name = 'yard-sky-dome';
  m.frustumCulled = false;
  m.renderOrder = -2000;
  m.raycast = () => {};      // never pickable
  m.onBeforeRender = () => { m.position.copy(camera.position); m.updateMatrixWorld(); };
  return m;
}

const _z = new THREE.Color();
function tick() {
  if (!active) return;
  const w = getGradeWeight();
  if (w !== lastWeight) {
    lastWeight = w;
    setExposureBase(THREE.MathUtils.lerp(BASE_EXPOSURE, G.exposure, w));
    setCurve(w > 0.01);
  }
  if (!dome) return;
  const bg = scene.background?.isColor ? scene.background : null;
  dome.visible = !!bg && w > 0.01;
  if (!dome.visible) return;
  const u = dome.material.uniforms;
  u.horizon.value.copy(bg);
  // without the grade the zenith is just a deeper take on HA's own sky colour
  _z.copy(bg).multiplyScalar(0.7);
  u.zenith.value.copy(_z).lerp(ZENITH, w);
  u.cloudAmt.value = w;
}

function setCurve(graded) {
  const want = graded ? THREE.CustomToneMapping : THREE.ACESFilmicToneMapping;
  if (renderer.toneMapping !== want) renderer.toneMapping = want;
}

let ticking = false;
export function setYardGrade(on, parent) {
  on = !!on;
  if (on === active) return;
  active = on;
  if (!ticking) { onFrame(tick); ticking = true; }
  const ground = scene.getObjectByName('ground');
  const grid = scene.getObjectByName('editGrid');
  if (on) {
    groundMat = ground?.material || null;
    gridMat = grid?.material || null;
    if (groundMat) { groundWas = groundMat.visible; groundMat.visible = false; }
    if (gridMat) { gridWas = gridMat.visible; gridMat.visible = false; }
    if (!dome) dome = makeDome();
    if (parent && dome.parent !== parent) parent.add(dome);
    lastWeight = -1;
    setShadowFrustum(true);
    setDaylightGrade(grade);
    tick();
  } else {
    if (groundMat) groundMat.visible = groundWas;
    if (gridMat) gridMat.visible = gridWas;
    groundMat = gridMat = null;
    if (dome?.parent) dome.parent.remove(dome);
    setDaylightGrade(null);
    setExposureBase(BASE_EXPOSURE);
    setCurve(false);
    setShadowFrustum(false);
    lastWeight = -1;
  }
}

export function isYardGraded() { return active; }

// Which tone curve the grade WOULD pick right now (it is weighted by sun
// elevation and weather), without turning it on: environment.js warms that
// curve's shader programs first, before the yard is first shown. The weight is
// only computed inside daylight.js's target pass, so the grade is set and
// cleared again synchronously (daylight snaps its eased values to target once).
export function predictGradeCurve() {
  if (active) return renderer.toneMapping;
  setDaylightGrade(grade);
  const w = getGradeWeight();
  setDaylightGrade(null);
  return w > 0.01 ? THREE.CustomToneMapping : THREE.ACESFilmicToneMapping;
}

// snapshots.js: room cards are persisted by geometry hash, so the grade must
// never be baked into one. Puts the ungraded tone curve and resting exposure
// in place for one synchronous render; returns the restore. Uniforms only, no
// program change. A no-op while the grade is off. (The capture sets its own
// sun/hemi intensities and backdrop; the light COLOURS keep the graded tint,
// as they always kept the live time-of-day tint.)
export function suspendYardGrade() {
  if (!active) return () => {};
  const exp = renderer.toneMappingExposure;
  const custom = renderer.toneMapping === THREE.CustomToneMapping;
  renderer.toneMappingExposure = custom ? -BASE_EXPOSURE : BASE_EXPOSURE;
  return () => { renderer.toneMappingExposure = exp; };
}

// console tuning: __yardgrade.G.sunIntensity = 4; __yardgrade.refresh()
window.__yardgrade = { G, refresh() { if (active) setDaylightGrade(grade); } };
