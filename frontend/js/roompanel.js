// Room focus panel: opens with room focus mode (left side, ~30% wide) and
// shows every visible entity in the room as a tile — sensor readouts,
// tap-to-toggle switches/lights, live camera views, embedded controls — plus
// an edit mode that persists per-placement visibility to the layout DB.
import { api } from './api.js';
import { getState, friendlyName, stateLabel, isOn, onStateApplied } from './state.js';
import { renderControls, createCameraView, isSliderActive } from './controls.js';
import { onFocusChanged, exitFocus } from './focus.js';
import { setLabelHidden } from './labels.js';
import { setMarkerHidden } from './devices.js';
import { openDevicePanel, showBanner } from './ui.js';

const $ = (id) => document.getElementById(id);
const onError = (m) => showBanner(m, 4000);

let house = null;
let currentRoomId = null;
let editMode = false;
const tiles = new Map();    // entity_id -> { render } (non-camera tiles only)
const camViews = new Map(); // entity_id -> camera view handle
let shownIds = new Set();   // entity_ids currently rendered as tiles

const TOGGLE_DOMAINS = new Set(['light', 'switch', 'fan', 'input_boolean']);

// tile grouping, in display order; anything unmatched lands in "Other"
const SECTIONS = [
  { title: 'Cameras', domains: new Set(['camera']) },
  { title: 'Climate', domains: new Set(['climate']) },
  { title: 'Lights & switches', domains: TOGGLE_DOMAINS },
  { title: 'Covers & locks', domains: new Set(['cover', 'lock']) },
  { title: 'Media', domains: new Set(['media_player']) },
  { title: 'Sensors', domains: new Set(['sensor', 'binary_sensor']) },
  { title: 'Scenes & scripts', domains: new Set(['scene', 'script']) },
];

function findRoom(roomId) {
  for (const f of house?.floors || []) {
    const r = (f.rooms || []).find((r) => r.id === roomId);
    if (r) return r;
  }
  return null;
}

function domainOf(dev) {
  return dev.entity_id.split('.')[0];
}

// unknown/unavailable entities render as dead cards — keep them out of the
// tile view (they stay listed in edit mode, and reappear if they come back)
function isUsable(dev) {
  const s = getState(dev.entity_id);
  return !!s && s.state !== 'unknown' && s.state !== 'unavailable';
}

function shownDevices(room) {
  return (room.devices || []).filter((d) => d.visible !== 0 && isUsable(d));
}

// ---------------------------------------------------------------- tiles

function cameraTile(dev) {
  const tile = document.createElement('div');
  tile.className = 'tile camera';
  const view = createCameraView(dev.entity_id, { live: true, onError });
  camViews.set(dev.entity_id, view);

  const name = document.createElement('span');
  name.className = 't-name';
  name.textContent = friendlyName(dev.entity_id);

  const toggle = document.createElement('button');
  toggle.className = 'cam-toggle small secondary';
  const paint = () => {
    toggle.textContent = view.isLive() ? '⏸ Pause' : '▶ Live';
    toggle.title = view.isLive() ? 'Pause (switch to snapshots)' : 'Start live stream';
  };
  toggle.onclick = () => { view.setLive(!view.isLive()); paint(); };
  view.onModeChange = paint; // stream failure falls back to snapshots
  paint();

  tile.append(view.el, name, toggle);
  return tile;
}

function sensorTile(dev) {
  const tile = document.createElement('div');
  tile.className = 'tile tappable';
  tile.title = dev.entity_id;
  tile.onclick = () => openDevicePanel(dev.entity_id);

  const name = document.createElement('div');
  name.className = 't-name';
  const value = document.createElement('div');
  value.className = 't-value';
  const sub = document.createElement('div');
  sub.className = 't-sub';
  tile.append(name, value, sub);

  const render = () => {
    name.textContent = friendlyName(dev.entity_id);
    value.textContent = stateLabel(dev.entity_id);
    const dc = getState(dev.entity_id)?.attributes?.device_class;
    sub.textContent = (dc || domainOf(dev)).replaceAll('_', ' ');
  };
  render();
  tiles.set(dev.entity_id, { render });
  return tile;
}

