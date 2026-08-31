// Bootstrap: load data, build the 3D scene, wire UI + realtime.
import * as THREE from 'three';
import { api } from './api.js';
import { initScene, scene, camera, renderer, applyEnvIntensity, refitStage, wasMultiTouch } from './scene.js';
import { initStage } from './stage.js';
import { initSideRail } from './siderail.js';
import { buildHouse, roomMeshes, stairGroups, paintRoomEmissive, getLevel, houseShellReady } from './house.js';
import { setModelVersions } from './models.js';
import { buildDevices, markers } from './devices.js';
import { buildObjects, objects3d } from './objects.js';
import { setAllStates, applyState, friendlyName, stateLabel, styleMarker, paintModelState } from './state.js';
import { buildLabels, showLabel, hideLabel } from './labels.js';
import { initFocus, enterFocus, exitFocus, suspendFocusForRebuild,
         resumeFocusAfterRebuild } from './focus.js';
import { connectRealtime } from './socket.js';
import { initUI, updateData, setConnStatus, showBanner, openDevicePanel, openObjectPanel, appMode } from './ui.js';
import { initDrag, isTransforming, setSelected } from './drag.js';
import { initRoomPanel, updateRoomPanelData } from './roompanel.js';
import { initPlanner } from './planner.js';
import { initDaylight, settleDaylight } from './daylight.js';
import { initEnvironment, setEnvironmentData } from './environment.js';
import { initWeather } from './weather.js';
import { initRoomLights, setRoomLightsData, repaintFixture, settleRoomLights } from './roomlights.js';
import { initFloorView } from './floorview.js';
import { initCutaway, setCutawayData } from './cutaway.js';
import { initUndo } from './undo.js';
import { initDashboard, calendarReady } from './dashboard.js';
import { initCameras } from './cameras.js';
import { initRoomCards, setRoomCardsData, cardImagesReady } from './roomcards.js';
import { requestSnapshots, snapshotsIdle } from './snapshots.js';
import { startBoot, bootStage, bootProgress, settleLoaders, orTimeout, finishBoot,
  bootHouseBuilt } from './boot.js';

let structure = null;

// `pending` lets boot pass an already-in-flight request (see main()); the
// background retry loop calls with no argument and starts a fresh one.
async function loadStructure(pending) {
  try {
    structure = await (pending || api.getStructure());
    showBanner(null);
  } catch (e) {
    structure = null;
    showBanner(e.status === 503
      ? `Home Assistant not connected yet — ${e.detail || 'check backend/.env and restart'}. The 3D editor still works.`
      : `Could not load HA structure: ${e.message}`);
  }
}

async function loadStates(pending) {
  try {
    const states = await (pending || api.getStates());
    if (Array.isArray(states)) setAllStates(states);
  } catch { /* HA offline — markers stay grey */ }
}

