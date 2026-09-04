// The ADD tray: one bottom sheet of things you can put into the scene, opened
// by whoever wants it and filled from whatever catalogue they hand over.
//
// There are two callers and they want the same widget for the same reason —
// an editor that can only ever move and erase what is already there is half an
// editor:
//
//   * yardkit.js — the Outside editor. Its catalogue is the yard's own
//     vocabulary (trees, shrubs, beds, paving, props, read back off the yard
//     that is actually standing) plus the whole model library.
//   * ui.js — the room editor's Furniture & objects section. Its catalogue is
//     the model library alone: a room has no procedural vocabulary, its
//     contents ARE .glb files.
//
// This module owns the sheet, the chips, the search, the tiles and their
// pictures. It owns no domain: a caller passes entries and an onAdd, and what
// an "entry" means past `id/kind/label` is the caller's business.
//
// Thumbnails are shot from the real geometry with the app's own renderer — the
// pattern snapshots.js uses for room cards: render into the live canvas, crop
// it, put the view back in the same task so no frame of it reaches the screen.
// A name cannot separate "Shrub" from "Shrub mound" from "Bush", and it
// certainly cannot tell you what "Rios Pouf Teal" looks like. Library tiles are
// shot LAZILY, as they scroll into view: there are ~290 models and shooting
// them all up front would be seconds of work for pictures nobody scrolled to.
import * as THREE from 'three';
import { renderer, renderView } from './scene.js';
import { getInstance } from './models.js';

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------------
// Classifying a library model
// ---------------------------------------------------------------------------
//
// The library is named `<Room> <Thing>` — "Living Sofa South", "Kitchen Range",
// "Master Closet Wall Wash Skins" — so the THING is at the end and the room at
// the front. Two rules fall out of that and they are the whole classifier:
//
//   * strip trailing position/variant words first ("North", "Two", "Dark"), or
//     "Living Window North" reads as a compass point rather than a window;
//   * then a name ENDING in an architectural noun is room shell. Anchoring to
//     the end is what separates "Printers Ceiling" (the ceiling of the room
//     called Printers) from "Ceiling Fan" (a fan), and "Dining Floor" from
//     "Living Floor Rug" — a keyword search anywhere in the name gets both of
//     those backwards.
//
// Everything else is a first-match-wins keyword sweep. It is a convenience for
// finding things, not a contract: a piece in the wrong chip is still one search
// away, and nothing but the chip depends on the answer.
const VARIANT_SUFFIX =
  /\s+(north|south|east|west|[nsew]|one|two|three|[ab]|left|right|dark|small|large|round|drum|grey|gray|teal|white|\d+)$/i;
const SHELL_TAIL =
  /(ceilings?|baseboards?|floors?|walls?|wall wash(es)?|openings?|windows?|doors?|planks?|skins?|crown|vents?|trim|casings?|lining|treads?|rail|flight|fittings|pier|shadows?|balustrade|slider|moulding|stairwell|house|steps)$/i;
const MODEL_CATS = [
  ['m:outdoor', /backyard|frontyard|driveway|porch|deck|patio|parasol|grill|outdoor/],
  ['m:lighting', /lamp|sconce|chandelier|pendant|lantern/],
  ['m:screens', /\btvs?\b|monitor|projector|arcade cabinet/],
  ['m:seating', /sofa|chair|stool|bench|ottoman|pouf|sectional|chaise|booth|lounge|\bbeds?\b/],
  ['m:plants', /plant|fig tree|fern|succulent|planter|wreath|flower|rubber/],
  ['m:soft', /\brugs?\b|runner|carpet|\bmats?\b|cushions?|towels?|curtain|pillow|\bnap\b/],
  ['m:fixtures', /toilet|shower|\btub\b|vanity|sink|fireplace/],
  ['m:appliance', /fridge|range|oven|washer|dryer|dishwasher|\bfans?\b|heater|vacuum|extinguisher|printers?|speaker|trash/],
  ['m:tables', /\btables?\b|desks?|console|island|nightstand|counter|buffet|workstation/],
  ['m:storage', /dresser|cabinets?|shelf|shelves|shelving|chest|closet|wardrobe|etagere|rack|basket|\bbin\b|crate|drawer|cubby|stock|uppers|pegboard/],
  ['m:decor', /\bart\b|mirror|clock|decor|clutter|banner|birdcage|gallery|frame|props|panels?|boards|gear|brooms|paper|items/],
];

