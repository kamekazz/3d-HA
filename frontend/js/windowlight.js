// Windows follow the sun. Every window GLB in this house fakes "bright daylight
// outside" with emissive materials -- the master bedroom's `win_glass` is
// emissiveFactor 0.98 with KHR_materials_emissive_strength 3.4, and the Dining
// bay (model 122) paints a whole emissive outdoor scene across skyhi / skymid /
// wtrees / wrail / wlawn. That is deliberate and it is what makes a window read
// as "outdoors" at noon; nothing scaled it by time of day, so after dark it was
// backwards. Measured: room 14 at 22:00 with every lamp off metered a centre
// luminance of 12.7 while the blinds clipped to white -- the window was the
// brightest thing in a pitch-dark bedroom.
//
// So the authored look is kept as the DAY end of a ramp and faded toward a
// moonlit pane as daylight.js's night factor rises. Two properties matter:
//
//   * at nightFactor 0 no material is written AT ALL, so a daytime frame is
//     byte-for-byte the frame this module does not exist in;
//   * at 1 the brightest emissive material in a window sits at NIGHT_LUM, below
//     what the unlit room around it should read, and every other material in
//     that window keeps its authored RATIO to it -- so the Dining bay's sky is
//     still brighter than its lawn, and the master blinds still darker than the
//     glass behind them.
//
// There is no easing of its own: getNightFactor() is already the eased value
// (daylight.js current, not target), so the ☀/☾ mode button fades the windows
// with everything else and settleDaylight() at boot settles these too.
//
// TWO detectors reach that ramp, because not every window is called one: the
// object name (WINDOW_RE) and a closed list of "the view outside" material
// names (VIEW_MATS). The second is what covers the five `* Baseboards` runs,
// each of which is a trim piece with a glazed unit inside it. A name match dims
// the whole object; a material match dims only the materials that matched, so
// the baseboard stays baseboard.
//
// ---------------------------------------------------------------------------
// THE SECOND LIE: FAUX FILL (mode 'fill')
// ---------------------------------------------------------------------------
// A window fakes the view out. The other authored emissive in this house fakes
// the BOUNCE IN -- a flat grey emissiveFactor added to a diffuse material at
// authoring time so a cabinet door, a ceiling or a wall skin reads as lit
// without costing a light. It is the same bug with the same shape: the value
// only makes sense at noon, nothing scaled it by hour, and after dark it is the
// brightest thing in a room that is supposed to be dark. Measured in the OFF
// frame at 22:00 before this: the Kitchen's cabinet faces (`white` 0.178,
// `trim` 0.153, `whitelo` 0.093 over ~1000 sq ft of vertical door) held the
// unlit room at centre 47.1 against 86.8 lit -- a 1.84:1 lit:unlit ratio, and
// no light_cfg anywhere could move it, because none of that light came from a
// light. The Garage's door leaf (`gleaf` 0.212 over ~349 sq ft) is the same
// trick on one big flat panel.
//
// In most rooms it landed on the CEILING, which the cutaway deletes, so it was
// invisible and stayed unfixed for months. It shows only where it landed on a
// wall, a cabinet face or a prop.
//
// It is NOT a window, so it does not get the window treatment. A pane ramps
// toward MOON because a pane really is showing you a moonlit outdoors; a
// cabinet door is not showing you anything -- it should simply stop
// self-illuminating and be lit by the room's lamps like every other surface.
// So mode 'fill' is an intensity ramp to zero with NO tint: emissive colour is
// handed back verbatim and only emissiveIntensity moves. Tinting it would give
// a dark kitchen blue cupboards, which is a different wrong answer.
//
// The detector matches on what the material was authored to DO, never on what
// it is called -- see isFillMat. That is deliberate: the offending names here
// are `white`, `trim`, `black`, `steel`, `glass`, `paper`, `quartz`, and a
// name list of those would collide with half the library the first time
// someone uploads a lamp whose lens is called `white`.
import * as THREE from 'three';
import { onFrame } from './scene.js';
import { getNightFactor } from './daylight.js';

