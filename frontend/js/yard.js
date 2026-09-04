// The Outside editor: touch up the exterior the way the room editor touches up
// a room. Trees, shrubs, beds, paving, props, the neighbours and the street are
// all one grabbable piece each — click one in the 3D view, drag it with the
// usual gizmo, erase it, put it back, or duplicate it.
//
// This module owns only the UI and the network. The pieces themselves come from
// environment.js, which builds the whole exterior procedurally and files every
// geometry under an item key — read "EDITABLE YARD" there first, it explains
// why a tree has an identity at all. What gets stored is the DELTA against that
// generated yard, never the yard itself.
import * as THREE from 'three';
import { api } from './api.js';
import { showAlert, showConfirm } from './dialog.js';
import { setSelected, getSelected, onDragMoved, setGizmoMode } from './drag.js';
import {
  setYardEditing, isYardEditing, getYardItems, getYardItem, getYardPickables,
  getYardClickTargets, rebuildYard, applyYardEdit, dropYardEdit,
} from './environment.js';
import { setLevel, getBuildingBox } from './house.js';
import { exitFocus } from './focus.js';
import { camera, controls } from './scene.js';
import { appMode, showBanner, setActiveLevelBtn } from './ui.js';
import {
  initYardKit, closeYardKit, refreshYardKit, isYardKitOpen, pickSource,
} from './yardkit.js';

const $ = (id) => document.getElementById(id);

let open = false;
let selectedKey = null;
let onDoneEditing = null;   // main.js hands us the reload it wants on close

export function isYardEditorOpen() {
  return open;
}

// main.js raycasts these before rooms while the editor is open. Empty
// otherwise, so the viewer never pays for it.
export function yardPickTargets() {
  return open ? getYardClickTargets() : [];
}

export function initYardEditor({ onClose } = {}) {
  onDoneEditing = onClose || null;
  $('btn-yard').onclick = () => (open ? closeYardEditor() : openYardEditor());
  $('yard-close').onclick = closeYardEditor;
  $('yp-close').onclick = () => selectYardPiece(null);

  // The add tray owns its own button and its own tiles; it hands us back the
  // catalogue entry that was tapped and we decide where the piece lands.
  initYardKit({ onAdd: addFromKit });

  $('yp-erase').onclick = eraseSelected;
  $('yp-duplicate').onclick = duplicateSelected;
  $('yp-reset').onclick = resetSelected;
  $('yard-reset-all').onclick = resetEverything;

  for (const id of ['yp-x', 'yp-y', 'yp-z', 'yp-rot', 'yp-scale']) {
    $(id).addEventListener('change', onNumberEdit);
  }

  // Delete erases the selected piece, the way it deletes a selected room in the
  // planner. Skipped while typing, or the panel's own number fields would eat
  // a backspace as an erase.
  window.addEventListener('keydown', (e) => {
    if (!open) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target?.tagName)) return;
    // Escape unwinds one layer at a time: the selection first, then the tray.
    if (!selectedKey) {
      if (e.key === 'Escape' && isYardKitOpen()) closeYardKit();
      return;
    }
    if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault();
      eraseSelected();
    } else if (e.key === 'Escape') {
      selectYardPiece(null);
    }
  });

  // The gizmo finished a gesture on a yard piece: drag.js has already saved it
  // and folded it into environment.js's copy, so this only refreshes the panel.
  onDragMoved(({ kind, id }) => {
    if (kind !== 'yard' || id !== selectedKey) return;
    paintPanel(getYardItem(selectedKey));
  });

  // Leaving edit mode entirely closes the editor with it.
  window.addEventListener('appModeChanged', (e) => {
    if (open && e.detail.mode !== 'edit') closeYardEditor();
  });
}

export function openYardEditor() {
  if (open || appMode !== 'edit') return;
  open = true;
  exitFocus({ flyBack: false });
  setLevel('all');            // the exterior only exists in the whole-house view
  setActiveLevelBtn('all');
  setYardEditing(true);       // environment.js rebuilds one mesh per piece
  setGizmoMode('translate');
  $('btn-yard').classList.add('active');
  $('yard-bar').classList.remove('hidden');
  paintErasedList();
  showBanner('Outside: click a tree, shrub, slab or prop to move, scale or erase it '
             + '— or hit Add to drop a new one in.', 4500);
}

