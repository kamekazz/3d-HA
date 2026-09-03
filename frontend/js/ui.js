// Level selector, device side panel, room editor, model library, object panel.
import { api } from './api.js';
import { floorGroups, setLevel, getLevel, highlightRoom,
         setShellTransform, getShellRoot, getShellConfig } from './house.js';
import { getState, friendlyName, stateLabel, onStateApplied } from './state.js';
import { enterFocus, exitFocus, getFocusedRoomId, onFocusChanged } from './focus.js';
import { renderControls, createCameraView, isSliderActive } from './controls.js';
import { markers } from './devices.js';
import { objects3d, applyAllObjectVisibility } from './objects.js';
import { setSelected, onDragMoved, setGizmoMode } from './drag.js';
import { setRoomLightsData } from './roomlights.js';
import { buildLabels } from './labels.js';
import { invalidateModel } from './models.js';
import { fillTextureSelect } from './textures.js';
import { canEdit } from './route.js';
import { showAlert, showConfirm } from './dialog.js';

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
    closeEditor();
    $('object-panel').classList.add('hidden');
    $('models-modal').classList.add('hidden');
    $('planner').classList.add('hidden');
  }
  updateAlignAvailability();
  // dashboard.js/roomcards.js hide their chrome off this class (CSS-only)
  document.body.classList.toggle('app-edit', mode === 'edit');

  // Update scene background and grid when mode changes. devices.js also
  // listens: markers are edit-only, so this is what shows/hides them.
  const ev = new CustomEvent('appModeChanged', { detail: { mode } });
  window.dispatchEvent(ev);
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
  // The house shell GLB failed to fetch/parse (house.js). Everything else in
  // the scene is procedural, so this looks like a render glitch instead of the
  // deploy problem it almost always is — say so instead of hiding it in the
  // console. No timeout: the scene stays wrong until it's fixed.
  window.addEventListener('shellLoadFailed', (e) => {
    showBanner(`House model (id ${e.detail.modelId}) failed to load — the 3D `
      + 'house can\'t render. Check the browser console, then '
      + 'docs/TROUBLESHOOTING-house-shell.md');
  });
  // Initialize UI state — /edit opens ready to edit, the toggle previews.
  $('chk-edit-mode').checked = canEdit;
  setAppMode(canEdit ? 'edit' : 'view');

  $('btn-editor').onclick = () => {
    if ($('editor').classList.contains('hidden')) openEditor();
    else closeEditor();
  };
  $('editor-back').onclick = leaveRoomScreen;
  $('btn-add-room').onclick = () => {
    resetRoomForm();      // blank fields, #placement-section hidden
    setEditorView('room'); // no focus: there is no room to fly to yet
    $('rf-name').focus();
  };

  // The 3D view is the other way into a room. Clicking a room mesh focuses it
  // (main.js), and this brings the editor along, so the mesh and the room list
  // land in exactly the same place. Rebuilds are invisible here — focus.js
  // suspends and resumes around them without emitting.
  onFocusChanged((roomId) => {
    if (appMode !== 'edit') return;
    if (roomId === null) {
      if ($('editor').dataset.view === 'room') backToRoomList();
    } else if (roomId !== selectedRoomId) {
      selectRoom(roomId);
    }
  });
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
      showAlert(parts.length ? `${parts.join(', ')}.`
                             : 'Already in sync with Home Assistant.',
                { title: 'Synced with HA' });
    } catch (e) {
      showAlert(e.message, { title: 'Sync failed' });
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
      showAlert(res.rooms || res.devices
        ? `Added ${res.rooms} room(s) and ${res.devices} device(s) from HA.`
        : 'Nothing new — every HA area is already in the layout.',
        { title: 'Generate from HA' });
    } catch (e) {
      showAlert(e.message, { title: 'Generate failed' });
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
      if (btn.dataset.close === 'editor') closeEditor();
    };
  });

  $('room-form').onsubmit = onRoomFormSubmit;
  $('rf-cancel').onclick = leaveRoomScreen;

  $('btn-models').onclick = openModelsModal;
  $('mm-upload-form').onsubmit = onModelUpload;
  $('btn-align').onclick = openAlignPanel;
  wireShellPanel();
  $('obj-add').onclick = onAddObject;
  wireObjectPanel();
  refreshModels(); // async fill of the library-dependent selects

  // drag ended: server already PATCHed — sync the cached house + open panels
  // without a full reload (the mesh is already where the user left it)
  onDragMoved(({ kind, id, x, y, z, rot_y, scale }) => {
    if (kind === 'house-shell') {
      setShellTransform({ x, y, z, rot_y, scale }); // keep shellConfig in sync
      if (!$('shell-panel').classList.contains('hidden')) {
        // every field, not just x/z: the panel PUTs all five back on the next
        // keystroke, so a stale one silently reverts the gesture
        $('shell-x').value = +x.toFixed(2);
        $('shell-y').value = +y.toFixed(2);
        $('shell-z').value = +z.toFixed(2);
        $('shell-rot').value = Math.round(rot_y * 180 / Math.PI);
        $('shell-scale').value = scale;
      }
      return;
    }
    if (kind === 'device') {
      const found = findPlacementById(id);
      if (found) {
        Object.assign(found.dev.position, { x, y, z });
        found.dev.rot_y = rot_y;
        found.dev.scale = scale;
      }
      if (selectedRoomId && found?.room.id === selectedRoomId) renderPlacementSection();
    } else {
      const found = findObjectById(id);
      if (found) {
        Object.assign(found.obj.position, { x, y, z });
        found.obj.rot_y = rot_y;
        found.obj.scale = scale;
      }
      if (panelObjectId === id) {
        $('op-x').value = x; $('op-y').value = y; $('op-z').value = z;
        $('op-rot').value = Math.round(rot_y * 180 / Math.PI);
        $('op-scale').value = scale;
      }
      if (selectedRoomId && found?.room.id === selectedRoomId) renderPlacementSection();
    }
  });

  wireGizmoBar();

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
    // deleted, or undone out of existence, while its screen was open
    backToRoomList();
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

