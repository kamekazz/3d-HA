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
import { modelsIdle } from './models.js';

const $ = (id) => document.getElementById(id);

// Absolute wall-clock cap. A wedged GLB, an unreachable HA or a backgrounded
// tab (snapshots.js parks its pump when document.hidden) must never leave the
// user staring at a black screen forever.
const FAILSAFE_MS = 15000;

let shown = 0;      // last painted fraction — the bar only ever moves forward
let band = [0, 1];  // [floor, ceiling] the current stage may move within
let done = false;
let failsafe = null;

// ------------------------------------------------------------------ progress

function paint(fraction) {
  const clamped = Math.max(shown, Math.min(1, fraction));
  if (clamped === shown) return;
  shown = clamped;
  const fill = $('boot-fill');
  if (fill) fill.style.width = `${(clamped * 100).toFixed(1)}%`;
}

/** Enter a stage: label it and reserve the band the bar may move within. */
export function bootStage(label, floor, ceiling) {
  if (done) return;
  band = [floor, ceiling];
  paint(floor);
  const status = $('boot-status');
  if (status) status.textContent = label;
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

THREE.DefaultLoadingManager.onStart = (url, loaded, total) => {
  managerIdle = false; mgrLoaded = loaded; mgrTotal = total; mgrLast = url;
};
THREE.DefaultLoadingManager.onLoad = () => { managerIdle = true; };
THREE.DefaultLoadingManager.onProgress = (url, loaded, total) => {
  mgrLoaded = loaded; mgrTotal = total; mgrLast = url;
  managerIdle = total > 0 && loaded >= total;
  if (total > 0) bootProgress(loaded / total);
};

// console handle: __boot.state() during a hang says which gate is holding
window.__boot = {
  state: () => ({ managerIdle, mgrLoaded, mgrTotal, mgrLast, shown, band, done }),
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
//
// modelsIdle() is what actually holds the loop - every getInstance is already
// in flight before settleLoaders is called - so a fast yield cannot let it exit
// early.
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
 */
export async function settleLoaders({ deadline = Date.now() + FAILSAFE_MS } = {}) {
  let consecutive = 0;
  while (consecutive < 2) {
    if (Date.now() > deadline) return;
    await modelsIdle();
    await nextFrame();
    consecutive = managerIdle ? consecutive + 1 : 0;
  }
}

/** Race any promise against the failsafe so one hung step can't hold the app. */
export function orTimeout(promise, ms) {
  return Promise.race([promise, new Promise((r) => setTimeout(r, ms))]);
}

// ------------------------------------------------------------------- curtain

let startedAt = 0;

export function startBoot() {
  startedAt = performance.now();
  failsafe = setTimeout(() => {
    if (done) return;
    console.warn(`boot: ${FAILSAFE_MS}ms failsafe fired — revealing anyway`);
    finishBoot();
  }, FAILSAFE_MS);
}

export function finishBoot() {
  if (done) return;
  done = true;
  clearTimeout(failsafe);
  // stop driving a bar that no longer exists; the app loads models on demand
  // (room editor, planner) for the rest of the session
  const mgr = THREE.DefaultLoadingManager;
  mgr.onStart = mgr.onLoad = mgr.onProgress = undefined;
  // one line, on purpose: "the dashboard takes a while to come up" is otherwise
  // impossible to reason about from the outside
  console.info(`boot: ready in ${Math.round(performance.now() - startedAt)}ms`);
  paint(1);
  const screen = $('boot-screen');
  if (!screen) return;
  // let the 100% bar paint before the fade starts - via nextFrame, never a bare
  // rAF, or a backgrounded tab never lifts the curtain at all
  nextFrame().then(() => {
    document.body.classList.add('booted');
    const drop = () => screen.remove();
    screen.addEventListener('transitionend', drop, { once: true });
    setTimeout(drop, 1000); // belt and braces: reduced motion has no transition
  });
}
