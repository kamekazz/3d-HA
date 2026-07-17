// Left-column camera grid (2 columns of idling snapshots, favorites first,
// sliced to exactly what fits — the wall tablet never scrolls) + a full-screen
// all-cameras view (tiles sized so every camera fits the screen) + a
// full-screen single-camera live view. When cameras overflow the column, the
// grid's last slot becomes an "All cameras" button. Snapshots load through a
// small round-robin queue (2 in flight, short gap between requests) — a house
// can have dozens of cameras, and letting every tile poll independently floods
// HA/Nabu Casa with concurrent camera_proxy calls that 502 and then
// retry-storm. A failed tile simply rejoins the cycle. Tapping a tile opens
// the live MJPEG view (one stream max — each holds a backend worker thread);
// the queue pauses while a stream is up, the tab is hidden, or CSS hides the
// column.
import { findEntities, friendlyName, onStateApplied } from './state.js';
import { createCameraView } from './controls.js';
import { showBanner } from './ui.js';

const WORKERS = 2;        // concurrent snapshot fetches
const REQUEST_GAP_MS = 200;
const CYCLE_REST_MS = 5000; // pause between full refresh sweeps
const GRID_GAP = 10;        // must match #left-dash / #cam-all-grid gap
const FAVS_KEY = '3dha.favCameras';

let gridTiles = [];    // {id, tile, img, broken} — left-column grid
let allTiles = [];     // same shape — all-cameras overlay
let tiles = [];        // whichever list the pump is currently sweeping
let session = 0;       // bumped on every pump restart — stale workers stop
let capacity = 0;      // how many tiles fit the column with no scrolling
let gridSig = '';      // capacity + visible ids — skip no-op rebuilds
let favs = new Set();

let allOpen = false;   // all-cameras overlay up
let overlayOpen = false; // live view up
let liveId = null;     // entity shown in the live view
let liveView = null;   // createCameraView handle while the live view is up

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

// Favorites first, each group ordered by display name. The left grid shows
// the first slice; the all-cameras view and prev/next cycle the whole list.
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

// Round-robin over the active tile list forever (until the session changes):
// workers share one advancing index, so a slow camera never blocks the rest
// of the grid; whichever worker wraps past the last tile takes the long rest.
async function pump(mySession) {
  const dash = $('left-dash');
  let next = 0;
  const worker = async () => {
    while (mySession === session && tiles.length) {
      if (overlayOpen || document.hidden || (!allOpen && !dashVisible(dash))) {
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

function startPump(list) {
  tiles = list;
  session += 1;
  pump(session);
}

function teardownTiles(list) {
  for (const t of list) { t.img.onload = t.img.onerror = null; t.img.src = ''; }
}

// ---------------------------------------------------------------- tiles

function makeCameraTile(id) {
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
  return { id, tile, img, broken: false };
}

// ---------------------------------------------------------------- left grid

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

  // cameras overflow the column → the last slot becomes the "All" button
  const overflow = all.length > capacity;
  const visible = overflow ? all.slice(0, capacity - 1) : all;
  const sig = `${capacity}|${all.length}|${visible.join()}`;
  if (sig === gridSig) return; // set unchanged — keep the DOM
  gridSig = sig;

  teardownTiles(gridTiles);
  gridTiles = [];
  dash.innerHTML = '';

  for (const id of visible) {
    const t = makeCameraTile(id);
    dash.appendChild(t.tile);
    gridTiles.push(t);
  }
  if (overflow) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cam-tile cam-all-btn';
    btn.innerHTML =
      '<span class="cab-icon">⊞</span><span class="cab-text">All cameras</span>' +
      `<span class="cab-count">${all.length}</span>`;
    btn.onclick = openAll;
    dash.appendChild(btn);
  }
  if (!allOpen) startPump(gridTiles); // all-view owns the pump while it's up
}

// ---------------------------------------------------------------- all view

// Pick the column count that maximizes tile size while every camera fits the
// stage with no scrolling (16:9 tiles, GRID_GAP gaps).
function layoutAllGrid() {
  const grid = $('cam-all-grid');
  const n = allTiles.length;
  if (!n) return;
  const style = getComputedStyle(grid);
  const W = grid.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  const H = grid.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
  let best = { cols: Math.ceil(Math.sqrt(n)), w: 0 };
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols);
    const w = (W - (cols - 1) * GRID_GAP) / cols;
    const h = w * (9 / 16);
    if (w > best.w && rows * h + (rows - 1) * GRID_GAP <= H) best = { cols, w };
  }
  grid.style.gridTemplateColumns = `repeat(${best.cols}, ${Math.floor(best.w)}px)`;
}

let allSig = ''; // camera set+order — skip rebuilds on mere state changes

function renderAll() {
  const grid = $('cam-all-grid');
  const ids = orderedCameras();
  const sig = ids.join();
  if (sig === allSig) return;
  allSig = sig;
  teardownTiles(allTiles);
  allTiles = [];
  grid.innerHTML = '';
  for (const id of ids) {
    const t = makeCameraTile(id);
    grid.appendChild(t.tile);
    allTiles.push(t);
  }
  layoutAllGrid();
  startPump(allTiles);
}

function onAllKeydown(e) {
  if (e.key !== 'Escape' || overlayOpen) return; // live view's Esc wins
  e.stopPropagation(); // focus.js's Esc (exit room focus) must not also fire
  closeAll();
}

function openAll() {
  allOpen = true;
  $('cam-all').classList.remove('hidden');
  document.addEventListener('keydown', onAllKeydown, true);
  renderAll();
}

function closeAll() {
  document.removeEventListener('keydown', onAllKeydown, true);
  teardownTiles(allTiles);
  allTiles = [];
  allSig = '';
  $('cam-all-grid').innerHTML = '';
  $('cam-all').classList.add('hidden');
  allOpen = false;
  startPump(gridTiles);
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
  $('cam-all-close').onclick = closeAll;
  $('cam-prev').onclick = () => stepCamera(-1);
  $('cam-next').onclick = () => stepCamera(1);
  $('cam-fav').onclick = () => {
    if (!liveId) return;
    toggleFav(liveId);
    syncFavButton();
    gridSig = ''; // favorites reorder the grids behind the overlay
    renderGrid();
    if (allOpen) renderAll();
  };

  let resizeTimer = 0;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      computeCapacity();
      renderGrid();
      if (allOpen) layoutAllGrid();
    }, 150);
  });

  onStateApplied((entityId) => {
    if (entityId === null || entityId.startsWith('camera.')) {
      renderGrid();
      if (allOpen) renderAll();
    }
  });
  renderGrid();
}
