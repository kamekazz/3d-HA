// Right-hand room-card panel (view mode): one tappable card per room, grouped
// by floor (top floor first). Tapping a card flies into the room (focus mode);
// the switch on the card toggles the room's lights (same entity sets that
// drive the night glow in roomlights.js). Card images prefer the picture set
// on the room's linked HA area (proxied via /api/ha/area-picture); rooms
// without one fall back to 3D snapshots from snapshots.js, with a flat accent
// placeholder until the capture lands.
import { api } from './api.js';
import { enterFocus } from './focus.js';
import { getRoomLightIds, getRoomsForEntity } from './roomlights.js';
import { isOn, getState, onStateApplied } from './state.js';
import { showBanner } from './ui.js';
import { getSnapshot, onSnapshotReady } from './snapshots.js';

const cards = new Map(); // roomId -> {sub, switchEl, input, img, placeholder, areaPic, pendingUntil, intended}
const pictureAreas = new Set(); // HA area_ids whose registry entry has a picture

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

function updateCard(roomId) {
  const c = cards.get(roomId);
  if (!c) return;
  const lightIds = [...getRoomLightIds(roomId)];
  const known = lightIds.filter((id) => getState(id));
  let n = known.filter((id) => isOn(id)).length;
  let anyOn = n > 0;

  if (c.pendingUntil && performance.now() < c.pendingUntil) {
    if (anyOn === c.intended) {
      c.pendingUntil = 0; // HA confirmed — back to live state
    } else {
      anyOn = c.intended;  // optimistic display until echo/timeout
      n = c.intended ? Math.max(n, known.length) : 0;
    }
  } else {
    c.pendingUntil = 0;
  }
  c.switchEl.classList.toggle('pending', !!c.pendingUntil);

  if (!known.length) {
    c.sub.textContent = lightIds.length ? 'lights unavailable' : 'no lights';
    c.sub.classList.remove('lit');
    c.switchEl.classList.add('hidden');
    return;
  }
  c.switchEl.classList.remove('hidden');
  c.input.checked = anyOn;
  c.sub.textContent = anyOn ? `${n} light${n === 1 ? '' : 's'} on` : 'lights off';
  c.sub.classList.toggle('lit', anyOn);
}

async function toggleRoomLights(roomId) {
  const c = cards.get(roomId);
  const known = [...getRoomLightIds(roomId)].filter((id) => getState(id));
  if (!c || !known.length) return;
  const intended = !known.some((id) => isOn(id));
  c.intended = intended;
  c.pendingUntil = performance.now() + 4000;
  updateCard(roomId);
  setTimeout(() => updateCard(roomId), 4100); // reconcile if echoes were lost
  const service = intended ? 'turn_on' : 'turn_off';
  const results = await Promise.allSettled(known.map((id) =>
    api.control({ entity_id: id, domain: 'light', service })));
  if (results.some((r) => r.status === 'rejected')) {
    c.pendingUntil = 0;
    updateCard(roomId);
    showBanner('Some lights did not respond', 4000);
  }
}

function buildCard(room) {
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
                  areaPic: false, pendingUntil: 0, intended: false };
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
  card.addEventListener('click', () => enterFocus(room.id));

  entry.sub = sub;
  entry.switchEl = switchEl;
  entry.input = input;
  cards.set(room.id, entry);
  return card;
}

// Full re-render from a fresh /api/house payload (boot + every reloadHouse).
export function setRoomCardsData(house, structure) {
  if (structure) {
    pictureAreas.clear();
    for (const floor of structure.floors || [])
      for (const area of floor.areas || [])
        if (area.picture) pictureAreas.add(area.area_id);
  }
  const panel = document.getElementById('room-cards');
  panel.innerHTML = '';
  cards.clear();
  const floors = [...(house?.floors || [])]
    .filter((f) => (f.rooms || []).length)
    .sort((a, b) => b.level - a.level); // top floor first, like the building
  for (const floor of floors) {
    const heading = document.createElement('h4');
    heading.className = 'floor-heading';
    heading.textContent = floor.name;
    panel.appendChild(heading);
    for (const room of floor.rooms) {
      panel.appendChild(buildCard(room));
      updateCard(room.id);
    }
  }
}

export function initRoomCards() {
  onSnapshotReady((roomId, url) => {
    const c = cards.get(roomId);
    if (!c || c.areaPic) return; // never stomp a real HA area photo
    c.img.src = url;
    c.img.classList.remove('hidden');
    c.placeholder.classList.add('hidden');
  });

  onStateApplied((entityId) => {
    if (entityId === null) {
      for (const roomId of cards.keys()) updateCard(roomId);
    } else if (entityId.startsWith('light.')) {
      for (const roomId of getRoomsForEntity(entityId)) updateCard(roomId);
    }
  });
}
