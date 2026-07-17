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
    `<span class="bb-icon" style="background:rgba(43,108,176,.35)">${emoji}</span>` +
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
    `<span class="bb-icon" style="background:${n ? 'rgba(224,177,0,.35)' : 'rgba(255,255,255,.08)'}">💡</span>` +
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
  disarmed: ['Disarmed', 'rgba(255,255,255,.08)'],
  armed_home: ['Armed home', 'rgba(53,194,106,.3)'],
  armed_away: ['Armed away', 'rgba(53,194,106,.3)'],
  armed_night: ['Armed night', 'rgba(53,194,106,.3)'],
  armed_vacation: ['Armed', 'rgba(53,194,106,.3)'],
  arming: ['Arming…', 'rgba(224,177,0,.3)'],
  pending: ['Pending…', 'rgba(224,177,0,.3)'],
  triggered: ['ALARM', 'rgba(214,69,69,.45)'],
};

function renderSecurity() {
  const tile = $('bb-security');
  const alarms = findEntities('alarm_control_panel.');
  const locks = findEntities('lock.');
  if (!alarms.length && !locks.length) { tile.classList.add('hidden'); return; }
  tile.classList.remove('hidden');
  if (alarms.length) {
    const s = getState(alarms[0]);
    const [label, tint] = ALARM_LABELS[s?.state] || [s?.state ?? '—', 'rgba(255,255,255,.08)'];
    tile.innerHTML =
      `<span class="bb-icon" style="background:${tint}">🛡️</span>` +
      `<div class="bb-main"><div class="bb-value">${label}</div>` +
      `<div class="bb-label">security</div></div>`;
  } else {
    const unlocked = locks.filter((id) => getState(id)?.state === 'unlocked').length;
    const ok = unlocked === 0;
    tile.innerHTML =
      `<span class="bb-icon" style="background:${ok ? 'rgba(53,194,106,.3)' : 'rgba(224,177,0,.3)'}">${ok ? '🔒' : '🔓'}</span>` +
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
    `<span class="bb-icon" style="background:rgba(155,44,44,.35)">🌡️</span>` +
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

// ---------------------------------------------------------------- init

export function initDashboard() {
  renderClock();
  setInterval(renderClock, 15_000);

  $('home-btn').onclick = () => {
    exitFocus();
    if (getLevel() !== 'all') setLevel('all');
  };
  $('bb-lights').onclick = allLightsOff;

  // ambient chrome yields to the focus panel while a room is focused
  onFocusChanged((roomId) => {
    document.body.classList.toggle('room-focused', roomId !== null);
  });

  onStateApplied((entityId) => {
    if (entityId === null) { // bulk load / reconnect: (re)pick entities
      renderTemp(); renderLights();
      renderSecurity(); renderClimate();
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
