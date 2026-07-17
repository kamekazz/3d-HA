// Left-column camera grid (2 columns of idling snapshots, favorites first,
// sliced to exactly what fits — the wall tablet never scrolls) + full-screen
// single-camera live view. Grid snapshots load through a small round-robin
// queue (2 in flight, short gap between requests) — a house can have dozens
// of cameras, and letting every tile poll independently floods HA/Nabu Casa
// with concurrent camera_proxy calls that 502 and then retry-storm. A failed
// tile simply rejoins the cycle. Tapping a tile opens the live MJPEG view
// (one stream max — each holds a backend worker thread); the queue pauses
// while a stream is up, the tab is hidden, or CSS hides the column.
import { findEntities, friendlyName, onStateApplied } from './state.js';
import { createCameraView } from './controls.js';
import { showBanner } from './ui.js';

const WORKERS = 2;        // concurrent snapshot fetches
const REQUEST_GAP_MS = 200;
const CYCLE_REST_MS = 5000; // pause between full refresh sweeps
const GRID_GAP = 10;        // must match #left-dash gap in style.css
const FAVS_KEY = '3dha.favCameras';

let tiles = [];        // {id, tile, img, broken}
let session = 0;       // bumped on every grid rebuild — stale workers stop
let capacity = 0;      // how many tiles fit the column with no scrolling
let gridSig = '';      // capacity + visible ids — skip no-op rebuilds
let favs = new Set();

let overlayOpen = false;
let liveId = null;     // entity shown in the overlay
let liveView = null;   // createCameraView handle while the overlay is up

const $ = (id) => document.getElementById(id);

// #left-dash is position:fixed, so offsetParent is always null — detect
// display:none (own .hidden class or the room-focus/edit/narrow-screen CSS)
// by rendered size instead.
const dashVisible = (dash) => dash.offsetWidth > 0;

