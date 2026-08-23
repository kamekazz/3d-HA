// Room focus mode: single-click a room to fly the camera in and isolate it —
// same-floor siblings ghost out, other floors hide, the room's device labels
// show. Exit with Esc, the "back" chip, or clicking empty space.
//
// The Frontyard and Backyard are the exception, and deliberately so: they are
// not rooms, they are the outside of the house. Isolating one used to drop the
// level selector onto the first floor, which left House mode — so the shell,
// the lawn, the trees and every other room went away and you were left staring
// at a bare 1 ft slab on a studio backdrop. Tapping the front of the house has
// to show the front of the house. See enterOutdoorFocus below.
import * as THREE from 'three';
import { camera, controls, flyTo, getViewPose, MIN_ZOOM, MAX_ZOOM } from './scene.js';
import { roomMeshes, stairGroups, setLevel, getLevel, setRoomOpacity, getBuildingBox,
         isOutdoorRoom } from './house.js';
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

// stateless restore: put every room on a level back to normal (markers are
// restored by clearing/replacing the focus scope in devices.js)
function restoreLevelVisuals(level) {
  for (const mesh of roomMeshes.values()) {
    if (mesh.userData.level !== level) continue;
    mesh.visible = true;
    setRoomOpacity(mesh, 1.0);
    mesh.userData.pickable = true;
    // the accent rim is a child of each wall now, so setRoomOpacity above has
    // already restored it along with the wall
  }
}

// ------------------------------------------------------------------- outdoor

const _v = new THREE.Vector3();

// Frame a yard from OUTSIDE, with the building in the shot. A yard only reads
// as the front (or the back) of THIS house if the house is behind it, so the
// fit box is the yard unioned with the building, the camera stands on the far
// side of the yard from the building, and the target is biased back toward the
// house so the yard holds the foreground. Nothing here is hard-coded to a
// compass direction: the same code frames the Frontyard from the street and
// the Backyard from the lawn, because it derives the stand-off from where the
// yard sits relative to the building.
function outdoorPose(mesh) {
  const yard = new THREE.Box3().setFromObject(mesh);
  const yc = yard.getCenter(new THREE.Vector3());

  // The shell GLB is the visible house — but its own bbox is the whole LOT
  // (113 x 152 ft here, pad and fences included), which centres nowhere near
  // the building and points the stand-off at the wrong quadrant. getBuildingBox
  // isolates the actual mass. Without a shell, the generated rooms are the house.
  const built = getBuildingBox() ?? new THREE.Box3();
  if (built.isEmpty()) {
    for (const m of roomMeshes.values()) {
      if (m === mesh || isOutdoorRoom(m.userData.roomName)) continue;
      built.union(new THREE.Box3().setFromObject(m));
    }
  }
  if (built.isEmpty()) built.copy(yard);
  const bc = built.getCenter(new THREE.Vector3());

  // Snap to the cardinal axis the yard is furthest out along, rather than
  // using the raw yard-to-house vector: these rects overlap the building on
  // the other axis, so raw comes out a 50-degree diagonal and you get the
  // corner of the house instead of the back of it. The elevation is the
  // subject — "the front of the house" means the front, square-on.
  const dx = yc.x - bc.x, dz = yc.z - bc.z;
  const away = Math.abs(dz) >= Math.abs(dx)
    ? new THREE.Vector3(0, 0, Math.sign(dz) || 1)
    : new THREE.Vector3(Math.sign(dx) || 1, 0, 0);
  // Then swing off dead-on: a facade shot exactly square to the wall reads
  // flat, and this is the one view where the house is the subject.
  away.applyAxisAngle(_v.set(0, 1, 0), THREE.MathUtils.degToRad(25));

  const fit = yard.clone().union(built);
  const size = fit.getSize(new THREE.Vector3());
  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const dist = THREE.MathUtils.clamp(
    0.85 * (0.5 * size.length()) / Math.sin(Math.min(vFov, hFov) / 2),
    MIN_ZOOM, MAX_ZOOM);

  const target = yc.clone().lerp(bc, 0.4);
  // Aim a bit above the eaves — high enough that the roofline stays in frame,
  // low enough that the yard keeps the bottom half. Off the BUILDING's height,
  // not the fit box's: the fit box grows with the yard and would drift up.
  target.y = built.min.y + (built.max.y - built.min.y) * 0.28;

  // Much flatter than the 30-degree look-down a room gets: you walk up to a
  // house, you do not hover over it. Not flat either — the yard is half the
  // subject and it is on the ground.
  const elev = THREE.MathUtils.degToRad(16);
  const h = dist * Math.cos(elev);
  return {
    position: new THREE.Vector3(target.x + away.x * h,
                                target.y + dist * Math.sin(elev),
                                target.z + away.z * h),
    target,
  };
}

// Hide nothing, drop no level, fly to the street. The only thing that narrows
// is the device markers, which scope to this yard — and which House mode would
// otherwise hide outright, so this is also the only way to reach the outdoor
// cameras and lights (devices.js reads focusScope.outdoor for both).
function enterOutdoorFocus(mesh, roomId) {
  focusedRoomId = roomId;
  setLevel('all');
  setActiveLevelButton('all');
  setFocusMarkerScope({ outdoor: true, roomId });
  setObjectFocusScope(null);
  const pose = outdoorPose(mesh);
  flyTo(pose.position, pose.target);
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

  // the outdoor branch shares everything up to here — the saved pose, the
  // previous room's restore — and none of the isolation below it
  if (isOutdoorRoom(mesh.userData.roomName)) {
    enterOutdoorFocus(mesh, roomId);
    controls.enablePan = false;
    const chipOut = document.getElementById('focus-exit');
    chipOut.textContent = `← ${mesh.userData.roomName}`;
    chipOut.classList.remove('hidden');
    emitFocus(roomId);
    return;
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
