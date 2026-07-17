// Right-hand room-card panel (view mode): a 2-column grid of tappable room
// cards, sliced to exactly what fits — the wall tablet never scrolls (same
// philosophy as the camera column in cameras.js). When rooms overflow, the
// last slot becomes an "All rooms" button opening a full-screen grid where
// every room fits with no scrolling, grouped by floor. Tapping a card flies
// into the room (focus mode); the switch on the card toggles the room's
// lights (same entity sets that drive the night glow in roomlights.js).
// Card images prefer the picture set on the room's linked HA area (proxied
// via /api/ha/area-picture); rooms without one fall back to 3D snapshots
// from snapshots.js, with a flat accent placeholder until the capture lands.
//
// A room can have two live card instances at once (rail + overlay), so the
// per-room optimistic toggle state lives in roomState while DOM refs live in
// railInstances/overlayInstances; updateCard() computes the light state once
// and applies it to whichever instances exist.
import { api } from './api.js';
import { enterFocus } from './focus.js';
import { getRoomLightIds, getRoomsForEntity } from './roomlights.js';
import { isOn, getState, onStateApplied } from './state.js';
import { showBanner } from './ui.js';
import { getSnapshot, onSnapshotReady } from './snapshots.js';

const GAP = 10;          // must match #room-cards / #rooms-all-grid CSS gap
const CARD_ASPECT = 1.6; // must match .room-card aspect-ratio

const railInstances = new Map();    // roomId -> DOM refs of the rail card
const overlayInstances = new Map(); // roomId -> DOM refs of the all-rooms card
const roomState = new Map();        // roomId -> {pendingUntil, intended}
const pictureAreas = new Set();     // HA area_ids whose registry entry has a picture

let floorsData = []; // filtered + sorted floors from the last setRoomCardsData
let roomsFlat = [];  // rooms flattened in floor order (rail slice order)
let capacity = 0;    // grid slots that fit the rail with no scrolling
let railSig = '';    // capacity + visible ids — skip no-op rebuilds
let allOpen = false; // all-rooms overlay up

const $ = (id) => document.getElementById(id);

const ROOM_EMOJI = [
  [/kitchen|cocina/i, '🍳'], [/living|sala|lounge|family/i, '🛋️'],
  [/bed|master|dormit/i, '🛏️'], [/bath|baño|shower|toilet/i, '🛁'],
  [/office|desk|study/i, '💻'], [/garage/i, '🚗'], [/laundry|utility/i, '🧺'],
  [/dining|comedor/i, '🍽️'], [/hall|entry|foyer|pasillo/i, '🚪'],
  [/gym|workout/i, '🏋️'], [/kid|play|nursery/i, '🧸'],
  [/basement|cellar/i, '🔦'], [/attic/i, '📦'],
];

function roomEmoji(name) {
  for (const [re, emoji] of ROOM_EMOJI) if (re.test(name)) return emoji;
  return '🏠';
}

function instancesOf(roomId) {
  return [railInstances.get(roomId), overlayInstances.get(roomId)].filter(Boolean);
}

function updateCard(roomId) {
  const entries = instancesOf(roomId);
  const st = roomState.get(roomId);
  if (!entries.length || !st) return;
  const lightIds = [...getRoomLightIds(roomId)];
  const known = lightIds.filter((id) => getState(id));
  let n = known.filter((id) => isOn(id)).length;
  let anyOn = n > 0;

  if (st.pendingUntil && performance.now() < st.pendingUntil) {
    if (anyOn === st.intended) {
      st.pendingUntil = 0; // HA confirmed — back to live state
    } else {
      anyOn = st.intended;  // optimistic display until echo/timeout
      n = st.intended ? Math.max(n, known.length) : 0;
    }
  } else {
    st.pendingUntil = 0;
  }

  for (const c of entries) {
    c.switchEl.classList.toggle('pending', !!st.pendingUntil);
    if (!known.length) {
      c.sub.textContent = lightIds.length ? 'lights unavailable' : 'no lights';
      c.sub.classList.remove('lit');
      c.switchEl.classList.add('hidden');
      continue;
    }
    c.switchEl.classList.remove('hidden');
    c.input.checked = anyOn;
    c.sub.textContent = anyOn ? `${n} light${n === 1 ? '' : 's'} on` : 'lights off';
    c.sub.classList.toggle('lit', anyOn);
  }
}

