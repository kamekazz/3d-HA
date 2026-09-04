// The Outside editor's ADD tray: a bottom sheet of everything you can put in
// the yard, so touching up the exterior is not only erasing what the builder
// drew. Owned by yard.js, which supplies the placement.
//
// Two catalogues in one grid, filtered by the same chips:
//
//   * the YARD's own vocabulary — trees, shrubs, beds, paving, props. Not a
//     hand-written list: environment.js already gives every piece an identity
//     (read "EDITABLE YARD" there), so this reads back the yard that is
//     actually standing and groups it by label. The tray therefore cannot offer
//     a piece environment.js does not draw, and never goes stale when a factory
//     is added or renamed. Adding one is the existing CLONE.
//   * the MODEL LIBRARY — every uploaded .glb, so a bench, a grill, a lamp or a
//     TV can stand outside like any other yard piece. Adding one is a
//     `yard_edits` row carrying `model_id`.
//
// Neither needs new client state: both end up as one row in the same table, so
// undo/redo, erase and the gizmo cover them without knowing the difference.
//
// Thumbnails are shot from the real geometry with the app's own renderer — the
// pattern snapshots.js uses for room cards: render into the live canvas, crop
// it, put the view back in the same task so no frame of it reaches the screen.
// A name cannot separate "Shrub" from "Shrub mound" from "Bush", and it
// certainly cannot tell you what "Rios Pouf Teal" looks like. The library side
// is shot LAZILY, as tiles scroll into view: there are ~250 models and shooting
// them all up front would be seconds of work for pictures nobody scrolled to.
import * as THREE from 'three';
import { api } from './api.js';
import { renderer, renderView } from './scene.js';
import { getYardItems, getYardPickables, isYardEditing } from './environment.js';
import { getInstance } from './models.js';

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------------
// What the tray offers, and how it is grouped
// ---------------------------------------------------------------------------

// Yard kinds the tray does NOT offer, and why. Everything else in
// ITEM_FACTORIES is a discrete thing you might want a second one of.
//   lawn   — one item covering the whole lot; a second lot-sized lawn is not a
//            thing anyone wants, and it is not even clickable (SURFACE_KINDS).
//   street — likewise, the street is the street.
//   piece  — the unscoped runs (a hand-built step platform, a scattered row of
//            cobbles). Real pieces, but they all carry the generic label
//            "Yard piece", so six of them here would be six identical names.
//            They stay duplicable from the panel, where the thing you are
//            copying is the one you just clicked.
const SKIP_KINDS = new Set(['lawn', 'street', 'piece']);

// Chip order and headings. Yard kinds first — this is the yard editor — then
// the library. Model kinds are prefixed `m:` so they can never collide with a
// factory kind: the yard has `plant` (mums, grass clumps) and the library has
// houseplants, and they are not the same chip.
const SECTIONS = [
  ['tree', 'Trees'], ['shrub', 'Shrubs'], ['plant', 'Plants'],
  ['bed', 'Beds'], ['edge', 'Edging'], ['paving', 'Paving'],
  ['prop', 'Props'], ['building', 'Buildings'],
  ['m:outdoor', 'Outdoor'], ['m:lighting', 'Lighting'],
  ['m:seating', 'Seating'], ['m:tables', 'Tables'],
  ['m:storage', 'Storage'], ['m:screens', 'Screens'],
  ['m:appliance', 'Appliances'], ['m:fixtures', 'Fixtures'],
  ['m:plants', 'Houseplants'], ['m:soft', 'Rugs & soft'],
  ['m:decor', 'Decor'], ['m:shell', 'Room shells'], ['m:other', 'Other'],
];

// Kinds shot from higher up: a bed, a slab, a rug and a ceiling are flat, and
// at the ~30° the standing pieces are shot from they collapse to a line.
const FLAT_KINDS = new Set(['bed', 'edge', 'paving', 'm:soft', 'm:shell']);

// ---- classifying a library model -------------------------------------------
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

