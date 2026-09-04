// The Outside editor's ADD tray: a bottom sheet of everything the exterior is
// built out of, so touching up the yard is not only erasing what the builder
// drew. Owned by yard.js, which supplies the placement.
//
// The catalogue is not a hand-written list. environment.js already gives every
// tree, shrub, slab and prop an identity (read "EDITABLE YARD" there), so this
// module reads the yard that is actually standing and groups it by label —
// which means the tray can never offer something the builder does not draw, and
// never goes stale when environment.js gains or loses a factory. Adding one is
// the existing CLONE: a `yard_edits` row with `src` pointing at a piece already
// in the yard. No new storage, and undo/redo covers it for free.
//
// Thumbnails are shot from that same geometry with the app's own renderer (the
// pattern snapshots.js uses for room cards: render into the live canvas, crop
// it, restore the view in the same task so no frame of it ever reaches the
// screen). A name alone cannot separate "Shrub" from "Shrub mound" from "Bush";
// a 112px render of the real thing can.
import * as THREE from 'three';
import { renderer, renderView } from './scene.js';
import { getYardItems, getYardPickables, isYardEditing } from './environment.js';

const $ = (id) => document.getElementById(id);

// What the tray does NOT offer, and why. Everything else in ITEM_FACTORIES is
// a discrete thing you might want a second one of.
//   lawn   — one item covering the whole lot; a second lot-sized lawn is not a
//            thing anyone wants, and it is not even clickable (SURFACE_KINDS).
//   street — likewise, the street is the street.
//   piece  — the unscoped runs (a hand-built step platform, a scattered row of
//            cobbles). Real pieces, but they all carry the generic label
//            "Yard piece", so six of them in the tray would be six identical
//            names. They stay duplicable from the panel, where the thing you
//            are copying is the one you just clicked.
const SKIP_KINDS = new Set(['lawn', 'street', 'piece']);

// Section order and headings. Anything with a kind not listed here still shows
// up, under "Other", so a new factory kind is visible before this list knows
// about it.
const SECTIONS = [
  ['tree', 'Trees'], ['shrub', 'Shrubs'], ['plant', 'Plants'],
  ['bed', 'Beds'], ['edge', 'Edging'], ['paving', 'Paving'],
  ['prop', 'Props'], ['building', 'Buildings'],
];

// Kinds that read better from higher up: a bed, a slab and a cobble rim are
// flat, and at the 30° the standing pieces are shot from they turn into a line.
const FLAT_KINDS = new Set(['bed', 'edge', 'paving']);

const THUMB_PX = 112;

let open = false;
let onAddPiece = null;      // yard.js: (entry) => Promise<void>
let entries = [];           // the catalogue, rebuilt on every open/rebuild
let filterKind = 'all';
let busy = false;

// Thumbnails survive a yard rebuild: a "Bare tree" is drawn from the same
// geometry every time, so re-shooting 28 of them on every undo would be work
// for an identical picture. Keyed by kind/label, module-lifetime.
const thumbs = new Map();

export function isYardKitOpen() {
  return open;
}

export function initYardKit({ onAdd } = {}) {
  onAddPiece = onAdd || null;
  $('yard-add').onclick = () => (open ? closeYardKit() : openYardKit());
  $('yk-close').onclick = closeYardKit;
}

export function openYardKit() {
  // The tray's button lives inside #yard-bar, so this is not reachable with the
  // Outside editor shut -- but the tiles are shot from the per-item groups that
  // only exist while it is, so refuse rather than paint a tray of blanks.
  if (open || !isYardEditing()) return;
  open = true;
  document.body.classList.add('kit-open');   // lifts the bars clear of the tray
  $('yard-add').classList.add('active');
  $('yard-kit').classList.remove('hidden');
  refreshYardKit();
}

export function closeYardKit() {
  if (!open) return;
  open = false;
  document.body.classList.remove('kit-open');
  $('yard-add').classList.remove('active');
  $('yard-kit').classList.add('hidden');
}

// The item SET changed (a piece added, an undo, a house reload), so the source
// keys the tiles clone from have to be re-read. Cheap: only the tiles whose
// thumbnail has never been shot cost a render.
export function refreshYardKit() {
  if (!open) return;
  entries = buildCatalogue();
  shootMissingThumbs();
  paintChips();
  paintTiles();
}

// ---- the catalogue ---------------------------------------------------------

