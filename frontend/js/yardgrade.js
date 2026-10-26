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
import { scene, renderer, onFrame, setExposureBase, camera, sunLight, setOpticsMoon } from './scene.js';
import { setDaylightGrade, getGradeWeight } from './daylight.js';
import { getShellRoot } from './house.js';
import { ISLAND } from './island.js';

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
  sunIntensity: 3.3,   // stronger key, lower fill ratio (~0.25): sun vs shade must differ
  // Blue-violet sky fill at ~0.35-0.4 of the key: shade must stay a coloured
  // mid-tone (shaded hedges and the car's shadow were crushing to black at
  // 0.8). Shadow SHAPES stay crisp -- they come from the map, not the fill.
  hemiSky: new THREE.Color(0xa2d0de),   // cyan-leaning blue: shade keeps chroma (blue-green on grass, light blue on walls), not grey-green or lilac   // blue-violet: cast shadows read cool, not neutral grey
  hemiGround: new THREE.Color(0x45402f),   // dim bounce: walls get their brightness from the sun, not from every side // brighter warm bounce: shaded siding/roof keep colour instead of going muddy
  hemiIntensity: 1.6,   // shadow floor: lawn cast shadow ~60% of adjacent sun (measured)
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
const SATURATION = 1.22;   // round 11: the lawn measured S 0.76 vs Sims 0.85-0.92 with its blue already at ~0
const TOE_LIFT = 0.0035;   // linear; round 11: 0.007 floored every blue at sRGB 20, capping lawn S at ~0.8 (Sims 0.85-0.92); shade lift is the light builder's fill now
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
const SHELL_ALBEDO = 0.6;
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

// "Sims night": the same yard under a full moon (2026-10-18; bar: EA's own
// lunar-cycle screenshot, scratchpad/moon/ref). The iPhone-photo night in
// daylight.js's ramp (black sky, the house lit only by its own LEDs) stays the
// night everywhere the yard is not shown; while it is, the exterior gets a
// cool key from a fixed moon, a blue sky fill, a navy horizon the fog melts
// into, and the dome below draws the moon, stars and moonlit cloud. The moon
// is scene-fixed (HA knows the sun, not the moon) and hangs ~30 deg up in the
// north-east, so it is in frame from the street side (the view looks north)
// and the roof planes and east faces take the key.
const N = {
  // The KEY and the DISC are two directions on purpose, as in the Sims itself:
  // a key in frame lights the faces turned away from you, and the view that
  // matters looks north from the street. The key comes from the south-east,
  // ~40 deg up, so the street-facing pitches and the east faces take it and
  // the west faces fall to the fill; the disc hangs low (~16 deg) in the
  // north-east, inside what the orbit's polar clamp (controls.maxPolarAngle,
  // ~2 deg above level, 55 deg fov) can ever frame.
  moonDir: new THREE.Vector3(0.68, 0.60, 0.42).normalize(),   // ESE, ~36 deg: the shadow falls WNW, beside the house from the street
  moonSkyDir: new THREE.Vector3(0.60, 0.36, -0.72).normalize(),   // ~21 deg up, az ~40: clear of the gable ridge and the east oak from the front lawn
  moonColor: new THREE.Color(0xb9c7e6),   // cool, low chroma: a bluer counterpoint to the amber bulbs, short of round-1's gel
  moonIntensity: 0.8,                     // the Sims' moonlit white siding is L~71 sRGB; lit:shaded must model the pitches (1.0 read near-white, round 2)
  hemiSky: new THREE.Color(0x3f5490),     // blue sky fill: shade stays a navy mid-tone, not black
  hemiGround: new THREE.Color(0x0e1018),
  hemiIntensity: 0.28,                    // ~1/3 of the key: at 0.55 the fill flattened every pitch to one grey (round-3 critic)
  bg: new THREE.Color(0x2a3560),          // horizon/fog: the reference's cloud band is (40,47,78)
  zenith: new THREE.Color(0x121a3a),      // (21,25,45) in the reference, read through ACES
  fogNear: 220,
  fogFar: 900,
  envIntensity: 0.06,                     // the day sky IBL, dimmed: a touch of blue on every face
  cloud: 0.85,                            // moonlit cumulus coverage, weather or not (the Sims night is never a bare sky)
};
let nightW = 0;   // how much of N is applied right now (0 by day; the dome reads it)
export function getMoonWeight() { return nightW; }

