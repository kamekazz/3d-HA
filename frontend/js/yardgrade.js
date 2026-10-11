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
import { getShellRoot } from './house.js';

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
  sunColor: new THREE.Color(0xffd7a6),   // the warmth lives in the light, below the shoulder
  sunIntensity: 2.9,   // stronger key, lower fill ratio (~0.25): sun vs shade must differ
  // Blue-violet sky fill at ~0.35-0.4 of the key: shade must stay a coloured
  // mid-tone (shaded hedges and the car's shadow were crushing to black at
  // 0.8). Shadow SHAPES stay crisp -- they come from the map, not the fill.
  hemiSky: new THREE.Color(0xb2c6e4),   // cyan-leaning blue: shade keeps chroma (blue-green on grass, light blue on walls), not grey-green or lilac   // blue-violet: cast shadows read cool, not neutral grey
  hemiGround: new THREE.Color(0x6a6250),   // dim bounce: walls get their brightness from the sun, not from every side // brighter warm bounce: shaded siding/roof keep colour instead of going muddy
  hemiIntensity: 1.05,   // shadow floor: lawn cast shadow ~60% of adjacent sun (measured)
  // Light sky-blue horizon = fog = background (warm pale/white read as milky
  // overcast). The fog is the distance haze: clear across the lot and its tree
  // ring, then the far ground melts into the horizon by the 1200 ft disc edge,
  // so there is no hard green-against-sky line.
  bg: new THREE.Color(0x80bde8),   // sky-blue, leaning cyan: the haze must never read lilac
  fogNear: 140,   // aerial perspective: far treeline and lake lift toward pale blue past the lot
  fogFar: 760,
  envIntensity: 0.25,  // of the SKY environment below, not RoomEnvironment   // RoomEnvironment is grey: it is what made shade murky
  exposure: 1.0,
  // A raking key: the sun is lowered to at most this elevation and swung this
  // far round, so shadows run long and diagonal across the lot instead of
  // pooling under things at a clinical noon. HA's sun still decides which side
  // of the house is lit; this only biases the angle.
  maxElevationDeg: 35,
  // ...except a sun in the northern sky (only ever forced by a test/simulate --
  // a real one never stands there at midday here) is RAISED to at least this:
  // the rear oak woodland stands north of the back lawn, and a low north sun
  // laid its leaf shadows over the whole back yard as dark pools.
  northMinElevationDeg: 55,
  // Swung TOWARD the east by up to this much, whichever way that is: the front
  // sun (az 155) goes to ~105 and the back sun (335) to ~25, so both the street
  // and the rear views see a lit face and a shaded face (a fixed +50 put the
  // back sun in the west and left every face the rear cameras see in shade).
  azimuthSwingDeg: 62,   // ~75 deg off the front/back camera axes for side light; deck stays out of the north treeline's shade (raycast-checked)
};
const ZENITH = new THREE.Color(0x1d58c6);
// Crisper sun shadows while graded: the same 2048 map over a tighter ortho
// frustum (the lot, not the 280 ft the viewer covers) -- ~0.1 ft per texel
// instead of ~0.14. No define changes, so no recompile; restored on close.
const SHADOW_HALF = 150;   // the lot plus the hero/backdrop trees around it
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
// Warm by pulling green/blue DOWN, never pushing red past 1: a red gain clipped
// first on lit siding and the warmth vanished into neutral grey-white.
const WB = [1.0, 0.975, 0.905];        // display-linear white balance multiplier
const SATURATION = 1.12;
const TOE_LIFT = 0.007;   // linear; round 6: 0.003 let lawn shadows go near-black
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

