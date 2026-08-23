// Standalone furniture/decor: library models placed in rooms, no HA entity.
// Mirrors devices.js — one root Group per object, added to its floor group so
// the level selector shows/hides it for free.
import * as THREE from 'three';
import { floorGroups, isOutdoorRoom } from './house.js';
import { getInstance } from './models.js';

export const objects3d = new Map(); // object_id -> root Group

// Furniture is by far the heaviest thing in the scene — hundreds of GLB models
// against a handful of room shells — so it, not the walls, decides the frame
// rate. Room focus therefore hides every other room's furniture outright rather
// than fading it: a ghosted mesh still draws, and a transparent one costs MORE
// than an opaque one (no early-Z, plus depth sorting and blending).
//
// Mirrors devices.js: this module is the SINGLE writer of object visibility, so
// house.js deliberately skips `kind: 'object'` in its setLevel sweep. Level
// visibility still comes free from the parent floor group.
let houseModeActive = false;
let focusScope = null; // { level, roomId } | null

function syncObjectVisibility(root) {
  const ud = root.userData;
  const focusHidden = !!focusScope &&
    ud.level === focusScope.level && ud.roomId !== focusScope.roomId;
  const cutAway = (ud.wallFade ?? 1) <= 0.01;
  // House mode hides the generated geometry and shows the shell instead. The
  // yards' furniture is the one thing that must survive it: the deck, the
  // porch and the driveway pieces ARE the outside of that shell, and hiding
  // them leaves the whole-house view — the only view the exterior is ever seen
  // from — showing a house with no deck on it.
  root.visible = (!houseModeActive || ud.outdoor) && !focusHidden && !cutAway;
}

// Materials we have already flipped to transparent. Flipping it is what
// recompiles a shader, so it happens once per material and never again — after
// that the cutaway only animates a uniform.
const fadeMats = new WeakSet();

// Wall-mounted pieces dim with the wall they hang on (see cutaway.js). Only
// objects the cutaway has bound to a wall carry userData.wallFade at all;
// everything else never enters this path and keeps its authored materials.
export function fadeSubtree(obj, opacity) {
  obj.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (!fadeMats.has(m)) {
        m.transparent = true;
        m.needsUpdate = true;
        fadeMats.add(m);
      }
      m.opacity = opacity;
      m.depthWrite = opacity > 0.5;
    }
  });
}

function applyObjectFade(root) {
  const f = root.userData.wallFade;
  if (f === undefined) return;
  fadeSubtree(root, f);
}

// cutaway.js is the only caller. Kept here because objects.js is the single
// writer of object visibility — a fade that wrote root.visible itself would
// fight the House-mode and room-focus sweeps below.
export function setObjectWallFade(objectId, opacity) {
  const root = objects3d.get(objectId);
  if (!root || root.userData.wallFade === opacity) return;
  root.userData.wallFade = opacity;
  applyObjectFade(root);
  syncObjectVisibility(root);
}

export function applyAllObjectVisibility() {
  for (const o of objects3d.values()) syncObjectVisibility(o);
}

export function setObjectFocusScope(scope) {
  focusScope = scope;
  applyAllObjectVisibility();
}

window.addEventListener('levelChanged', (e) => {
  houseModeActive = e.detail.houseMode;
  applyAllObjectVisibility();
});

function makePlaceholder() {
  return new THREE.Mesh(
    new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshStandardMaterial({ color: 0x777f8a, roughness: 0.8 }));
}

export function buildObjects(house) {
  for (const obj of objects3d.values()) obj.parent?.remove(obj);
  objects3d.clear();

  for (const floor of house.floors || []) {
    const group = floorGroups.get(floor.level);
    if (!group) continue;
    for (const room of floor.rooms || []) {
      for (const o of room.objects || []) {
        const root = makeObject(o, room, floor);
        group.add(root);
        objects3d.set(o.id, root);
        syncObjectVisibility(root); // a rebuild during focus must not un-hide it
      }
    }
  }
}

// Room-scale architectural surfaces placed as objects: a floor plane over the
// slab, a ceiling, emissive wall washes, baseboard runs. They span the whole
// room, and pick() raycasts objects before rooms — so left pickable they would
// swallow every click in that room and the room editor could never be opened.
// They are scenery, not furniture: not selectable, and so not draggable either,
// which is what you want for a ceiling. Matched on the placed object's name.
const SURFACE_RE = /\b(floor|ceiling|wall wash|baseboards?|crown)\b/i;

function makeObject(o, room, floor) {
  const root = new THREE.Group();
  getInstance(o.model_id, 'bottom')
    // models load async: a piece that resolves after its wall has already
    // faded has to be dimmed on arrival or it pops in over the cutaway
    .then((inst) => { root.add(inst); applyObjectFade(root); })
    .catch((err) => {
      console.warn(`model ${o.model_id} failed for object ${o.id}:`, err);
      root.add(makePlaceholder());
    });
  const fp = room.footprint;
  root.position.set(
    fp.x + o.position.x,
    o.position.y,
    fp.z + o.position.z);
  root.rotation.y = o.rot_y || 0;
  root.scale.setScalar(o.scale || 1);
  const name = o.name || o.model_name || '';
  root.userData = {
    kind: 'object',
    objectId: o.id,
    name,
    pickable: !SURFACE_RE.test(name),
    modelId: o.model_id,
    roomId: room.id,
    roomName: room.name,
    level: floor.level,
    outdoor: isOutdoorRoom(room.name), // cached: syncObjectVisibility is hot
    fpX: fp.x, // room footprint origin: converts world XZ <-> room-relative
    fpZ: fp.z,
  };
  return root;
}
