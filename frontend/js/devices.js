// Places device markers inside rooms; each marker is bound to an entity_id.
import * as THREE from 'three';
import { floorGroups } from './house.js';
import { getInstance } from './models.js';
// circular with state.js, but only called long after both modules evaluate
import { styleMarker } from './state.js';

export const markers = new Map(); // entity_id -> marker root (Mesh or Group)

const BASE_COLORS = {
  light: 0xffd54a,
  switch: 0x35c26a,
  sensor: 0x4a9eff,
  binary_sensor: 0xff7043,
  climate: 0xb388ff,
  cover: 0x80cbc4,
  media_player: 0xf06292,
  lock: 0xffab40,
  camera: 0x26c6da,
  default: 0x9e9e9e,
};

export function baseColor(type) {
  return BASE_COLORS[type] ?? BASE_COLORS.default;
}

// one shared geometry per domain so the shape says what a device is (sizes in ft)
const sphere = new THREE.SphereGeometry(0.45, 20, 16);
const smallBox = new THREE.BoxGeometry(0.65, 0.65, 0.65);
// 4-sided frustum laid on its side: reads as a wall-mounted camera/lens cone
const cameraFrustum = new THREE.CylinderGeometry(0.2, 0.45, 0.85, 4, 1);
cameraFrustum.rotateZ(Math.PI / 2);
const GEOMETRIES = {
  light: sphere,
  switch: smallBox,
  input_boolean: smallBox,
  sensor: new THREE.OctahedronGeometry(0.5),
  binary_sensor: new THREE.ConeGeometry(0.4, 0.8, 12),
  climate: new THREE.CylinderGeometry(0.45, 0.45, 0.3, 20),
  cover: new THREE.BoxGeometry(0.9, 0.65, 0.16),
  media_player: new THREE.BoxGeometry(1.0, 0.6, 0.2),
  lock: new THREE.TorusGeometry(0.33, 0.15, 10, 20),
  camera: cameraFrustum,
  default: sphere,
};

export function buildDevices(house) {
  for (const marker of markers.values()) marker.parent?.remove(marker);
  markers.clear();

  for (const floor of house.floors || []) {
    const group = floorGroups.get(floor.level);
    if (!group) continue;
    for (const room of floor.rooms || []) {
      for (const dev of room.devices || []) {
        const marker = makeMarker(dev, room, floor);
        group.add(marker);
        markers.set(dev.entity_id, marker);
      }
    }
  }
}

function makePrimitiveMesh(type) {
  const mat = new THREE.MeshStandardMaterial({
    color: baseColor(type),
    emissive: 0x000000,
    roughness: 0.4,
  });
  return new THREE.Mesh(GEOMETRIES[type] ?? GEOMETRIES.default, mat);
}

function makeMarker(dev, room, floor) {
  // model-backed markers are a Group filled asynchronously; primitives stay a
  // plain Mesh so buildDevices remains synchronous either way
  let marker;
  if (dev.model_id) {
    marker = new THREE.Group();
    getInstance(dev.model_id, 'center')
      .then((inst) => {
        marker.add(inst);
        styleMarker(dev.entity_id); // apply current state to the new materials
      })
      .catch((err) => {
        // broken/missing model: degrade to the primitive, never a blank spot
        console.warn(`model ${dev.model_id} failed for ${dev.entity_id}:`, err);
        marker.userData.modelId = null;
        marker.add(makePrimitiveMesh(dev.type));
        styleMarker(dev.entity_id);
      });
  } else {
    marker = makePrimitiveMesh(dev.type);
  }
  const fp = room.footprint;
  marker.position.set(
    fp.x + dev.position.x,
    dev.position.y,
    fp.z + dev.position.z);
  marker.rotation.y = dev.rot_y || 0;
  marker.scale.setScalar(dev.scale || 1);
  marker.visible = dev.visible !== 0;
  marker.userData = {
    kind: 'device',
    entityId: dev.entity_id,
    placementId: dev.id,
    type: dev.type,
    roomId: room.id,
    roomName: room.name,
    level: floor.level,
    hiddenByUser: dev.visible === 0,
    modelId: dev.model_id ?? null,
    userScale: dev.scale || 1,
    fpX: fp.x, // room footprint origin: converts world XZ <-> room-relative
    fpZ: fp.z,
  };
  return marker;
}

// Flip an entity's user-hidden flag without rebuilding (room panel edit mode).
export function setMarkerHidden(entityId, hidden) {
  const marker = markers.get(entityId);
  if (!marker) return;
  marker.userData.hiddenByUser = hidden;
  marker.visible = !hidden;
}