async function reloadHouse() {
  setSelected(null); // every mesh below is about to be replaced
  // The rebuild disposes the meshes focus mode holds references to, so it has
  // to let go — but not as exitFocus, which every listener reads as the user
  // navigating out. Every edit made inside the room editor lands here.
  suspendFocusForRebuild();
  const house = await api.getHouse();
  setModelVersions(house.model_versions); // a re-written .glb on disk busts its URL
  buildHouse(house);
  buildDevices(house);
  buildObjects(house);
  setCutawayData(house); // wall meshes + furniture are new objects after a rebuild
  // after buildObjects: the object focus scope has to land on the new instances
  resumeFocusAfterRebuild();
  buildLabels(house);
  setEnvironmentData(house); // yard follows the (possibly moved) footprints
  setRoomLightsData({ house, structure }); // fresh slab materials — repoint glow
  applyEnvIntensity(); // fresh materials default to envMapIntensity 1
  await loadStates();
  updateData({ structure, house });
  updateRoomPanelData(house);
  setRoomCardsData(house, structure); // after setRoomLightsData — cards read its light sets
  requestSnapshots(house);   // re-capture rooms whose geometry changed
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
    // NDC off the window, not the canvas rect — correct only because
    // #scene-container is position:fixed; inset:0. It stays correct under
    // scene.js's view offset, since setFromCamera unprojects through
    // projectionMatrixInverse, which includes it. If the canvas ever gets
    // inset, switch to renderer.domElement.getBoundingClientRect().
    pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);

    // only rooms + stairs — never the whole scene: the house-shell GLB alone
    // has thousands of meshes, and raycasting it per pointermove tanked fps
    // (the shell was never pickable anyway; grid/ground/labels have no kind)
    const hits = raycaster.intersectObjects(
      [...roomMeshes.values(), ...stairGroups], true);

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
      // pickable === false: architectural surface objects (room-wide floors,
      // ceilings, wall washes, baseboards). They cover the whole room, so
      // without this they'd swallow every click and the room editor could
      // never be opened again. See objects.js SURFACE_RE.
      if (owner && owner.userData.pickable !== false && isShown(hit.object)) {
        return owner;
      }
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
      paintRoomEmissive(hovered, ud.baseEmissive ?? 0);
    } else if (ud.kind === 'device') {
      styleMarker(ud.entityId); // state-driven restore, can't desync
      hideLabel(ud.entityId); // labels are hover-only now, even in focus mode
    } else if (ud.kind === 'object' && ud.entityId) {
      // roomlights.js owns this piece's emissive and repaints it whenever its
      // eased glow moves; force that on the next tick so the boost comes off
      // even while the light is sitting at a steady level.
      repaintFixture(ud.objectId);
      hideLabel(ud.entityId);
    }
    hovered = null;
  }

  function applyHover(obj) {
    hovered = obj;
    const ud = obj.userData;
    if (ud.kind === 'room') {
      // accent-tinted glow: walls are opaque now, so opacity can't signal.
      // Goes through paintRoomEmissive because the glow lives on the per-edge
      // wall meshes, not on the room mesh itself.
      paintRoomEmissive(obj, (ud.baseEmissive ?? 0) + 0.15);
    } else if (ud.kind === 'device') {
      obj.scale.multiplyScalar(1.25);
      showLabel(ud.entityId);
    } else if (ud.kind === 'object' && ud.entityId) {
      // a bound fixture gets an emissive lift, NOT the marker's 1.25x pop — a
      // lamp that grows when you point at it reads as broken
      paintModelState(obj, { emissiveHex: 0x2997ff, emissiveIntensity: 0.35 });
      showLabel(ud.entityId);
    }
  }

  // hover raycasts are rAF-gated (many pointermoves per frame otherwise) and
  // skipped entirely while the button is down — orbiting doesn't need hover
  let pendingMove = null;
  let moveQueued = false;
  renderer.domElement.addEventListener('pointermove', (e) => {
    pendingMove = e;
    if (moveQueued) return;
    moveQueued = true;
    requestAnimationFrame(() => {
      moveQueued = false;
      if (!downAt) handleHover(pendingMove);
    });
  });

  function handleHover(e) {
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
  }

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
    // A <=5px nudge on a gizmo arrow is not a click on the room behind it.
    // This handler runs before TransformControls' own pointerup, so tc.dragging
    // is still set here — which is the only way to tell the two apart.
    if (isTransforming()) { downAt = null; return; }
    const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
    const pinched = wasMultiTouch();
    downAt = null;
    if (moved > 5) return; // it was an orbit drag, not a click
    if (pinched) return;   // a pinch whose fingers barely moved is not a tap
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
    // A furniture piece bound to an entity behaves exactly like that entity's
    // marker in view mode -- it IS the device now. In edit mode it stays a
    // piece of furniture, so it can be moved, rebound or hidden.
    if (ud.kind === 'object' && ud.entityId && appMode !== 'edit') {
      handleEntityClick(ud.entityId, isDouble);
      return;
    }
    if (ud.kind === 'device') {
      handleEntityClick(ud.entityId, isDouble);
    } else if (ud.kind === 'object') {
      if (appMode === 'edit') openObjectPanel(ud.objectId);
      // view mode, unbound: plain scenery. Fall through to its room rather
      // than opening an editor panel a viewer can't use.
      else enterFocus(ud.roomId);
    } else if (ud.kind === 'room') {
      // One gesture, both modes: focus the room. In edit mode ui.js follows the
      // focus event and opens that room's editor screen, so a click on the mesh
      // and "Edit" in the room list land in exactly the same place.
      enterFocus(ud.roomId);
    }
  });

  // Shared by device markers and bound furniture: single click toggles (like a
  // real switch), double click opens the detail panel.
  function handleEntityClick(entityId, isDouble) {
    const domain = entityId.split('.')[0];
    if (!QUICK_TOGGLE_DOMAINS.has(domain)) {
      openDevicePanel(entityId);
      return;
    }
    // click = toggle (like a real switch), double-click = detail panel;
    // the short window keeps a double-click from also toggling
    if (isDouble) {
      if (toggleTimer) { clearTimeout(toggleTimer); toggleTimer = null; }
      openDevicePanel(entityId);
      return;
    }
    if (toggleTimer) clearTimeout(toggleTimer);
    toggleTimer = setTimeout(() => {
      toggleTimer = null;
      api.control({ entity_id: entityId, domain, service: 'toggle' })
        .catch((err) => showBanner(`Control failed: ${err.message}`, 4000));
    }, DOUBLE_MS);
  }
}

