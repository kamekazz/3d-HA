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
  default: 0x9e9e9e,
};

export function baseColor(type) {
  return BASE_COLORS[type] ?? BASE_COLORS.default;
}

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
  const marker = new THREE.Mesh(new THREE.SphereGeometry(0.14, 20, 16), mat);
  const fp = room.footprint;
  marker.position.set(
    fp.x + dev.position.x,
    dev.position.y,
    fp.z + dev.position.z);
  marker.userData = {
    kind: 'device',
    entityId: dev.entity_id,
    placementId: dev.id,
    type: dev.type,
    roomId: room.id,
    roomName: room.name,
    level: floor.level,
  };
  return marker;
}