async function toggleRoomLights(roomId) {
  const st = roomState.get(roomId);
  const known = [...getRoomLightIds(roomId)].filter((id) => getState(id));
  if (!st || !known.length) return;
  const intended = !known.some((id) => isOn(id));
  st.intended = intended;
  st.pendingUntil = performance.now() + 4000;
  updateCard(roomId);
  setTimeout(() => updateCard(roomId), 4100); // reconcile if echoes were lost
  const service = intended ? 'turn_on' : 'turn_off';
  const results = await Promise.allSettled(known.map((id) =>
    api.control({ entity_id: id, domain: 'light', service })));
  if (results.some((r) => r.status === 'rejected')) {
    st.pendingUntil = 0;
    updateCard(roomId);
    showBanner('Some lights did not respond', 4000);
  }
}

function buildCard(room, inOverlay) {
  const card = document.createElement('div');
  card.className = 'room-card';

  const img = document.createElement('img');
  img.className = 'rc-img hidden';
  img.alt = room.name;
  const placeholder = document.createElement('div');
  placeholder.className = 'rc-placeholder';
  placeholder.style.background =
    `linear-gradient(135deg, ${room.color || '#8fa8bf'}33, #10141a 85%)`;
  placeholder.textContent = roomEmoji(room.name);

  const entry = { sub: null, switchEl: null, input: null, img, placeholder,
                  areaPic: false };
  if (room.ha_area_id && pictureAreas.has(room.ha_area_id)) {
    entry.areaPic = true;
    img.onerror = () => {
      // one-shot: never let a bad snapshot dataURL re-fire this
      img.onerror = null;
      entry.areaPic = false;
      const snap = getSnapshot(room.id);
      if (snap) {
        img.src = snap;
      } else {
        img.classList.add('hidden');
        placeholder.classList.remove('hidden');
      }
    };
    img.src = `/api/ha/area-picture/${encodeURIComponent(room.ha_area_id)}`;
    img.classList.remove('hidden');
    placeholder.classList.add('hidden');
  } else {
    const snap = getSnapshot(room.id);
    if (snap) {
      img.src = snap;
      img.classList.remove('hidden');
      placeholder.classList.add('hidden');
    }
  }

  const body = document.createElement('div');
  body.className = 'rc-body';
  const text = document.createElement('div');
  text.className = 'rc-text';
  const name = document.createElement('div');
  name.className = 'rc-name';
  name.textContent = room.name;
  const sub = document.createElement('div');
  sub.className = 'rc-sub';
  text.append(name, sub);

  const switchEl = document.createElement('label');
  switchEl.className = 'tswitch';
  switchEl.title = 'Toggle this room’s lights';
  const input = document.createElement('input');
  input.type = 'checkbox';
  const knob = document.createElement('span');
  knob.className = 'knob';
  switchEl.append(input, knob);
  switchEl.addEventListener('click', (e) => e.stopPropagation());
  input.addEventListener('change', () => toggleRoomLights(room.id));

  body.append(text, switchEl);
  card.append(img, placeholder, body);
  card.addEventListener('click', () => {
    if (inOverlay) closeAllRooms(); // first, so the 3D fly-in is visible
    enterFocus(room.id);
  });

  entry.sub = sub;
  entry.switchEl = switchEl;
  entry.input = input;
  if (!roomState.has(room.id)) roomState.set(room.id, { pendingUntil: 0, intended: false });
  (inOverlay ? overlayInstances : railInstances).set(room.id, entry);
  return card;
}

// ---------------------------------------------------------------- rail

// Same measured-capacity trick as cameras.js computeCapacity(), but for
// CARD_ASPECT cards and a column count the narrow-screen media query can
// change. #room-cards is position:fixed, so detect display:none (edit mode /
// room focus) by rendered size and keep the last good value.
function computeCapacity() {
  const panel = $('room-cards');
  if (panel.offsetWidth === 0) return;
  const cols = getComputedStyle(panel).gridTemplateColumns.split(' ').length;
  const tileH = ((panel.clientWidth - (cols - 1) * GAP) / cols) / CARD_ASPECT;
  const rows = Math.max(1, Math.floor((panel.clientHeight + GAP) / (tileH + GAP)));
  capacity = rows * cols;
}

function renderRail() {
  const panel = $('room-cards');
  if (!capacity) computeCapacity();

  // rooms overflow the rail → the last slot becomes the "All rooms" button
  const overflow = roomsFlat.length > capacity;
  const visible = overflow ? roomsFlat.slice(0, Math.max(0, capacity - 1)) : roomsFlat;
  const sig = `${capacity}|${roomsFlat.length}|${visible.map((r) => r.id).join()}`;
  if (sig === railSig) return; // set unchanged — keep the DOM
  railSig = sig;

  panel.innerHTML = '';
  railInstances.clear();
  for (const room of visible) {
    panel.appendChild(buildCard(room, false));
    updateCard(room.id);
  }
  if (overflow) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'room-card rooms-all-btn';
    btn.innerHTML =
      '<span class="rab-icon">⊞</span><span class="rab-text">All rooms</span>' +
      `<span class="rab-count">${roomsFlat.length}</span>`;
    btn.onclick = openAllRooms;
    panel.appendChild(btn);
  }
}

