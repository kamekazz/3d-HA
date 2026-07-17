// Level selector, device side panel, room editor, model library, object panel.
import { api } from './api.js';
import { floorGroups, setLevel, getLevel, highlightRoom,
         setShellTransform, getShellRoot, getShellConfig } from './house.js';
import { getState, friendlyName, stateLabel, onStateApplied } from './state.js';
import { exitFocus, getFocusedRoomId } from './focus.js';
import { renderControls, createCameraView, isSliderActive } from './controls.js';
import { markers, areMarkersShown, setMarkersShown } from './devices.js';
import { objects3d } from './objects.js';
import { setSelected, onDragMoved } from './drag.js';
import { invalidateModel } from './models.js';
import { fillTextureSelect } from './textures.js';
import { canEdit } from './route.js';

const $ = (id) => document.getElementById(id);

let structure = null;   // HA tree from /api/ha/structure (may be null)
let house = null;       // our layout from /api/house
let reloadHouse = null; // callback from main.js: refetch + rebuild scene
let selectedRoomId = null;
let panelEntityId = null;
let panelObjectId = null;
let modelsList = [];    // library from /api/house/models

export let appMode = 'view'; // 'view' or 'edit'

export function setAppMode(mode) {
  if (!canEdit) mode = 'view'; // "/" is the viewer — edit mode isn't reachable
  appMode = mode;
  document.querySelectorAll('.edit-only').forEach(el => {
    el.classList.toggle('hidden', mode === 'view');
  });
  if (mode === 'view') {
    $('editor').classList.add('hidden');
    $('object-panel').classList.add('hidden');
    $('models-modal').classList.add('hidden');
    $('planner').classList.add('hidden');
  }
  updateAlignAvailability();
  // dashboard.js/roomcards.js hide their chrome off this class (CSS-only)
  document.body.classList.toggle('app-edit', mode === 'edit');

  // Update scene background and grid when mode changes
  const ev = new CustomEvent('appModeChanged', { detail: { mode } });
  window.dispatchEvent(ev);
  paintMarkersBtn();
}

// ○ Devices topbar button: show/hide device markers on floor levels. The
// House (shell) view always hides markers, and edit mode force-shows them
// (drag/placement need them) — the button is disabled in both, and the
// user's preference resumes on a normal floor view.
let inHouseMode = false; // kept fresh via onLevelChanged in initUI
function paintMarkersBtn() {
  const btn = $('btn-markers');
  if (!btn) return;
  btn.textContent = areMarkersShown() ? '◉ Devices' : '○ Devices';
  btn.disabled = appMode === 'edit' || inHouseMode;
  btn.title = inHouseMode
    ? 'Devices are hidden in the House view'
    : appMode === 'edit'
      ? 'Markers are always visible in edit mode'
      : 'Show or hide device markers';
}

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

function findObjectById(objectId) {
  for (const f of house.floors) {
    for (const r of f.rooms || []) {
      const o = (r.objects || []).find((o) => o.id === objectId);
      if (o) return { obj: o, room: r, floor: f };
    }
  }
  return null;
}

