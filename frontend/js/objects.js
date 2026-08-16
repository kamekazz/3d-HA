// Standalone furniture/decor: library models placed in rooms, no HA entity.
// Mirrors devices.js — one root Group per object, added to its floor group so
// the level selector shows/hides it for free.
import * as THREE from 'three';
import { floorGroups } from './house.js';
import { getInstance } from './models.js';

export const objects3d = new Map(); // object_id -> root Group

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
    .then((inst) => root.add(inst))
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
    fpX: fp.x, // room footprint origin: converts world XZ <-> room-relative
    fpZ: fp.z,
  };
  return root;
}
