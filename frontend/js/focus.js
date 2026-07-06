// Room focus mode: single-click a room to fly the camera in and isolate it —
// same-floor siblings ghost out, other floors hide, the room's device labels
// show. Exit with Esc, the "back" chip, or clicking empty space.
import * as THREE from 'three';
import { camera, controls, flyTo, getViewPose, MIN_ZOOM, MAX_ZOOM } from './scene.js';
import { roomMeshes, setLevel, getLevel, setRoomOpacity } from './house.js';
import { markers } from './devices.js';
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

// stateless restore: put every room + marker on a level back to normal
function restoreLevelVisuals(level) {
  for (const mesh of roomMeshes.values()) {
    if (mesh.userData.level !== level) continue;
    setRoomOpacity(mesh, 0.18);
    mesh.userData.pickable = true;
    const edges = roomEdges(mesh);
    if (edges) edges.visible = true;
  }
  for (const marker of markers.values()) {
    marker.visible = !marker.userData.hiddenByUser;
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

  for (const sib of roomMeshes.values()) {
    if (sib === mesh || sib.userData.level !== level) continue;
    setRoomOpacity(sib, 0.04);
    sib.userData.pickable = false;
    const edges = roomEdges(sib);
    if (edges) edges.visible = false;
  }
  setRoomOpacity(mesh, 0.3);
  for (const marker of markers.values()) {
    if (marker.userData.level === level && marker.userData.roomId !== roomId) {
      marker.visible = false;
    }
  }
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
  hideAllLabels();
  focusedRoomId = null;

  setLevel(savedLevel ?? 'all');
  setActiveLevelButton(savedLevel ?? 'all');
  controls.enablePan = true;
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