// Objects whose emissive is faking the outdoors, matched on the placed object's
// NAME -- the same handle objects.js SURFACE_RE and cutaway.js WALL_ARCH_RE
// take. Deliberately narrow. This house has no skylights; add the noun when it
// gets one.
const WINDOW_RE = /\bwindows?\b/i;

// ...and the second detector, for the windows that are not CALLED windows. Five
// objects in this house carry a glazed unit inside a piece named for the trim
// run around it -- `Guest Baseboards`, `Master Bath Baseboards`, `Bath2F
// Baseboards` (material `pane`, emissiveFactor 1.0 x strength 2.6), `Office
// Baseboards` (`pane`, x2.2) and `Movie Baseboards` (`m2pane`, x1.5). Same fake
// daylight, different bag, and WINDOW_RE cannot see any of it.
//
// So this is a closed, hand-checked list of the material names that paint the
// VIEW OUT: sky, foliage, lawn, the rail across the bottom, and the glazing
// itself. It is an exact-name Set and not a substring test on purpose -- the
// obvious loosening is exactly the thing the original comment here warned
// against. `shade`, `lens`, a bare `glass`, `bulb` and `ember` are what a lamp,
// a recessed can and "Ceiling Fan"'s `fan_glass` are made of; those are
// emissive because someone meant them to be, and roomlights.js `light_cfg
// .glow_part` matches on `shade|lens|glass` for that very reason. Note
// `win_glass` is safe only for its `win_` prefix -- do not shorten it.
// Blender's de-duplication suffix (`pane.001`) is stripped before the lookup;
// nothing else is normalised away.
const VIEW_MATS = new Set([
  'pane', 'm2pane',              // the glazing itself
  'skyhi', 'skymid',             // the sky behind it, high and low
  'wtrees', 'leafout',           // foliage outside
  'wlawn', 'wrail',              // ground, and the rail across the sill
  'win_glass',                   // master bedroom units (prefix, never bare `glass`)
]);
const isViewMat = (m) => VIEW_MATS.has((m.name || '').toLowerCase().replace(/\.\d+$/, ''));

// ...and the third detector, for the faux fill described at the top. It reads
// the AUTHORED record (`__orig`), never the live material, and it asks three
// questions of the value rather than one question of the name. All three have
// to pass, and each one is carrying a specific thing this must not break.
//
//  1. NEUTRAL. A fill is written as one grey number typed into all three
//     channels; every deliberate emitter in this house is tinted, because a
//     thing that emits light has a colour of light. Measured over every placed
//     GLB: the fills sit at saturation 0.000 (`white` 0.178^3, `ceil` 0.445^3)
//     up to 0.034 (`gleaf`, and the recessed-can cones, which carry a one-byte
//     warm skew), while the nearest deliberate emitter is `black` at 0.135 and
//     the arcade's screens and marquees run 0.3 to 0.93. FILL_SAT 0.06 sits in
//     that gap with a 2x margin on the side that matters. Saturation is read in
//     the LINEAR working space, which is where Color keeps it -- note
//     `__orig.emissive` is a getHex() round trip, so it is quantised to 8 bits
//     per channel first, which is why the threshold is expressed as a ratio and
//     not as an absolute channel difference.
//
//  2. NO EMISSIVE STRENGTH. `orig.emissiveIntensity` is exactly 1 only when the
//     GLB carried no KHR_materials_emissive_strength at all (three's
//     GLTFMaterialsEmissiveStrength writes the extension's value straight into
//     it, and the default is 1). Reaching for that extension is the author
//     saying "this emits"; a bare emissiveFactor is the author saying "this is
//     a bit brighter than it should be". It is what spares the Kitchen
//     ceiling's `glow` (1,1,1 x1.55) and the Garage's `gshop` (x2.2), both of
//     which are neutral enough to pass test 1. Exact equality, not a tolerance:
//     the Master bedroom's per-panel ceiling bake runs x0.56 .. x1.64 including
//     one panel at x1.0036, and a tolerance would catch that ONE panel out of
//     eleven and shade it differently from its neighbours.
//
//  3. NOT A FIXTURE'S OWN LENS. The forbidden nouns from VIEW_MATS' comment,
//     as a substring test this time, because here they are a veto and not a
//     match -- a false positive costs nothing and a false negative puts out a
//     lamp. `glow`, `globe`, `flame`, `neon` and `candle` join them: the Office
//     desk lamp's globe and the Movie props' bulb are unbound lamp bulbs, which
//     belong to roomlights.js and a binding, not here.
//
// VIEW_MATS is excluded outright so a material can never be claimed by both
// ramps at once (`pane` is (1,1,1) with strength, so it fails test 2 anyway --
// this is belt and braces, and it is what keeps the two modes' entries for one
// object disjoint).
const FIXTURE_MAT_RE = /shade|lens|glass|bulb|ember|glow|globe|flame|neon|candle/i;
const FILL_SAT = 0.06;
const _f = new THREE.Color(); // own scratch: _c is live inside measurePeak/paint

