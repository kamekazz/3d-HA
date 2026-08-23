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
//
// RAIL ORDER IS EARNED, not structural: every card tap (fly into the room) and
// every card light-toggle scores that room a point, and the rail sorts by that
// score so the rooms this house actually uses claim the top slots and the ones
// it doesn't fall past the "All rooms" button. See the "usage" section below
// for the decay model and for why the reorder is deferred until the rail is
// off-screen. The all-rooms overlay stays grouped by floor — that view is for
// finding a room you rarely open, so it must not move under you too.
import { api } from './api.js';
import { enterFocus, onFocusChanged } from './focus.js';
import { getRoomLightIds, getRoomsForEntity } from './roomlights.js';
import { isHiddenRoom } from './house.js';
import { isOn, getState, onStateApplied } from './state.js';
import { showBanner } from './ui.js';
import { getSnapshot, onSnapshotReady } from './snapshots.js';
import { onLayoutChanged, bumpLayout } from './stage.js';
import { tokenNum, tokenPx } from './layout.js';

// Gaps and aspects used to be hand-kept copies of the CSS. They are read back
// from what the browser actually laid out now, so the two cannot drift: the
// gap off the element's own used value, the aspect off the token that the
// stylesheet itself uses for .room-card.
const gapOf = (el) => parseFloat(getComputedStyle(el).columnGap) || 0;
const cardAspect = () => tokenNum('--card-aspect') || 1.6;

const railInstances = new Map();    // roomId -> DOM refs of the rail card
const overlayInstances = new Map(); // roomId -> DOM refs of the all-rooms card
const roomState = new Map();        // roomId -> {pendingUntil, intended}
const pictureAreas = new Set();     // HA area_ids whose registry entry has a picture

let floorsData = [];   // filtered + sorted floors from the last setRoomCardsData
let naturalFlat = [];  // rooms flattened in floor order (the overlay's order)
let roomsFlat = [];    // the same rooms in usage order — the rail's slice order
let capacity = 0;      // grid slots that fit the rail with no scrolling
let railSig = '';      // capacity + visible ids — skip no-op rebuilds
let allOpen = false;   // all-rooms overlay up

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

// ---------------------------------------------------------------- usage

// Which rooms this tablet actually gets used for, so the rail can rank them.
// A plain hit counter would freeze the order a month in: the room you opened
// forty times last winter would outrank the one you have opened daily since.
// So each room keeps a *decaying* score — one point per use, halving every
// HALF_LIFE_MS — which is a running average of recent use, not a lifetime
// total. Decay is applied lazily (on write, and again when reading for the
// sort) rather than on a timer, so an idle tab costs nothing and a tablet left
// asleep for a week wakes up with the right order.
const USE_KEY = 'roomUse:v1';
const HALF_LIFE_MS = 14 * 24 * 60 * 60 * 1000; // 14 days

let useScores = {};      // roomId -> {score, ts} , ts = when score was last decayed
let orderDirty = false;  // a use was scored; rail order is stale

function loadUse() {
  try {
    const raw = JSON.parse(localStorage.getItem(USE_KEY));
    if (raw && typeof raw === 'object') {
      for (const [id, rec] of Object.entries(raw)) {
        if (Number.isFinite(rec?.score) && Number.isFinite(rec?.ts)) useScores[id] = rec;
      }
    }
  } catch { /* garbage or private mode — everyone starts at zero */ }
}

function saveUse() {
  try { localStorage.setItem(USE_KEY, JSON.stringify(useScores)); } catch { /* private mode */ }
}

loadUse(); // at import, not in initRoomCards — setRoomCardsData must never
           // run first and rank a house against an empty score table

const decayed = (rec, now) =>
  (rec ? rec.score * Math.pow(0.5, Math.max(0, now - rec.ts) / HALF_LIFE_MS) : 0);

// Called from the card itself: a tap that flies into the room, or a flip of the
// room's light switch. Both are "I came here for this room". Deliberately NOT
// wired to focus.js — entering a room by clicking it in the 3D scene shouldn't
// silently reshuffle a rail the user wasn't even looking at.
function recordUse(roomId) {
  const now = Date.now();
  useScores[roomId] = { score: decayed(useScores[roomId], now) + 1, ts: now };
  saveUse();
  orderDirty = true;
}

// Adopt the new ranking. Only ever called with the rail off-screen — see
// renderRail() and the onFocusChanged hook in initRoomCards().
function rerank() {
  roomsFlat = byUsage(naturalFlat);
  orderDirty = false;
}

// Most-used first; equal scores (and every never-used room) keep their natural
// floor order, so a fresh install looks exactly like it did before.
function byUsage(rooms) {
  const now = Date.now();
  return rooms
    .map((room, i) => ({ room, i, score: decayed(useScores[room.id], now) }))
    .sort((a, b) => (b.score - a.score) || (a.i - b.i))
    .map((e) => e.room);
}

