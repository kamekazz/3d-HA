// Room focus mode: single-click a room to fly the camera in and isolate it —
// same-floor siblings ghost out, other floors hide, the room's device labels
// show. Exit with Esc, the "back" chip, or clicking empty space.
import * as THREE from 'three';
import { camera, controls, flyTo, getViewPose, MIN_ZOOM, MAX_ZOOM } from './scene.js';
import { roomMeshes, stairGroups, setLevel, getLevel, setRoomOpacity } from './house.js';
import { setFocusMarkerScope } from './devices.js';
import { setObjectFocusScope } from './objects.js';
import { hideAllLabels } from './labels.js';

let focusedRoomId = null;
let savedPose = null;  // camera pose before the first enterFocus
let savedLevel = null; // level selector value before the first enterFocus

export function getFocusedRoomId() {
  return focusedRoomId;
}

// Fired with the room id on enter/switch and null on exit. Lets the room
// panel follow focus without focus.js importing any UI module.
const focusListeners = new Set();

export function onFocusChanged(fn) {
  focusListeners.add(fn);
}

function emitFocus(roomId) {
  for (const fn of focusListeners) fn(roomId);
}

// focus.js deliberately never imports ui.js (ui.js imports us) — the level
// buttons are synced by touching the DOM directly.
function setActiveLevelButton(level) {
  document.querySelectorAll('#levels button').forEach((b) => {
    b.classList.toggle('active', String(b.dataset.level) === String(level));
  });
}

function roomEdges(mesh) {
  return mesh.children.find((c) => c.userData.part === 'edges');
}

// stateless restore: put every room on a level back to normal (markers are
// restored by clearing/replacing the focus scope in devices.js)
function restoreLevelVisuals(level) {
  for (const mesh of roomMeshes.values()) {
    if (mesh.userData.level !== level) continue;
    mesh.visible = true;
    setRoomOpacity(mesh, 1.0);
    mesh.userData.pickable = true;
    const edges = roomEdges(mesh);
    if (edges) edges.visible = true;
  }
}

export function enterFocus(roomId) {
  const mesh = roomMeshes.get(roomId);
  if (!mesh || focusedRoomId === roomId) return;
  const level = mesh.userData.level;

  if (focusedRoomId === null) {
    savedPose = getViewPose();
    savedLevel = getLevel();
  } else {
    // switching focus: restore the previous room's floor, keep the saved pose
    const prev = roomMeshes.get(focusedRoomId);
    if (prev) restoreLevelVisuals(prev.userData.level);
    hideAllLabels();
  }
  focusedRoomId = roomId;

  setLevel(level);
  setActiveLevelButton(level);

  // Siblings are HIDDEN, not ghosted. Ghosting at opacity 0.04 still drew every
  // wall, slab and edge — and a transparent mesh costs more than an opaque one
  // (no early-Z, plus depth sorting and blending), so the old "isolate" mode
  // actually made the scene slower than the full floor. Hiding skips the draw
  // entirely. setObjectFocusScope does the same for the room's furniture, which
  // is the bulk of the geometry.
  for (const sib of roomMeshes.values()) {
    if (sib === mesh || sib.userData.level !== level) continue;
    sib.visible = false;
    sib.userData.pickable = false;
  }
  mesh.visible = true;
  setRoomOpacity(mesh, 1.0);
  // Stairs live on the house root, not in a floor group, so setLevel leaves
  // them on. With the surrounding rooms gone they hang in the backdrop next to
  // the room, which reads as a bug rather than as a cutaway.
  for (const g of stairGroups) g.visible = false;
  setFocusMarkerScope({ level, roomId });
  setObjectFocusScope({ level, roomId });
  // no showRoomLabels here: the room panel carries the info; hover still
  // pops a single label

  // frame the room: distance that fits its bounding sphere in the tighter FOV.
  // Box3 works for both BoxGeometry (rect) and ExtrudeGeometry (polygon)
  // rooms and is world-space, so the floor's Y offset is already included.
  const box = new THREE.Box3().setFromObject(mesh);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const radius = 0.5 * size.length();
  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const fit = Math.min(vFov, hFov);
  const dist = THREE.MathUtils.clamp(
    1.15 * radius / Math.sin(fit / 2), MIN_ZOOM, MAX_ZOOM);
  // keep the user's current azimuth, come down to a ~30° elevation
  const az = Math.atan2(camera.position.x - center.x, camera.position.z - center.z);
  const polar = 1.05; // angle from vertical
  flyTo(new THREE.Vector3(
    center.x + dist * Math.sin(polar) * Math.sin(az),
    center.y + dist * Math.cos(polar),
    center.z + dist * Math.sin(polar) * Math.cos(az)), center);

  controls.enablePan = false;
  const chip = document.getElementById('focus-exit');
  chip.textContent = `← ${mesh.userData.roomName}`;
  chip.classList.remove('hidden');
  emitFocus(roomId);
}

export function exitFocus({ flyBack = true } = {}) {
  if (focusedRoomId === null) return;
  const mesh = roomMeshes.get(focusedRoomId);
  if (mesh) restoreLevelVisuals(mesh.userData.level);
  setFocusMarkerScope(null);
  setObjectFocusScope(null);
  hideAllLabels();
  focusedRoomId = null;

  // setLevel re-derives stair visibility from the level, undoing the hide above
  setLevel(savedLevel ?? 'all');
  setActiveLevelButton(savedLevel ?? 'all');
  // floor view (floorview.js) keeps pan off — only House view pans freely
  controls.enablePan = (savedLevel ?? 'all') === 'all';
  document.getElementById('focus-exit').classList.add('hidden');
  if (flyBack && savedPose) flyTo(savedPose.position, savedPose.target);
  savedPose = null;
  savedLevel = null;
  emitFocus(null);
}

export function initFocus() {
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') exitFocus();
  });
  document.getElementById('focus-exit').addEventListener('click', () => exitFocus());
}