function isFillMat(m, orig) {
  if (!orig || orig.emissive === null) return false;
  if (orig.emissiveIntensity !== 1) return false;
  const name = (m.name || '').toLowerCase().replace(/\.\d+$/, '');
  if (FIXTURE_MAT_RE.test(name) || VIEW_MATS.has(name)) return false;
  _f.setHex(orig.emissive);
  const hi = Math.max(_f.r, _f.g, _f.b);
  if (hi <= 0.002) return false; // authored black, or one byte off it
  return (hi - Math.min(_f.r, _f.g, _f.b)) / hi <= FILL_SAT;
}

// The moonlit pane. Measured off the Sims 4 night references in
// scratchpad/lightgauntlet/ref: every moonlit outdoor surface in them sits cool
// blue around sRGB (43,51,93). setRGB must name sRGB explicitly -- it defaults
// to the LINEAR working space in r160 (only setHex defaults to sRGB), the same
// trap roomlights.js kelvinToColor documents.
const MOON = new THREE.Color().setRGB(43 / 255, 51 / 255, 93 / 255, THREE.SRGBColorSpace);

// Linear emissive luminance the brightest material of a window lands on at full
// night. Emissive is added before ACES tone mapping at exposure 1.15 (scene.js)
// and then through the night optics' lift, which puts the pane at sRGB ~(43,53,99)
// on screen -- measured, and within a couple of bytes of the (43,51,93) the
// reference night shots put a moonlit outdoor surface at. It is also two orders
// below the night stack's bloom threshold (1.2, linear HDR), so a window stops
// flaring at the same moment it stops glowing.
//
// This is the one knob. The reference also wants an unlit interior at L ~28 and
// ours still meters ~9 (logged in scratchpad/lightgauntlet/PLAN.md as a global
// ambient question, not a per-room one) -- so until that is settled centrally a
// window still reads brighter than its room here, just no longer by 5x.
const NIGHT_LUM = 0.04;

// [{ root, peak, matTest, mode }] -- object roots with authored emissive that
// is standing in for daylight, one entry per (object, mode).
//
// `matTest` is null when the OBJECT is the window (dim everything emissive in
// it, which is what this module has always done), and `isViewMat` / `isFillMat`
// when only some materials of it are (dim just those). A baseboard run is
// mostly baseboard: the trim has to keep its authored look after dark and only
// the pane inside it follows the sun.
//
// One object can hold BOTH modes -- "Kitchen Counter Items" is a shelf of props
// with fill on the boxes, "Movie Baseboards" is a trim run with a pane in it --
// so it gets two entries whose matTests are disjoint by construction. Two
// entries is cheaper than one entry with a per-material mode: `peak` is a
// property of the SET of materials a mode owns (the window ramp aims the
// brightest of them at NIGHT_LUM), so the modes cannot share one.
const windows = [];
let lastApplied = -1;  // night factor the materials currently hold (-1 = untouched)
let suspended = false;
let enabled = true;    // debug kill switch (__windowlight.setEnabled), like __cutaway's

const _c = new THREE.Color();
const lum = (c) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b; // linear working space

