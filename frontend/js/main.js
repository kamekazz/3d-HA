// Bootstrap: load data, build the 3D scene, wire UI + realtime.
import * as THREE from 'three';
import { api } from './api.js';
import { initScene, scene, camera, renderer } from './scene.js';
import { buildHouse, roomMeshes } from './house.js';
import { buildDevices, markers } from './devices.js';
import { setAllStates, applyState, friendlyName, stateLabel } from './state.js';
import { connectRealtime } from './socket.js';
import { initUI, updateData, setConnStatus, showBanner, openDevicePanel, selectRoom } from './ui.js';

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
  const house = await api.getHouse();
  buildHouse(house);
  buildDevices(house);
  await loadStates();
  updateData({ structure, house });
  return house;
}

// ------------------------------------------------------------- picking

function setupPicking() {
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const tooltip = document.getElementById('tooltip');
  let downAt = null;

  function pick(event) {
    pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(scene.children, true);
    for (const hit of hits) {
      const ud = hit.object.userData;
      if (ud?.kind && hit.object.parent?.visible !== false) {
        // skip rooms/devices on hidden floors
        let node = hit.object, visible = true;
        while (node) { if (!node.visible) { visible = false; break; } node = node.parent; }
        if (visible) return hit.object;
      }
    }
    return null;
  }

  renderer.domElement.addEventListener('pointermove', (e) => {
    const obj = pick(e);
    if (!obj) { tooltip.classList.add('hidden'); return; }
    const ud = obj.userData;
    if (ud.kind === 'device') {
      tooltip.innerHTML =
        `<strong>${friendlyName(ud.entityId)}</strong><br>` +
        `<span class="sub">${stateLabel(ud.entityId)} · ${ud.roomName}</span>`;
    } else {
      tooltip.innerHTML = `<strong>${ud.roomName}</strong><br><span class="sub">Level ${ud.level}</span>`;
    }
    tooltip.style.left = `${e.clientX + 14}px`;
    tooltip.style.top = `${e.clientY + 14}px`;
    tooltip.classList.remove('hidden');
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
    if (!obj) return;
    const ud = obj.userData;
    if (ud.kind === 'device') openDevicePanel(ud.entityId);
    else if (ud.kind === 'room' && e.detail === 2) selectRoom(ud.roomId);
  });
}

// ------------------------------------------------------------- boot

async function main() {
  initScene(document.getElementById('scene-container'));
  setupPicking();

  await loadStructure();
  const house = await api.getHouse();
  buildHouse(house);
  buildDevices(house);
  initUI({ structure, house, onReload: reloadHouse });
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
        }
      }, 5000);
    }
  }
}

main().catch((e) => {
  showBanner(`App failed to start: ${e.message}`);
  console.error(e);
});