export function closeYardEditor() {
  if (!open) return;
  open = false;
  selectYardPiece(null);
  closeYardKit();
  setYardEditing(false);      // back to the six merged meshes
  $('btn-yard').classList.remove('active');
  $('yard-bar').classList.add('hidden');
  $('yard-panel').classList.add('hidden');
  onDoneEditing?.();
}

// ---- selection -------------------------------------------------------------

export function selectYardPiece(group) {
  selectedKey = group?.userData?.yardKey ?? null;
  setSelected(group || null);
  if (!group) {
    $('yard-panel').classList.add('hidden');
    return;
  }
  paintPanel(getYardItem(selectedKey));
  $('yard-panel').classList.remove('hidden');
}

function selectedGroup() {
  const sel = getSelected();
  return sel?.userData?.kind === 'yard' && sel.userData.yardKey === selectedKey ? sel : null;
}

function paintPanel(item) {
  const g = selectedGroup();
  if (!item || !g) return;
  $('yp-name').textContent = item.label + (item.isClone ? ' (copy)' : '');
  const [px, , pz] = item.pivot;
  $('yp-where').textContent =
    `${item.kind} · generated at ${px.toFixed(1)}, ${pz.toFixed(1)} ft`;
  $('yp-x').value = +g.position.x.toFixed(2);
  $('yp-y').value = +g.position.y.toFixed(2);
  $('yp-z').value = +g.position.z.toFixed(2);
  $('yp-rot').value = Math.round((g.rotation.y * 180 / Math.PI) % 360);
  $('yp-scale').value = +g.scale.x.toFixed(3);
  $('yp-reset').disabled = !item.edit;
}

// ---- edits -----------------------------------------------------------------

// Every change goes the same way: move the group (so the view is right at
// once), save the delta against the piece's generated pivot, and fold it into
// environment.js's copy so the next rebuild keeps it. Nothing here rebuilds the
// yard — the group already carries the transform.
async function saveTransform(g) {
  const item = getYardItem(g.userData.yardKey);
  if (!item) return;
  const [px, py, pz] = item.pivot;
  const payload = {
    dx: +(g.position.x - px).toFixed(2),
    dy: +(g.position.y - py).toFixed(2),
    dz: +(g.position.z - pz).toFixed(2),
    rot_y: +((g.rotation.y % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2)).toFixed(4),
    scale: +g.scale.x.toFixed(3),
  };
  try {
    await api.updateYard(item.key, {
      kind: item.kind, label: item.label, ...payload });
    applyYardEdit(item.key, payload);
    paintPanel(item);
  } catch (err) {
    showAlert(`Could not save that change: ${err.message}`);
  }
}

function onNumberEdit() {
  const g = selectedGroup();
  if (!g) return;
  g.position.set(+$('yp-x').value || 0, +$('yp-y').value || 0, +$('yp-z').value || 0);
  g.rotation.y = (+$('yp-rot').value || 0) * Math.PI / 180;
  const s = Math.max(0.05, Math.min(20, +$('yp-scale').value || 1));
  g.scale.setScalar(s);
  g.userData.userScale = s;
  saveTransform(g);
}

// Erasing hides the piece and lets go of it. The geometry stays in the scene so
// putting it back costs nothing — that happens from the erased list below,
// which is the only handle on something you can no longer see.
async function eraseSelected() {
  const g = selectedGroup();
  const item = getYardItem(selectedKey);
  if (!g || !item) return;
  try {
    await api.updateYard(item.key, {
      kind: item.kind, label: item.label, deleted: 1 });
    applyYardEdit(item.key, { deleted: 1 });
    g.visible = false;
    selectYardPiece(null);
    paintErasedList();
    showBanner(`Erased ${item.label}. Put it back from the Erased list.`, 3000);
  } catch (err) {
    showAlert(`Could not erase that: ${err.message}`);
  }
}

