// Level selector, device side panel, room editor.
import { api } from './api.js';
import { floorGroups, setLevel, getLevel, highlightRoom } from './house.js';
import { getState, friendlyName, stateLabel, onStateApplied } from './state.js';
import { exitFocus, getFocusedRoomId } from './focus.js';
import { renderControls, createCameraView, isSliderActive } from './controls.js';

const $ = (id) => document.getElementById(id);

let structure = null;   // HA tree from /api/ha/structure (may be null)
let house = null;       // our layout from /api/house
let reloadHouse = null; // callback from main.js: refetch + rebuild scene
let selectedRoomId = null;
let panelEntityId = null;

// ---------------------------------------------------------------- helpers

function areaById(areaId) {
  if (!structure || !areaId) return null;
  for (const f of structure.floors) {
    const a = f.areas.find((a) => a.area_id === areaId);
    if (a) return a;
  }
  return null;
}

function allAreas() {
  if (!structure) return [];
  return structure.floors.flatMap((f) =>
    f.areas.map((a) => ({ ...a, floorName: f.name })));
}

function findRoom(roomId) {
  for (const f of house.floors) {
    const r = (f.rooms || []).find((r) => r.id === roomId);
    if (r) return { room: r, floor: f };
  }
  return null;
}

// ---------------------------------------------------------------- init

export function initUI({ structure: s, house: h, onReload }) {
  structure = s;
  house = h;
  reloadHouse = onReload;

  buildLevelButtons();
  fillFloorSelect();
  fillAreaSelect();
  renderRoomList();

  $('btn-editor').onclick = () => $('editor').classList.toggle('hidden');
  $('btn-refresh').onclick = async () => {
    try { await api.refreshHA(); } catch { /* not configured */ }
    setTimeout(reloadHouse, 1500);
  };
  $('btn-sync').onclick = async () => {
    const btn = $('btn-sync');
    const label = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Syncing…';
    try {
      // Pull the latest registries first, then let the WS refresh land before
      // reconciling against the cache.
      try { await api.refreshHA(); } catch { /* HA not configured */ }
      await new Promise((r) => setTimeout(r, 1500));
      const res = await api.syncHouse();
      await reloadHouse();
      const parts = [];
      if (res.floors_added) parts.push(`${res.floors_added} floor(s) added`);
      if (res.rooms_moved) parts.push(`${res.rooms_moved} room(s) moved`);
      if (res.rooms_added) parts.push(`${res.rooms_added} room(s) added`);
      if (res.devices_added) parts.push(`${res.devices_added} device(s) added`);
      if (res.floors_removed) parts.push(`${res.floors_removed} empty floor(s) removed`);
      alert(parts.length ? `Synced with HA: ${parts.join(', ')}.`
                         : 'Already in sync with Home Assistant.');
    } catch (e) {
      alert(`Sync failed: ${e.message}`);
    }
    btn.disabled = false;
    btn.textContent = label;
  };
  $('btn-generate').onclick = async () => {
    const btn = $('btn-generate');
    btn.disabled = true;
    try {
      const res = await api.generateHouse();
      await reloadHouse();
      alert(res.rooms || res.devices
        ? `Added ${res.rooms} room(s) and ${res.devices} device(s) from HA.`
        : 'Nothing new — every HA area is already in the layout.');
    } catch (e) {
      alert(`Generate failed: ${e.message}`);
    }
    btn.disabled = false;
  };
  document.querySelectorAll('.close[data-close]').forEach((btn) => {
    btn.onclick = () => {
      $(btn.dataset.close).classList.add('hidden');
      if (btn.dataset.close === 'device-panel') {
        panelEntityId = null;
        stopDeviceCamera(); // drop the MJPEG connection, don't stream unseen
      }
    };
  });

  $('room-form').onsubmit = onRoomFormSubmit;
  $('rf-cancel').onclick = resetRoomForm;

  onStateApplied((entityId) => {
    if (isSliderActive()) return; // HA echoes mid-drag must not rebuild the slider
    if (panelEntityId && (entityId === null || entityId === panelEntityId)) {
      renderDevicePanel(panelEntityId);
    }
  });
}