// The authored-material record for one mesh, or null.
//
// Normally that is models.js's own `__orig` on the mesh (state.js's
// convention). The exception is what made this module do nothing at all in the
// Dining room: cutaway.js splitMerged rebuilds a sub-mesh that skins several
// walls as one child mesh PER WALL, each with its own material clone, and drops
// the parent's geometry — so the mesh carrying `__orig` is the one that stopped
// drawing, and the five visible panes had no record of their own. "Dining
// Windows" is exactly that shape: five units on four walls in one GLB. The
// split children are single-material by construction (splitMerged bails on
// material arrays), so the parent's index 0 is theirs.
function origFor(child) {
  if (child.userData.__orig) return child.userData.__orig;
  const p = child.parent;
  return p?.isMesh && p.userData.__orig ? p.userData.__orig : null;
}

// Brightest authored emissive in this instance, as linear luminance, over the
// materials `matTest` admits (null = all of them). Read from the `__orig`
// record, never from the live material, which is what this module has been
// writing to. `matTest(m, orig)` gets both: the name lives on the LIVE material
// (`__orig` records colour and intensity only, and Material.clone() carries
// `name` across both the models.js instance clone and cutaway.js splitMerged's)
// while isFillMat has to judge the AUTHORED value, which is only in `__orig`.
//
// For mode 'fill' the number is not used as a target -- that ramp goes to zero,
// not to NIGHT_LUM -- but a peak of 0 is still the answer to "does this object
// have any of this in it", which is how one traversal does both jobs.
function measurePeak(root, matTest) {
  let peak = 0;
  root.traverse((child) => {
    if (!child.isMesh) return;
    const origs = origFor(child);
    if (!origs) return;
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    mats.forEach((m, i) => {
      const orig = origs[i];
      if (!m.emissive || !orig || orig.emissive === null) return;
      if (matTest && !matTest(m, orig)) return;
      peak = Math.max(peak, lum(_c.setHex(orig.emissive)) * orig.emissiveIntensity);
    });
  });
  return peak;
}

function paint(w, night) {
  // 'fill' goes to zero: the value is standing in for daylight bounce, and
  // after dark there is none to stand in for. Everything the room then shows
  // has to come from roomlights.js, which is the whole point.
  //
  // 'window' caps, never lifts. `Kitchen Window West` is authored at emissive
  // 0.35 with no strength extension and is already darker than the night floor
  // -- pulling it UP to NIGHT_LUM after dark would be this bug with the sign
  // flipped.
  const gain = w.mode === 'fill'
    ? 1 - night
    : THREE.MathUtils.lerp(1, Math.min(1, NIGHT_LUM / w.peak), night);
  w.root.traverse((child) => {
    if (!child.isMesh) return;
    const origs = origFor(child);
    if (!origs) return;
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    mats.forEach((m, i) => {
      const orig = origs[i];
      if (!m.emissive || !orig || orig.emissive === null) return;
      if (w.matTest && !w.matTest(m, orig)) return; // the trim, not the pane: leave it alone
      if (night <= 0) { // hand the authored daylight back verbatim
        m.emissive.setHex(orig.emissive);
        m.emissiveIntensity = orig.emissiveIntensity;
        return;
      }
      if (w.mode === 'fill') {
        // Colour handed back untouched and only the intensity moved: a cabinet
        // door is not a light source of its own, so it has no colour of its own
        // to go cool. Writing the hex back each time (rather than leaving it)
        // keeps this idempotent if some other writer -- main.js's selection
        // highlight, a state repaint -- got at the material in between.
        m.emissive.setHex(orig.emissive);
        m.emissiveIntensity = orig.emissiveIntensity * gain;
        return;
      }
      // Hue goes cool with the light; INTENSITY carries the window's structure.
      // The two have to be solved together: tinting toward MOON changes the
      // material's own luminance (0.98 -> 0.037), so a plain multiply on
      // emissiveIntensity would land ~27x under the target. Aim the emitted
      // luminance and divide the tint back out.
      const want = lum(_c.setHex(orig.emissive)) * orig.emissiveIntensity * gain;
      m.emissive.setHex(orig.emissive).lerp(MOON, night);
      m.emissiveIntensity = want / Math.max(lum(m.emissive), 1e-4);
    });
  });
}

