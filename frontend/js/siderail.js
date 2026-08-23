// The side rail's segmented control: Rooms | Cameras.
//
// Rooms and cameras used to be two 380px columns flanking the house, which
// covered 64% of an iPad Air's width and put 19 photo tiles on screen at equal
// weight. They now share one glass rail and only one grid is visible at a time.
//
// cameras.js and roomcards.js are untouched — they still own #left-dash and
// #room-cards and still compute their own capacity. This module only decides
// which of the two is displayed, and tells the layout bus to re-measure the
// one it just revealed (a display:none grid measures 0, so its computeCapacity
// bails and keeps a stale value).

import { bumpLayout } from './stage.js';

const KEY = '3dha.railPanel';   // same pattern as daylight.js's 3dha.lightMode
const PANELS = ['rooms', 'cams'];

let active = 'rooms';

function apply(panel) {
  active = PANELS.includes(panel) ? panel : 'rooms';
  // A data attribute, not .hidden on the grids: cameras.js already owns a
  // class on the rail for "HA has no cameras", and two writers of .hidden on
  // the same element would fight. CSS resolves both.
  document.getElementById('sr-body')?.setAttribute('data-panel', active);
  for (const btn of document.querySelectorAll('#sr-tabs button')) {
    btn.setAttribute('aria-selected', String(btn.dataset.panel === active));
  }
  // The revealed grid was display:none and measured 0 until this frame.
  bumpLayout();
}

export function getRailPanel() { return active; }

export function setRailPanel(panel) {
  apply(panel);
  try { localStorage.setItem(KEY, active); } catch { /* private mode */ }
}

export function initSideRail() {
  const tabs = document.getElementById('sr-tabs');
  if (!tabs) return;
  tabs.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-panel]');
    if (btn) setRailPanel(btn.dataset.panel);
  });
  let saved = null;
  try { saved = localStorage.getItem(KEY); } catch { /* private mode */ }
  apply(saved || 'rooms');
}