// A sky-tinted image-based light, swapped in for RoomEnvironment while graded.
// The house shell GLB is authored metalness 1, so it takes NO diffuse light
// from the hemisphere at all: everything a shaded wall or roof plane receives
// is the environment map. RoomEnvironment is a neutral grey studio, which is
// exactly why shaded siding read muddy grey and the roof went near-black no
// matter what the hemisphere did. This one is the Sims sky the critics keep
// asking for: blue-violet above, a pale bright horizon, warm sunlit-ground
// bounce below. Same PMREM size as scene.js's (256), so swapping the texture
// re-keys to the SAME programs -- no shader compile, just a uniform.
let skyEnv = null;
let envWas = null;
const envVS = `varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const envFS = `varying vec3 vDir;
  void main(){
    vec3 d = normalize(vDir);
    vec3 zen = vec3(0.42, 0.50, 0.88);
    vec3 hor = vec3(0.58, 0.62, 0.68);
    vec3 gnd = vec3(0.34, 0.30, 0.22);
    vec3 c = d.y >= 0.0 ? mix(hor, zen, pow(d.y, 0.6)) : mix(hor * 0.85, gnd, pow(-d.y, 0.4));
    gl_FragColor = vec4(c, 1.0);
  }`;
function getSkyEnv() {
  if (skyEnv) return skyEnv;
  const s = new THREE.Scene();
  const m = new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16),
    new THREE.ShaderMaterial({ vertexShader: envVS, fragmentShader: envFS, side: THREE.BackSide }));
  s.add(m);
  const pmrem = new THREE.PMREMGenerator(renderer);
  skyEnv = pmrem.fromScene(s, 0).texture;
  pmrem.dispose();
  m.geometry.dispose(); m.material.dispose();
  return skyEnv;
}
function setSkyEnv(on) {
  if (on) {
    if (envWas === null) envWas = scene.environment;
    scene.environment = getSkyEnv();
  } else if (envWas !== null) {
    scene.environment = envWas;
    envWas = null;
  }
}

// The house shell GLB is authored metalness 1 / roughness 1 on every material
// (no metalness/roughness maps -- checked), so it took no Lambert term from the
// sun at all: no lit face vs shaded face, just env-map light from every side.
// While graded its metallic materials are made dielectric. metalness and
// roughness are plain uniforms here (no maps), so this re-keys no program.
// Originals are kept per material and put back when the grade turns off, and
// for snapshots.js's room cards (suspendYardGrade). A reloadHouse hands out a
// fresh shell clone, so tick() re-applies when the shell root changes.
const SHELL_ROUGHNESS = 0.85;
// ...and their albedo scaled down a little: white siding at full albedo hit the
// tone curve's shoulder in sun AND in the fill alone, so lit and shaded faces
// both clipped to the same flat white. Headroom is what lets the sun model it.
const SHELL_ALBEDO = 0.72;
const shellOrig = new Map();   // material -> [metalness, roughness]
let shellRootSeen = null;
function setShellDielectric(on) {
  if (on) {
    const root = getShellRoot?.();
    shellRootSeen = root || null;
    if (!root) return;
    root.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of [].concat(o.material)) {
        if (!m || !m.isMeshStandardMaterial || shellOrig.has(m) || m.metalness < 0.5
            || m.metalnessMap || m.roughnessMap) continue;
        shellOrig.set(m, [m.metalness, m.roughness, m.color.clone()]);
        m.metalness = 0;
        m.roughness = SHELL_ROUGHNESS;
        m.color.multiplyScalar(SHELL_ALBEDO);
      }
    });
  } else {
    for (const [m, [met, rough, col]] of shellOrig) { m.metalness = met; m.roughness = rough; m.color.copy(col); }
    shellOrig.clear();
    shellRootSeen = null;
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
    let elT = Math.min(el, THREE.MathUtils.degToRad(G.maxElevationDeg));
    if (d.z < 0) {   // north half of the sky (scene north = -Z)
      const north = THREE.MathUtils.clamp(-d.z / h, 0, 1);
      elT = Math.max(elT, THREE.MathUtils.degToRad(G.northMinElevationDeg) * north);
    }
    const el2 = L(el, elT, k);
    const th = Math.atan2(d.x, d.z);   // = PI - HA azimuth; east (az 90) is th = PI/2
    let toEast = Math.PI / 2 - th;
    toEast = Math.atan2(Math.sin(toEast), Math.cos(toEast));   // wrap to (-PI, PI]
    const swing = Math.sign(toEast) * Math.min(Math.abs(toEast), THREE.MathUtils.degToRad(G.azimuthSwingDeg));
    const az = th + swing * k;
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
      float c = smoothstep(0.50, 0.60, n) * smoothstep(0.0, 0.05, d.y) * cloudAmt * 0.9;
      // lit tops, slightly blue-grey bellies: read as puffy, not as fog
      float top = smoothstep(0.5, 0.8, fbm(p * 1.3 + vec2(0.4, 1.9)));
      vec3 cloud = mix(horizon * 0.85 + vec3(0.05, 0.06, 0.10), vec3(1.15, 1.12, 1.05), 0.6 + 0.4 * top);
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
  if (getShellRoot?.() !== shellRootSeen) setShellDielectric(true);
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
    setSkyEnv(true);
    setShellDielectric(true);
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
    setSkyEnv(false);
    setShellDielectric(false);
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
  const env = scene.environment;
  if (envWas !== null) scene.environment = envWas;   // cards keep the studio IBL
  const shell = [...shellOrig];   // cards render the shell as authored
  for (const [m, [met, rough, col]] of shell) { m.metalness = met; m.roughness = rough; m.color.copy(col); }
  return () => {
    renderer.toneMappingExposure = exp; scene.environment = env;
    for (const [m, [, , col]] of shell) {
      m.metalness = 0; m.roughness = SHELL_ROUGHNESS; m.color.copy(col).multiplyScalar(SHELL_ALBEDO);
    }
  };
}

// console tuning: __yardgrade.G.sunIntensity = 4; __yardgrade.refresh()
window.__yardgrade = { G, refresh() { if (active) setDaylightGrade(grade); } };