const CONN_TEXT = { connected: 'live', polling: 'polling', offline: 'offline' };

export function setConnStatus(status) {
  const dot = $('conn-status');
  dot.className = 'status-dot ' + status;
  $('conn-label').textContent = status;
  // The view-only home screen hides the whole topbar, so #conn-status is the
  // one thing it has no way to show. #hb-sub used to read a hard-coded
  // "all systems" that nothing ever updated — give it the real status instead.
  // Not a light count: that would just repeat the dock's lights tile, and this
  // house reports 1196 light entities (LED strip segments), so any count off
  // them is noise rather than information.
  const sub = $('hb-sub');
  if (!sub) return;
  sub.textContent = CONN_TEXT[status] || status;
  sub.classList.toggle('is-warn', status !== 'connected');
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

// --------------------------------------------------- the editor's two screens
//
// #editor is a room LIST and a single ROOM, not one long column. Picking a room
// flies the camera into it (focus.js does the isolating) and swaps the panel to
// that room's controls; the back button flies out again. Both screens live in
// the same markup and are switched by one attribute.

function setEditorView(view) {
  $('editor').dataset.view = view;
  document.body.classList.toggle('editor-room', view === 'room');
  $('editor').scrollTop = 0;
}

function openEditor() {
  $('editor').classList.remove('hidden');
}

function closeEditor() {
  $('editor').classList.add('hidden');
  // leaving by the X or by flipping to view mode still means leaving the room
  if (getFocusedRoomId()) exitFocus();
  selectedRoomId = null;
  setEditorView('list');
  document.body.classList.remove('editor-room');
}

// Back out to the list. Routed through exitFocus where possible so the camera
// flies home; the direct call covers a room that never had a mesh to fly to.
function leaveRoomScreen() {
  if (getFocusedRoomId()) exitFocus(); // emits null -> backToRoomList below
  else backToRoomList();
}

function backToRoomList() {
  selectedRoomId = null;
  resetRoomForm();          // clears the fields and hides #placement-section
  setEditorView('list');
}

function renderRoomList() {
  const list = $('room-list');
  list.innerHTML = '';
  for (const f of [...house.floors].sort((a, b) => a.level - b.level)) {
    if (!(f.rooms || []).length) continue;
    // a floor heading beats an "(L1)" suffix on all 24 rows
    const head = document.createElement('h4');
    head.className = 'ed-floor';
    head.textContent = `${f.level} · ${f.name}`;
    list.appendChild(head);
    for (const room of f.rooms || []) {
      const item = document.createElement('div');
      item.className = 'room-item' + (room.id === selectedRoomId ? ' selected' : '');
      const name = document.createElement('span');
      name.className = 'name';
      name.textContent = room.name;
      name.onclick = () => selectRoom(room.id);
      const edit = document.createElement('button');
      edit.className = 'small secondary';
      edit.textContent = 'Edit';
      edit.onclick = () => selectRoom(room.id);
      const rm = document.createElement('button');
      rm.className = 'small danger';
      rm.textContent = '✕';
      rm.onclick = async () => {
        if (!await showConfirm('Its device placements and furniture go with it.',
              { title: `Delete "${room.name}"?`, okLabel: 'Delete', danger: true })) return;
        await api.deleteRoom(room.id);
        if (selectedRoomId === room.id) { selectedRoomId = null; resetRoomForm(); }
        reloadHouse();
      };
      item.append(name, edit, rm);
      list.appendChild(item);
    }
  }
  if (!list.children.length) {
    list.innerHTML = '<p class="muted">No rooms yet — use “+ Room”.</p>';
  }
}

export function selectRoom(roomId) {
  const found = findRoom(roomId);
  if (!found) return;
  // before enterFocus: the focus event it emits comes straight back to our own
  // listener, which compares against this and drops the re-entry
  selectedRoomId = roomId;
  const { room, floor } = found;
  openEditor();
  // Transport. Drops the level selector to the room's floor, hides its
  // siblings, scopes markers + furniture to it and flies in. A no-op when we
  // are already focused there, so refreshing the form never re-flies.
  enterFocus(roomId);
  setEditorView('room');
  // fallback for a room with no mesh yet (just created, pre-rebuild), where
  // enterFocus early-returns: focus mode otherwise owns room opacities
  if (!getFocusedRoomId()) highlightRoom(roomId);

  $('room-form-title').textContent = room.name;
  $('room-form-sub').textContent = `${floor.level} · ${floor.name}`;
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
  $('room-form-title').textContent = 'New room';
  $('room-form-sub').textContent = '';
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
    showAlert(err.message, { title: 'Save failed' });
  }
}