function modelKind(name) {
  let base = (name || '').trim();
  for (let prev = null; prev !== base;) { prev = base; base = base.replace(VARIANT_SUFFIX, ''); }
  if (SHELL_TAIL.test(base) || /wall wash/i.test(base)) return 'm:shell';
  const low = (name || '').toLowerCase();
  for (const [kind, re] of MODEL_CATS) if (re.test(low)) return kind;
  return 'm:other';
}

const THUMB_PX = 112;
const THUMB_BATCH = 4;      // shot per turn, so a fast scroll stays responsive
const EAGER_TILES = 24;     // roughly a screenful, shot without waiting on the observer

let open = false;
let onAddPiece = null;      // yard.js: (entry) => Promise<void>
let entries = [];           // the whole catalogue
let library = [];           // GET /api/house/models, refreshed on open
let filterKind = 'all';
let query = '';
let busy = false;

// Thumbnails survive a yard rebuild and a re-open: a "Bare tree" and a "Living
// Sofa East" are drawn from the same geometry every time, so re-shooting them
// would be work for an identical picture. Keyed by entry id, module-lifetime.
const thumbs = new Map();

export function isYardKitOpen() {
  return open;
}

export function initYardKit({ onAdd } = {}) {
  onAddPiece = onAdd || null;
  $('yard-add').onclick = () => (open ? closeYardKit() : openYardKit());
  $('yk-close').onclick = closeYardKit;
  $('yk-search').addEventListener('input', (e) => {
    query = e.target.value.trim().toLowerCase();
    paintTiles();
  });
}

export function openYardKit() {
  // The tray's button lives inside #yard-bar, so this is not reachable with the
  // Outside editor shut -- but the yard tiles are shot from the per-item groups
  // that only exist while it is, so refuse rather than paint a tray of blanks.
  if (open || !isYardEditing()) return;
  open = true;
  document.body.classList.add('kit-open');   // lifts the bars clear of the tray
  $('yard-add').classList.add('active');
  $('yard-kit').classList.remove('hidden');
  refreshYardKit();
  // The library can have changed since the last open (the Models button uploads
  // and deletes), so it is re-read every time rather than cached for the
  // session. Fire and forget: the yard half of the tray is already painted.
  api.getModels()
    // GET /api/house/models answers with a bare array, not {models: [...]} --
    // both shapes accepted so this cannot quietly empty the library again.
    .then((res) => {
      library = Array.isArray(res) ? res : (res?.models || []);
      if (open) refreshYardKit();
    })
    .catch((err) => console.warn('model library unavailable:', err));
}

export function closeYardKit() {
  if (!open) return;
  open = false;
  document.body.classList.remove('kit-open');
  $('yard-add').classList.remove('active');
  $('yard-kit').classList.add('hidden');
}

// The item SET changed (a piece added, an undo, a house reload), so the source
// keys the yard tiles clone from have to be re-read.
export function refreshYardKit() {
  if (!open) return;
  entries = buildCatalogue();
  paintChips();
  paintTiles();
}

// ---- the catalogue ---------------------------------------------------------

// Yard entries are one per distinct label, holding every generated piece that
// carries it. Several sources rather than one is the point: there are 17 bare
// trees and 54 shrub mounds out there, all different, so adding five bushes
// gives five different bushes instead of the same one stamped out five times.
// Library entries are one per model, and carry no sources at all.
function buildCatalogue() {
  const by = new Map();
  for (const item of getYardItems()) {
    // Clones are skipped as SOURCES: a clone of a clone is legal but only
    // resolves when its own source row is read first, and there is no reason to
    // reach for one when the generated original is right there. Models are
    // skipped because the library entry below is the way to add another.
    if (item.isClone || item.isModel || SKIP_KINDS.has(item.kind)) continue;
    const id = `yard/${item.kind}/${item.label}`;
    if (!by.has(id)) {
      by.set(id, { id, source: 'yard', kind: item.kind, label: item.label, keys: [] });
    }
    by.get(id).keys.push({ key: item.key, erased: !!item.edit?.deleted });
  }
  const out = [...by.values()];
  for (const m of library) {
    out.push({
      id: `model/${m.id}`, source: 'model', kind: modelKind(m.name),
      label: m.name || `Model ${m.id}`, modelId: m.id,
    });
  }
  const order = new Map(SECTIONS.map(([k], i) => [k, i]));
  return out.sort((a, b) =>
    (order.get(a.kind) ?? 99) - (order.get(b.kind) ?? 99) ||
    a.label.localeCompare(b.label));
}

