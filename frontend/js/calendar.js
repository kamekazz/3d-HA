// Calendar card in the left dashboard column: upcoming events across all HA
// calendars, fetched through the backend (/api/ha/calendar) since HA's
// calendar REST API needs the token. Refreshes every 15 min plus whenever the
// tab wakes from a stale background (tablets sleep — intervals don't fire
// while hidden). Hides itself quietly when HA has no calendars (or no HA).
import { api } from './api.js';

const REFRESH_MS = 15 * 60_000;
const STALE_MS = 5 * 60_000;
const MAX_EVENTS = 5;

// per-calendar dot tints, assigned by calendar index (stable per fetch)
const CAL_TINTS = ['#4c9ee8', '#35c26a', '#e0b100', '#b083e8', '#e07b5f'];

let lastFetch = 0;

// HA all-day events use plain "YYYY-MM-DD" — new Date('YYYY-MM-DD') parses as
// UTC midnight and renders as *yesterday* evening in the Americas, so split.
function parseStart(ev) {
  if (ev.all_day) {
    const [y, m, d] = ev.start.split('T')[0].split('-').map(Number);
    return new Date(y, m - 1, d);
  }
  return new Date(ev.start);
}

function dayLabel(date) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const day = new Date(date);
  day.setHours(0, 0, 0, 0);
  const diff = Math.round((day - today) / 86_400_000);
  if (diff <= 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff < 7) return date.toLocaleDateString([], { weekday: 'long' });
  return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

function render(data) {
  const card = document.getElementById('calendar-card');
  const list = document.getElementById('cal-list');
  card.classList.remove('hidden');
  list.innerHTML = '';

  const tintByCal = new Map();
  (data.calendars || []).forEach((c, i) =>
    tintByCal.set(c.entity_id, CAL_TINTS[i % CAL_TINTS.length]));

  const events = (data.events || []).slice(0, MAX_EVENTS);
  if (!events.length) {
    const empty = document.createElement('div');
    empty.className = 'cal-empty muted';
    empty.textContent = 'No upcoming events';
    list.appendChild(empty);
    return;
  }

  let lastDay = null;
  for (const ev of events) {
    const start = parseStart(ev);
    const label = dayLabel(start);
    if (label !== lastDay) {
      lastDay = label;
      const day = document.createElement('div');
      day.className = 'cal-day';
      day.textContent = label;
      list.appendChild(day);
    }
    const row = document.createElement('div');
    row.className = 'cal-event';
    const dot = document.createElement('span');
    dot.className = 'cal-dot';
    dot.style.background = tintByCal.get(ev.calendar) || CAL_TINTS[0];
    const time = document.createElement('span');
    time.className = 'cal-time';
    time.textContent = ev.all_day ? 'all day'
      : start.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const title = document.createElement('span');
    title.className = 'cal-title';
    title.textContent = ev.summary; // external text — never innerHTML
    title.title = ev.summary;
    row.append(dot, time, title);
    list.appendChild(row);
  }
}

async function refresh() {
  const card = document.getElementById('calendar-card');
  try {
    const data = await api.getCalendar(31); // sparse home calendars — look a month out
    lastFetch = Date.now();
    if (!data?.calendars?.length) {
      card.classList.add('hidden');
      return;
    }
    render(data);
  } catch {
    // HA unconfigured (503) or unreachable (502) — no card, no noise
    card.classList.add('hidden');
  }
}

export function initCalendar() {
  refresh();
  setInterval(refresh, REFRESH_MS);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && Date.now() - lastFetch > STALE_MS) refresh();
  });
}