// ---------------------------------------------------------------- placements

// ---- light fixtures: bind furniture to the entity it actually is ----------
// Deliberately NOT matching "ceiling": that token names the room-scale ceiling
// PLANE in ~7 rooms of this house, not a fixture. "Ceiling Fan" still matches
// through `fan`.
const FIXTURE_NAME_RE = /\b(lamp|light|sconce|chandelier|pendant|fan)\b/i;

// Score a candidate pairing by shared words. Deliberately weak — this only
// ORDERS the dropdown and seeds the auto-match proposal; a human confirms.
function nameScore(objName, entity) {
  const words = (t) => new Set(String(t).toLowerCase().match(/[a-z]{3,}/g) || []);
  const a = words(objName);
  const b = words(`${entity.name} ${entity.entity_id.split('.')[1] || ''}`);
  let hits = 0;
  for (const w of a) if (b.has(w)) hits++;
  return hits;
}

function roomFixtureEntities(room) {
  const area = areaById(room.ha_area_id);
  return (area?.entities || []).filter((e) => {
    const d = e.entity_id.split('.')[0];
    return d === 'light' || d === 'switch' || d === 'fan';
  });
}

function renderFixtureSection(room) {
  const list = $('fixture-list');
  list.innerHTML = '';
  const candidates = (room.objects || [])
    .filter((o) => o.entity_id || FIXTURE_NAME_RE.test(o.name || o.model_name || ''));
  const entities = roomFixtureEntities(room);
  setSectionCount('ed-n-fixtures', candidates.length);

  if (!candidates.length) {
    list.innerHTML = '<p class="muted">No lamp-like furniture in this room. '
      + 'Bind any piece from its object panel instead.</p>';
  }
  if (!entities.length) {
    const p = document.createElement('p');
    p.className = 'muted';
    p.textContent = room.ha_area_id
      ? 'This room’s HA area has no light, switch or fan entity — nothing to bind here.'
      : 'Link this room to an HA area to see its entities.';
    list.appendChild(p);
  }

  for (const o of candidates) {
    const row = document.createElement('div');
    row.className = 'placed-item fixture-row';
    const name = document.createElement('span');
    name.className = 'name';
    name.textContent = o.name || o.model_name;
    name.title = 'Open this piece';
    name.onclick = () => openObjectPanel(o.id);
    row.appendChild(name);

    const sel = document.createElement('select');
    sel.innerHTML = '<option value="">— unbound —</option>';
    // best name match first: in a room with one lamp and six lights that is
    // usually the right answer already
    const ranked = entities.slice()
      .sort((a, b) => nameScore(o.name || o.model_name, b) - nameScore(o.name || o.model_name, a));
    for (const e of ranked) {
      const opt = document.createElement('option');
      opt.value = e.entity_id;
      opt.textContent = `${e.name} · ${e.entity_id}`;
      sel.appendChild(opt);
    }
    if (o.entity_id && !ranked.some((e) => e.entity_id === o.entity_id)) {
      const opt = document.createElement('option');
      opt.value = o.entity_id;
      opt.textContent = o.entity_id;
      sel.appendChild(opt);
    }
    sel.value = o.entity_id || '';
    sel.onchange = async () => {
      try {
        await api.updateObject(o.id, { entity_id: sel.value || null });
        applyObjectLocally(o.id, { entity_id: sel.value || null });
        if (panelObjectId === o.id) openObjectPanel(o.id);
        renderPlacementSection();
      } catch (e) {
        showAlert(e.message, { title: 'Bind failed' });
      }
    };
    row.appendChild(sel);
    list.appendChild(row);
  }

  // Auto-match proposes, never commits: name matching will not get
  // "Master Lamp Small" -> light.rosemary_bedside_light on its own.
  $('fx-auto').disabled = !candidates.length || !entities.length;
  $('fx-auto').onclick = async () => {
    const free = entities.filter((e) =>
      !(room.objects || []).some((o) => o.entity_id === e.entity_id));
    const proposals = [];
    for (const o of candidates) {
      if (o.entity_id) continue;
      const best = free
        .filter((e) => !proposals.some((p) => p.entity.entity_id === e.entity_id))
        .map((e) => ({ e, s: nameScore(o.name || o.model_name, e) }))
        .sort((a, b) => b.s - a.s)[0];
      if (best && best.s > 0) proposals.push({ obj: o, entity: best.e });
    }
    if (!proposals.length) {
      showAlert('No confident name matches. Bind them with the dropdowns instead.',
                { title: 'Auto-match' });
      return;
    }
    const lines = proposals
      .map((p) => `${p.obj.name || p.obj.model_name}  →  ${p.entity.entity_id}`)
      .join('\n');
    if (!await showConfirm(lines, { title: `Bind ${proposals.length} fixture(s)?`,
                                    okLabel: 'Bind' })) return;
    for (const p of proposals) {
      try {
        await api.updateObject(p.obj.id, { entity_id: p.entity.entity_id });
        applyObjectLocally(p.obj.id, { entity_id: p.entity.entity_id });
      } catch (e) {
        showAlert(`${p.obj.name}: ${e.message}`, { title: 'Bind failed' });
      }
    }
    renderPlacementSection();
  };
}

