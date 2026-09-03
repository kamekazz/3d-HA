// Per-room 3D snapshot capture for the room cards. Reuses the main renderer
// and canvas with a temporary camera: isolate the room (hide everything else),
// render once, copy the canvas into a small 2D canvas, restore everything and
// immediately repaint the real view — the user's camera never moves and no
// snapshot frame is ever displayed. preserveDrawingBuffer is false, so the
// render → drawImage readback must stay synchronous (never await between).
//
// Captures are queued one room per animation frame (no jank) and cached by a
// geometry hash of the /api/house payload, persisted to localStorage so cards
// paint instantly on the next boot. Snapshots are geometry, not live state —
// nothing recaptures on entity state changes.
import * as THREE from 'three';
import { scene, camera, renderer, hemiLight, sunLight } from './scene.js';
import { roomMeshes, floorGroups, stairGroups, getShellRoot } from './house.js';
import { scoreForCamera } from './cutaway.js';
import { getEnvironmentRoot } from './environment.js';
import { getWeatherRoot } from './weather.js';
import { getFocusedRoomId } from './focus.js';
import { suspendRoomLights } from './roomlights.js';
import { suspendEaveLights } from './eavelights.js';
import { GIZMO_NAME } from './drag.js';

const SNAP_W = 384, SNAP_H = 240;      // card image (1.6 aspect)
const ASPECT = SNAP_W / SNAP_H;
const JPEG_Q = 0.82;
const STORE_PREFIX = '3dha.snap.';

const cache = new Map();               // roomId -> { hash, url }
const readyListeners = new Set();
const idleWaiters = new Set();   // boot.js: resolve when the queue drains
let queue = [];                        // [{roomId, hash}] pending capture
let pumping = false;
let sweepTimers = [];

const snapCam = new THREE.PerspectiveCamera(50, ASPECT, 0.1, 1600);
const snapCanvas = document.createElement('canvas');
snapCanvas.width = SNAP_W;
snapCanvas.height = SNAP_H;
const snapCtx = snapCanvas.getContext('2d');
let backdropTex = null;

export function onSnapshotReady(fn) { readyListeners.add(fn); }

function emitReady(roomId, url) {
  for (const fn of readyListeners) fn(roomId, url);
}

export function getSnapshot(roomId) {
  const hit = cache.get(roomId);
  if (hit) return hit.url;
  try { // not captured this session yet — a previous boot may have it
    const raw = localStorage.getItem(STORE_PREFIX + roomId);
    if (raw) {
      const { hash, url } = JSON.parse(raw);
      cache.set(roomId, { hash, url });
      return url;
    }
  } catch { /* corrupt entry — recapture will replace it */ }
  return null;
}

// ---------------------------------------------------------------- hashing

