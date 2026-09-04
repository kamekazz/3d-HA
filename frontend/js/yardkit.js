// The Outside editor's half of the add tray: what the YARD offers, and where
// its pictures come from. The sheet itself is addkit.js — this module only
// builds the catalogue and hands it over, so the room editor's tray and this
// one are literally the same widget.
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
import { api } from './api.js';
import { getYardItems, getYardPickables, isYardEditing } from './environment.js';
import {
  openAddKit, closeAddKit, refreshAddKit, isAddKitOpen, modelEntries,
  MODEL_SECTIONS,
} from './addkit.js';

const $ = (id) => document.getElementById(id);

const KIT_ID = 'yard';

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
// the library's own, appended verbatim.
const SECTIONS = [
  ['tree', 'Trees'], ['shrub', 'Shrubs'], ['plant', 'Plants'],
  ['bed', 'Beds'], ['edge', 'Edging'], ['paving', 'Paving'],
  ['prop', 'Props'], ['building', 'Buildings'],
  ...MODEL_SECTIONS,
];

let library = [];           // GET /api/house/models, refreshed on open
let onAddPiece = null;      // yard.js: (entry) => Promise<void>

export function isYardKitOpen() {
  return isAddKitOpen(KIT_ID);
}

export function initYardKit({ onAdd } = {}) {
  onAddPiece = onAdd || null;
  $('yard-add').onclick = () => (isYardKitOpen() ? closeYardKit() : openYardKit());
}

export function openYardKit() {
  // The tray's button lives inside #yard-bar, so this is not reachable with the
  // Outside editor shut -- but the yard tiles are shot from the per-item groups
  // that only exist while it is, so refuse rather than paint a tray of blanks.
  if (isYardKitOpen() || !isYardEditing()) return;
  $('yard-add').classList.add('active');
  openAddKit({
    id: KIT_ID,
    title: 'Add to the yard',
    sections: SECTIONS,
    build: buildCatalogue,
    resolve: resolveYardPiece,
    onAdd: (entry) => onAddPiece?.(entry),
    onClose: () => $('yard-add').classList.remove('active'),
  });
  // The library can have changed since the last open (the Models button uploads
  // and deletes), so it is re-read every time rather than cached for the
  // session. Fire and forget: the yard half of the tray is already painted.
  api.getModels()
    // GET /api/house/models answers with a bare array, not {models: [...]} --
    // both shapes accepted so this cannot quietly empty the library again.
    .then((res) => {
      library = Array.isArray(res) ? res : (res?.models || []);
      refreshYardKit();
    })
    .catch((err) => console.warn('model library unavailable:', err));
}

export function closeYardKit() {
  closeAddKit(KIT_ID);   // its onClose unpresses the bar's button
}

// The item SET changed (a piece added, an undo, a house reload), so the source
// keys the yard tiles clone from have to be re-read.
export function refreshYardKit() {
  refreshAddKit(KIT_ID);
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
  for (const e of out) {
    e.hint = e.keys.length > 1
      ? `Add one — ${e.keys.length} to pick from, so no two are identical`
      : 'Add one to the yard';
  }
  for (const e of modelEntries(library)) {
    out.push({ ...e, hint: `Add ${e.label} to the yard` });
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

// The geometry behind a yard tile's picture: the piece itself, posed at the
// origin. clone(true) shares geometry and materials, so the copy costs a matrix
// and there is nothing to release afterwards.
function resolveYardPiece(entry) {
  const g = getYardPickables().find((o) => o.userData.yardKey === pickSource(entry));
  if (!g) return null;
  const c = g.clone(true);
  c.position.set(0, 0, 0);
  c.rotation.set(0, 0, 0);
  c.scale.setScalar(1);
  c.visible = true;
  return c;
}