// A collapsed section shows nothing of what it holds, so each one carries its
// own count in the summary.
function setSectionCount(id, n) {
  $(id).textContent = n ? ` ${n}` : '';
}

function renderPlacementSection() {
  const found = findRoom(selectedRoomId);
  if (!found) return;
  const { room } = found;
  $('placement-section').classList.remove('hidden');

  setSectionCount('ed-n-devices', (room.devices || []).length);
  setSectionCount('ed-n-objects', (room.objects || []).length);
  renderFixtureSection(room);

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
    setSectionCount('ed-n-entities', 0);
    list.innerHTML = structure
      ? '<p class="muted">Link the room to an HA area to list its entities.</p>'
      : '<p class="muted">HA structure not loaded.</p>';
    return;
  }
  const placedIds = new Set((room.devices || []).map((d) => d.entity_id));
  const candidates = area.entities.filter((e) => !e.hidden && !placedIds.has(e.entity_id));
  setSectionCount('ed-n-entities', candidates.length);
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
    showAlert(e.message, { title: 'Could not add object' });
  }
}

// ---------------------------------------------------------------- object panel

// Domains where binding a fixture means something you can click and light with.
const FIXTURE_DOMAINS = new Set(['light', 'switch', 'fan', 'input_boolean']);

// Entity picker: the room's own HA area first (that is nearly always the one
// you want), then everything else. Sorted, and grouped so a house with several
// hundred entities is still navigable.
function fillEntitySelect(sel, room, current) {
  sel.textContent = '';
  const none = document.createElement('option');
  none.value = '';
  none.textContent = '— none (plain furniture) —';
  sel.appendChild(none);

  const seen = new Set();
  const addGroup = (label, entities) => {
    const list = entities.filter((e) => !seen.has(e.entity_id));
    if (!list.length) return;
    const g = document.createElement('optgroup');
    g.label = label;
    for (const e of list) {
      seen.add(e.entity_id);
      const o = document.createElement('option');
      o.value = e.entity_id;
      o.textContent = `${e.name} · ${e.entity_id}`;
      g.appendChild(o);
    }
    sel.appendChild(g);
  };

  const area = areaById(room?.ha_area_id);
  const byName = (a, b) => a.entity_id.localeCompare(b.entity_id);
  const areaEnts = (area?.entities || []).slice().sort(byName);
  addGroup(area ? `This room — ${area.name}` : 'This room', areaEnts);
  const rest = allAreas().flatMap((a) => a.entities || []).slice().sort(byName);
  addGroup('Everywhere else', rest);

  // A bound entity that is no longer in the registry must still be selectable,
  // or opening the panel would silently unbind it on the next change.
  if (current && !seen.has(current)) {
    const g = document.createElement('optgroup');
    g.label = 'Bound (not in the HA registry)';
    const o = document.createElement('option');
    o.value = current;
    o.textContent = current;
    g.appendChild(o);
    sel.appendChild(g);
  }
  sel.value = current || '';
}

