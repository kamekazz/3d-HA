// Tablet dashboard chrome (view mode): live tiles (clock / temperature /
// lights / security / climate) along the bottom, and the Home button that
// returns to the whole-house view. (The left column is the camera grid,
// owned by cameras.js.) Every tile hides itself when HA has no matching
// entities; everything updates live off state.js's onStateApplied.
import { api } from './api.js';
import { setLevel, getLevel } from './house.js';
import { exitFocus, onFocusChanged } from './focus.js';
import { getState, findEntities, isOn, onStateApplied } from './state.js';
import { getAllHouseLightIds } from './roomlights.js';
import { showBanner } from './ui.js';

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------- clock

function renderClock() {
  const now = new Date();
  $('bb-time').textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  $('bb-date').textContent = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

// ---------------------------------------------------------------- temp tile

// first weather entity wins; a thermostat's measured temperature is the backup
function pickTempSource() {
  for (const id of findEntities('weather.')) {
    if (getState(id)?.attributes?.temperature != null) return { id, attr: 'temperature' };
  }
  for (const id of findEntities('climate.')) {
    if (getState(id)?.attributes?.current_temperature != null) {
      return { id, attr: 'current_temperature' };
    }
  }
  return null;
}

const CONDITION_EMOJI = {
  'clear-night': '🌙', cloudy: '☁️', fog: '🌫️', hail: '🌨️', lightning: '⛈️',
  'lightning-rainy': '⛈️', partlycloudy: '⛅', pouring: '🌧️', rainy: '🌧️',
  snowy: '🌨️', 'snowy-rainy': '🌨️', sunny: '☀️', windy: '🌬️',
  'windy-variant': '🌬️', exceptional: '⚠️',
};

function renderTemp() {
  const tile = $('bb-temp');
  const src = pickTempSource();
  if (!src) { tile.classList.add('hidden'); return; }
  const s = getState(src.id);
  const t = s.attributes[src.attr];
  const isWeather = src.id.startsWith('weather.');
  const emoji = isWeather ? (CONDITION_EMOJI[s.state] || '🌡️') : '🏠';
  tile.classList.remove('hidden');
  tile.innerHTML =
    `<span class="bb-icon">${emoji}</span>` +
    `<div class="bb-main"><div class="bb-value">${Math.round(t)}°</div>` +
    `<div class="bb-label">${isWeather ? s.state.replaceAll('-', ' ') : 'indoor'}</div></div>`;
}

// ---------------------------------------------------------------- lights tile

let lightsPendingUntil = 0; // optimistic "0 on" until an echo or timeout

function renderLights() {
  const tile = $('bb-lights');
  // only lights that belong to a room of the house — not every light.* in HA
  const all = [...getAllHouseLightIds()].filter((id) => getState(id));
  if (!all.length) { tile.classList.add('hidden'); return; }
  let n = all.filter((id) => isOn(id)).length;
  if (performance.now() < lightsPendingUntil) n = 0;
  tile.classList.remove('hidden');
  tile.classList.toggle('tappable', n > 0);
  tile.title = n ? 'Tap to turn all lights off' : 'All lights are off';
  tile.innerHTML =
    `<span class="bb-icon${n ? ' is-active' : ''}">💡</span>` +
    `<div class="bb-main"><div class="bb-value">${n}</div>` +
    `<div class="bb-label">light${n === 1 ? '' : 's'} on</div></div>`;
}

async function allLightsOff() {
  const on = [...getAllHouseLightIds()].filter((id) => getState(id) && isOn(id));
  if (!on.length) return;
  lightsPendingUntil = performance.now() + 4000;
  renderLights();
  setTimeout(renderLights, 4100); // reconcile from real state if echoes were lost
  const results = await Promise.allSettled(on.map((id) =>
    api.control({ entity_id: id, domain: 'light', service: 'turn_off' })));
  if (results.some((r) => r.status === 'rejected')) {
    lightsPendingUntil = 0;
    renderLights();
    showBanner('Some lights did not respond', 4000);
  }
}

// ---------------------------------------------------------------- security tile

const ALARM_LABELS = {
  disarmed: ['Disarmed', ''],
  armed_home: ['Armed home', ''],
  armed_away: ['Armed away', ''],
  armed_night: ['Armed night', ''],
  armed_vacation: ['Armed', ''],
  arming: ['Arming…', 'is-active'],
  pending: ['Pending…', 'is-active'],
  triggered: ['ALARM', 'is-alert'],
};

function renderSecurity() {
  const tile = $('bb-security');
  const alarms = findEntities('alarm_control_panel.');
  const locks = findEntities('lock.');
  if (!alarms.length && !locks.length) { tile.classList.add('hidden'); return; }
  tile.classList.remove('hidden');
  if (alarms.length) {
    const s = getState(alarms[0]);
    const [label, cls] = ALARM_LABELS[s?.state] || [s?.state ?? '—', ''];
    tile.innerHTML =
      `<span class="bb-icon ${cls}">🛡️</span>` +
      `<div class="bb-main"><div class="bb-value">${label}</div>` +
      `<div class="bb-label">security</div></div>`;
  } else {
    const unlocked = locks.filter((id) => getState(id)?.state === 'unlocked').length;
    const ok = unlocked === 0;
    tile.innerHTML =
      `<span class="bb-icon${ok ? '' : ' is-active'}">${ok ? '🔒' : '🔓'}</span>` +
      `<div class="bb-main"><div class="bb-value">${ok ? 'Locked' : `${unlocked} unlocked`}</div>` +
      `<div class="bb-label">door${locks.length === 1 ? '' : 's'}</div></div>`;
  }
}

// ---------------------------------------------------------------- climate tile

function pickClimate() {
  for (const id of findEntities('climate.')) {
    if (getState(id)?.attributes?.temperature != null) return id;
  }
  return null;
}

function renderClimate() {
  const tile = $('bb-climate');
  const id = pickClimate();
  if (!id) { tile.classList.add('hidden'); return; }
  const a = getState(id).attributes;
  tile.classList.remove('hidden');
  tile.innerHTML =
    `<span class="bb-icon">🌡️</span>` +
    `<div class="bb-main"><div class="bb-value">${a.temperature}°</div>` +
    `<div class="bb-label">thermostat</div></div>` +
    `<div class="bb-steppers">` +
    `<button type="button" data-dir="-1" title="Lower target">−</button>` +
    `<button type="button" data-dir="1" title="Raise target">+</button></div>`;
  tile.querySelectorAll('.bb-steppers button').forEach((btn) => {
    btn.onclick = () => {
      const step = a.target_temp_step || 0.5;
      let next = a.temperature + Number(btn.dataset.dir) * step;
      if (a.min_temp != null) next = Math.max(a.min_temp, next);
      if (a.max_temp != null) next = Math.min(a.max_temp, next);
      next = Math.round(next * 10) / 10;
      tile.querySelector('.bb-value').textContent = `${next}°`; // optimistic
      api.control({ entity_id: id, domain: 'climate', service: 'set_temperature',
                    data: { temperature: next } })
        .catch((e) => showBanner(`Thermostat failed: ${e.message}`, 4000));
    };
  });
}

// ---------------------------------------------------------------- calendar tile

// Calendars are sparse, so look far ahead (past the 30-day default) to surface
// the next real event. Unlike the other tiles, this data isn't in the live
// state stream — it's fetched over HTTP and refreshed on a slow timer.
const CAL_HORIZON_DAYS = 180;
const CAL_REFRESH_MS = 15 * 60_000;
let calEvents = [];

// All-day events carry a bare "YYYY-MM-DD" (no zone) — build it in local time so
// it doesn't slip a day; timed events carry a full ISO string with an offset.
function eventStart(ev) {
  if (ev.all_day && /^\d{4}-\d{2}-\d{2}$/.test(ev.start)) {
    const [y, m, d] = ev.start.split('-').map(Number);
    return new Date(y, m - 1, d);
  }
  return new Date(ev.start);
}

function calDayDiff(date) {
  const a = new Date(); a.setHours(0, 0, 0, 0);
  const b = new Date(date); b.setHours(0, 0, 0, 0);
  return Math.round((b - a) / 86_400_000);
}

function formatWhen(ev) {
  const d = eventStart(ev);
  const diff = calDayDiff(d);
  let day;
  if (diff === 0) day = 'Today';
  else if (diff === 1) day = 'Tomorrow';
  else if (diff > 1 && diff < 7) day = d.toLocaleDateString([], { weekday: 'long' });
  else day = d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  if (ev.all_day) return day;
  return `${day} · ${d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
}

function renderCalendar() {
  const tile = $('bb-calendar');
  const next = calEvents[0];
  if (!next) { tile.classList.add('hidden'); closeCalPopover(); return; }
  tile.classList.remove('hidden');
  const more = calEvents.length - 1;
  tile.title = more > 0 ? `Tap for ${calEvents.length} upcoming events` : 'Next event';
  tile.innerHTML =
    `<span class="bb-icon">📅</span>` +
    `<div class="bb-main"><div class="bb-value">${escapeHtml(next.summary)}</div>` +
    `<div class="bb-label">${escapeHtml(formatWhen(next))}</div></div>`;
  if (!$('cal-popover').classList.contains('hidden')) renderCalPopover();
}

async function refreshCalendar() {
  try {
    const data = await api.getCalendar(CAL_HORIZON_DAYS);
    calEvents = data?.events || [];
  } catch {
    calEvents = []; // HA not configured / unreachable → tile just hides
  }
  renderCalendar();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

// -------- upcoming-events popover

function renderCalPopover() {
  const pop = $('cal-popover');
  pop.innerHTML =
    `<div class="cal-pop-head">Upcoming</div>` +
    calEvents.slice(0, 8).map((ev) =>
      `<div class="cal-row"><span class="cal-when">${escapeHtml(formatWhen(ev))}</span>` +
      `<span class="cal-summary">${escapeHtml(ev.summary)}</span></div>`).join('');
}

function openCalPopover() {
  const pop = $('cal-popover');
  renderCalPopover();
  pop.classList.remove('hidden');
  // anchor above the tile
  const r = $('bb-calendar').getBoundingClientRect();
  pop.style.left = `${Math.round(r.left)}px`;
  pop.style.bottom = `${Math.round(window.innerHeight - r.top + 10)}px`;
}

function closeCalPopover() { $('cal-popover').classList.add('hidden'); }

function toggleCalPopover() {
  if ($('cal-popover').classList.contains('hidden')) openCalPopover();
  else closeCalPopover();
}

// ---------------------------------------------------------------- init

export function initDashboard() {
  renderClock();
  setInterval(renderClock, 15_000);

  $('home-btn').onclick = () => {
    exitFocus();
    if (getLevel() !== 'all') setLevel('all');
  };
  $('bb-lights').onclick = allLightsOff;

  refreshCalendar();
  setInterval(refreshCalendar, CAL_REFRESH_MS);
  $('bb-calendar').onclick = (e) => { e.stopPropagation(); toggleCalPopover(); };
  // dismiss the popover on any outside click or Esc
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#cal-popover, #bb-calendar')) closeCalPopover();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeCalPopover(); });

  // ambient chrome yields to the focus panel while a room is focused
  onFocusChanged((roomId) => {
    document.body.classList.toggle('room-focused', roomId !== null);
  });

  onStateApplied((entityId) => {
    if (entityId === null) { // bulk load / reconnect: (re)pick entities
      renderTemp(); renderLights();
      renderSecurity(); renderClimate();
      refreshCalendar(); // HA may have just connected after our first attempt
      return;
    }
    if (entityId.startsWith('light.')) {
      if (isOn(entityId)) lightsPendingUntil = 0; // external turn-on wins
      renderLights();
    } else if (entityId.startsWith('alarm_control_panel.')) {
      renderSecurity();
    } else if (entityId.startsWith('lock.')) {
      renderSecurity();
    } else if (entityId.startsWith('climate.')) {
      renderClimate(); renderTemp();
    } else if (entityId.startsWith('weather.')) {
      renderTemp();
    }
  });
}