export function modelKind(name) {
  let base = (name || '').trim();
  for (let prev = null; prev !== base;) { prev = base; base = base.replace(VARIANT_SUFFIX, ''); }
  if (SHELL_TAIL.test(base) || /wall wash/i.test(base)) return 'm:shell';
  const low = (name || '').toLowerCase();
  for (const [kind, re] of MODEL_CATS) if (re.test(low)) return kind;
  return 'm:other';
}

// Chip order and headings for the library half. Model kinds are prefixed `m:`
// so they can never collide with a yard factory kind: the yard has `plant`
// (mums, grass clumps) and the library has houseplants, and they are not the
// same chip.
export const MODEL_SECTIONS = [
  ['m:seating', 'Seating'], ['m:tables', 'Tables'], ['m:storage', 'Storage'],
  ['m:lighting', 'Lighting'], ['m:appliance', 'Appliances'],
  ['m:fixtures', 'Fixtures'], ['m:screens', 'Screens'],
  ['m:soft', 'Rugs & soft'], ['m:plants', 'Houseplants'],
  ['m:decor', 'Decor'], ['m:outdoor', 'Outdoor'],
  ['m:shell', 'Room shells'], ['m:other', 'Other'],
];

// One catalogue entry per library model. Both callers offer the library, and
// both want it grouped and labelled the same way.
export function modelEntries(models) {
  return (models || []).map((m) => ({
    id: `model/${m.id}`, source: 'model', kind: modelKind(m.name),
    label: m.name || `Model ${m.id}`, modelId: m.id,
  }));
}

// Kinds shot from higher up: a bed, a slab, a rug and a ceiling are flat, and
// at the ~30° the standing pieces are shot from they collapse to a line.
const FLAT_KINDS = new Set(['bed', 'edge', 'paving', 'm:soft', 'm:shell']);

const THUMB_PX = 112;
const THUMB_BATCH = 4;      // shot per turn, so a fast scroll stays responsive
const EAGER_TILES = 24;     // roughly a screenful, shot without waiting on the observer

// The catalogue currently in the tray:
//   { id, title, sections, noun?, inset?, build(), resolve(entry),
//     onAdd(entry), onClose() }
// `id` is how a caller asks whether the tray is ITS tray — both editors can be
// on screen at once in principle, and neither may close or refresh the other's.
let spec = null;
let entries = [];
let filterKind = 'all';
let query = '';
let busy = false;

// Thumbnails survive a rebuild, a re-open and a switch between catalogues: a
// "Bare tree" and a "Living Sofa East" are drawn from the same geometry every
// time, so re-shooting them would be work for an identical picture. Keyed by
// entry id, module-lifetime.
const thumbs = new Map();

export function isAddKitOpen(id) {
  return !!spec && (id === undefined || spec.id === id);
}

export function initAddKit() {
  $('ak-close').onclick = () => closeAddKit();
  $('ak-search').addEventListener('input', (e) => {
    query = e.target.value.trim().toLowerCase();
    paintTiles();
  });
}

// Fill the tray and show it. Opening it over another catalogue takes the sheet
// away from whoever had it, which is a close as far as they are concerned --
// there is one sheet, and the button they opened it with has to unpress.
export function openAddKit(next) {
  spec?.onClose?.();
  spec = next;
  filterKind = 'all';
  query = '';
  $('ak-search').value = '';
  $('ak-title').textContent = spec.title || 'Add';
  document.body.classList.add('kit-open');   // lifts the bottom bars clear
  // Inset past the side panels rather than run tiles under them: the room
  // editor reaches the bottom of the screen and sits ABOVE the tray (z 35 to
  // 26), so several columns of the yard's full-width sheet would be behind it.
  document.body.classList.toggle('kit-inset', !!spec.inset);
  $('add-kit').classList.remove('hidden');
  refreshAddKit();
}

export function closeAddKit(id) {
  if (!isAddKitOpen(id)) return;
  // The owner gets told, because the tray is opened from a button that has to
  // come back out of its pressed state however it was shut -- the sheet's own
  // close, Escape, or the editor going away underneath it.
  const closing = spec;
  spec = null;
  closing.onClose?.();
  entries = [];
  document.body.classList.remove('kit-open', 'kit-inset');
  $('add-kit').classList.add('hidden');
}

// The entry SET changed (a piece added, an undo, a model uploaded), so the
// catalogue has to be rebuilt from whatever the caller is holding now.
export function refreshAddKit(id) {
  if (!isAddKitOpen(id)) return;
  entries = spec.build() || [];
  paintChips();
  paintTiles();
}

// ---- thumbnails ------------------------------------------------------------

let mini = null, thumbCam = null, thumbCanvas = null, thumbCtx = null;