function paintLightSection(entityId, cfg) {
  const domain = (entityId || '').split('.')[0];
  const show = FIXTURE_DOMAINS.has(domain);
  $('op-light').classList.toggle('hidden', !show);
  if (!show) return;
  const c = cfg || {};
  $('op-lc-auto').checked = !c.color;
  $('op-lc-color').value = c.color || '#ffb466';
  $('op-lc-color').disabled = !c.color;
  $('op-lc-intensity').value = c.intensity ?? '';
  $('op-lc-offset').value = c.offset_y ?? '';
  $('op-lc-range').value = c.range ?? '';
}

export function openObjectPanel(objectId) {
  const found = findObjectById(objectId);
  if (!found) return;
  panelObjectId = objectId;
  const { obj, room } = found;
  $('op-name').textContent = obj.name || obj.model_name;
  if (obj.entity_id) {
    const tag = document.createElement('span');
    tag.className = 'op-bound';
    tag.textContent = `bound to ${obj.entity_id}`;
    $('op-name').appendChild(tag);
  }
  $('op-model').textContent = `Model: ${obj.model_name} · ${room.name}`;
  $('op-x').value = obj.position.x;
  $('op-y').value = obj.position.y;
  $('op-z').value = obj.position.z;
  $('op-rot').value = Math.round((obj.rot_y || 0) * 180 / Math.PI);
  $('op-scale').value = obj.scale ?? 1;
  $('op-rename').value = obj.name || '';
  $('op-visible').checked = obj.visible !== 0;
  fillEntitySelect($('op-entity'), room, obj.entity_id);
  paintLightSection(obj.entity_id, obj.light_cfg);
  setSelected(objects3d.get(objectId) || null);
  $('object-panel').classList.remove('hidden');
}

// Apply a saved object change to the live scene and the cached house copy,
// WITHOUT a full reloadHouse. The old panel rebuilt the whole house on every
// keystroke, which also drops you out of room focus — unusable for the "open a
// room, tweak the lamp" flow this panel exists for.
function applyObjectLocally(objectId, data) {
  const found = findObjectById(objectId);
  if (!found) return;
  const { obj, room } = found;
  const root = objects3d.get(objectId);
  let rebindLights = false;
  let rebuildLabels = false;

  for (const [k, v] of Object.entries(data)) {
    if (k === 'x' || k === 'y' || k === 'z') {
      obj.position[k] = v;
      if (root) {
        root.position.set(
          room.footprint.x + obj.position.x,
          obj.position.y,
          room.footprint.z + obj.position.z);
      }
    } else if (k === 'rot_y') {
      obj.rot_y = v;
      if (root) root.rotation.y = v;
    } else if (k === 'scale') {
      obj.scale = v;
      if (root) { root.scale.setScalar(v); root.userData.userScale = v; }
    } else if (k === 'name') {
      obj.name = v;
      if (root) {
        root.userData.name = v;
        root.userData.pickable = !!obj.entity_id || !SURFACE_NAME_RE.test(v);
      }
    } else if (k === 'entity_id') {
      obj.entity_id = v || null;
      if (root) {
        root.userData.entityId = obj.entity_id;
        // binding overrides the scenery name test — see objects.js isPickable
        root.userData.pickable = !!obj.entity_id
          || !SURFACE_NAME_RE.test(obj.name || obj.model_name || '');
      }
      rebindLights = true;
      rebuildLabels = true;   // the label moves marker <-> fixture
    } else if (k === 'visible') {
      obj.visible = v ? 1 : 0;
      if (root) root.userData.hiddenByUser = !v;
      rebindLights = true;    // a hidden fixture stops lighting the room
    } else if (k === 'light_cfg') {
      obj.light_cfg = v;
      if (root) root.userData.lightCfg = v;
      rebindLights = true;
    }
  }

  if (data.visible !== undefined) applyAllObjectVisibility();
  if (rebuildLabels) buildLabels(house);
  // rebuilds fixture records and boundEntities from the cached house copy
  // we just edited
  if (rebindLights) setRoomLightsData({ house, structure });
}

