// In-3D transform for the selected device marker, furniture object or the
// house shell. Selection-gated: only the thing picked via a panel (or an
// edit-mode click) can be moved, so grabbing anywhere else still orbits.
//
// The handles are three's TransformControls. Movement happens live on the mesh
// and nothing hits the network until the gesture ends, then a single PATCH --
// the same contract the old plane-drag had, widened from XZ to full XYZ plus
// rotation and uniform scale.
import * as THREE from 'three';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { api } from './api.js';
import { applyYardEdit } from './environment.js';
import { scene, camera, renderer, controls, onFrame, getStageFovScale } from './scene.js';
import { onStageChanged } from './stage.js';
import { appMode } from './ui.js';

let selected = null;  // root Object3D with userData.kind 'device' | 'object' | 'house-shell'
let helper = null;    // selection highlight
let tc = null;        // TransformControls
let startScale = 1;   // uniform scale at the moment a scale gesture began

const movedListeners = new Set();

// The gizmo is drawn with depthTest:false and renderOrder Infinity, so it sits
// on top of everything -- including a room-card capture. snapshots.js finds it
// by this name and hides it for the shot.
export const GIZMO_NAME = 'transformGizmo';

const GIZMO_SIZE = 1.0;
const MIN_SCALE = 0.05;
const MAX_SCALE = 20;

// fn({kind, id, x, y, z, rot_y, scale}) with ROOM-RELATIVE x/z, called after the
// PATCH lands — ui.js uses it to refresh open panel inputs and its cached house
// copy without a rebuild.
export function onDragMoved(fn) {
  movedListeners.add(fn);
}

export function setSelected(obj) {
  if (helper) {
    scene.remove(helper);
    helper.dispose();
    helper = null;
  }
  // "/" is the viewer: nothing is movable there, ever
  if (appMode === 'view' || !obj) {
    selected = null;
    tc?.detach();
    announce();
    return;
  }
  selected = obj;
  tc?.attach(obj);
  helper = new THREE.BoxHelper(selected, 0x2997ff);
  scene.add(helper);
  announce();
}

// One event beats patching every setSelected call site: ui.js shows and hides
// the gizmo mode bar off this.
function announce() {
  window.dispatchEvent(new CustomEvent('selectionChanged', {
    detail: { kind: selected?.userData?.kind ?? null },
  }));
}

export function getSelected() {
  return selected;
}

// main.js's click handler fires on pointerup before TransformControls' own, so
// tc.dragging is still true here — that is what lets a <=5px nudge on a gizmo
// arrow be told apart from a click on the room behind it.
export function isTransforming() {
  return !!tc && (tc.dragging || tc.axis !== null);
}

export function setGizmoMode(mode) {
  if (!tc) return;
  tc.mode = mode;
  // Furniture stands on a floor: yaw is the only rotation that means anything,
  // and rot_y is the only one the schema stores. Hiding X and Z also hides the
  // free-rotate rings (three hides E/XYZE unless all three axes show) and makes
  // them genuinely unpickable, not merely invisible.
  const rotating = mode === 'rotate';
  tc.showX = !rotating;
  tc.showY = true;
  tc.showZ = !rotating;
  tc.rotationSnap = rotating ? Math.PI / 24 : null; // 7.5 degrees
  tc.translationSnap = null;
  tc.scaleSnap = null; // fights the uniformiser below
  window.dispatchEvent(new CustomEvent('gizmoModeChanged', { detail: { mode } }));
}

export function getGizmoMode() {
  return tc?.mode ?? 'translate';
}

function syncGizmoSize() {
  if (!tc) return;
  // camera.fov describes the VIRTUAL frame once applyStage sets a view offset,
  // and TransformControls scales its handles straight off camera.fov. Undo it
  // with the same factor scene.js already uses for OrbitControls' pan.
  const size = GIZMO_SIZE * getStageFovScale();
  if (Math.abs(tc.size - size) > 1e-4) tc.size = size;
}

// Yaw, read off the QUATERNION rather than object.rotation.y.
//
// This is not defensiveness: Euler decomposition in XYZ order expresses a pure
// 180-degree yaw as (PI, 0, PI) — x and z carry it and `rotation.y` reads
// exactly 0. Persisting rotation.y therefore threw away every rotation at or
// past a half turn, silently. Projecting the object's forward axis is exact for
// any yaw and independent of Euler order.
const _fwd = new THREE.Vector3();

function yawOf(obj) {
  _fwd.set(0, 0, 1).applyQuaternion(obj.quaternion);
  return Math.atan2(_fwd.x, _fwd.z);
}

// Furniture stands on a floor and the schema stores one angle, so fold whatever
// the ring produced back to a pure yaw. Re-derived from _quaternionStart on
// every move inside TransformControls, so this never accumulates drift.
function constrainYaw() {
  selected.rotation.set(0, yawOf(selected), 0);
}

// Scale mode writes each axis independently and will happily go negative past
// the pivot (a mirrored model with inverted normals). The schema stores ONE
// uniform scale, so fold the gesture back to the axis that moved furthest.
function uniformiseScale() {
  const s = selected.scale;
  const r = [s.x, s.y, s.z]
    .map((v) => v / startScale)
    .reduce((a, b) => (Math.abs(b - 1) > Math.abs(a - 1) ? b : a), 1);
  s.setScalar(THREE.MathUtils.clamp(startScale * r, MIN_SCALE, MAX_SCALE));
}

