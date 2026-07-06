// Places device markers inside rooms; each marker is bound to an entity_id.
import * as THREE from 'three';
import { floorGroups } from './house.js';

export const markers = new Map(); // entity_id -> marker mesh

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

// one shared geometry per domain so the shape says what a device is
const sphere = new THREE.SphereGeometry(0.14, 20, 16);
const smallBox = new THREE.BoxGeometry(0.2, 0.2, 0.2);
// 4-sided frustum laid on its side: reads as a wall-mounted camera/lens cone
const cameraFrustum = new THREE.CylinderGeometry(0.06, 0.14, 0.26, 4, 1);
cameraFrustum.rotateZ(Math.PI / 2);
const GEOMETRIES = {
  light: sphere,
  switch: smallBox,
  input_boolean: smallBox,
  sensor: new THREE.OctahedronGeometry(0.15),
  binary_sensor: new THREE.ConeGeometry(0.12, 0.24, 12),
  climate: new THREE.CylinderGeometry(0.14, 0.14, 0.09, 20),
  cover: new THREE.BoxGeometry(0.28, 0.2, 0.05),
  media_player: new THREE.BoxGeometry(0.3, 0.18, 0.06),
  lock: new THREE.TorusGeometry(0.1, 0.045, 10, 20),
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

function makeMarker(dev, room, floor) {
  const mat = new THREE.MeshStandardMaterial({
    color: baseColor(dev.type),
    emissive: 0x000000,
    roughness: 0.4,
  });
  const marker = new THREE.Mesh(GEOMETRIES[dev.type] ?? GEOMETRIES.default, mat);
  const fp = room.footprint;
  marker.position.set(
    fp.x + dev.position.x,
    dev.position.y,
    fp.z + dev.position.z);
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