// ---- adding a piece --------------------------------------------------------
//
// Both ways of getting a NEW piece into the yard -- the panel's Duplicate and
// the add tray's tiles -- are the same clone row: `src` naming a piece that
// already exists, plus a delta measured from that piece's generated pivot.
// This is also the one kind of edit that has to rebuild, because environment.js
// draws a clone off its source's geometry and the copy does not exist until it
// has.
async function placeClone(item, delta, banner) {
  try {
    const { key } = await api.cloneYard(item.key, {
      kind: item.kind, label: item.label, ...delta });
    // The whole delta, not just src/kind/label. applyYardEdit fills anything
    // it is not given from IDENTITY_EDIT, so leaving dx/dz out of the local
    // copy drew the new piece exactly on top of the one it was copied from --
    // it only jumped to where it had been saved on the next page load.
    applyYardEdit(key, { src: item.key, kind: item.kind, label: item.label, ...delta });
    rebuildYard();
    selectByKey(key);
    paintErasedList();
    if (banner) showBanner(banner, 3000);
    return key;
  } catch (err) {
    showAlert(`Could not add that: ${err.message}`);
    return null;
  }
}

// A duplicate is a second copy of the same generated piece, offset a few feet
// so it isn't hiding inside the original.
async function duplicateSelected() {
  const g = selectedGroup();
  const item = getYardItem(selectedKey);
  if (!g || !item) return;
  const [px, py, pz] = item.pivot;
  await placeClone(item, {
    dx: +(g.position.x - px + 6).toFixed(2),
    dy: +(g.position.y - py).toFixed(2),
    dz: +(g.position.z - pz).toFixed(2),
    rot_y: +g.rotation.y.toFixed(4),
    scale: +g.scale.x.toFixed(3),
  });
}

// Kinds a random spin flatters. A tree, a shrub, a clump of grass and a wheelie
// bin all have no canonical facing, so turning each copy stops five of them
// reading as one thing stamped out five times. Beds, paving and edging are laid
// to the house and the drive -- turning those is only ever wrong.
const SPIN_KINDS = new Set(['tree', 'shrub', 'plant', 'prop']);

const _dir = new THREE.Vector3();
const DROP_NEAR = 8, DROP_FAR = 140;   // ft along the view ray

// Where a tile drops its piece: the ground under the middle of what you are
// looking at. Straight down the camera's own ray to y=0 rather than the orbit
// target, because the target is usually up inside the house while the yard is
// at grade. Looking level or up (no ground ahead) falls back to the target.
function dropPoint() {
  camera.getWorldDirection(_dir);
  let x, z;
  if (_dir.y < -0.02 && camera.position.y > 0) {
    const t = Math.min(DROP_FAR, Math.max(DROP_NEAR, -camera.position.y / _dir.y));
    x = camera.position.x + _dir.x * t;
    z = camera.position.z + _dir.z * t;
  } else {
    x = controls?.target.x ?? 0;
    z = controls?.target.z ?? 0;
  }
  // Scattered, so tapping one tile five times gives five bushes rather than a
  // stack of five you cannot tell apart or pull off each other.
  return clearOfHouse(x + (Math.random() - 0.5) * 5, z + (Math.random() - 0.5) * 5);
}

const HOUSE_CLEAR = 6;   // ft of daylight between a new piece and the walls

// The ray under the middle of the view lands on the ground THROUGH whatever is
// in the way, and what is usually in the way is the house -- look at the place
// you are working on and the drop point is inside its footprint, where the new
// piece is swallowed by the shell and you cannot even see what you added. So a
// point inside the building leaves by its nearest wall. It is still the yard,
// which is the only place a yard piece can go.
function clearOfHouse(x, z) {
  const box = getBuildingBox();
  if (!box) return { x, z };
  const x0 = box.min.x - HOUSE_CLEAR, x1 = box.max.x + HOUSE_CLEAR;
  const z0 = box.min.z - HOUSE_CLEAR, z1 = box.max.z + HOUSE_CLEAR;
  if (x < x0 || x > x1 || z < z0 || z > z1) return { x, z };
  const out = [
    { d: x - x0, x: x0, z }, { d: x1 - x, x: x1, z },
    { d: z - z0, x, z: z0 }, { d: z1 - z, x, z: z1 },
  ].sort((a, b) => a.d - b.d)[0];
  return { x: out.x, z: out.z };
}

