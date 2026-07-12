// Rooms glow when their HA lights are on — but only at night (scaled by
// daylight.js's night factor). Two layers: an emissive tint on every lit
// room's slab, plus real light spill from a fixed pool of point lights.
import * as THREE from 'three';
import { scene, controls, onFrame } from './scene.js';
import { roomMeshes, floorBaseY, getLevel } from './house.js';
import { getState, isOn, onStateApplied } from './state.js';
import { getNightFactor } from './daylight.js';

// The pool is fixed-size and its lights are never added/removed/hidden:
// changing the number of active lights in the scene forces three.js to
// recompile every MeshStandardMaterial's shader (a visible hitch). Driving
// intensity to 0 does not.
const POOL_SIZE = 6;
const GLOW_COLOR = 0xffb466;
const SLAB_GLOW = new THREE.Color(0xffa64d);
const SLAB_INTENSITY = 0.45;
const POOL_INTENSITY = 2.2;
const SMOOTH_TAU = 0.4;

let rooms = [];                    // [{roomId, level, center, radius, lightIds, lit, glow}]
const byEntity = new Map();        // entity_id -> [room records]
const pool = [];                   // [{light, room, targetIntensity}]
let assignmentDirty = false;
let lastLevel = null;

export function initRoomLights() {
  for (let i = 0; i < POOL_SIZE; i++) {
    const light = new THREE.PointLight(GLOW_COLOR, 0, 10, 2);
    scene.add(light);
    pool.push({ light, room: null });
  }

  onStateApplied((entityId) => {
    if (entityId === null) {
      for (const r of rooms) refreshLit(r);
      assignmentDirty = true;
    } else {
      const records = byEntity.get(entityId);
      if (!records) return;
      for (const r of records) refreshLit(r);
      assignmentDirty = true;
    }
  });

  onFrame(tick);

  if (window.__daylight) {
    window.__daylight.rooms = () => rooms.map((r) => ({
      roomId: r.roomId, level: r.level, lit: r.lit,
      lights: [...r.lightIds],
      pooled: pool.some((p) => p.room === r),
    }));
  }
}

// (Re)build room records after any house rebuild — old slab materials are
// disposed by buildHouse, so records must repoint at the fresh meshes.
export function setRoomLightsData({ house, structure }) {
  rooms = [];
  byEntity.clear();
  for (const p of pool) p.room = null;

  // ha_area_id -> Set(light entity_ids) from the HA registry tree, so rooms
  // glow even for lights that were never placed as 3D markers
  const areaLights = new Map();
  for (const f of structure?.floors || []) {
    for (const a of f.areas || []) {
      const set = new Set();
      for (const e of a.entities || []) {
        if (e.entity_id?.startsWith('light.')) set.add(e.entity_id);
      }
      if (set.size) areaLights.set(a.area_id, set);
    }
  }

  for (const floor of house?.floors || []) {
    for (const room of floor.rooms || []) {
      const lightIds = new Set();
      for (const dev of room.devices || []) {
        if (dev.entity_id?.startsWith('light.')) lightIds.add(dev.entity_id);
      }
      for (const id of areaLights.get(room.ha_area_id) || []) lightIds.add(id);
      if (!lightIds.size) continue;

      const fp = room.footprint;
      const baseY = floorBaseY.get(floor.level) ?? 0;
      const rec = {
        roomId: room.id,
        level: floor.level,
        center: new THREE.Vector3(
          fp.x + fp.width / 2,
          baseY + (room.height || 8) * 0.6,
          fp.z + fp.depth / 2),
        radius: Math.hypot(fp.width, fp.depth) / 2,
        lightIds,
        lit: false,
        glow: 0, // eased slab emissive intensity
      };
      rooms.push(rec);
      for (const id of lightIds) {
        if (!byEntity.has(id)) byEntity.set(id, []);
        byEntity.get(id).push(rec);
      }
    }
  }

  for (const r of rooms) refreshLit(r);
  assignmentDirty = true;
}

function refreshLit(rec) {
  rec.lit = [...rec.lightIds].some((id) => getState(id) && isOn(id));
}

// Give the pool lights to the lit rooms on visible levels; when there are
// more lit rooms than lights, the ones nearest the camera target win.
function reassignPool() {
  const level = getLevel();
  const candidates = rooms
    .filter((r) => r.lit && (level === 'all' || r.level === level))
    .sort((a, b) =>
      a.center.distanceToSquared(controls.target) -
      b.center.distanceToSquared(controls.target));
  const winners = candidates.slice(0, POOL_SIZE);

  // keep already-assigned winners on their light so they don't blink
  const freed = pool.filter((p) => !winners.includes(p.room));
  for (const p of freed) p.room = null;
  for (const room of winners) {
    if (pool.some((p) => p.room === room)) continue;
    const slot = pool.find((p) => !p.room);
    if (!slot) break;
    slot.room = room;
    slot.light.position.copy(room.center);
    slot.light.distance = room.radius * 2.5;
  }
}

function tick(dt) {
  const level = getLevel();
  if (level !== lastLevel) {
    lastLevel = level;
    assignmentDirty = true;
  }
  if (assignmentDirty) {
    assignmentDirty = false;
    reassignPool();
  }

  const night = getNightFactor();
  const k = 1 - Math.exp(-dt / SMOOTH_TAU);

  for (const r of rooms) {
    const goal = r.lit ? SLAB_INTENSITY * night : 0;
    if (Math.abs(r.glow - goal) < 1e-3 && r.glow === 0) continue;
    r.glow = THREE.MathUtils.lerp(r.glow, goal, k);
    if (r.glow < 1e-3 && goal === 0) r.glow = 0;
    const mesh = roomMeshes.get(r.roomId);
    const slab = mesh?.children.find((c) => c.userData.part === 'slab');
    if (!slab) continue;
    slab.material.emissive.copy(SLAB_GLOW);
    slab.material.emissiveIntensity = r.glow;
  }

  for (const p of pool) {
    const goal = p.room && p.room.lit ? POOL_INTENSITY * night : 0;
    p.light.intensity = THREE.MathUtils.lerp(p.light.intensity, goal, k);
    if (p.light.intensity < 1e-3 && goal === 0) p.light.intensity = 0;
  }
}