// ---------------------------------------------------------------- all view

// Like cameras.js layoutAllGrid — pick the column count that maximizes card
// size while everything fits with no scrolling — but with one slim heading
// row per floor (grid-column: 1/-1) between the card rows.
function layoutAllRoomsGrid() {
  const grid = $('rooms-all-grid');
  const n = roomsFlat.length;
  if (!n) return;
  const HEAD_H = 22; // .floor-heading row height incl. its top margin
  const style = getComputedStyle(grid);
  const W = grid.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  const H = grid.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
  let best = { cols: Math.ceil(Math.sqrt(n)), w: 0 };
  for (let cols = 1; cols <= n; cols++) {
    const cardRows = floorsData.reduce((s, f) => s + Math.ceil(f.rooms.length / cols), 0);
    const w = (W - (cols - 1) * GAP) / cols;
    const h = w / CARD_ASPECT;
    const rowCount = cardRows + floorsData.length;
    const total = cardRows * h + floorsData.length * HEAD_H + (rowCount - 1) * GAP;
    if (w > best.w && total <= H) best = { cols, w };
  }
  grid.style.gridTemplateColumns = `repeat(${best.cols}, ${Math.floor(best.w)}px)`;
}

function renderAllRooms() {
  const grid = $('rooms-all-grid');
  grid.innerHTML = '';
  overlayInstances.clear();
  for (const floor of floorsData) {
    const heading = document.createElement('h4');
    heading.className = 'floor-heading';
    heading.textContent = floor.name;
    grid.appendChild(heading);
    for (const room of floor.rooms) {
      grid.appendChild(buildCard(room, true));
      updateCard(room.id);
    }
  }
  layoutAllRoomsGrid();
}

function onAllRoomsKeydown(e) {
  if (e.key !== 'Escape') return;
  e.stopPropagation(); // focus.js's Esc (exit room focus) must not also fire
  closeAllRooms();
}

function openAllRooms() {
  allOpen = true;
  $('rooms-all').classList.remove('hidden');
  document.addEventListener('keydown', onAllRoomsKeydown, true);
  renderAllRooms();
}

function closeAllRooms() {
  document.removeEventListener('keydown', onAllRoomsKeydown, true);
  overlayInstances.clear();
  $('rooms-all-grid').innerHTML = '';
  $('rooms-all').classList.add('hidden');
  allOpen = false;
}

// ---------------------------------------------------------------- data + init

// Full re-render from a fresh /api/house payload (boot + every reloadHouse).
export function setRoomCardsData(house, structure) {
  if (structure) {
    pictureAreas.clear();
    for (const floor of structure.floors || [])
      for (const area of floor.areas || [])
        if (area.picture) pictureAreas.add(area.area_id);
  }
  // The stray "error" HA floor holds a whole-house catch-all area, not a real
  // room — skip it here (fixing that floor in HA is the real cure).
  floorsData = [...(house?.floors || [])]
    .filter((f) => (f.rooms || []).length && f.ha_floor_id !== 'error')
    .sort((a, b) => b.level - a.level); // top floor first, like the building
  roomsFlat = floorsData.flatMap((f) => f.rooms);
  railSig = ''; // same ids may carry new names/colors — force the rebuild
  computeCapacity();
  renderRail();
  if (allOpen) renderAllRooms();
}

export function initRoomCards() {
  $('rooms-all-close').onclick = closeAllRooms;

  onSnapshotReady((roomId, url) => {
    for (const c of instancesOf(roomId)) {
      if (c.areaPic) continue; // never stomp a real HA area photo
      c.img.src = url;
      c.img.classList.remove('hidden');
      c.placeholder.classList.add('hidden');
    }
  });

  onStateApplied((entityId) => {
    if (entityId === null) {
      const ids = new Set([...railInstances.keys(), ...overlayInstances.keys()]);
      for (const roomId of ids) updateCard(roomId);
    } else if (entityId.startsWith('light.')) {
      for (const roomId of getRoomsForEntity(entityId)) updateCard(roomId);
    }
  });

  let resizeTimer = 0;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      computeCapacity();
      renderRail();
      if (allOpen) layoutAllRoomsGrid();
    }, 150);
  });

  // leaving edit mode re-shows the rail — re-measure in case the window
  // changed size while it was display:none (resize can't measure it then)
  window.addEventListener('appModeChanged', () => {
    computeCapacity();
    renderRail();
  });
}