// ----------------------------------------------------------------

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
    // .lit on the CARD is the rail's whole visual hierarchy: a lit room keeps
    // its photo at full brightness, everything else recedes (see .room-card
    // .rc-img in style.css). Every card used to shout equally.
    c.card?.classList.toggle('lit', !!known.length && anyOn);
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
  placeholder.textContent = roomEmoji(room.name);

  const entry = { card, sub: null, switchEl: null, input: null, img, placeholder,
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
  input.addEventListener('change', () => {
    recordUse(room.id);
    toggleRoomLights(room.id);
  });

  body.append(text, switchEl);
  card.append(img, placeholder, body);
  card.addEventListener('click', () => {
    recordUse(room.id);
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
// --card-aspect cards and a column count the breakpoints can
// change. #room-cards is position:fixed, so detect display:none (edit mode /
// room focus) by rendered size and keep the last good value.
function computeCapacity() {
  const panel = $('room-cards');
  if (panel.offsetWidth === 0) return;
  const gap = gapOf(panel);
  const cols = getComputedStyle(panel).gridTemplateColumns.split(' ').length;
  const tileH = ((panel.clientWidth - (cols - 1) * gap) / cols) / cardAspect();
  const rows = Math.max(1, Math.floor((panel.clientHeight + gap) / (tileH + gap)));
  capacity = rows * cols;
}

function renderRail() {
  const panel = $('room-cards');
  if (!capacity) computeCapacity();

  // Re-rank only while the rail is off-screen. Promoting a card the instant it
  // is used would slide the rest of the grid out from under the finger that
  // just tapped it, and a light toggle would move its own card mid-gesture; the
  // order the user sees is always the one they arrived on. This covers the
  // rail's own tab switch (siderail.js bumpLayout()s into the layout bus);
  // room focus arrives via onFocusChanged in initRoomCards.
  if (orderDirty && panel.offsetWidth === 0) rerank();

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
  // Measure a real heading rather than trusting a constant — renderAllRooms
  // appends them before calling this, so one exists.
  const headEl = grid.querySelector('.floor-heading');
  const HEAD_H = headEl
    ? headEl.offsetHeight + parseFloat(getComputedStyle(headEl).marginTop)
    : tokenPx('--head-h');
  const GAP = gapOf(grid);
  const ASPECT = cardAspect();
  const style = getComputedStyle(grid);
  const W = grid.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  const H = grid.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
  let best = { cols: Math.ceil(Math.sqrt(n)), w: 0 };
  for (let cols = 1; cols <= n; cols++) {
    const cardRows = floorsData.reduce((s, f) => s + Math.ceil(f.rooms.length / cols), 0);
    const w = (W - (cols - 1) * GAP) / cols;
    const h = w / ASPECT;
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
  // Two exclusions, both here rather than at render time: layoutAllRoomsGrid
  // solves the overlay's column count off floorsData, so anything filtered
  // downstream of it would leave that fit math counting cards it no longer
  // draws. The stray "error" HA floor holds a whole-house catch-all area, not a
  // real room (fixing that floor in HA is the real cure); isHiddenRoom drops
  // the structural shells one level down — see house.js. The {...f} copy keeps
  // the floor's own rooms array intact for every other consumer of `house`.
  floorsData = (house?.floors || [])
    .filter((f) => f.ha_floor_id !== 'error')
    .map((f) => ({ ...f, rooms: (f.rooms || []).filter((r) => !isHiddenRoom(r.name)) }))
    .filter((f) => f.rooms.length)
    .sort((a, b) => b.level - a.level); // top floor first, like the building
  naturalFlat = floorsData.flatMap((f) => f.rooms);
  // Rooms deleted in the planner would otherwise keep their score forever and
  // hand it straight to whatever row id SQLite reuses next.
  const live = new Set(naturalFlat.map((r) => String(r.id)));
  let pruned = false;
  for (const id of Object.keys(useScores)) {
    if (!live.has(id)) { delete useScores[id]; pruned = true; }
  }
  if (pruned) saveUse();
  // A full reload rebuilds every card anyway, so this is the one moment the
  // reorder is free — no gesture to disturb, no DOM to keep.
  roomsFlat = byUsage(naturalFlat);
  orderDirty = false;
  railSig = ''; // same ids may carry new names/colors — force the rebuild
  computeCapacity();
  renderRail();
  if (allOpen) renderAllRooms();
}

// boot.js awaits this before lifting the loading curtain. Rail cards whose room
// has an HA area picture fetch it per card (buildCard below), so without this
// the rail would finish assembling itself in full view. Bounded per image: one
// slow or broken area picture must not hold the curtain.
export function cardImagesReady(timeoutMs = 2000) {
  const pending = [];
  for (const entry of railInstances.values()) {
    const { img } = entry;
    if (!img || !img.src || img.complete) continue;
    pending.push(Promise.race([
      img.decode().catch(() => {}),   // decode() rejects on a broken image
      new Promise((resolve) => setTimeout(resolve, timeoutMs)),
    ]));
  }
  return Promise.all(pending);
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

  // Entering a room display:none's the whole rail, and a ResizeObserver does
  // NOT fire for that (Chrome reports nothing for an element with no box, only
  // 0x0 for one that still has one) — measured, not assumed. So the reorder
  // takes its cue from the focus bus instead: rebuild the rail off-screen while
  // the user is inside the room, and it is already re-ranked when they come
  // back out. Nothing re-ranks on the way back in.
  // rerank() rather than letting renderRail()'s width guard decide: this
  // listener and the one in dashboard.js that actually sets body.room-focused
  // fire off the same bus, in registration order, so the rail may still measure
  // non-zero here.
  onFocusChanged((roomId) => {
    if (roomId === null) return;
    if (orderDirty) rerank();
    renderRail();
  });

  // One layout bus (stage.js) instead of a private debounce: it coalesces
  // window resize, orientationchange, visualViewport and the ResizeObserver on
  // the stage probe, so a rotation and a breakpoint flip arrive identically.
  onLayoutChanged(() => {
    computeCapacity();
    renderRail();
    if (allOpen) layoutAllRoomsGrid();
  });

  // ...and observe the rail itself. A display:none rail measures 0, so
  // computeCapacity() bails and keeps the last value; window.resize fires
  // while it is hidden (edit mode, room focus, the other rail tab) and is then
  // never repeated, which is what left a capacity computed for the old
  // orientation after rotating. This fires the moment it comes back at size.
  new ResizeObserver(bumpLayout).observe($('room-cards'));
}
