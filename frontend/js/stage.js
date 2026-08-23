// The "stage": the unobstructed rect of the canvas that the 3D house is framed
// into, plus the one layout-changed bus the whole app shares.
//
// The rect is owned by CSS. #stage-rect is an invisible fixed div inset by the
// --stage-* tokens, so ONE getBoundingClientRect() resolves calc(), env(), the
// media queries, the live orientation and the body-state overrides at once.
// getComputedStyle cannot do that job: an unregistered custom property returns
// its token stream, not a used value, so --stage-left comes back as the literal
// string "calc(env(safe-area-inset-left,0px) + 20px)".
//
// This module imports nothing from scene.js — scene.js imports it.

import { invalidateTokens } from './layout.js';

let probe = null;
let rect = { x: 0, y: 0, w: 1, h: 1 };
let raf = 0;

const stageListeners = new Set();   // fn(rect) — camera framing
const layoutListeners = new Set();  // fn()     — panel capacity math

/** Camera framing: fires only when the stage rect actually moved or resized. */
export function onStageChanged(fn) { stageListeners.add(fn); }

/** Panel capacity math: fires on every settled layout change. */
export function onLayoutChanged(fn) { layoutListeners.add(fn); }

export function getStageRect() { return { ...rect }; }

function measure() {
  if (!probe) return;
  // a breakpoint may have flipped, so cached token values are stale
  invalidateTokens();
  const r = probe.getBoundingClientRect();
  const W = window.innerWidth, H = window.innerHeight;
  // A mis-tokened layout must never produce a degenerate frustum.
  const w = Math.min(Math.max(r.width, 120), W);
  const h = Math.min(Math.max(r.height, 120), H);
  const changed = r.left !== rect.x || r.top !== rect.y || w !== rect.w || h !== rect.h;
  rect = { x: r.left, y: r.top, w, h };

  // Stage listeners first (scene.js re-aims the camera), THEN the generic bus,
  // so anything reading getStageRect() in a layout listener sees the new value.
  if (changed) for (const fn of stageListeners) fn(getStageRect());
  for (const fn of layoutListeners) fn();
  // Same bus, event flavour — matches the repo's levelChanged/appModeChanged
  // pattern, and lets focus.js/floorview.js decide who owns the camera without
  // scene.js having to import them (that would be a cycle).
  if (changed) window.dispatchEvent(new CustomEvent('stageChanged', { detail: getStageRect() }));
}

// Two rAFs, not a timeout: iOS reports a stale innerWidth/innerHeight for one
// frame after a rotation, and ResizeObserver can fire mid-layout on a
// breakpoint flip. Two frames is both cheaper and more reliable than the 150ms
// timers this replaces in cameras.js / roomcards.js.
function schedule() {
  if (raf) return;
  raf = requestAnimationFrame(() => requestAnimationFrame(() => { raf = 0; measure(); }));
}

/** Ask for a re-measure — e.g. after revealing a panel that was display:none. */
export const bumpLayout = schedule;

export function initStage() {
  probe = document.getElementById('stage-rect');
  if (!probe) return;
  new ResizeObserver(schedule).observe(probe);
  // ResizeObserver misses a pure MOVE (same size, new offset).
  window.addEventListener('resize', schedule);
  // iPadOS never fires orientationchange for a Split View resize, which is why
  // ResizeObserver is the primary signal; this is the belt to its braces.
  window.addEventListener('orientationchange', schedule);
  // The ONLY events that fire when Safari's URL bar collapses or the software
  // keyboard opens — window.resize fires for neither on iOS.
  window.visualViewport?.addEventListener('resize', schedule);
  window.visualViewport?.addEventListener('scroll', schedule);
  measure();
}
