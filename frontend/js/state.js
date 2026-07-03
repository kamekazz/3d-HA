// Holds live entity states and applies them to the 3D markers.
import { markers, baseColor } from './devices.js';

const states = new Map(); // entity_id -> HA state object
const listeners = new Set();

const ON_STATES = new Set(['on', 'open', 'playing', 'home', 'unlocked', 'heat',
                           'cool', 'heat_cool', 'auto', 'cleaning']);

export function getState(entityId) {
  return states.get(entityId);
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

export function stateLabel(entityId) {
  const s = states.get(entityId);
  if (!s) return 'unknown';
  const unit = s.attributes?.unit_of_measurement;
  return unit ? `${s.state} ${unit}` : s.state;
}

function styleMarker(entityId) {
  const marker = markers.get(entityId);
  if (!marker) return;
  const s = states.get(entityId);
  const type = marker.userData.type;
  const base = baseColor(type);

  if (!s || s.state === 'unavailable' || s.state === 'unknown') {
    marker.material.color.setHex(0x3a4149);
    marker.material.emissive.setHex(0x000000);
    marker.scale.setScalar(0.8);
    return;
  }

  const isToggleable = ['light', 'switch', 'binary_sensor', 'fan', 'cover',
                        'lock', 'media_player', 'input_boolean',
                        'climate'].includes(type);
  if (isToggleable) {
    if (ON_STATES.has(s.state)) {
      marker.material.color.setHex(base);
      marker.material.emissive.setHex(base);
      marker.material.emissiveIntensity = 0.7;
      marker.scale.setScalar(1.25);
    } else {
      marker.material.color.setHex(0x555e69);
      marker.material.emissive.setHex(0x000000);
      marker.scale.setScalar(1.0);
    }
  } else {
    // sensors etc: always show the type color, dimly lit
    marker.material.color.setHex(base);
    marker.material.emissive.setHex(base);
    marker.material.emissiveIntensity = 0.25;
    marker.scale.setScalar(1.0);
  }
}