function toggleTile(dev) {
  const tile = document.createElement('div');
  tile.className = 'tile tappable';
  tile.title = dev.entity_id;

  const name = document.createElement('div');
  name.className = 't-name';
  const value = document.createElement('div');
  value.className = 't-value';
  const more = document.createElement('button');
  more.className = 't-more';
  more.textContent = '⋯';
  more.title = 'Details & sliders';
  more.onclick = (e) => {
    e.stopPropagation();
    openDevicePanel(dev.entity_id);
  };
  tile.append(more, name, value);

  tile.onclick = () => {
    api.control({ entity_id: dev.entity_id, domain: domainOf(dev), service: 'toggle' })
      .catch((e) => onError(`Control failed: ${e.message}`));
  };

  const render = () => {
    name.textContent = friendlyName(dev.entity_id);
    value.textContent = stateLabel(dev.entity_id);
    tile.classList.toggle('on', isOn(dev.entity_id));
  };
  render();
  tiles.set(dev.entity_id, { render });
  return tile;
}

function richTile(dev) {
  const tile = document.createElement('div');
  tile.className = 'tile wide';
  tile.title = dev.entity_id;

  const name = document.createElement('div');
  name.className = 't-name';
  const body = document.createElement('div');
  body.className = 'controls';
  tile.append(name, body);

  const render = () => {
    name.textContent = friendlyName(dev.entity_id);
    body.innerHTML = '';
    renderControls(body, dev.entity_id, { compact: true, onError });
  };
  render();
  tiles.set(dev.entity_id, { render });
  return tile;
}

function makeTile(dev) {
  const domain = domainOf(dev);
  if (domain === 'camera') return cameraTile(dev);
  if (domain === 'sensor' || domain === 'binary_sensor') return sensorTile(dev);
  if (TOGGLE_DOMAINS.has(domain)) return toggleTile(dev);
  return richTile(dev);
}

// ---------------------------------------------------------------- rendering

function teardownTiles() {
  for (const view of camViews.values()) view.destroy(); // aborts MJPEG streams
  camViews.clear();
  tiles.clear();
  $('rp-tiles').innerHTML = '';
}

function renderTiles(room) {
  teardownTiles();
  const container = $('rp-tiles');
  const devices = shownDevices(room);
  shownIds = new Set(devices.map((d) => d.entity_id));
  const byName = (a, b) =>
    friendlyName(a.entity_id).localeCompare(friendlyName(b.entity_id));

  const remaining = [...devices];
  const groups = [];
  for (const sec of SECTIONS) {
    const members = remaining.filter((d) => sec.domains.has(domainOf(d)));
    if (members.length) {
      groups.push({ title: sec.title, members: members.sort(byName) });
      for (const m of members) remaining.splice(remaining.indexOf(m), 1);
    }
  }
  if (remaining.length) groups.push({ title: 'Other', members: remaining.sort(byName) });

  for (const group of groups) {
    const heading = document.createElement('div');
    heading.className = 'rp-section';
    heading.textContent = group.title;
    container.appendChild(heading);
    for (const dev of group.members) container.appendChild(makeTile(dev));
  }
  if (!devices.length) {
    const placed = (room.devices || []).length;
    container.innerHTML = !placed
      ? '<p class="muted">No devices placed in this room yet.</p>'
      : (room.devices || []).some((d) => d.visible !== 0)
        ? '<p class="muted">All entities in this room are currently unavailable.</p>'
        : '<p class="muted">All entities in this room are hidden — use Edit to show some.</p>';
  }
}