function findPlacementById(placementId) {
  for (const f of house.floors) {
    for (const r of f.rooms || []) {
      const d = (r.devices || []).find((d) => d.id === placementId);
      if (d) return { dev: d, room: r, floor: f };
    }
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
  fillTextureSelect($('rf-wall-tex'));
  fillTextureSelect($('rf-floor-tex'));
  fillTextureSelect($('rf-floor-tex'));
  renderRoomList();

  // The topbar is editor chrome: CSS hides it on "/", and the level selector
  // and panels move up into the space it leaves.
  document.body.classList.toggle('view-only', !canEdit);

  $('chk-edit-mode').onchange = (e) => {
    setAppMode(e.target.checked ? 'edit' : 'view');
  };
  $('btn-markers').onclick = () => {
    setMarkersShown(!areMarkersShown());
    paintMarkersBtn();
  };
  window.addEventListener('levelChanged', (e) => {
    inHouseMode = e.detail.houseMode;
    paintMarkersBtn();
  });
  // Initialize UI state — /edit opens ready to edit, the toggle previews.
  $('chk-edit-mode').checked = canEdit;
  setAppMode(canEdit ? 'edit' : 'view');

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
        setSelected(null);
      }
      if (btn.dataset.close === 'object-panel') {
        panelObjectId = null;
        setSelected(null);
      }
      if (btn.dataset.close === 'shell-panel') {
        setSelected(null); // stop dragging the shell
      }
    };
  });

  $('room-form').onsubmit = onRoomFormSubmit;
  $('rf-cancel').onclick = resetRoomForm;

  $('btn-models').onclick = openModelsModal;
  $('mm-upload-form').onsubmit = onModelUpload;
  $('btn-align').onclick = openAlignPanel;
  wireShellPanel();
  $('obj-add').onclick = onAddObject;
  wireObjectPanel();
  refreshModels(); // async fill of the library-dependent selects

  // drag ended: server already PATCHed — sync the cached house + open panels
  // without a full reload (the mesh is already where the user left it)
  onDragMoved(({ kind, id, x, z }) => {
    if (kind === 'house-shell') {
      setShellTransform({ x, z }); // keep shellConfig in sync with the drag
      if (!$('shell-panel').classList.contains('hidden')) {
        $('shell-x').value = +x.toFixed(2);
        $('shell-z').value = +z.toFixed(2);
      }
      return;
    }
    if (kind === 'device') {
      const found = findPlacementById(id);
      if (found) { found.dev.position.x = x; found.dev.position.z = z; }
      if (selectedRoomId && found?.room.id === selectedRoomId) renderPlacementSection();
    } else {
      const found = findObjectById(id);
      if (found) { found.obj.position.x = x; found.obj.position.z = z; }
      if (panelObjectId === id) { $('op-x').value = x; $('op-z').value = z; }
      if (selectedRoomId && found?.room.id === selectedRoomId) renderPlacementSection();
    }
  });

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
  // scene was rebuilt: re-point the drag selection at the fresh meshes
  if (panelObjectId) {
    if (findObjectById(panelObjectId)) {
      setSelected(objects3d.get(panelObjectId) || null);
    } else {
      panelObjectId = null;
      $('object-panel').classList.add('hidden');
      setSelected(null);
    }
  } else if (panelEntityId) {
    setSelected(markers.get(panelEntityId) || null);
  } else if (!$('shell-panel').classList.contains('hidden')) {
    // scene rebuilt while aligning: re-point drag at the fresh shell root
    setSelected(getShellRoot());
  }
  updateAlignAvailability();
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
  // 'all' is also "House" mode when a shell model is configured (house.js
  // swaps the generated geometry for the model); label it House either way.
  mk('House', 'all');
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
  // the open panel makes this marker the drag target in the 3D view
  setSelected(markers.get(entityId) || null);
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
  $('rf-wall-color').value = room.wall_color || '#f2ede3';
  $('rf-wall-tex').value = room.wall_texture || '';
  $('rf-floor-color').value = room.floor_color || '#e5decf';
  $('rf-floor-tex').value = room.floor_texture || '';
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
  $('rf-wall-color').value = '#f2ede3'; $('rf-wall-tex').value = '';
  $('rf-floor-color').value = '#e5decf'; $('rf-floor-tex').value = '';
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
    wall_color: $('rf-wall-color').value,
    wall_texture: $('rf-wall-tex').value || null,
    floor_color: $('rf-floor-color').value,
    floor_texture: $('rf-floor-tex').value || null,
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
    placed.appendChild(renderModelRow(dev));
  }
  if (!placed.children.length) {
    placed.innerHTML = '<p class="muted">Nothing placed yet.</p>';
  }

  renderObjectSection(room);

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