// One entry per distinct label, holding every generated piece that carries it.
// Several sources rather than one is the point: there are 17 bare trees and 54
// shrub mounds in this yard, all different, so adding five bushes gives five
// different bushes instead of the same one stamped out five times.
function buildCatalogue() {
  const by = new Map();
  for (const item of getYardItems()) {
    // Clones are skipped as SOURCES: a clone of a clone is legal but only
    // resolves when its own source row is read first, and there is no reason
    // to reach for one when the generated original is right there.
    if (item.isClone || SKIP_KINDS.has(item.kind)) continue;
    const id = `${item.kind}/${item.label}`;
    if (!by.has(id)) by.set(id, { id, kind: item.kind, label: item.label, keys: [] });
    by.get(id).keys.push({ key: item.key, erased: !!item.edit?.deleted });
  }
  const order = new Map(SECTIONS.map(([k], i) => [k, i]));
  return [...by.values()].sort((a, b) =>
    (order.get(a.kind) ?? 99) - (order.get(b.kind) ?? 99) ||
    a.label.localeCompare(b.label));
}

// A source to copy, preferring one that is still standing — cloning an erased
// piece works (environment.js copies its geometry before the deletion sweep)
// but "add a bush" should not depend on a bush the user has hidden.
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

// Shoot every tile that has never been shot, then put the real view back — all
// in ONE task, so the browser never composites a frame with a thumbnail in it.
// Measured here: ~11 ms a piece, so a first open of the full 28-tile tray costs
// about a third of a second, once.
function shootMissingThumbs() {
  const todo = entries.filter((e) => !thumbs.has(e.id));
  if (!todo.length) return;
  initThumbScene();
  const groups = new Map(getYardPickables().map((g) => [g.userData.yardKey, g]));
  for (const e of todo) {
    const g = groups.get(pickSource(e));
    if (g) thumbs.set(e.id, shoot(g, e.kind));
  }
  renderView();   // repaint the live scene before this task yields
}

const _box = new THREE.Box3();
const _size = new THREE.Vector3();
const _center = new THREE.Vector3();

function shoot(group, kind) {
  // clone(true) shares geometry and materials, so the copy costs a matrix and
  // there is nothing to dispose afterwards.
  const c = group.clone(true);
  c.position.set(0, 0, 0);
  c.rotation.set(0, 0, 0);
  c.scale.setScalar(1);
  c.visible = true;
  mini.add(c);

  // Same bounding-sphere fit focus.js and snapshots.js use, against the
  // centred SQUARE crop of a canvas that is almost never square.
  const src = renderer.domElement;
  const aspect = src.width / src.height;
  _box.setFromObject(c);
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
  const url = thumbCanvas.toDataURL('image/png');
  mini.remove(c);
  return url;
}

// ---- the tray --------------------------------------------------------------

function paintChips() {
  const bar = $('yk-chips');
  const kinds = [...new Set(entries.map((e) => e.kind))];
  if (!kinds.includes(filterKind)) filterKind = 'all';
  const named = new Map(SECTIONS);
  const list = [['all', 'All']].concat(
    SECTIONS.filter(([k]) => kinds.includes(k)),
    kinds.filter((k) => !named.has(k)).map((k) => [k, k]));
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

function paintTiles() {
  const grid = $('yk-grid');
  grid.innerHTML = '';
  const shown = entries.filter((e) => filterKind === 'all' || e.kind === filterKind);
  for (const e of shown) {
    const tile = document.createElement('button');
    tile.type = 'button';
    tile.className = 'yk-tile';
    tile.title = e.keys.length > 1
      ? `Add one — ${e.keys.length} to pick from, so no two are identical`
      : 'Add one to the yard';
    const thumb = thumbs.get(e.id);
    tile.innerHTML =
      (thumb ? `<img class="yk-thumb" src="${thumb}" alt="" width="${THUMB_PX}" height="${THUMB_PX}">`
             : '<span class="yk-thumb yk-thumb-blank"></span>') +
      `<span class="yk-name">${e.label}</span>`;
    tile.onclick = () => addOne(e, tile);
    grid.appendChild(tile);
  }
  $('yk-empty').classList.toggle('hidden', shown.length > 0);
}

// One add at a time: the clone POSTs, then environment.js rebuilds the whole
// yard around it, and a second click landing mid-rebuild would clone a source
// key from the list this one is about to replace.
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
