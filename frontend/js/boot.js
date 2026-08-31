// The boot curtain: an opaque full-screen overlay that hides the app while it
// assembles itself, plus the readiness gates that decide when to lift it.
//
// Why this exists: main() awaits three fetches and then resolves, but the scene
// it kicked off is nowhere near finished — a couple of hundred furniture GLBs,
// the DRACO house shell, wall/floor textures and the room-card thumbnails all
// land afterwards, each as its own visible pop-in, and the camera re-frames when the
// shell arrives (house.js refitStage). Nothing in the app tracked any of it
// collectively, so this module owns the join point.
//
// The markup is STATIC in index.html, not created here: <head> blocks on
// socket.io and the three.js importmap from a CDN before this module is even
// parsed, so a JS-built overlay would flash the empty chrome first.
import * as THREE from 'three';
import { modelsIdle, modelsPending } from './models.js';

const $ = (id) => document.getElementById(id);

// How long after startBoot the watchdog first checks in. It is NOT a reveal
// deadline: a flat one was the bug this file was rewritten to fix. Assembly on
// this house takes 16-20s (271 GLBs, ~640 tracked sub-loads), so a blind 15s
// timer fired *inside* settleLoaders and lifted the curtain at 633/640 items —
// measured, and exactly the "two or three things pop up afterwards" report.
// Everything downstream of settleLoaders (the shell's re-frame, the shader
// precompile, the room-card snapshots) therefore ran in full view. The curtain
// now lifts on completion; the watchdog only breaks a genuine STALL.
const FAILSAFE_MS = 15000;
const HOUSE_POLL_MS = 500;

// Nothing has moved for this long => something is wedged, reveal what we have.
// Must stay comfortably longer than the worst gap between two asset
// completions, or a slow cold load reveals early again — the same bug in a new
// dress. __boot.timeline() is how you check that.
const STALL_MS = 8000;

// Absolute backstop. Now that the watchdog is the ONLY thing that can force a
// reveal, this is the point past which a blank app beats a curtain that never
// lifts.
const HARD_CAP_MS = 120000;

let shown = 0;      // last painted fraction — the bar only ever moves forward
let band = [0, 1];  // [floor, ceiling] the current stage may move within
let done = false;
let failsafe = null;
let houseBuilt = false;

/** main() calls this the moment buildHouse has put geometry in the scene. */
export function bootHouseBuilt() { houseBuilt = true; }

// ------------------------------------------------------------------ progress

function paint(fraction) {
  const clamped = Math.max(shown, Math.min(1, fraction));
  if (clamped === shown) return;
  shown = clamped;
  const fill = $('boot-fill');
  if (fill) fill.style.width = `${(clamped * 100).toFixed(1)}%`;
}

// Per-stage wall clock, so a future "it revealed too early" is one console line
// (__boot.timeline()) instead of a re-derivation from scratch.
const timeline = [];

function stamp() { return Math.round(performance.now() - startedAt); }

/** Enter a stage: label it and reserve the band the bar may move within. */
export function bootStage(label, floor, ceiling) {
  if (done) return;
  band = [floor, ceiling];
  paint(floor);
  const status = $('boot-status');
  if (status) status.textContent = label;
  const now = stamp();
  const prev = timeline[timeline.length - 1];
  if (prev && prev.endMs === null) prev.endMs = now;
  timeline.push({ stage: label, startMs: now, endMs: null });
}

/** Move within the current stage. `t` is 0..1 across the band. */
export function bootProgress(t) {
  if (done) return;
  const [floor, ceiling] = band;
  paint(floor + (ceiling - floor) * Math.max(0, Math.min(1, t)));
}

// Real numbers for the models stage. Every loader in the app is constructed
// with no explicit manager (models.js GLTFLoader/DRACOLoader, textures.js
// TextureLoader), so they all report through DefaultLoadingManager and its
// counts cover GLBs, the DRACO decoder wasm and textures alike.
//
// The counts have to be mirrored here: LoadingManager keeps itemsLoaded /
// itemsTotal as closure locals, so they are NOT readable off the instance -
// reading manager.itemsLoaded gives undefined, which would make the idle check
// below trivially true and silently drop textures from the gate.
let managerIdle = true;
let mgrLoaded = 0, mgrTotal = 0, mgrLast = '';