// A tile in the add tray was tapped. The entry names every generated piece
// carrying that label, and pickSource takes one at random -- 17 bare trees and
// 54 shrub mounds means adding several gives several different ones.
async function addFromKit(entry) {
  const srcKey = pickSource(entry);
  const item = srcKey && getYardItem(srcKey);
  if (!item) {
    showAlert(`There is no ${entry.label.toLowerCase()} in this yard to copy.`);
    return;
  }
  const [px, , pz] = item.pivot;
  const { x, z } = dropPoint();
  await placeClone(item, {
    dx: +(x - px).toFixed(2),
    // dy 0: the piece keeps the height the builder drew it at, which for
    // everything out here means sitting on the ground.
    dy: 0,
    dz: +(z - pz).toFixed(2),
    rot_y: SPIN_KINDS.has(item.kind)
      ? +(Math.random() * Math.PI * 2).toFixed(4) : 0,
    scale: 1,
  }, `Added a ${entry.label.toLowerCase()} — drag it where you want it.`);
}

// Back to however the builder drew it — and for a duplicate, that means the
// duplicate stops existing.
async function resetSelected() {
  const item = getYardItem(selectedKey);
  if (!item?.edit) return;
  const wasClone = !!item.isClone;
  try {
    await api.resetYardPiece(item.key);
    dropYardEdit(item.key);
    if (wasClone) {
      selectYardPiece(null);
      rebuildYard();
    } else {
      const g = selectedGroup();
      if (g) {
        g.position.set(...item.pivot);
        g.rotation.y = 0;
        g.scale.setScalar(1);
        g.visible = true;
        g.userData.userScale = 1;
      }
      paintPanel(item);
    }
    paintErasedList();
  } catch (err) {
    showAlert(`Could not reset that: ${err.message}`);
  }
}

async function resetEverything() {
  if (!await showConfirm(
    'Throw away every change to the outside and go back to the generated yard?',
    { okLabel: 'Reset the yard', danger: true })) return;
  try {
    await api.resetYard();
    for (const item of getYardItems()) if (item.edit) dropYardEdit(item.key);
    selectYardPiece(null);
    rebuildYard();
    paintErasedList();
  } catch (err) {
    showAlert(`Could not reset the yard: ${err.message}`);
  }
}

function selectByKey(key) {
  const g = getYardPickables().find((o) => o.userData.yardKey === key);
  if (g) selectYardPiece(g);
}

// ---- the erased list -------------------------------------------------------
//
// An erased piece is invisible, so the 3D view can't offer it back. This is the
// only way to reach one.
function paintErasedList() {
  const box = $('yard-erased');
  const erased = getYardItems().filter((i) => i.edit?.deleted);
  box.innerHTML = '';
  $('yard-erased-wrap').classList.toggle('hidden', !erased.length);
  $('yard-erased-count').textContent = String(erased.length);
  for (const item of erased) {
    const row = document.createElement('button');
    row.type = 'button';
    row.className = 'yard-erased-row';
    const [px, , pz] = item.pivot;
    row.innerHTML = `<span>${item.label}</span>` +
                    `<span class="muted">${px.toFixed(0)}, ${pz.toFixed(0)}</span>`;
    row.title = 'Put this one back';
    row.onclick = async () => {
      try {
        await api.updateYard(item.key, { deleted: 0 });
        applyYardEdit(item.key, { deleted: 0 });
        selectByKey(item.key);
        const g = getYardPickables().find((o) => o.userData.yardKey === item.key);
        if (g) g.visible = true;
        paintErasedList();
      } catch (err) {
        showAlert(`Could not put that back: ${err.message}`);
      }
    };
    box.appendChild(row);
  }
}

// A rebuild from anywhere else (undo, a house reload) throws away the groups
// this module is holding, so the selection has to go with them.
function yardRebuilt() {
  if (!open) return;
  if (!isYardEditing()) return;
  const key = selectedKey;
  selectYardPiece(null);
  if (key) selectByKey(key);   // gone (erased, or reset away) => nothing selected
  paintErasedList();
  refreshYardKit();            // the tiles' source keys came from the old build
}
window.addEventListener('yardRebuilt', yardRebuilt);
