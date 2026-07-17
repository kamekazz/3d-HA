// Cameras button (left column) + full-screen grid overlay of every camera.*
// entity. Grid snapshots load through a small round-robin queue (2 in flight,
// short gap between requests) — a house can have dozens of cameras, and
// letting every tile poll independently floods HA/Nabu Casa with concurrent
// camera_proxy calls that 502 and then retry-storm. A failed tile simply
// rejoins the cycle. Tapping a tile promotes it to a large live MJPEG view
// (one stream max — each holds a backend worker thread); the queue pauses
// while a stream is up. Closing destroys everything, aborting in-flight work.
import { findEntities, friendlyName, onStateApplied } from './state.js';
import { createCameraView } from './controls.js';
import { showBanner } from './ui.js';

const WORKERS = 2;        // concurrent snapshot fetches
const REQUEST_GAP_MS = 200;
const CYCLE_REST_MS = 5000; // pause between full refresh sweeps

let tiles = [];        // {id, tile, img, broken}
let liveView = null;   // createCameraView handle while a stream is promoted
let liveTile = null;
let session = 0;       // bumped on open/close — stale workers see it and stop

function cameraLabel(id) {
  // Ring names every camera "<place> Live view" — redundant inside this grid
  return friendlyName(id).replace(/\s+live view$/i, '');
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function loadSnapshot(t) {
  return new Promise((resolve) => {
    const done = (ok) => {
      t.img.onload = t.img.onerror = null;
      t.broken = !ok;
      t.tile.classList.toggle('broken', !ok);
      resolve();
    };
    t.img.onload = () => done(true);
    t.img.onerror = () => done(false);
    t.img.src = `/api/camera/${t.id}/snapshot?t=${Date.now()}`;
  });
}

// Round-robin over all tiles forever (until the session changes): workers
// share one advancing index, so a slow camera never blocks the rest of the
// grid; whichever worker wraps past the last tile takes the long rest.
async function pump(mySession) {
  let next = 0;
  const worker = async () => {
    while (mySession === session && tiles.length) {
      if (liveView) { await sleep(500); continue; } // stream up — hold the queue
      const t = tiles[next++ % tiles.length];
      await loadSnapshot(t);
      if (mySession !== session) return;
      await sleep(next % tiles.length === 0 ? CYCLE_REST_MS : REQUEST_GAP_MS);
    }
  };
  await Promise.all(Array.from({ length: WORKERS }, worker));
}

function demote() {
  const overlay = document.getElementById('cam-overlay');
  overlay.classList.remove('expanded');
  liveTile?.classList.remove('big');
  liveTile?.querySelector('img')?.classList.remove('hidden');
  liveView?.destroy();
  liveView = null;
  liveTile = null;
}

function promote(t) {
  demote();
  liveTile = t.tile;
  liveView = createCameraView(t.id, {
    live: true,
    onError: (msg) => showBanner(msg, 4000),
  });
  // stream refused → controls.js falls back to snapshot mode; drop to grid
  liveView.onModeChange = (isLive) => { if (!isLive) demote(); };
  t.img.classList.add('hidden'); // the live <img> takes the tile over
  t.tile.insertBefore(liveView.el, t.img);
  t.tile.classList.add('big');
  document.getElementById('cam-overlay').classList.add('expanded');
}

function onKeydown(e) {
  if (e.key !== 'Escape') return;
  e.stopPropagation(); // focus.js's Esc (exit room focus) must not also fire
  close();
}

function open() {
  const overlay = document.getElementById('cam-overlay');
  const grid = document.getElementById('cam-grid');
  grid.innerHTML = '';
  tiles = [];

  for (const id of findEntities('camera.')) {
    const tile = document.createElement('div');
    tile.className = 'cam-tile';
    const img = document.createElement('img');
    img.alt = `Camera: ${cameraLabel(id)}`;
    const label = document.createElement('div');
    label.className = 'cam-label';
    label.textContent = cameraLabel(id);
    tile.append(img, label);
    const t = { id, tile, img, broken: false };
    tile.addEventListener('click', () => {
      if (liveTile === tile) demote();
      else promote(t);
    });
    grid.appendChild(tile);
    tiles.push(t);
  }

  overlay.classList.remove('hidden', 'expanded');
  document.addEventListener('keydown', onKeydown, true);
  session += 1;
  pump(session);
}

function close() {
  session += 1; // stops the pump workers
  document.removeEventListener('keydown', onKeydown, true);
  demote(); // destroys a live stream if one is up
  for (const t of tiles) { t.img.onload = t.img.onerror = null; t.img.src = ''; }
  tiles = [];
  document.getElementById('cam-grid').innerHTML = '';
  document.getElementById('cam-overlay').classList.add('hidden');
}

export function initCameras() {
  const btn = document.getElementById('cameras-btn');
  btn.onclick = open;
  document.getElementById('cam-close').onclick = close;

  onStateApplied((entityId) => {
    if (entityId === null || entityId.startsWith('camera.')) {
      btn.classList.toggle('hidden', !findEntities('camera.').length);
    }
  });
}