// The island's void (island.js): no horizon, no haze -- the lot floats in a
// deep navy that glows faintly behind it and falls away to near-black at the
// frame's edges, as in the diorama references. Fog is pushed past anything
// the camera can frame (it stays a Fog, not null: fog is a program define).
const VOID = {
  // r4: measured against reference 1's void through the tone curve -- its
  // corners are sRGB ~(5,19,45) and behind the island ~(12,36,70); r3's
  // corners came out (2,4,12), "a flat blue-black the soil melts into"
  // r5: more vignette (r4: "flat, no vignette"); r6: darker and gentler
  // again (r5: "a saturated mid-blue radial blob")
  centre: new THREE.Color(0.0085, 0.028, 0.080),   // linear, before the tone curve
  edge: new THREE.Color(0.0032, 0.013, 0.040),
  fogNear: 2400, fogFar: 4000,
};
function grade(t, sun) {
  const k = gradeSky(t, sun);
  if (ISLAND && nightW > 0) {
    // the island's night is reference 1's dusk: a brighter blue fill so the
    // lawn and the tree ring stay readable (r4: "the island reads as a dark mass")
    t.hemiIntensity = THREE.MathUtils.lerp(t.hemiIntensity, 0.5, nightW);
  }
  if (ISLAND) {
    t.bg.copy(VOID.edge);
    t.fogNear = VOID.fogNear;
    t.fogFar = VOID.fogFar;
  }
  return k;
}
function gradeSky(t, { elevation, sunX }) {
  const day = THREE.MathUtils.smoothstep(elevation, 3, 22);
  const clear = THREE.MathUtils.clamp((sunX - 0.3) / 0.7, 0, 1);
  const k = day * clear;
  const L = THREE.MathUtils.lerp;
  // Night: the moon takes over once the sun is well down (-4..-12 deg), so
  // dusk still runs the ramp's own colours. Cloud (sunX) dims the moon's key
  // but not the sky fill: an overcast night is flatter, not blacker.
  nightW = THREE.MathUtils.smoothstep(-elevation, 4, 12);
  if (nightW > 0) {
    const n = nightW, moonK = n * L(0.35, 1, clear);
    t.sunDir.lerp(N.moonDir, n).normalize();
    t.sunColor.lerp(N.moonColor, n);
    t.sunIntensity = L(t.sunIntensity, N.moonIntensity, moonK);
    t.hemiSky.lerp(N.hemiSky, n);
    t.hemiGround.lerp(N.hemiGround, n);
    t.hemiIntensity = L(t.hemiIntensity, N.hemiIntensity, n);
    t.bg.lerp(N.bg, n);
    t.fogNear = L(t.fogNear, N.fogNear, n);
    t.fogFar = L(t.fogFar, N.fogFar, n);
    t.envIntensity = L(t.envIntensity, N.envIntensity, n);
  }
  if (k <= 0) return 0;
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
  uniform float voidAmt;
  uniform vec3 voidCentre;
  uniform vec3 voidEdge;
  uniform vec3 camFwd;
  varying vec3 vDir;
  float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float n2(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x),
               mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
  }
  float fbm(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { s += a * n2(p); p = p * 2.03 + vec2(7.1, 3.3); a *= 0.5; }
    return s;
  }
  // --- night: moon, stars, moonlit cloud ---
  uniform float night;
  uniform vec3 moonDir;
  uniform vec3 nightZenith;
  uniform float cloudNight;
  vec3 nightSky(vec3 d, vec3 hor) {
    float h = max(d.y, 0.0);
    // steeper than the day dome: the reference's zenith is half the value of
    // its horizon band, and a flat navy read as a void (round-3 critic)
    vec3 col = mix(hor, nightZenith, pow(smoothstep(0.0, 0.6, h), 0.7));   // near-black by ~35 deg, lighter slate at the horizon
    // stars: one per cell of a lat/long grid, a few percent of cells lit,
    // point-sized, fading out in the haze near the horizon
    if (d.y > 0.02) {
      vec2 sc = vec2(atan(d.z, d.x) * 28.0, asin(clamp(d.y, -1.0, 1.0)) * 28.0);
      vec2 cell = floor(sc);
      float r = h21(cell);
      if (r > 0.9) {
        vec2 off = vec2(h21(cell + 3.7), h21(cell + 9.1)) * 0.6 + 0.2;
        float dist = length(fract(sc) - off);
        float s = smoothstep(0.045, 0.0, dist) * (0.35 + 0.65 * h21(cell + 1.3));
        col += vec3(0.85, 0.9, 1.0) * s * smoothstep(0.03, 0.2, d.y) * 1.2;
      }
    }
    // the moon: a full disc ~5 deg across (the reference's is big) with limb
    // darkening and faint maria, held UNDER the night composer's bloom
    // threshold so its edge stays crisp (round 3: a blown disc read as an
    // edgeless bloom), and a wide faint halo the cloud edges catch
    float m = dot(d, moonDir);
    vec3 mu = normalize(cross(moonDir, vec3(0.0, 1.0, 0.0)));
    vec3 mv = cross(mu, moonDir);
    vec2 q = vec2(dot(d, mu), dot(d, mv)) / 0.0454;   // disc-local, radius 1 (~2.6 deg: round 12 read twice the reference's size)
    float qr = length(q);
    float disc = 1.0 - smoothstep(0.975, 1.015, qr);
    float limb = 0.45 + 0.55 * sqrt(max(0.0, 1.0 - qr * qr));
    float maria = 1.0 - 0.5 * smoothstep(0.46, 0.62, fbm(q * 1.9 + vec2(4.2, 1.7)));
    // a touch past full (waxing gibbous, ~90% lit): a soft terminator down the
    // west limb is what makes a disc read as a sphere at thumbnail size
    float term = 1.0 - 0.88 * smoothstep(0.05, 0.55, -q.x);   // a decisive gibbous terminator: the reference's moon is half-lit
    vec3 moonCol = vec3(0.88, 0.89, 0.92) * limb * maria * term;   // off ACES's shoulder, so maria and limb keep their contrast (round 8: a pasted white disc)
    float halo = pow(max(m, 0.0), 1400.0) * 0.10 + pow(max(m, 0.0), 80.0) * 0.012;   // barely there: the limb must sit on clean navy (round 12)
    col += vec3(0.55, 0.6, 0.72) * halo;
    // moonlit cumulus in two layers (near big masses, far small ones), lit
    // where the density falls off toward the moon and shadowed where it
    // thickens away from it: lit tops and dark bellies, not flat streaks
    if (cloudNight > 0.001 && d.y > 0.0) {
      vec3 belly = nightZenith * 0.42;                 // bellies darker than the sky behind them
      vec3 litC = vec3(0.30, 0.33, 0.47);   // lilac-grey tops at the reference's cloud-band value (L~48), well under the moon
      float rim = pow(max(m, 0.0), 5.0);
      // Mercator: locally isotropic, so a mass is the same round shape at
      // the zenith as near the horizon (the planar map stretched the low sky
      // into streaks and smeared the high sky into one blob -- round 4)
      float elev = asin(clamp(d.y, 0.0, 0.985));
      vec2 merc = vec2(atan(d.z, d.x), log(tan(elev * 0.5 + 0.7854)));
      for (int k = 0; k < 2; k++) {
        float sc = k == 0 ? 3.2 : 7.0;   // finest octave ~0.5 deg: edges resolve at ~5 px, not 20
        vec2 p = merc * sc + (k == 0 ? vec2(3.0, 11.0) : vec2(27.0, 5.0));
        float n = fbm(p);
        n += 0.04 * (abs(n2(p * 7.0 + vec2(1.3, 8.8)) - 0.5) * 2.0 - 0.5);   // cauliflower edge detail: value noise alone is airbrushed
        n += 0.07 * (n2(p * 3.3 + vec2(5.5, 2.1)) - 0.5);                      // lobes: a mass breaks into puffs instead of one smudge
        float lo = k == 0 ? 0.46 : 0.51;   // a deck with gaps, not blobs on a void (round 8)
        float c = smoothstep(lo, lo + 0.05, n) * smoothstep(0.0, 0.14, d.y) * cloudNight * (k == 0 ? 1.0 : 0.75);   // feathered rims (round 9: hard edges read as cardboard); thins toward the horizon
        c *= 1.0 - 0.97 * pow(max(m, 0.0), 12.0);   // a wide clearing round the moon: the disc must not touch lit cloud (round 7)
        // Shaded like a surface: the density gradient is a pseudo-normal
        // (normal = toward thinner air), lit from above and the moon's side,
        // so every mass gets a lit rim on top and a dark underside, whatever
        // its shape (rounds 8-10: a one-sided density step lit only one edge)
        vec2 e = vec2(0.035, 0.0);
        vec2 g = vec2(fbm(p + e.xy) - fbm(p - e.xy), fbm(p + e.yx) - fbm(p - e.yx)) / (2.0 * e.x);
        vec2 L2 = normalize(vec2(0.45, 1.0));
        float shade = smoothstep(-0.9, 1.1, dot(-g, L2));
        float thick = smoothstep(lo, lo + 0.20, n);             // deep in the mass = dark belly
        vec3 cc = mix(belly, litC + vec3(0.22, 0.22, 0.24) * rim, clamp(shade * (1.0 - 0.7 * thick) + 0.04, 0.0, 1.0));
        float edge = smoothstep(0.0, 0.45, c) * (1.0 - smoothstep(0.45, 1.0, c));
        cc += vec3(0.14, 0.15, 0.18) * edge * shade * (0.3 + 0.7 * rim);   // the lit edge is nearest the moon, faint elsewhere
        col = mix(col, cc, c);
        disc *= 1.0 - c * 0.85;   // cloud in front of the moon
      }
    }
    col = mix(col, moonCol, disc);
    return col;
  }
  void main() {
    vec3 d = normalize(vDir);
    if (voidAmt > 0.5) {
      // radial, about the view axis: a soft glow behind the island
      float c = smoothstep(0.30, 1.0, dot(d, camFwd));
      vec3 col = mix(voidEdge, voidCentre, c * c);
      // a whisper of grain so the gradient never bands on an 8-bit panel
      col *= 1.0 + (h21(gl_FragCoord.xy) - 0.5) * 0.10;   // dither: r5 saw banding
      gl_FragColor = vec4(col, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
      return;
    }
    float h = max(d.y, 0.0);
    vec3 col = mix(horizon, zenith, pow(smoothstep(0.0, 0.16, h), 0.6));
    if (night > 0.001) {
      gl_FragColor = vec4(mix(col, nightSky(d, horizon), night), 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
      return;
    }
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
    night: { value: 0 },
    moonDir: { value: N.moonSkyDir.clone() },
    nightZenith: { value: N.zenith.clone() },
    cloudNight: { value: 0 },
    voidAmt: { value: ISLAND ? 1 : 0 },
    voidCentre: { value: VOID.centre.clone() },
    voidEdge: { value: VOID.edge.clone() },
    camFwd: { value: new THREE.Vector3(0, 0, -1) },
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
  setOpticsMoon(nightW);
  if (!dome) return;
  const bg = scene.background?.isColor ? scene.background : null;
  dome.visible = !!bg && (ISLAND || w > 0.01 || nightW > 0.01);
  if (!dome.visible) return;
  const u = dome.material.uniforms;
  camera.getWorldDirection(u.camFwd.value);
  // the day curve (contrast + saturation, exposure 1.0) lifts the void far more
  // than night's plain ACES through the composer: r4's day void read royal blue
  const vk = 1 - 0.5 * w;
  u.voidCentre.value.copy(VOID.centre).multiplyScalar(vk);
  u.voidEdge.value.copy(VOID.edge).multiplyScalar(vk);
  u.horizon.value.copy(bg);
  // without the grade the zenith is just a deeper take on HA's own sky colour
  _z.copy(bg).multiplyScalar(0.7);
  u.zenith.value.copy(_z).lerp(ZENITH, w);
  u.cloudAmt.value = w;
  u.night.value = nightW;
  u.moonDir.value.copy(N.moonSkyDir);
  u.nightZenith.value.copy(N.zenith);
  u.cloudNight.value = N.cloud;
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
window.__yardgrade = { G, N, VOID, refresh() { if (active) setDaylightGrade(grade); } };