function djb2(str) {
  let h = 5381;
  for (let i = 0; i < str.length; i++) h = ((h << 5) + h + str.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

// everything that changes how the room *looks* in 3D (not live entity state)
function roomHash(room, floor) {
  return djb2(JSON.stringify({
    fp: room.footprint, h: room.height, lvl: floor.level,
    c: [room.color, room.wall_color, room.floor_color,
        room.wall_texture, room.floor_texture],
    dev: (room.devices || []).map((d) =>
      [d.entity_id, d.model_id, d.visible, d.rot_y, d.scale,
       d.position.x, d.position.y, d.position.z]),
    obj: (room.objects || []).map((o) =>
      [o.model_id, o.rot_y, o.scale, o.position.x, o.position.y, o.position.z]),
    op: (room.openings || []).map((o) => [o.type, o.x, o.width, o.height]),
  }));
}

// dark card-matched studio sweep — neutral greys so it blends with
// .room-card's surface (var(--card-bg) #1d1d1f / --surface-2 #2a2a2c)
function makeBackdrop() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 105, 30, 128, 128, 175);
  grad.addColorStop(0, '#3a3a3d');
  grad.addColorStop(0.55, '#2a2a2c');
  grad.addColorStop(1, '#1a1a1c');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// ---------------------------------------------------------------- capture

function captureRoom(roomId) {
  const mesh = roomMeshes.get(roomId);
  if (!mesh) return null;
  const level = mesh.userData.level;
  const group = floorGroups.get(level);
  if (!group) return null;

  // ---- save + isolate: only this room, its devices and its furniture
  const saved = [];
  const setVis = (o, v) => { if (o && o.visible !== v) { saved.push([o, o.visible]); o.visible = v; } };
  for (const [lvl, g] of floorGroups) setVis(g, lvl === level);
  for (const child of group.children) {
    if (child === mesh) { setVis(child, true); continue; }
    if (child.isSprite) continue; // hover labels own their visibility
    // this room's markers/objects. Markers are edit-only, so scope them but
    // never promote a hidden one -- the card must match the live scene.
    const keep = child.userData.roomId === roomId
      && (child.userData.kind !== 'device' || child.visible);
    setVis(child, keep);
  }
  for (const st of stairGroups) setVis(st, false);
  setVis(getShellRoot(), false);
  setVis(getEnvironmentRoot(), false);
  setVis(getWeatherRoot(), false);
  setVis(scene.getObjectByName('editGrid'), false);
  setVis(scene.getObjectByName('editGround'), false);

  const savedBg = scene.background, savedFog = scene.fog;
  backdropTex = backdropTex || makeBackdrop();
  scene.background = backdropTex;
  scene.fog = null;

  // consistent "studio" lighting so cards match regardless of time of day
  const savedHemi = hemiLight.intensity, savedSun = sunLight.intensity;
  hemiLight.intensity = 1.05;
  sunLight.intensity = 1.25;

  // ---- frame: bounding-sphere fit (same math as focus.js), fixed viewpoint
  const box = new THREE.Box3().setFromObject(mesh);
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(0.5 * box.getSize(new THREE.Vector3()).length(), 1);
  const src = renderer.domElement;
  const srcAspect = src.width / src.height;
  snapCam.aspect = srcAspect; // render undistorted, then crop to 1.6
  snapCam.updateProjectionMatrix();
  // effective FOVs of the centered 1.6-aspect crop region
  const vFov = THREE.MathUtils.degToRad(snapCam.fov);
  const tanV = Math.tan(vFov / 2);
  const hFovEff = srcAspect > ASPECT
    ? 2 * Math.atan(tanV * ASPECT) : 2 * Math.atan(tanV * srcAspect);
  const vFovEff = srcAspect > ASPECT
    ? vFov : 2 * Math.atan((tanV * srcAspect) / ASPECT);
  const fit = Math.min(vFovEff, hFovEff);
  const dist = 1.15 * radius / Math.sin(fit / 2);
  const az = THREE.MathUtils.degToRad(-35); // fixed angle: all cards match
  const polar = 0.95;                        // ~35° above the horizon
  snapCam.position.set(
    center.x + dist * Math.sin(polar) * Math.sin(az),
    center.y + dist * Math.cos(polar),
    center.z + dist * Math.sin(polar) * Math.cos(az));
  snapCam.lookAt(center);

  // ---- render + synchronous readback (center-crop to the card aspect)
  // the wall cutaway is scored against the live camera; re-score it for this
  // one or the card is shot through the back of a solid near wall
  const restoreCutaway = scoreForCamera(snapCam);
  // Cards are keyed by GEOMETRY and persisted, so anything live in the pixels
  // is baked in forever. The pool lights are scene children the per-room
  // isolation sweep above never touches, and a fixture's glow is deliberately
  // not night-gated — shoot the room unlit and let roomcards.js signal lit-ness
  // with its own `.lit` class instead.
  const restoreLights = suspendRoomLights();
  const restoreEaves = suspendEaveLights(); // same reason: the porch lights at night
  // depthTest:false + renderOrder Infinity: the gizmo would paint straight over
  // the card if anything happened to be selected when a sweep fired
  setVis(scene.getObjectByName(GIZMO_NAME), false);
  renderer.render(scene, snapCam);
  let sw = src.width, sh = src.height, sx = 0, sy = 0;
  if (srcAspect > ASPECT) { sw = sh * ASPECT; sx = (src.width - sw) / 2; }
  else { sh = sw / ASPECT; sy = (src.height - sh) / 2; }
  snapCtx.drawImage(src, sx, sy, sw, sh, 0, 0, SNAP_W, SNAP_H);
  const url = snapCanvas.toDataURL('image/jpeg', JPEG_Q);

  // ---- restore, then repaint the real view so no snapshot frame ever shows
  restoreCutaway();
  restoreLights();
  restoreEaves();
  for (const [o, v] of saved) o.visible = v;
  scene.background = savedBg;
  scene.fog = savedFog;
  hemiLight.intensity = savedHemi;
  sunLight.intensity = savedSun;
  renderer.render(scene, camera);
  return url;
}

// ---------------------------------------------------------------- queue pump

function releaseIfIdle() {
  if (pumping || queue.length || !idleWaiters.size) return;
  const waiters = [...idleWaiters];
  idleWaiters.clear();
  for (const resolve of waiters) resolve();
}

// Resolves once every queued room has been captured. boot.js awaits this so the
// room rail is fully populated before the loading curtain lifts.
export function snapshotsIdle() {
  if (!pumping && !queue.length) return Promise.resolve();
  return new Promise((resolve) => idleWaiters.add(resolve));
}

function pump() {
  if (!queue.length) { pumping = false; releaseIfIdle(); return; }
  // a focused room has ghosted siblings and a mid-flight camera; a hidden tab
  // has no rAF — park the queue and try again shortly
  if (document.hidden || getFocusedRoomId() !== null) {
    setTimeout(() => requestAnimationFrame(pump), 1000);
    return;
  }
  const { roomId, hash } = queue.shift();
  try {
    const url = captureRoom(roomId);
    if (url) {
      cache.set(roomId, { hash, url });
      try { localStorage.setItem(STORE_PREFIX + roomId, JSON.stringify({ hash, url })); }
      catch { /* quota — memory cache still works */ }
      emitReady(roomId, url);
    }
  } catch (e) {
    console.warn(`snapshot failed for room ${roomId}:`, e);
  }
  requestAnimationFrame(pump);
}

function startPump() {
  if (pumping) return;
  pumping = true;
  requestAnimationFrame(pump);
}

// ---------------------------------------------------------------- scheduling

function enqueueSweep(house, { force = false } = {}) {
  const known = new Set();
  for (const floor of house?.floors || []) {
    for (const room of floor.rooms || []) {
      known.add(room.id);
      const hash = roomHash(room, floor);
      getSnapshot(room.id); // pull any localStorage entry into the memory cache
      const cached = cache.get(room.id);
      if (!force && cached?.hash === hash) continue;
      if (!queue.some((q) => q.roomId === room.id)) queue.push({ roomId: room.id, hash });
      else queue.find((q) => q.roomId === room.id).hash = hash;
    }
  }
  // deleted rooms: drop their stored images
  for (const key of Object.keys(localStorage)) {
    if (!key.startsWith(STORE_PREFIX)) continue;
    const id = Number(key.slice(STORE_PREFIX.length));
    if (!known.has(id)) { try { localStorage.removeItem(key); } catch { /* */ } }
  }
  if (queue.length) startPump();
}

// Called on boot and after every reloadHouse. The two timers are a fudge
// factor: they wait for GLB device models / textures / daylight to settle, and
// the second (forced) sweep catches models that were still streaming in during
// the first pass.
//
// `immediate` is boot.js's path, and is strictly better: by then modelsIdle()
// has actually resolved, so there is nothing left to wait for and nothing left
// to catch. Both timers are skipped — the forced one especially, since it would
// recapture every room and swap the card images under the user after the
// curtain has already lifted.
export function requestSnapshots(house, { immediate = false } = {}) {
  for (const t of sweepTimers) clearTimeout(t);
  sweepTimers = [];
  if (immediate) { enqueueSweep(house); return; }
  sweepTimers = [
    setTimeout(() => enqueueSweep(house), 1500),
    setTimeout(() => enqueueSweep(house, { force: true }), 6500),
  ];
}

// console handle for testing: __snapshots.capture(roomId) forces one capture
window.__snapshots = {
  capture: (roomId) => captureRoom(roomId),
  cache,
  queue: () => queue.map((q) => q.roomId),
};