// objects.js's scenery test, mirrored so a rename can re-evaluate pickability
// without a rebuild. Keep the two in step.
const SURFACE_NAME_RE = /\b(floor|ceiling|wall wash|baseboards?|crown)\b/i;

function wireObjectPanel() {
  const patch = async (data, { repaint = false } = {}) => {
    if (!panelObjectId) return;
    const keep = panelObjectId;
    try {
      await api.updateObject(keep, data);
      applyObjectLocally(keep, data);
      if (repaint) openObjectPanel(keep);
      if (selectedRoomId === findObjectById(keep)?.room.id) renderPlacementSection();
    } catch (e) {
      showAlert(e.message, { title: 'Update failed' });
    }
  };
  const lightCfg = () => {
    const num = (id) => {
      const v = $(id).value.trim();
      return v === '' ? null : Number(v);
    };
    return {
      color: $('op-lc-auto').checked ? null : $('op-lc-color').value,
      intensity: num('op-lc-intensity'),
      offset_y: num('op-lc-offset'),
      range: num('op-lc-range'),
    };
  };
  $('op-x').onchange = () => patch({ x: Number($('op-x').value) });
  $('op-y').onchange = () => patch({ y: Number($('op-y').value) });
  $('op-z').onchange = () => patch({ z: Number($('op-z').value) });
  $('op-rot').onchange = () => patch({ rot_y: Number($('op-rot').value) * Math.PI / 180 });
  $('op-scale').onchange = () => patch({ scale: Number($('op-scale').value) || 1 });
  $('op-rename').onchange = () => patch({ name: $('op-rename').value.trim() });
  $('op-entity').onchange = () =>
    patch({ entity_id: $('op-entity').value || null }, { repaint: true });
  $('op-visible').onchange = () => patch({ visible: $('op-visible').checked });
  for (const id of ['op-lc-color', 'op-lc-intensity', 'op-lc-offset', 'op-lc-range']) {
    $(id).onchange = () => patch({ light_cfg: lightCfg() });
  }
  $('op-lc-auto').onchange = () => {
    $('op-lc-color').disabled = $('op-lc-auto').checked;
    patch({ light_cfg: lightCfg() });
  };
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

// ---- transform gizmo mode bar -------------------------------------------
// Only meaningful while something is selected, so it follows selection rather
// than sitting in the topbar. `.edit-only` already hides it in view mode.
function wireGizmoBar() {
  const bar = $('gizmo-bar');
  if (!bar) return;
  for (const btn of bar.querySelectorAll('button')) {
    btn.onclick = () => {
      setGizmoMode(btn.dataset.gizmo);
      for (const b of bar.querySelectorAll('button')) {
        b.classList.toggle('active', b === btn);
      }
    };
  }
  window.addEventListener('selectionChanged', (e) => paintGizmoBar(!!e.detail.kind));
  window.addEventListener('appModeChanged', () => paintGizmoBar(false));
  paintGizmoBar(false);
}

function paintGizmoBar(hasSelection) {
  $('gizmo-bar')?.classList.toggle('hidden', !hasSelection || appMode !== 'edit');
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
      // models are file-lifecycle, outside undo/redo — say so
      if (!await showConfirm(warn.length ? warn.join('\n') : 'This cannot be undone.',
            { title: `Delete "${m.name}"?`, okLabel: 'Delete', danger: true })) return;
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
    showAlert(err.message, { title: 'Upload failed' });
  }
  btn.disabled = false;
  btn.textContent = 'Upload';
}