export function updateData({ structure: s, house: h }) {
  if (s) structure = s;
  house = h;
  buildLevelButtons();
  fillFloorSelect();
  fillAreaSelect();
  renderRoomList();
  if (selectedRoomId && !findRoom(selectedRoomId)) {
    selectedRoomId = null;
    resetRoomForm();
  }
  if (selectedRoomId) renderPlacementSection();
}

export function setConnStatus(status) {
  const dot = $('conn-status');
  dot.className = 'status-dot ' + status;
  $('conn-label').textContent = status;
}

let bannerTimer = null;

export function showBanner(msg, timeoutMs = 0) {
  const b = $('banner');
  clearTimeout(bannerTimer);
  if (!msg) { b.classList.add('hidden'); return; }
  b.textContent = msg;
  b.classList.remove('hidden');
  if (timeoutMs) bannerTimer = setTimeout(() => b.classList.add('hidden'), timeoutMs);
}

// ---------------------------------------------------------------- levels

function buildLevelButtons() {
  const nav = $('levels');
  nav.innerHTML = '';
  const mk = (label, value) => {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.dataset.level = value;
    if (String(getLevel()) === String(value)) btn.classList.add('active');
    btn.onclick = () => {
      exitFocus({ flyBack: false }); // level switch overrides room focus
      setLevel(value === 'all' ? 'all' : Number(value));
      nav.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
    };
    nav.appendChild(btn);
  };
  mk('All floors', 'all');
  for (const f of [...house.floors].sort((a, b) => a.level - b.level)) {
    mk(`${f.level} · ${f.name}`, f.level);
  }
}

// ---------------------------------------------------------------- camera view

// The device panel shows at most one camera; the view is only recreated when
// the entity changes, so panel re-renders from live state echoes never touch
// the <img> (an MJPEG stream would reconnect on every echo otherwise).
let dpCam = null;

function applyDeviceCamera(entityId) {
  if (!dpCam || dpCam.entityId !== entityId) {
    stopDeviceCamera();
    dpCam = createCameraView(entityId, {
      onError: (m) => showBanner(m, 4000),
    });
    $('dp-camera').replaceChildren(dpCam.el);
  }
  $('dp-camera').classList.remove('hidden');
}

function stopDeviceCamera() {
  dpCam?.destroy();
  dpCam = null;
  $('dp-camera').classList.add('hidden');
}

// ---------------------------------------------------------------- device panel

export function openDevicePanel(entityId) {
  panelEntityId = entityId;
  renderDevicePanel(entityId);
  $('device-panel').classList.remove('hidden');
}

function renderDevicePanel(entityId) {
  const s = getState(entityId);
  $('dp-name').textContent = friendlyName(entityId);
  $('dp-entity').textContent = entityId;
  $('dp-state').textContent = stateLabel(entityId);

  const attrs = $('dp-attrs');
  attrs.innerHTML = '';
  const interesting = ['brightness', 'color_temp_kelvin', 'temperature',
    'current_temperature', 'humidity', 'battery_level', 'device_class',
    'media_title', 'last_changed'];
  const a = s?.attributes || {};
  for (const key of interesting) {
    if (a[key] !== undefined) {
      const row = document.createElement('div');
      row.innerHTML = `<span>${key}</span><span>${a[key]}</span>`;
      attrs.appendChild(row);
    }
  }
  if (s?.last_changed) {
    const row = document.createElement('div');
    row.innerHTML = `<span>last changed</span><span>${new Date(s.last_changed).toLocaleTimeString()}</span>`;
    attrs.appendChild(row);
  }

  const controls = $('dp-controls');
  controls.innerHTML = '';
  const domain = entityId.split('.')[0];

  if (domain === 'camera') {
    applyDeviceCamera(entityId);
    const live = document.createElement('button');
    const paint = () => {
      live.textContent = dpCam.isLive() ? 'Stop live view' : 'Live view';
      live.className = dpCam.isLive() ? 'secondary' : '';
    };
    live.onclick = () => {
      dpCam.setLive(!dpCam.isLive());
      paint();
    };
    dpCam.onModeChange = paint; // stream failure falls back to snapshots
    paint();
    controls.appendChild(live);
  } else {
    stopDeviceCamera();
    renderControls(controls, entityId, {
      onError: (m) => showBanner(m, 4000),
    });
  }
}

