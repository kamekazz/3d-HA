// Bootstrap: load data, build the 3D scene, wire UI + realtime.
import * as THREE from 'three';
import { api } from './api.js';
import { initScene, scene, camera, renderer } from './scene.js';
import { buildHouse, roomMeshes } from './house.js';
import { buildDevices, markers } from './devices.js';
import { buildObjects, objects3d } from './objects.js';
import { setAllStates, applyState, friendlyName, stateLabel, styleMarker } from './state.js';
import { buildLabels, showLabel, hideLabel } from './labels.js';
import { initFocus, enterFocus, exitFocus } from './focus.js';
import { connectRealtime } from './socket.js';
import { initUI, updateData, setConnStatus, showBanner, openDevicePanel, openObjectPanel, selectRoom } from './ui.js';
import { initDrag } from './drag.js';
import { initRoomPanel, updateRoomPanelData } from './roompanel.js';
import { initPlanner } from './planner.js';
import { initDaylight } from './daylight.js';
import { initRoomLights, setRoomLightsData } from './roomlights.js';

let structure = null;

async function loadStructure() {
  try {
    structure = await api.getStructure();
    showBanner(null);
  } catch (e) {
    structure = null;
    showBanner(e.status === 503
      ? `Home Assistant not connected yet — ${e.detail || 'check backend/.env and restart'}. The 3D editor still works.`
      : `Could not load HA structure: ${e.message}`);
  }
}

async function loadStates() {
  try {
    const states = await api.getStates();
    if (Array.isArray(states)) setAllStates(states);
  } catch { /* HA offline — markers stay grey */ }
}

async function reloadHouse() {
  // rebuild disposes the meshes focus mode holds references to
  exitFocus({ flyBack: false });
  const house = await api.getHouse();
  buildHouse(house);
  buildDevices(house);
  buildObjects(house);
  buildLabels(house);
  setRoomLightsData({ house, structure }); // fresh slab materials — repoint glow
  await loadStates();
  updateData({ structure, house });
  updateRoomPanelData(house);
  return house;
}

// ------------------------------------------------------------- picking

// domains where a single click on the marker toggles the device directly
const QUICK_TOGGLE_DOMAINS = new Set(['light', 'switch', 'fan', 'input_boolean']);