// edit mode: checklist of every placed device, hidden ones included
function renderEditList(room) {
  teardownTiles();
  const container = $('rp-tiles');
  const devices = [...(room.devices || [])].sort((a, b) =>
    friendlyName(a.entity_id).localeCompare(friendlyName(b.entity_id)));

  for (const dev of devices) {
    const row = document.createElement('label');
    row.className = 'rp-editrow';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = dev.visible !== 0;
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = friendlyName(dev.entity_id);
    name.title = dev.entity_id;
    const tag = document.createElement('span');
    tag.className = 'muted';
    tag.textContent = domainOf(dev);

    cb.onchange = () => {
      const next = cb.checked ? 1 : 0;
      // optimistic in-place update — reloading the house here would exit
      // focus mode and slam this panel shut mid-edit
      dev.visible = next;
      setLabelHidden(dev.entity_id, next === 0);
      setMarkerHidden(dev.entity_id, next === 0);
      updateHeader(room);
      api.updatePlacement(dev.id, { visible: next }).catch((e) => {
        dev.visible = next ? 0 : 1;
        cb.checked = !cb.checked;
        setLabelHidden(dev.entity_id, next === 1);
        setMarkerHidden(dev.entity_id, next === 1);
        updateHeader(room);
        onError(`Save failed: ${e.message}`);
      });
    };

    row.append(cb, name, tag);
    container.appendChild(row);
  }
  if (!devices.length) {
    container.innerHTML = '<p class="muted">No devices placed in this room yet.</p>';
  }
}

function updateHeader(room) {
  $('rp-name').textContent = room.name;
  const total = (room.devices || []).length;
  const shown = shownDevices(room).length;
  $('rp-count').textContent = shown < total
    ? `${shown} of ${total} entities`
    : `${total} entit${total === 1 ? 'y' : 'ies'}`;
  const btn = $('rp-edit');
  btn.textContent = editMode ? 'Done' : 'Edit';
  btn.classList.toggle('secondary', !editMode);
}

function render() {
  const room = findRoom(currentRoomId);
  if (!room) return;
  updateHeader(room);
  if (editMode) renderEditList(room);
  else renderTiles(room);
}

// ---------------------------------------------------------------- open/close

export function openRoomPanel(roomId) {
  if (currentRoomId === roomId) return;
  if (currentRoomId !== null) teardownTiles(); // switching rooms: drop old streams
  if (!findRoom(roomId)) return;
  currentRoomId = roomId;
  editMode = false;
  render();
  $('room-panel').classList.remove('hidden');
  document.body.classList.add('room-panel-open');
}

export function closeRoomPanel() {
  if (currentRoomId === null) return;
  teardownTiles();
  currentRoomId = null;
  editMode = false;
  $('room-panel').classList.add('hidden');
  document.body.classList.remove('room-panel-open');
}

export function updateRoomPanelData(h) {
  house = h;
  // reloadHouse exits focus first, which closes the panel before data swaps;
  // this only refreshes the reference for the next open
}

export function initRoomPanel({ house: h }) {
  house = h;

  onFocusChanged((roomId) => {
    if (roomId) openRoomPanel(roomId);
    else closeRoomPanel();
  });

  $('rp-close').onclick = () => exitFocus(); // emits null -> closeRoomPanel
  $('rp-edit').onclick = () => {
    if (currentRoomId === null) return;
    editMode = !editMode;
    render();
  };

  onStateApplied((entityId) => {
    if (currentRoomId === null || editMode || isSliderActive()) return;
    // availability flips add/remove tiles, so rebuild when the shown set changed
    const room = findRoom(currentRoomId);
    if (room) {
      const want = shownDevices(room);
      if (want.length !== shownIds.size ||
          want.some((d) => !shownIds.has(d.entity_id))) {
        render();
        return;
      }
    }
    if (entityId === null) {
      for (const t of tiles.values()) t.render();
    } else {
      tiles.get(entityId)?.render();
    }
  });
}