function initThumbScene() {
  if (mini) return;
  mini = new THREE.Scene();
  // The tile's own ground colour (--surface-1), so the render reads as a lit
  // object on the tile rather than a photograph pasted onto it. The app's
  // renderer has no alpha buffer, so this is how transparency is faked.
  mini.background = new THREE.Color(0x272729);
  mini.add(new THREE.HemisphereLight(0xdfe8f5, 0x2a2b28, 2.0));
  const key = new THREE.DirectionalLight(0xfff4e0, 2.2);
  key.position.set(3, 6, 4);
  mini.add(key);
  thumbCam = new THREE.PerspectiveCamera(35, 1, 0.05, 500);
  thumbCanvas = document.createElement('canvas');
  thumbCanvas.width = thumbCanvas.height = THUMB_PX;
  thumbCtx = thumbCanvas.getContext('2d');
}

const _box = new THREE.Box3();
const _size = new THREE.Vector3();
const _center = new THREE.Vector3();

// Render one detached object and read the pixels back. Synchronous end to end,
// INCLUDING the restore: between the render and renderView() the live canvas is
// showing a thumbnail, so an await in there would let the browser composite a
// frame of it. The caller does its awaiting before it gets here.
export function shootObject(obj, kind) {
  initThumbScene();
  mini.add(obj);

  // Same bounding-sphere fit focus.js and snapshots.js use, against the centred
  // SQUARE crop of a canvas that is almost never square.
  const src = renderer.domElement;
  const aspect = src.width / src.height;
  _box.setFromObject(obj);
  _box.getCenter(_center);
  const radius = Math.max(0.5 * _box.getSize(_size).length(), 0.2);
  thumbCam.aspect = aspect;
  thumbCam.updateProjectionMatrix();
  const vFov = THREE.MathUtils.degToRad(thumbCam.fov);
  const fit = aspect > 1 ? vFov : 2 * Math.atan(Math.tan(vFov / 2) * aspect);
  const dist = 1.25 * radius / Math.sin(fit / 2);
  const az = THREE.MathUtils.degToRad(-35);
  const polar = FLAT_KINDS.has(kind) ? 0.72 : 1.05;   // from +Y: ~48° / ~30° up
  thumbCam.position.set(
    _center.x + dist * Math.sin(polar) * Math.sin(az),
    _center.y + dist * Math.cos(polar),
    _center.z + dist * Math.sin(polar) * Math.cos(az));
  thumbCam.lookAt(_center);

  renderer.render(mini, thumbCam);
  const s = Math.min(src.width, src.height);
  thumbCtx.clearRect(0, 0, THUMB_PX, THUMB_PX);
  thumbCtx.drawImage(src, (src.width - s) / 2, (src.height - s) / 2, s, s,
                     0, 0, THUMB_PX, THUMB_PX);
  const blank = isBlank();
  const url = blank ? null : thumbCanvas.toDataURL('image/png');
  mini.remove(obj);
  renderView();          // the live scene is back before this task yields
  return url;
}

// Did the render actually draw anything? A shoot that lands while the drawing
// buffer is being resized (a window resize, a pane reflow) reads back as
// nothing but the clear colour, and a thumbnail is CACHED for the life of the
// module -- so a blank one is a tile that stays empty forever, which is exactly
// what was seen. Returning null instead means it is simply not cached, and the
// next repaint of the grid queues it again.
function isBlank() {
  const d = thumbCtx.getImageData(0, 0, THUMB_PX, THUMB_PX).data;
  const step = 4 * 13;   // ~970 samples, enough to find any drawn pixel
  for (let i = step; i < d.length; i += step) {
    if (d[i] !== d[0] || d[i + 1] !== d[1] || d[i + 2] !== d[2]) return false;
  }
  return true;
}

// getInstance shares BufferGeometry with the model cache and clones only the
// materials, so a thumbnail instance may release the latter and must not touch
// the former — the same rule environment.js disposeCar spells out.
function disposeInstance(obj) {
  obj.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.dispose();
  });
}

// A library model is shot the same way for either catalogue, so this module
// does it; anything else is the caller's geometry and goes through resolve().
async function shootEntry(entry) {
  if (entry.modelId) {
    let inst;
    try {
      inst = await getInstance(entry.modelId, 'bottom');
    } catch (err) {
      console.warn('no thumbnail for model %s:', entry.modelId, err);
      return null;
    }
    const url = shootObject(inst, entry.kind);
    disposeInstance(inst);
    return url;
  }
  const obj = await spec?.resolve?.(entry);
  return obj ? shootObject(obj, entry.kind) : null;
}