function setupPicking() {
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const tooltip = document.getElementById('tooltip');
  let downAt = null;
  let hovered = null;
  let toggleTimer = null;
  // manual double-click detection: e.detail is 0 on pointerup in some
  // browsers/input paths, so track same-object clicks ourselves
  const DOUBLE_MS = 300;
  let lastClick = { obj: null, time: 0 };

  function isShown(obj) {
    // walk ancestors: skips rooms/devices on hidden floors and hidden markers
    let node = obj;
    while (node) { if (!node.visible) return false; node = node.parent; }
    return true;
  }

  function ownerOf(obj) {
    // model-backed markers/objects are Groups: hits land on child meshes, so
    // walk up to the ancestor that carries the pick metadata
    let node = obj;
    while (node && !node.userData?.kind) node = node.parent;
    return node;
  }

  function pick(event) {
    pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);

    const hits = raycaster.intersectObjects(scene.children, true);

    // nearest opaque room/stair surface: walls are solid now (dollhouse), so
    // markers behind one are invisible and must not win the priority pass
    // (hits are distance-sorted; edge outlines and ghost-faded walls don't
    // hide anything)
    let occluderDist = Infinity;
    for (const hit of hits) {
      if (hit.object.userData?.part === 'edges') continue;
      const kind = ownerOf(hit.object)?.userData?.kind;
      if ((kind === 'room' || kind === 'stairs') && isShown(hit.object)
          && (hit.object.material?.opacity ?? 1) > 0.5) {
        occluderDist = hit.distance;
        break;
      }
    }

    // device markers + objects first so they win over the room that contains
    // them (recursive: GLB groups only register through their children)
    const priorityHits = raycaster.intersectObjects(
      [...markers.values(), ...objects3d.values()], true);
    for (const hit of priorityHits) {
      if (hit.distance > occluderDist + 0.25) break; // hidden behind a wall
      const owner = ownerOf(hit.object);
      if (owner && isShown(hit.object)) return owner;
    }

    for (const hit of hits) {
      const owner = ownerOf(hit.object);
      const ud = owner?.userData;
      // pickable === false: ghosted sibling rooms while a room is focused
      if (ud?.kind && ud.pickable !== false && isShown(hit.object)) {
        return owner;
      }
    }
    return null;
  }

  function clearHover() {
    if (!hovered) return;
    const ud = hovered.userData;
    if (ud.kind === 'room') {
      hovered.material.emissiveIntensity = ud.baseEmissive ?? 0;
    } else if (ud.kind === 'device') {
      styleMarker(ud.entityId); // state-driven restore, can't desync
      hideLabel(ud.entityId); // labels are hover-only now, even in focus mode
    }
    hovered = null;
  }

  function applyHover(obj) {
    hovered = obj;
    const ud = obj.userData;
    if (ud.kind === 'room') {
      // accent-tinted glow: walls are opaque now, so opacity can't signal
      obj.material.emissive.copy(ud.accent);
      obj.material.emissiveIntensity = (ud.baseEmissive ?? 0) + 0.15;
    } else if (ud.kind === 'device') {
      obj.scale.multiplyScalar(1.25);
      showLabel(ud.entityId);
    }
  }

  renderer.domElement.addEventListener('pointermove', (e) => {
    const obj = pick(e);
    if (obj !== hovered) {
      clearHover();
      if (obj) applyHover(obj);
      renderer.domElement.style.cursor = obj ? 'pointer' : '';
    }
    if (!obj) { tooltip.classList.add('hidden'); return; }
    const ud = obj.userData;
    if (ud.kind === 'device') {
      tooltip.innerHTML =
        `<strong>${friendlyName(ud.entityId)}</strong><br>` +
        `<span class="sub">${stateLabel(ud.entityId)} · ${ud.roomName}</span>`;
    } else if (ud.kind === 'object') {
      tooltip.innerHTML =
        `<strong>${ud.name}</strong><br><span class="sub">${ud.roomName}</span>`;
    } else {
      tooltip.innerHTML = `<strong>${ud.roomName}</strong><br><span class="sub">Level ${ud.level}</span>`;
    }
    tooltip.style.left = `${e.clientX + 14}px`;
    tooltip.style.top = `${e.clientY + 14}px`;
    tooltip.classList.remove('hidden');
  });

  renderer.domElement.addEventListener('pointerleave', () => {
    clearHover();
    tooltip.classList.add('hidden');
    renderer.domElement.style.cursor = '';
  });

  renderer.domElement.addEventListener('pointerdown', (e) => {
    downAt = { x: e.clientX, y: e.clientY };
  });

  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!downAt) return;
    const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
    downAt = null;
    if (moved > 5) return; // it was an orbit drag, not a click
    const obj = pick(e);

    const now = performance.now();
    const isDouble = obj !== null && obj === lastClick.obj &&
                     (now - lastClick.time) < DOUBLE_MS;
    lastClick = { obj, time: now };

    if (!obj) {
      // clicking empty space leaves focus mode
      if (!isDouble) exitFocus();
      return;
    }

    const ud = obj.userData;
    if (ud.kind === 'device') {
      const domain = ud.entityId.split('.')[0];
      if (QUICK_TOGGLE_DOMAINS.has(domain)) {
        // click = toggle (like a real switch), double-click = detail panel;
        // the short window keeps a double-click from also toggling
        if (!isDouble) {
          if (toggleTimer) clearTimeout(toggleTimer);
          toggleTimer = setTimeout(() => {
            toggleTimer = null;
            api.control({ entity_id: ud.entityId, domain, service: 'toggle' })
              .catch((err) => showBanner(`Control failed: ${err.message}`, 4000));
          }, DOUBLE_MS);
        } else {
          if (toggleTimer) { clearTimeout(toggleTimer); toggleTimer = null; }
          openDevicePanel(ud.entityId);
        }
      } else {
        openDevicePanel(ud.entityId);
      }
    } else if (ud.kind === 'object') {
      openObjectPanel(ud.objectId);
    } else if (ud.kind === 'room') {
      if (isDouble) selectRoom(ud.roomId);
      else enterFocus(ud.roomId);
    }
  });
}

// ------------------------------------------------------------- boot

async function main() {
  initScene(document.getElementById('scene-container'));
  initDaylight();
  setupPicking();

  await loadStructure();
  const house = await api.getHouse();
  buildHouse(house);
  buildDevices(house);
  buildObjects(house);
  buildLabels(house);
  initFocus();
  initDrag();
  initUI({ structure, house, onReload: reloadHouse });
  initRoomPanel({ house });
  initPlanner({ getStructure: () => structure, onClose: reloadHouse });
  initRoomLights();
  setRoomLightsData({ house, structure });
  await loadStates();
  updateData({ structure, house });

  connectRealtime({
    onStateChanged: (entityId, newState) => applyState(entityId, newState),
    onBulkStates: (states) => setAllStates(states),
    onStatus: (status) => setConnStatus(status),
  });

  // if structure failed at boot (HA still connecting), retry in the background —
  // but only when the backend actually has HA configured
  if (!structure) {
    const status = await api.getStatus().catch(() => null);
    if (status?.configured) {
      const retry = setInterval(async () => {
        await loadStructure();
        if (structure) {
          clearInterval(retry);
          const h = await api.getHouse();
          updateData({ structure, house: h });
          setRoomLightsData({ house: h, structure }); // map area-level lights
        }
      }, 5000);
    }
  }
}

main().catch((e) => {
  showBanner(`App failed to start: ${e.message}`);
  console.error(e);
});