// A yard source to copy, preferring one that is still standing — cloning an
// erased piece works (environment.js copies its geometry before the deletion
// sweep) but "add a bush" should not depend on a bush the user has hidden.
export function pickSource(entry) {
  const live = entry.keys.filter((k) => !k.erased);
  const pool = live.length ? live : entry.keys;
  return pool[Math.floor(Math.random() * pool.length)]?.key || null;
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
function shootObject(obj, kind) {
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

async function shootEntry(entry) {
  if (entry.source === 'model') {
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
  const g = getYardPickables().find((o) => o.userData.yardKey === pickSource(entry));
  if (!g) return null;
  // clone(true) shares geometry and materials, so the copy costs a matrix and
  // there is nothing to release afterwards.
  const c = g.clone(true);
  c.position.set(0, 0, 0);
  c.rotation.set(0, 0, 0);
  c.scale.setScalar(1);
  c.visible = true;
  return shootObject(c, entry.kind);
}

// ---- the lazy queue --------------------------------------------------------
//
// Only what the user has actually scrolled to. ~250 library models at ~11 ms a
// render is nearly three seconds of work, almost all of it for tiles nobody
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
  }, { root: $('yk-grid'), rootMargin: '160px' });
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
  const bar = $('yk-chips');
  const kinds = new Set(entries.map((e) => e.kind));
  if (filterKind !== 'all' && !kinds.has(filterKind)) filterKind = 'all';
  const named = new Map(SECTIONS);
  const list = [['all', 'All']].concat(
    SECTIONS.filter(([k]) => kinds.has(k)),
    [...kinds].filter((k) => !named.has(k)).map((k) => [k, k]));
  bar.innerHTML = '';
  for (const [kind, name] of list) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'yk-chip' + (kind === filterKind ? ' active' : '');
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
  const grid = $('yk-grid');
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
    tile.className = 'yk-tile';
    tile.title = e.source === 'model'
      ? `Add ${e.label} to the yard`
      : (e.keys.length > 1
        ? `Add one — ${e.keys.length} to pick from, so no two are identical`
        : 'Add one to the yard');
    tile.innerHTML = `<span class="yk-shot"></span>` +
                     `<span class="yk-name">${escapeHtml(e.label)}</span>`;
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
  $('yk-search').placeholder = `Search ${entries.length} pieces…`;
  $('yk-empty').classList.toggle('hidden', list.length > 0);
}

function paintThumbs() {
  for (const [id, tile] of tiles) {
    const url = thumbs.get(id);
    if (url && !tile.querySelector('img')) paintThumb(tile, url);
  }
}

function paintThumb(tile, url) {
  const slot = tile.querySelector('.yk-shot');
  if (!slot) return;
  const img = document.createElement('img');
  img.className = 'yk-thumb';
  img.width = img.height = THUMB_PX;
  img.alt = '';
  img.src = url;
  slot.replaceWith(img);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// One add at a time: the row POSTs, then environment.js rebuilds the whole yard
// around it, and a second click landing mid-rebuild would clone a source key
// from the list this one is about to replace.
async function addOne(entry, tile) {
  if (busy || !onAddPiece) return;
  busy = true;
  tile.classList.add('adding');
  try {
    await onAddPiece(entry);
  } finally {
    busy = false;
    tile.classList.remove('adding');
  }
}