// model / rotation / scale controls for one placed device
function renderModelRow(dev) {
  const row = document.createElement('div');
  row.className = 'placed-model-row';

  const sel = document.createElement('select');
  sel.title = '3D model (replaces the default marker)';
  const none = document.createElement('option');
  none.value = '';
  none.textContent = '— default marker —';
  sel.appendChild(none);
  for (const m of modelsList) {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name;
    sel.appendChild(opt);
  }
  sel.value = dev.model_id ?? '';
  sel.onchange = async () => {
    await api.updatePlacement(dev.id, {
      model_id: sel.value ? Number(sel.value) : null,
    });
    reloadHouse();
  };

  const rot = document.createElement('input');
  rot.type = 'number'; rot.step = '15'; rot.title = 'rotation (degrees)';
  rot.value = Math.round((dev.rot_y || 0) * 180 / Math.PI);
  rot.onchange = async () => {
    await api.updatePlacement(dev.id, { rot_y: Number(rot.value) * Math.PI / 180 });
    reloadHouse();
  };

  const scale = document.createElement('input');
  scale.type = 'number'; scale.step = '0.05'; scale.min = '0.01'; scale.title = 'scale';
  scale.value = dev.scale ?? 1;
  scale.onchange = async () => {
    await api.updatePlacement(dev.id, { scale: Number(scale.value) || 1 });
    reloadHouse();
  };

  row.append(sel, rot, scale);
  return row;
}

// ---------------------------------------------------------------- objects

function renderObjectSection(room) {
  const list = $('object-list');
  list.innerHTML = '';
  for (const o of room.objects || []) {
    const item = document.createElement('div');
    item.className = 'placed-item';
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = o.name || o.model_name;
    name.title = 'Open the object panel (rotate, resize, drag)';
    name.onclick = () => openObjectPanel(o.id);

    const inputs = ['x', 'y', 'z'].map((axis) => {
      const inp = document.createElement('input');
      inp.type = 'number'; inp.step = '0.1'; inp.title = axis;
      inp.value = o.position[axis];
      inp.onchange = async () => {
        await api.updateObject(o.id, { [axis]: Number(inp.value) });
        reloadHouse();
      };
      return inp;
    });

    const rm = document.createElement('button');
    rm.className = 'small danger';
    rm.textContent = '✕';
    rm.onclick = async () => {
      await api.deleteObject(o.id);
      if (panelObjectId === o.id) {
        panelObjectId = null;
        $('object-panel').classList.add('hidden');
        setSelected(null);
      }
      reloadHouse();
    };
    item.append(name, ...inputs, rm);
    list.appendChild(item);
  }
  if (!list.children.length) {
    list.innerHTML = '<p class="muted">No objects in this room.</p>';
  }

  const sel = $('obj-model-select');
  sel.innerHTML = '';
  if (!modelsList.length) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '— upload models first —';
    sel.appendChild(opt);
    sel.disabled = true;
    $('obj-add').disabled = true;
  } else {
    sel.disabled = false;
    $('obj-add').disabled = false;
    for (const m of modelsList) {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.name;
      sel.appendChild(opt);
    }
  }
}

async function onAddObject() {
  const found = findRoom(selectedRoomId);
  const modelId = Number($('obj-model-select').value);
  if (!found || !modelId) return;
  const fp = found.room.footprint;
  try {
    const res = await api.addObject(found.room.id, {
      model_id: modelId,
      position: { x: +(fp.width / 2).toFixed(2), y: 0, z: +(fp.depth / 2).toFixed(2) },
    });
    await reloadHouse();
    openObjectPanel(res.id); // selected right away, ready to drag into place
  } catch (e) {
    alert(`Could not add object: ${e.message}`);
  }
}

// ---------------------------------------------------------------- object panel