async function persist() {
  if (!selected) return;
  const ud = selected.userData;
  const rot = +THREE.MathUtils.euclideanModulo(yawOf(selected), Math.PI * 2).toFixed(4);
  const scale = +selected.scale.x.toFixed(3);

  // The house shell sits on the house root (no room footprint offset); its
  // position IS world XZ, saved through the shell endpoint.
  if (ud.kind === 'house-shell') {
    const payload = {
      x: +selected.position.x.toFixed(2),
      y: +selected.position.y.toFixed(2),
      z: +selected.position.z.toFixed(2),
      rot_y: rot,
      scale,
    };
    try {
      await api.setHouseShell(payload);
      for (const fn of movedListeners) fn({ kind: 'house-shell', ...payload });
    } catch (err) {
      console.warn('shell transform save failed:', err);
    }
    return;
  }

  // A yard piece is not room-anchored: it sits in world space at the pivot the
  // procedural builder gave it, and what gets stored is the OFFSET from there
  // (see environment.js "EDITABLE YARD"). Subtracting the pivot is what keeps
  // an edit meaningful when the yard is regenerated around it.
  if (ud.kind === 'yard') {
    const [px, py, pz] = ud.pivot;
    const payload = {
      dx: +(selected.position.x - px).toFixed(2),
      dy: +(selected.position.y - py).toFixed(2),
      dz: +(selected.position.z - pz).toFixed(2),
      rot_y: rot,
      scale,
    };
    try {
      await api.updateYard(ud.yardKey, { kind: ud.yardKind, label: ud.name, ...payload });
      applyYardEdit(ud.yardKey, payload);
      ud.userScale = scale;
      for (const fn of movedListeners) fn({ kind: 'yard', id: ud.yardKey, ...payload });
    } catch (err) {
      console.warn('yard transform save failed:', err);
    }
    return;
  }

  // floor groups only offset Y, so world XZ maps straight onto local XZ, and
  // the stored y is already local/base-relative
  const payload = {
    x: +(selected.position.x - ud.fpX).toFixed(2),
    y: +selected.position.y.toFixed(2),
    z: +(selected.position.z - ud.fpZ).toFixed(2),
    rot_y: rot,
    scale,
  };
  try {
    if (ud.kind === 'device') await api.updatePlacement(ud.placementId, payload);
    else await api.updateObject(ud.objectId, payload);
    // keep userData in step so the next gesture composes, not resets
    ud.userScale = scale;
    const id = ud.kind === 'device' ? ud.placementId : ud.objectId;
    for (const fn of movedListeners) fn({ kind: ud.kind, id, ...payload });
  } catch (err) {
    console.warn('transform save failed:', err);
  }
}

export function initDrag() {
  const el = renderer.domElement;

  tc = new TransformControls(camera, el);
  tc.name = GIZMO_NAME;
  tc.space = 'world'; // room footprints are axis-aligned; local would make the
                      // arrows follow rot_y and the saved numbers unreadable
  scene.add(tc);      // r160: TransformControls IS an Object3D (no getHelper)
  setGizmoMode('translate');
  syncGizmoSize();
  onStageChanged(syncGizmoSize);

  // Capture phase, so this runs before OrbitControls' own bubble pointerdown.
  // Disabling there is not enough: OrbitControls would still have dispatched
  // its 'start' event, which scene.js reads as "the user took the camera" and
  // which permanently disables the automatic re-fit.
  el.addEventListener('pointerdown', (e) => {
    if (e.button !== 0 || !tc.object || !tc.enabled) return;
    const r = el.getBoundingClientRect();
    tc.pointerHover({
      x: ((e.clientX - r.left) / r.width) * 2 - 1,
      y: -((e.clientY - r.top) / r.height) * 2 + 1,
      button: e.button,
    });
    if (tc.axis !== null) controls.enabled = false;
  }, true);

  tc.addEventListener('dragging-changed', (e) => {
    if (!e.value) controls.enabled = true;
  });

  tc.addEventListener('mouseDown', () => {
    startScale = tc.object ? tc.object.scale.x : 1;
  });

  tc.addEventListener('objectChange', () => {
    if (!selected) return;
    if (tc.mode === 'scale') uniformiseScale();
    else if (tc.mode === 'rotate') constrainYaw();
    // BoxHelper.update() is a full setFromObject traversal. Fine for a lamp;
    // the house shell is thousands of meshes and would stall the drag.
    if (selected.userData.kind !== 'house-shell') helper?.update();
  });

  tc.addEventListener('mouseUp', persist);

  onFrame(() => {
    // scene.js's flyTo re-enables the orbit unconditionally when it lands, so a
    // focus/level animation finishing mid-gesture would hand the camera back.
    if (tc.dragging) controls.enabled = false;
    // A rebuild (planner close, undo, sync) replaces every mesh. TransformControls
    // console.errors once per frame forever if its target is orphaned, and the
    // stale reference pins a disposed subtree.
    if (selected && !selected.parent) setSelected(null);
  });
}