// objects.js calls this once a piece's GLB instance has landed -- for EVERY
// object, not only the ones that look like windows: the detectors below are
// what decide, and mode 'fill' means most placed pieces in this house now have
// something to say. It has to be here and not in buildObjects: models load
// async, so a window (or a cabinet run) routinely arrives long after the night
// factor settled -- the same reason applyObjectFade is called from that same
// `then`. The name is historical; it notes an object, of either kind.
export function noteWindowObject(root) {
  const ud = root.userData;
  // An object BOUND to an HA entity is a light fixture first, and roomlights.js
  // repaints a fixture's emissive on every frame its glow moves. Two writers of
  // one material would fight, so binding -- an explicit act -- wins outright and
  // this module keeps its hands off. Same precedence objects.js isPickable()
  // gives a binding over its name test. It is tested FIRST, because the material
  // detectors below would otherwise reach into a bound fixture's GLB -- and that
  // matters far more now that isFillMat exists, since a bound lamp's body, base
  // and shade are exactly the neutral unit-strength emissive it looks for.
  if (ud.entityId) return;
  // Named a window -> the whole object is one, and that claim is exclusive: a
  // window's blind slats and trim are authored neutral at strength <1 and would
  // otherwise ALSO read as fill, giving one material two owners writing it on
  // the same frame. Otherwise the two material detectors do double duty as the
  // "is it one of these at all" test, since measurePeak returns 0 for an object
  // holding none of that mode's materials. One traversal per mode per object,
  // once, when its GLB lands.
  if (WINDOW_RE.test(ud.name || '')) {
    note(root, null, 'window');
    return;
  }
  note(root, isViewMat, 'window');
  note(root, isFillMat, 'fill');
}

function note(root, matTest, mode) {
  const peak = measurePeak(root, matTest);
  if (peak <= 0) return; // "Living Window East Trim" and every plain object: nothing to dim
  const w = { root, peak, matTest, mode };
  windows.push(w);
  if (lastApplied > 0) paint(w, lastApplied); // arrived mid-night
}

// buildObjects is about to replace every object root (planner close, undo,
// sync); the ones held here are on their way off the scene graph.
export function resetWindowLight() {
  windows.length = 0;
}

function tick() {
  const night = (suspended || !enabled) ? 0 : getNightFactor();
  if (Math.abs(night - lastApplied) < 1e-3) return;
  // Untouched and still daylight: the authored materials ARE the day look, so
  // day never gets a single material write out of this module.
  if (night <= 0 && lastApplied < 0) { lastApplied = 0; return; }
  lastApplied = night;
  for (const w of windows) paint(w, night);
}

// snapshots.js brackets its room-card capture with this. Cards are shot under a
// fixed studio light whatever the hour, keyed by GEOMETRY and persisted -- so a
// card captured after dark would bake black windows, and an unlit kitchen, into
// a daylit room forever. Exactly why suspendRoomLights() and
// suspendEaveLights() exist. Both modes ride it: it walks the same array.
export function suspendWindowLight() {
  const was = lastApplied;
  suspended = true; // ...so tick() sees 0 == lastApplied and does not undo this
  if (was > 0) for (const w of windows) paint(w, 0);
  lastApplied = 0;
  return () => {
    suspended = false;
    if (was > 0) for (const w of windows) paint(w, was);
    lastApplied = was;
  };
}

export function initWindowLight() {
  onFrame(tick);
  window.__windowlight = {
    // Off = the authored daylight, at any hour. It is how a before/after of
    // this module is shot from one identical camera pose, and the first thing
    // to try when a window -- or a cabinet face -- looks wrong after dark.
    setEnabled: (v) => { enabled = !!v; },
    night: () => lastApplied,
    windows: () => windows.map((w) => ({
      name: w.root.userData.name,
      objectId: w.root.userData.objectId,
      peak: +w.peak.toFixed(3),
      mode: w.mode,                         // 'window' (ramp to MOON) | 'fill' (ramp to 0)
      via: w.matTest ? 'material' : 'name', // which detector caught it
    })),
  };
}