// ---------------------------------------------------------------- room editor

function fillFloorSelect() {
  const sel = $('rf-floor');
  sel.innerHTML = '';
  for (const f of [...house.floors].sort((a, b) => a.level - b.level)) {
    const opt = document.createElement('option');
    opt.value = f.id;
    opt.textContent = `${f.level} · ${f.name}`;
    sel.appendChild(opt);
  }
}

function fillAreaSelect() {
  const sel = $('rf-area');
  sel.innerHTML = '<option value="">— none —</option>';
  for (const a of allAreas()) {
    const opt = document.createElement('option');
    opt.value = a.area_id;
    opt.textContent = `${a.name}${a.floorName ? ` (${a.floorName})` : ''}`;
    sel.appendChild(opt);
  }
}

function renderRoomList() {
  const list = $('room-list');
  list.innerHTML = '';
  for (const f of [...house.floors].sort((a, b) => a.level - b.level)) {
    for (const room of f.rooms || []) {
      const item = document.createElement('div');
      item.className = 'room-item' + (room.id === selectedRoomId ? ' selected' : '');
      const name = document.createElement('span');
      name.className = 'name';
      name.textContent = `${room.name} (L${f.level})`;
      name.onclick = () => selectRoom(room.id);
      const edit = document.createElement('button');
      edit.className = 'small secondary';
      edit.textContent = 'Edit';
      edit.onclick = () => selectRoom(room.id);
      const rm = document.createElement('button');
      rm.className = 'small danger';
      rm.textContent = '✕';
      rm.onclick = async () => {
        if (!confirm(`Delete room "${room.name}"?`)) return;
        await api.deleteRoom(room.id);
        if (selectedRoomId === room.id) { selectedRoomId = null; resetRoomForm(); }
        reloadHouse();
      };
      item.append(name, edit, rm);
      list.appendChild(item);
    }
  }
  if (!list.children.length) {
    list.innerHTML = '<p class="muted">No rooms yet — add one below.</p>';
  }
}

export function selectRoom(roomId) {
  selectedRoomId = roomId;
  const found = findRoom(roomId);
  if (!found) return;
  const { room, floor } = found;
  // focus mode owns room opacities while active — don't fight its fades
  if (!getFocusedRoomId()) highlightRoom(roomId);
  $('editor').classList.remove('hidden');

  $('room-form-title').textContent = `Edit: ${room.name}`;
  $('rf-id').value = room.id;
  $('rf-name').value = room.name;
  $('rf-floor').value = floor.id;
  $('rf-area').value = room.ha_area_id || '';
  $('rf-width').value = room.footprint.width;
  $('rf-depth').value = room.footprint.depth;
  $('rf-height').value = room.height;
  $('rf-x').value = room.footprint.x;
  $('rf-z').value = room.footprint.z;
  $('rf-color').value = room.color || '#8fa8bf';
  $('rf-save').textContent = 'Update room';
  $('rf-cancel').classList.remove('hidden');

  renderRoomList();
  renderPlacementSection();
}

function resetRoomForm() {
  selectedRoomId = null;
  if (!getFocusedRoomId()) highlightRoom(null);
  $('room-form-title').textContent = 'Add room';
  $('room-form').reset();
  $('rf-id').value = '';
  $('rf-width').value = 13; $('rf-depth').value = 10; $('rf-height').value = 8;
  $('rf-x').value = 0; $('rf-z').value = 0; $('rf-color').value = '#8fa8bf';
  $('rf-save').textContent = 'Save room';
  $('rf-cancel').classList.add('hidden');
  $('placement-section').classList.add('hidden');
  renderRoomList();
}