// performance.now() of the last observed forward movement, in EITHER counter.
// This is what separates "still assembling" from "wedged" — see armFailsafe.
let progressAt = 0;
let lastPending = 0;

function markProgress() { progressAt = performance.now(); }

// modelsPending() has no callback to hook, so movement in it is sampled. Called
// from both the watchdog tick and the settle loop, which between them run far
// more often than STALL_MS.
function pollPending() {
  const n = modelsPending();
  if (n !== lastPending) { lastPending = n; markProgress(); }
  return n;
}

THREE.DefaultLoadingManager.onStart = (url, loaded, total) => {
  managerIdle = false; mgrLoaded = loaded; mgrTotal = total; mgrLast = url;
  markProgress();
};
THREE.DefaultLoadingManager.onLoad = () => { managerIdle = true; markProgress(); };
THREE.DefaultLoadingManager.onProgress = (url, loaded, total) => {
  mgrLoaded = loaded; mgrTotal = total; mgrLast = url;
  managerIdle = total > 0 && loaded >= total;
  markProgress();
  if (total > 0) bootProgress(loaded / total);
};

// console handle: __boot.state() during a hang says which gate is holding
window.__boot = {
  state: () => ({
    managerIdle, mgrLoaded, mgrTotal, mgrLast, shown, band, done, houseBuilt,
    pending: modelsPending(),
    msSinceProgress: Math.round(performance.now() - progressAt),
    elapsedMs: stamp(),
  }),
  timeline: () => timeline.map((t) => ({
    stage: t.stage,
    startMs: t.startMs,
    ms: (t.endMs === null ? stamp() : t.endMs) - t.startMs,
  })),
  reveal: () => finishBoot(),
};

// ------------------------------------------------------------------ the gate

// Yield long enough for a resolved load to reach the scene graph. rAF is the
// right signal for that, but it is NOT a reliable clock: Chrome pauses it
// outright whenever the tab is backgrounded, occluded or simply not being
// composited, and waiting on a bare rAF here hung the curtain until the
// failsafe (measured, not theoretical).
//
// A hidden tab needs its own path: it clamps timers to ~1s too, so a plain
// setTimeout fallback cost a full second per iteration and added seconds to a
// background boot. MessageChannel is a macrotask (loader callbacks still get to
// run) and is not throttled.
const macrotask = () => new Promise((resolve) => {
  const ch = new MessageChannel();
  ch.port1.onmessage = () => resolve();
  ch.port2.postMessage(0);
});

const nextFrame = () => {
  // Hidden tab: there is no frame to wait for and nothing is being painted, so
  // the wait collapses to "yield to the event loop" - a macrotask, so pending
  // loader callbacks still get to run.
  if (document.hidden) return macrotask();
  return new Promise((resolve) => {
    let settled = false;
    const go = () => { if (!settled) { settled = true; resolve(); } };
    requestAnimationFrame(go);          // ~16ms when frames are flowing
    setTimeout(go, 100);                // visible but uncomposited: rAF is paused
  });
};

/**
 * Resolves when every model instance AND every manager-tracked load is idle.
 *
 * Two signals, because neither is sufficient alone: DefaultLoadingManager's
 * pending count is the only thing that sees textures, but it dips to zero
 * between bursts; models.js's counter is authoritative for GLB instances but
 * blind to textures. Requiring both to be idle on two consecutive frames covers
 * the handoff — a model resolving can start its own texture loads.
 *
 * This deliberately carries NO deadline of its own any more. It used to default
 * to Date.now() + 15s, a second independent clock racing the watchdog; giving
 * up is the watchdog's job alone, and it now does so on a stall rather than on
 * a guess at how long a house takes to load.
 */
export async function settleLoaders() {
  let consecutive = 0;
  while (consecutive < 2) {
    if (done) return;   // the watchdog already revealed — stop holding the line
    if (performance.now() - startedAt > HARD_CAP_MS) return;
    // Race the idle signal against a short poll: a wedged GLB never drops
    // inFlight back to 0, and a bare `await modelsIdle()` would park this loop
    // forever, past every decision the watchdog makes.
    await Promise.race([modelsIdle(), new Promise((r) => setTimeout(r, 250))]);
    await nextFrame();
    const pending = pollPending();
    consecutive = (managerIdle && pending === 0) ? consecutive + 1 : 0;
  }
}