// ---- the lazy queue --------------------------------------------------------
//
// Only what the user has actually scrolled to. ~290 library models at ~11 ms a
// render is over three seconds of work, almost all of it for tiles nobody
// looked at, and it would have to happen with the tray already on screen.

const queue = [];
let draining = false;
let observer = null;

function ensureObserver() {
  if (observer) return observer;
  observer = new IntersectionObserver((rows) => {
    for (const row of rows) {
      if (!row.isIntersecting) continue;
      const entry = row.target.__entry;
      observer.unobserve(row.target);
      if (entry && !thumbs.has(entry.id)) queue.push(entry);
    }
    drain();
  }, { root: $('ak-grid'), rootMargin: '160px' });
  return observer;
}

async function drain() {
  if (draining) return;
  draining = true;
  try {
    while (queue.length) {
      let painted = false;
      for (const entry of queue.splice(0, THUMB_BATCH)) {
        if (thumbs.has(entry.id)) continue;
        const url = await shootEntry(entry);
        if (!url) continue;
        thumbs.set(entry.id, url);
        painted = true;
      }
      if (painted) paintThumbs();
      // let the frame land before the next batch, so scrolling stays smooth
      await new Promise((r) => setTimeout(r, 0));
    }
  } finally {
    draining = false;
  }
}

// ---- the tray --------------------------------------------------------------

function paintChips() {
  const bar = $('ak-chips');
  const kinds = new Set(entries.map((e) => e.kind));
  if (filterKind !== 'all' && !kinds.has(filterKind)) filterKind = 'all';
  const named = new Map(spec.sections);
  const list = [['all', 'All']].concat(
    spec.sections.filter(([k]) => kinds.has(k)),
    [...kinds].filter((k) => !named.has(k)).map((k) => [k, k]));
  bar.innerHTML = '';
  for (const [kind, name] of list) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'ak-chip' + (kind === filterKind ? ' active' : '');
    b.textContent = name;
    b.onclick = () => { filterKind = kind; paintChips(); paintTiles(); };
    bar.appendChild(b);
  }
}

function shown() {
  return entries.filter((e) =>
    (filterKind === 'all' || e.kind === filterKind) &&
    (!query || e.label.toLowerCase().includes(query)));
}

const tiles = new Map();   // entry id -> the tile element currently rendered

function paintTiles() {
  const grid = $('ak-grid');
  const io = ensureObserver();
  io.disconnect();
  queue.length = 0;
  grid.innerHTML = '';
  tiles.clear();
  grid.scrollTop = 0;
  const list = shown();
  for (const e of list) {
    const tile = document.createElement('button');
    tile.type = 'button';
    tile.className = 'ak-tile';
    tile.title = e.hint || `Add ${e.label}`;
    tile.innerHTML = `<span class="ak-shot"></span>` +
                     `<span class="ak-name">${escapeHtml(e.label)}</span>`;
    tile.onclick = () => addOne(e, tile);
    tile.__entry = e;
    grid.appendChild(tile);
    tiles.set(e.id, tile);
    if (thumbs.has(e.id)) paintThumb(tile, thumbs.get(e.id));
    else io.observe(tile);
  }
  // The first screenful is queued outright rather than waited for. An
  // IntersectionObserver delivers on the frame lifecycle, which a browser
  // suspends in a backgrounded or occluded tab exactly as it suspends rAF — so
  // a tray opened and left unlooked-at would come back to a grid of blanks.
  // These are the tiles that are on screen anyway; the observer covers the
  // scroll.
  for (const e of list.slice(0, EAGER_TILES)) {
    if (!thumbs.has(e.id)) queue.push(e);
  }
  drain();
  $('ak-search').placeholder =
    `Search ${entries.length} ${spec.noun || 'pieces'}…`;
  $('ak-empty').classList.toggle('hidden', list.length > 0);
}

function paintThumbs() {
  for (const [id, tile] of tiles) {
    const url = thumbs.get(id);
    if (url && !tile.querySelector('img')) paintThumb(tile, url);
  }
}

function paintThumb(tile, url) {
  const slot = tile.querySelector('.ak-shot');
  if (!slot) return;
  const img = document.createElement('img');
  img.className = 'ak-thumb';
  img.width = img.height = THUMB_PX;
  img.alt = '';
  img.src = url;
  slot.replaceWith(img);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// One add at a time: the row POSTs, then the scene rebuilds around it, and a
// second click landing mid-rebuild would work off the list this one is about to
// replace.
async function addOne(entry, tile) {
  if (busy || !spec?.onAdd) return;
  busy = true;
  tile.classList.add('adding');
  try {
    await spec.onAdd(entry);
  } finally {
    busy = false;
    tile.classList.remove('adding');
  }
}
