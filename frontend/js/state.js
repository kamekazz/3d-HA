// Holds live entity states and applies them to the 3D markers.
import * as THREE from 'three';
import { markers, baseColor } from './devices.js';

const states = new Map(); // entity_id -> HA state object
const listeners = new Set();

const ON_STATES = new Set(['on', 'open', 'playing', 'home', 'unlocked', 'heat',
                           'cool', 'heat_cool', 'auto', 'cleaning',
                           'recording', 'streaming']);

export function getState(entityId) {
  return states.get(entityId);
}

export function findEntities(prefix) {
  return [...states.keys()].filter((id) => id.startsWith(prefix)).sort();
}

export function onStateApplied(fn) {
  listeners.add(fn);
}

export function setAllStates(list) {
  for (const s of list) {
    states.set(s.entity_id, s);
    styleMarker(s.entity_id);
  }
  for (const fn of listeners) fn(null);
}

export function applyState(entityId, newState) {
  if (newState === null || newState === undefined) states.delete(entityId);
  else states.set(entityId, newState);
  styleMarker(entityId);
  for (const fn of listeners) fn(entityId);
}

export function isOn(entityId) {
  const s = states.get(entityId);
  return s ? ON_STATES.has(s.state) : false;
}

export function friendlyName(entityId) {
  return states.get(entityId)?.attributes?.friendly_name || entityId;
}

// binary_sensor device_class -> [label when on, label when off]
const BINARY_LABELS = {
  door: ['Open', 'Closed'],
  window: ['Open', 'Closed'],
  garage_door: ['Open', 'Closed'],
  opening: ['Open', 'Closed'],
  motion: ['Motion', 'Clear'],
  occupancy: ['Occupied', 'Clear'],
  presence: ['Present', 'Away'],
  moisture: ['Wet', 'Dry'],
  lock: ['Unlocked', 'Locked'],
  battery: ['Low', 'OK'],
  battery_charging: ['Charging', 'Not charging'],
  connectivity: ['Connected', 'Disconnected'],
  smoke: ['Smoke!', 'Clear'],
  gas: ['Gas!', 'Clear'],
  problem: ['Problem', 'OK'],
  plug: ['Plugged in', 'Unplugged'],
  vibration: ['Vibration', 'Clear'],
  running: ['Running', 'Idle'],
};

// ISO datetime states (timestamp sensors) read as raw machine strings —
// render them as relative time, falling back to "Jul 11, 1:04 PM" when old
const ISO_DATETIME = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;

function formatTimestamp(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  if (mins >= 0 && mins < 1) return 'Just now';
  if (mins >= 1 && mins < 60) return `${mins} min ago`;
  if (mins >= 60 && mins < 24 * 60) return `${Math.round(mins / 60)} hr ago`;
  const date = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  const time = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return `${date}, ${time}`;
}

export function stateLabel(entityId) {
  const s = states.get(entityId);
  if (!s) return 'unknown';
  if (entityId.startsWith('binary_sensor.') && (s.state === 'on' || s.state === 'off')) {
    const pair = BINARY_LABELS[s.attributes?.device_class];
    if (pair) return s.state === 'on' ? pair[0] : pair[1];
    return s.state === 'on' ? 'On' : 'Off';
  }
  if (s.attributes?.device_class === 'timestamp' || ISO_DATETIME.test(s.state)) {
    return formatTimestamp(s.state);
  }
  const unit = s.attributes?.unit_of_measurement;
  return unit ? `${s.state} ${unit}` : s.state;
}

const GREY_UNAVAILABLE = 0x3a4149;
const GREY_LERP_TARGET = new THREE.Color(GREY_UNAVAILABLE);

// Apply one visual state to a marker root. Primitives get the classic
// color+emissive repaint; model-backed markers (GLB Groups, multi-mesh,
// multi-material) keep their authored colors — state shows as an emissive
// glow (on), original materials (off), or a grey tint (unavailable).
// stateScale composes with the user's placement scale so a 2× couch stays 2×.
function applyStyle(marker, { color, emissiveHex, emissiveIntensity, grey, stateScale }) {
  marker.scale.setScalar((marker.userData.userScale ?? 1) * stateScale);

  if (!marker.userData.modelId) {
    const mat = marker.material;
    if (!mat) return; // model Group still loading its instance
    mat.color.setHex(grey ? GREY_UNAVAILABLE : color);
    mat.emissive.setHex(emissiveHex ?? 0x000000);
    if (emissiveIntensity !== undefined) mat.emissiveIntensity = emissiveIntensity;
    return;
  }

  paintModelState(marker, { emissiveHex, emissiveIntensity, grey });
}

// Repaint a GLB instance's materials from the per-instance originals stashed at
// child.userData.__orig by models.js buildInstance. Authored colours are never
// overwritten — state shows as an emissive glow, a grey tint (unavailable), or a
// restore to the authored look. Exported because bound light fixtures
// (roomlights.js) need exactly this and must NOT go through applyStyle, which
// also rescales the object.
//
// partFilter(mesh) -> bool optionally narrows the glow to the shade/bulb
// sub-meshes; meshes it rejects are restored to their authored materials.
export function paintModelState(root, { emissiveHex, emissiveIntensity, grey, partFilter }) {
  root.traverse((child) => {
    if (!child.isMesh || !child.userData.__orig) return;
    const lit = !partFilter || partFilter(child);
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    mats.forEach((m, i) => {
      const orig = child.userData.__orig[i];
      if (!orig) return;
      if (m.color && orig.color !== null) {
        m.color.setHex(orig.color);
        if (grey) m.color.lerp(GREY_LERP_TARGET, 0.7);
      }
      if (m.emissive) { // unlit materials (KHR_materials_unlit) have none
        if (lit && emissiveHex !== undefined && emissiveHex !== null && !grey) {
          m.emissive.setHex(emissiveHex);
          m.emissiveIntensity = emissiveIntensity ?? 1;
        } else {
          m.emissive.setHex(grey ? 0x000000 : (orig.emissive ?? 0x000000));
          m.emissiveIntensity = orig.emissiveIntensity;
        }
      }
    });
  });
}

export function styleMarker(entityId) {
  const marker = markers.get(entityId);
  if (!marker) return;
  const s = states.get(entityId);
  const type = marker.userData.type;
  const base = baseColor(type);

  if (!s || s.state === 'unavailable' || s.state === 'unknown') {
    applyStyle(marker, { grey: true, stateScale: 0.8 });
    return;
  }

  // camera: keep the type color even when idle (so cams stay findable),
  // glow + grow while recording/streaming
  if (type === 'camera') {
    const active = s.state === 'recording' || s.state === 'streaming';
    applyStyle(marker, {
      color: base, emissiveHex: base,
      emissiveIntensity: active ? 0.9 : 0.15,
      stateScale: active ? 1.3 : 1.0,
    });
    return;
  }

  const isToggleable = ['light', 'switch', 'binary_sensor', 'fan', 'cover',
                        'lock', 'media_player', 'input_boolean',
                        'climate'].includes(type);
  if (isToggleable) {
    if (ON_STATES.has(s.state)) {
      applyStyle(marker, { color: base, emissiveHex: base,
                           emissiveIntensity: 0.7, stateScale: 1.25 });
    } else {
      // model markers: null emissive = restore authored materials
      applyStyle(marker, { color: 0x555e69, emissiveHex: marker.userData.modelId
                           ? null : 0x000000, stateScale: 1.0 });
    }
  } else {
    // sensors etc: always show the type color, dimly lit
    applyStyle(marker, { color: base, emissiveHex: base,
                         emissiveIntensity: 0.25, stateScale: 1.0 });
  }
}