function cameraLabel(id) {
  // Ring names every camera "<place> Live view" — redundant inside this grid
  return friendlyName(id).replace(/\s+live view$/i, '');
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------- favorites

function loadFavs() {
  try {
    const raw = JSON.parse(localStorage.getItem(FAVS_KEY));
    if (Array.isArray(raw)) favs = new Set(raw.filter((v) => typeof v === 'string'));
  } catch { /* garbage or private mode — start empty */ }
}

function toggleFav(id) {
  if (favs.has(id)) favs.delete(id);
  else favs.add(id);
  try { localStorage.setItem(FAVS_KEY, JSON.stringify([...favs])); } catch { /* private mode */ }
}

// Favorites first, each group ordered by display name. Grid shows the first
// `capacity`; prev/next in the live view cycles the whole list, so cameras
// that didn't fit can still be reached (and starred into the grid).
function orderedCameras() {
  const byName = (a, b) => cameraLabel(a).localeCompare(cameraLabel(b));
  const all = findEntities('camera.');
  return [
    ...all.filter((id) => favs.has(id)).sort(byName),
    ...all.filter((id) => !favs.has(id)).sort(byName),
  ];
}

// ---------------------------------------------------------------- snapshots

function loadSnapshot(t) {
  return new Promise((resolve) => {
    const done = (ok) => {
      t.img.onload = t.img.onerror = null;
      t.broken = !ok;
      t.tile.classList.toggle('broken', !ok);
      // a failed <img> renders the browser's broken-image glyph — hide it so
      // the tile's 📷 placeholder + label show instead
      t.img.classList.toggle('hidden', !ok);
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
  const dash = $('left-dash');
  let next = 0;
  const worker = async () => {
    while (mySession === session && tiles.length) {
      if (overlayOpen || document.hidden || !dashVisible(dash)) {
        await sleep(1000); // stream up / tab hidden / column hidden — hold
        continue;
      }
      const t = tiles[next++ % tiles.length];
      await loadSnapshot(t);
      if (mySession !== session) return;
      await sleep(next % tiles.length === 0 ? CYCLE_REST_MS : REQUEST_GAP_MS);
    }
  };
  await Promise.all(Array.from({ length: WORKERS }, worker));
}

// ---------------------------------------------------------------- grid

// How many 16:9 tiles fit the fixed column? Measured at runtime so the
// edit-preview top offset and future CSS tweaks are absorbed automatically.
function computeCapacity() {
  const dash = $('left-dash');
  if (!dashVisible(dash)) return; // display:none measures 0 — keep last value
  const tileH = ((dash.clientWidth - GRID_GAP) / 2) * (9 / 16);
  const rows = Math.max(1, Math.floor((dash.clientHeight + GRID_GAP) / (tileH + GRID_GAP)));
  capacity = rows * 2;
}

function renderGrid() {
  const dash = $('left-dash');
  const all = orderedCameras();
  dash.classList.toggle('hidden', !all.length);
  if (!all.length) return;
  if (!capacity) computeCapacity();

  const visible = all.slice(0, capacity);
  const sig = `${capacity}|${visible.join()}`;
  if (sig === gridSig) return; // set unchanged — keep the DOM
  gridSig = sig;

  session += 1; // stop the old pump; tiles are rebuilt below
  for (const t of tiles) { t.img.onload = t.img.onerror = null; t.img.src = ''; }
  tiles = [];
  dash.innerHTML = '';

  for (const id of visible) {
    const tile = document.createElement('div');
    tile.className = 'cam-tile';
    const img = document.createElement('img');
    img.alt = ''; // the .cam-label names the camera; alt text would flash while loading
    const label = document.createElement('div');
    label.className = 'cam-label';
    label.textContent = cameraLabel(id);
    tile.append(img, label);
    if (favs.has(id)) {
      const badge = document.createElement('span');
      badge.className = 'cam-fav-badge';
      badge.textContent = '★';
      tile.appendChild(badge);
    }
    tile.setAttribute('role', 'button');
    tile.setAttribute('aria-label', `Open ${cameraLabel(id)} live view`);
    tile.addEventListener('click', () => openLive(id));
    dash.appendChild(tile);
    tiles.push({ id, tile, img, broken: false });
  }
  pump(session);
}

// ---------------------------------------------------------------- live view

function showCamera(id) {
  liveView?.destroy(); // before creating the next one — one MJPEG stream max
  liveId = id;
  liveView = createCameraView(id, {
    live: true,
    onError: (msg) => showBanner(msg, 4000),
  });
  // stream refused → controls.js already fell back to snapshot mode + banner;
  // staying open in degraded mode beats dumping the user back to the grid
  $('cam-title').textContent = cameraLabel(id);
  syncFavButton();
  $('cam-stage').insertBefore(liveView.el, $('cam-prev'));
}

function syncFavButton() {
  const btn = $('cam-fav');
  const isFav = favs.has(liveId);
  btn.textContent = isFav ? '★' : '☆';
  btn.classList.toggle('fav', isFav);
  btn.setAttribute('aria-pressed', String(isFav));
}

function stepCamera(dir) {
  const all = orderedCameras();
  if (!all.length) return;
  const i = Math.max(0, all.indexOf(liveId));
  showCamera(all[(i + dir + all.length) % all.length]);
}

function onKeydown(e) {
  if (e.key !== 'Escape') return;
  e.stopPropagation(); // focus.js's Esc (exit room focus) must not also fire
  closeLive();
}

function openLive(id) {
  overlayOpen = true; // pump holds while the stream is up
  $('cam-overlay').classList.remove('hidden');
  document.addEventListener('keydown', onKeydown, true);
  showCamera(id);
}

function closeLive() {
  document.removeEventListener('keydown', onKeydown, true);
  liveView?.destroy();
  liveView = null;
  liveId = null;
  $('cam-overlay').classList.add('hidden');
  overlayOpen = false; // pump resumes on its next poll tick
}

// ---------------------------------------------------------------- init

export function initCameras() {
  loadFavs();
  $('cam-close').onclick = closeLive;
  $('cam-prev').onclick = () => stepCamera(-1);
  $('cam-next').onclick = () => stepCamera(1);
  $('cam-fav').onclick = () => {
    if (!liveId) return;
    toggleFav(liveId);
    syncFavButton();
    gridSig = ''; // favorites reorder the grid behind the overlay
    renderGrid();
  };

  let resizeTimer = 0;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { computeCapacity(); renderGrid(); }, 150);
  });

  onStateApplied((entityId) => {
    if (entityId === null || entityId.startsWith('camera.')) renderGrid();
  });
  renderGrid();
}