export function openObjectPanel(objectId) {
  const found = findObjectById(objectId);
  if (!found) return;
  panelObjectId = objectId;
  const { obj } = found;
  $('op-name').textContent = obj.name || obj.model_name;
  $('op-model').textContent = `Model: ${obj.model_name} · ${found.room.name}`;
  $('op-x').value = obj.position.x;
  $('op-y').value = obj.position.y;
  $('op-z').value = obj.position.z;
  $('op-rot').value = Math.round((obj.rot_y || 0) * 180 / Math.PI);
  $('op-scale').value = obj.scale ?? 1;
  $('op-rename').value = obj.name || '';
  setSelected(objects3d.get(objectId) || null);
  $('object-panel').classList.remove('hidden');
}

function wireObjectPanel() {
  const patch = async (data) => {
    if (!panelObjectId) return;
    const keep = panelObjectId;
    try {
      await api.updateObject(keep, data);
      await reloadHouse();
      openObjectPanel(keep);
    } catch (e) {
      alert(`Update failed: ${e.message}`);
    }
  };
  $('op-x').onchange = () => patch({ x: Number($('op-x').value) });
  $('op-y').onchange = () => patch({ y: Number($('op-y').value) });
  $('op-z').onchange = () => patch({ z: Number($('op-z').value) });
  $('op-rot').onchange = () => patch({ rot_y: Number($('op-rot').value) * Math.PI / 180 });
  $('op-scale').onchange = () => patch({ scale: Number($('op-scale').value) || 1 });
  $('op-rename').onchange = () => patch({ name: $('op-rename').value.trim() });
  $('op-delete').onclick = async () => {
    if (!panelObjectId) return;
    await api.deleteObject(panelObjectId);
    panelObjectId = null;
    $('object-panel').classList.add('hidden');
    setSelected(null);
    reloadHouse();
  };
  $('object-form').onsubmit = (e) => e.preventDefault();
}

// ---------------------------------------------------------------- model library

async function refreshModels() {
  try {
    modelsList = await api.getModels();
  } catch {
    modelsList = [];
  }
  renderModelsList();
  updateAlignAvailability();
  if (selectedRoomId) renderPlacementSection();
}

function openModelsModal() {
  $('models-modal').classList.remove('hidden');
  refreshModels();
}

// ---- whole-house shell model alignment ------------------------------------

// Sync the level nav's active button without importing focus.js (which imports
// us). Mirrors focus.js's own DOM-only helper.
function setActiveLevelBtn(level) {
  document.querySelectorAll('#levels button').forEach((b) => {
    b.classList.toggle('active', String(b.dataset.level) === String(level));
  });
}

function shellModelName(cfg) {
  const m = modelsList.find((x) => x.id === cfg?.model_id);
  return m ? m.name : `model #${cfg?.model_id}`;
}

// Read the 5 alignment inputs into a shell-transform patch (deg -> rad).
function readShellForm() {
  const s = parseFloat($('shell-scale').value);
  return {
    x: parseFloat($('shell-x').value) || 0,
    y: parseFloat($('shell-y').value) || 0,
    z: parseFloat($('shell-z').value) || 0,
    rot_y: (parseFloat($('shell-rot').value) || 0) * Math.PI / 180,
    scale: s > 0 ? s : 1,
  };
}

function populateShellForm(cfg) {
  $('shell-x').value = cfg.x ?? 0;
  $('shell-y').value = cfg.y ?? 0;
  $('shell-z').value = cfg.z ?? 0;
  $('shell-rot').value = Math.round((cfg.rot_y ?? 0) * 180 / Math.PI);
  $('shell-scale').value = cfg.scale ?? 1;
}

// Show "Align house" only in edit mode with a shell configured; drop the panel
// if the shell was unset.
function updateAlignAvailability() {
  const has = !!house?.house_shell?.model_id;
  $('btn-align').classList.toggle('hidden', !(has && appMode === 'edit'));
  if (!has) $('shell-panel').classList.add('hidden');
}