// ------------------------------------------------------------- boot

async function main() {
  startBoot();
  bootStage('Reading Home Assistant…', 0, 0.15);

  // These used to be three serial round-trips (structure, then house, then
  // states) - two of them dead time. Fire all three now and await each exactly
  // where it was awaited before, so the ordering that matters is unchanged:
  // setAllStates still runs after buildDevices has created the markers it
  // styles. The bare .catch() only marks the rejection handled so an early
  // failure isn't an unhandled rejection; the real handling is at the await.
  const structureP = api.getStructure();
  const houseP = api.getHouse();
  const statesP = api.getStates();
  for (const p of [structureP, houseP, statesP]) p.catch(() => {});

  // First: the stage probe is what scene.js frames the house into, and
  // initScene reads it during setup.
  initStage();
  initSideRail();
  // House view's own re-fit. focus.js and floorview.js claim the stageChanged
  // event when they own the camera; this is the remaining case. Registered
  // before theirs, but it self-excludes on the same two conditions.
  window.addEventListener('stageChanged', () => {
    if (document.body.classList.contains('room-focused')) return;
    if (getLevel() !== 'all') return;
    refitStage();
  });
  initScene(document.getElementById('scene-container'));
  initDaylight();
  initEnvironment();
  initWeather();
  initFloorView();
  initCutaway();
  setupPicking();

  await loadStructure(structureP);
  bootProgress(0.6);
  const house = await houseP;
  // Before any getInstance: this is what lets the model files be cached.
  setModelVersions(house.model_versions);

  // The house goes up FIRST, and alone. buildHouse is synchronous for rooms /
  // floors / stairs, then kicks off the whole-house shell GLB — and we wait for
  // that before anything else asks the network for a byte. Three reasons:
  //
  //  - it is the first thing you see, so it should be the first thing loaded;
  //  - the shell is DRACO-compressed, and its decoder (763 KB across three
  //    files in vendor/draco/gltf/) is only requested once GLTFLoader has
  //    parsed the shell and met the extension. Issued after buildObjects, that
  //    request queues behind ~271 furniture fetches on a 6-connection pool;
  //  - setEnvironmentData below then measures a shell that already exists, so
  //    the yard is planted correctly once instead of being built and replanted
  //    when the shell's setLevel fires levelChanged.
  //
  // The band is set BEFORE the await on purpose: the shell's loader callbacks
  // must paint into the house band, not into whatever came before it.
  bootStage('Loading the house…', 0.15, 0.45);
  buildHouse(house);
  bootHouseBuilt();   // there is a stage to reveal now; the watchdog may fire
  // Resolves when the shell is added, masked, framed and levelled — or at once
  // when there is no shell or it failed (house.js dispatches shellLoadFailed
  // for the banner), so a 404 shell can never hang the boot.
  await houseShellReady();

  // Everything from here to the next await is synchronous, so no loader
  // callback can fire inside it - the furniture band is in place before
  // DefaultLoadingManager reports the first of its items.
  bootStage('Loading furniture…', 0.45, 0.85);
  buildDevices(house);
  buildObjects(house);
  setCutawayData(house); // wall meshes + furniture are new objects after a rebuild
  buildLabels(house);
  setEnvironmentData(house);
  initFocus();
  initDrag();
  initUI({ structure, house, onReload: reloadHouse });
  initRoomPanel({ house });
  initPlanner({ getStructure: () => structure, onClose: reloadHouse });
  initUndo({ defaultRefresh: reloadHouse });
  initRoomLights();
  setRoomLightsData({ house, structure });
  initDashboard();
  initCameras();
  initRoomCards();
  setRoomCardsData(house, structure); // after setRoomLightsData — cards read its light sets

  await loadStates(statesP);
  updateData({ structure, house });

  connectRealtime({
    onStateChanged: (entityId, newState) => applyState(entityId, newState),
    onBulkStates: (states) => setAllStates(states),
    onStatus: (status) => setConnStatus(status),
  });

  // ---- hold the curtain until the scene has actually finished assembling.
  // No deadline of its own: boot.js's watchdog owns giving up, and it does so
  // on a stall rather than on a guess at how long a house takes to load. The
  // shell needs no separate await here — it landed before the furniture band.
  await settleLoaders();          // every GLB and texture

  bootStage('Preparing the scene…', 0.85, 0.92);
  // Shaders for a few hundred fresh GLB materials compile on the first DRAW,
  // not on load — that hitch belongs behind the curtain. compileAsync is newer
  // than the pinned three, so fall back to the synchronous compile.
  if (renderer.compileAsync) await renderer.compileAsync(scene, camera);
  else renderer.compile(scene, camera);
  window.__cutaway?.settle();     // jump wall fades to target, don't fade them in
  settleDaylight();               // and don't fade day->night after the reveal
  settleRoomLights();             // nor ramp a dozen lamps up once it lifts

  bootStage('Rendering room previews…', 0.92, 0.99);
  // immediate: settleLoaders() has resolved, so the 1.5s/6.5s guesswork the
  // timers exist for is answered — nothing is still streaming in.
  requestSnapshots(house, { immediate: true });
  // Don't wait on a hidden tab. snapshots.js captures one room per rAF, which
  // drains ~25 rooms in well under a second when the page is visible - but a
  // backgrounded tab has no rAF at all AND its pump parks itself on
  // document.hidden by design, so waiting there can only ever burn the cap for
  // previews that physically cannot render. Nobody is looking; the pump picks
  // them up when the tab comes back. The cap covers the in-between case (a
  // visible but uncomposited window). Generous now that the watchdog reveals on
  // a stall rather than a clock: these two ARE the room cards, and cutting them
  // short is what put the rail's thumbnails on screen after the curtain lifted.
  if (!document.hidden) await orTimeout(snapshotsIdle(), 20000);
  await orTimeout(cardImagesReady(8000), 10000);
  // The calendar stays on a short leash by contrast: it is one dock tile, HA's
  // calendar API can be slow, and it is not worth holding the whole app for.
  await calendarReady(2000);

  finishBoot();

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
          setRoomCardsData(h, structure); // light counts / area pictures arrive with the HA registry
        }
      }, 5000);
    }
  }
}

main().catch((e) => {
  finishBoot(); // the banner is behind the curtain — lift it first, always
  showBanner(`App failed to start: ${e.message}`);
  console.error(e);
});