async function onRoomFormSubmit(e) {
  e.preventDefault();
  const payload = {
    name: $('rf-name').value.trim(),
    floor_id: Number($('rf-floor').value),
    ha_area_id: $('rf-area').value || null,
    footprint: {
      x: Number($('rf-x').value),
      z: Number($('rf-z').value),
      width: Number($('rf-width').value),
      depth: Number($('rf-depth').value),
    },
    height: Number($('rf-height').value),
    color: $('rf-color').value,
  };
  const id = $('rf-id').value;
  try {
    if (id) {
      await api.updateRoom(Number(id), payload);
    } else {
      const res = await api.createRoom(payload);
      selectedRoomId = res.id;
    }
    await reloadHouse();
    if (selectedRoomId) selectRoom(selectedRoomId);
  } catch (err) {
    alert(`Save failed: ${err.message}`);
  }
}

// ---------------------------------------------------------------- placements

function renderPlacementSection() {
  const found = findRoom(selectedRoomId);
  if (!found) return;
  const { room } = found;
  $('placement-section').classList.remove('hidden');
  $('placement-room-name').textContent = room.name;

  // already-placed devices with editable positions
  const placed = $('placed-list');
  placed.innerHTML = '';
  for (const dev of room.devices || []) {
    const item = document.createElement('div');
    item.className = 'placed-item';
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = friendlyName(dev.entity_id);
    name.title = dev.entity_id;
    name.onclick = () => openDevicePanel(dev.entity_id);

    const inputs = ['x', 'y', 'z'].map((axis) => {
      const inp = document.createElement('input');
      inp.type = 'number'; inp.step = '0.1'; inp.title = axis;
      inp.value = dev.position[axis];
      inp.onchange = async () => {
        await api.updatePlacement(dev.id, { [axis]: Number(inp.value) });
        reloadHouse();
      };
      return inp;
    });

    const rm = document.createElement('button');
    rm.className = 'small danger';
    rm.textContent = '✕';
    rm.onclick = async () => { await api.deletePlacement(dev.id); reloadHouse(); };
    item.append(name, ...inputs, rm);
    placed.appendChild(item);
  }
  if (!placed.children.length) {
    placed.innerHTML = '<p class="muted">Nothing placed yet.</p>';
  }

  // entities available in the linked HA area
  const list = $('entity-list');
  list.innerHTML = '';
  const area = areaById(room.ha_area_id);
  if (!area) {
    list.innerHTML = structure
      ? '<p class="muted">Link the room to an HA area to list its entities.</p>'
      : '<p class="muted">HA structure not loaded.</p>';
    return;
  }
  const placedIds = new Set((room.devices || []).map((d) => d.entity_id));
  const candidates = area.entities.filter((e) => !e.hidden && !placedIds.has(e.entity_id));
  for (const ent of candidates) {
    const item = document.createElement('div');
    item.className = 'entity-item';
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = `${ent.name}`;
    name.title = ent.entity_id;
    const tag = document.createElement('span');
    tag.className = 'muted';
    tag.textContent = ent.domain;
    const add = document.createElement('button');
    add.className = 'small';
    add.textContent = 'Place';
    add.onclick = async () => {
      const fp = room.footprint;
      await api.placeDevice(room.id, {
        entity_id: ent.entity_id,
        type: ent.domain,
        position: {
          x: +(fp.width * (0.2 + 0.6 * Math.random())).toFixed(2),
          y: ['light', 'camera'].includes(ent.domain)
            ? Math.max(room.height - 1.0, 1.5) : 4.0,
          z: +(fp.depth * (0.2 + 0.6 * Math.random())).toFixed(2),
        },
      });
      reloadHouse();
    };
    item.append(name, tag, add);
    list.appendChild(item);
  }
  if (!candidates.length) {
    list.innerHTML = '<p class="muted">All entities in this area are placed.</p>';
  }
}