function openAlignPanel() {
  const cfg = getShellConfig() || house?.house_shell;
  if (!cfg) return;
  $('models-modal').classList.add('hidden'); // if opened from the model list
  exitFocus({ flyBack: false });
  setLevel('all');            // House view: the shell is only visible here
  setActiveLevelBtn('all');
  populateShellForm(cfg);
  $('shell-model').textContent = `Model: ${shellModelName(cfg)}`;
  $('shell-panel').classList.remove('hidden');
  setSelected(getShellRoot()); // make the shell draggable (null until it loads)
}

function wireShellPanel() {
  for (const id of ['shell-x', 'shell-y', 'shell-z', 'shell-rot', 'shell-scale']) {
    // live-preview on every keystroke, persist once the field is committed
    $(id).addEventListener('input', () => setShellTransform(readShellForm()));
    $(id).addEventListener('change', () => { api.setHouseShell(readShellForm()); });
  }
  $('shell-unset').onclick = async () => {
    await api.setHouseShell({ model_id: null });
    $('shell-panel').classList.add('hidden');
    setSelected(null);
    await reloadHouse();
    await refreshModels();
  };
}

function renderModelsList() {
  const list = $('mm-list');
  list.innerHTML = '';
  for (const m of modelsList) {
    const item = document.createElement('div');
    item.className = 'mm-item';

    const name = document.createElement('input');
    name.className = 'name';
    name.value = m.name;
    name.title = 'Rename';
    name.onchange = async () => {
      const v = name.value.trim();
      if (!v) { name.value = m.name; return; }
      await api.renameModel(m.id, { name: v });
      refreshModels();
    };

    const usage = document.createElement('span');
    usage.className = 'muted';
    const parts = [];
    if (m.placement_count) parts.push(`${m.placement_count} device${m.placement_count > 1 ? 's' : ''}`);
    if (m.object_count) parts.push(`${m.object_count} object${m.object_count > 1 ? 's' : ''}`);
    usage.textContent = parts.join(' · ') || 'unused';

    // Mark this model as the whole-house shell shown in the "House" view.
    const isShell = house?.house_shell?.model_id === m.id;
    const useHouse = document.createElement('button');
    useHouse.className = 'small' + (isShell ? ' active' : ' secondary');
    useHouse.type = 'button';
    useHouse.textContent = isShell ? '✓ House model' : 'Use as house';
    useHouse.title = 'Show this model as the whole house in the House view';
    useHouse.onclick = async () => {
      await api.setHouseShell({ model_id: isShell ? null : m.id });
      await reloadHouse();      // updateData refreshes house + align availability
      await refreshModels();    // re-render the list's active state
      if (!isShell) openAlignPanel();
    };

    const rm = document.createElement('button');
    rm.className = 'small danger';
    rm.textContent = '✕';
    rm.onclick = async () => {
      const warn = [];
      if (m.placement_count) warn.push(`${m.placement_count} device marker(s) revert to defaults`);
      if (m.object_count) warn.push(`${m.object_count} placed object(s) will be removed`);
      if (!confirm(`Delete model "${m.name}"?` +
                   (warn.length ? `\n\n${warn.join('\n')}` : ''))) return;
      await api.deleteModel(m.id);
      invalidateModel(m.id);
      await refreshModels();
      reloadHouse();
    };

    item.append(name, usage, useHouse, rm);
    list.appendChild(item);
  }
  if (!list.children.length) {
    list.innerHTML = '<p class="muted">No models yet — upload a .glb above.</p>';
  }
}

async function onModelUpload(e) {
  e.preventDefault();
  const file = $('mm-file').files[0];
  if (!file) return;
  const btn = $('mm-upload');
  btn.disabled = true;
  btn.textContent = 'Uploading…';
  try {
    await api.uploadModel(file, $('mm-name').value.trim());
    $('mm-upload-form').reset();
    await refreshModels();
  } catch (err) {
    alert(`Upload failed: ${err.message}`);
  }
  btn.disabled = false;
  btn.textContent = 'Upload';
}