/** Race any promise against a timeout so one hung step can't hold the app. */
export function orTimeout(promise, ms) {
  return Promise.race([promise, new Promise((r) => setTimeout(r, ms))]);
}

// ------------------------------------------------------------------- curtain

let startedAt = 0;

export function startBoot() {
  startedAt = performance.now();
  progressAt = startedAt;
  armFailsafe(FAILSAFE_MS);
}

// The watchdog. It does not reveal on a clock — it reveals when the app has
// stopped making progress, or when HARD_CAP_MS says a blank app beats a curtain
// that never lifts.
function armFailsafe(ms) {
  failsafe = setTimeout(() => {
    if (done) return;
    const elapsed = performance.now() - startedAt;
    pollPending();
    const sinceProgress = performance.now() - progressAt;

    if (elapsed < HARD_CAP_MS) {
      if (!houseBuilt) {
        // Nothing to show yet. main() spends its first phase awaiting three
        // fetches, and if HA is still connecting they can outlast any timer —
        // revealing here would open the app onto an empty stage, which reads as
        // "the house doesn't render". Say whose wait it is instead.
        const status = $('boot-status');
        if (status) status.textContent = 'Waiting for Home Assistant…';
        armFailsafe(HOUSE_POLL_MS);
        return;
      }
      if (sinceProgress < STALL_MS) {
        // Assets are still landing. This is the whole point of the curtain:
        // keep waiting, however long it takes.
        armFailsafe(HOUSE_POLL_MS);
        return;
      }
    }
    console.warn(`boot: revealing after ${Math.round(elapsed)}ms — `
      + (!houseBuilt
        ? 'NO house (Home Assistant never answered)'
        : `no progress for ${Math.round(sinceProgress)}ms at ${mgrLoaded}/${mgrTotal}`
          + `, ${modelsPending()} model(s) in flight (last: ${mgrLast})`));
    finishBoot();
  }, ms);
}

export function finishBoot() {
  if (done) return;
  done = true;
  clearTimeout(failsafe);
  // stop driving a bar that no longer exists; the app loads models on demand
  // (room editor, planner) for the rest of the session
  const mgr = THREE.DefaultLoadingManager;
  mgr.onStart = mgr.onLoad = mgr.onProgress = undefined;
  const last = timeline[timeline.length - 1];
  if (last && last.endMs === null) last.endMs = stamp();
  // one line, on purpose: "the dashboard takes a while to come up" is otherwise
  // impossible to reason about from the outside
  console.info(`boot: ready in ${Math.round(performance.now() - startedAt)}ms`
    + ` (${mgrLoaded}/${mgrTotal} loaded) — __boot.timeline() for the breakdown`);
  paint(1);
  const screen = $('boot-screen');
  if (!screen) return;
  // Let the bar actually ARRIVE at 100% before the fade starts. #boot-fill
  // animates its width over 0.3s, so lifting the curtain one frame after
  // paint(1) cut that animation off around 90% - the bar visibly never
  // finished, which is what "it opens a second too early" looks like from the
  // outside. nextFrame(), never a bare rAF, or a backgrounded tab never lifts
  // the curtain at all.
  barFull().then(nextFrame).then(() => {
    document.body.classList.add('booted');
    const drop = () => screen.remove();
    screen.addEventListener('transitionend', drop, { once: true });
    setTimeout(drop, 1000); // belt and braces: reduced motion has no transition
  });
}

/**
 * Resolves when the progress bar has finished animating to 100%.
 *
 * transitionend is the accurate signal, but it never fires at all when the bar
 * was already full, when the transition is off (prefers-reduced-motion) or in
 * a backgrounded tab, so it is raced against the transition's own duration.
 */
function barFull() {
  const fill = $('boot-fill');
  if (!fill) return Promise.resolve();
  const ms = parseFloat(getComputedStyle(fill).transitionDuration) * 1000 || 0;
  if (!ms) return Promise.resolve();
  return new Promise((resolve) => {
    const go = () => { fill.removeEventListener('transitionend', go); resolve(); };
    fill.addEventListener('transitionend', go);
    setTimeout(go, ms + 60);
  });
}
