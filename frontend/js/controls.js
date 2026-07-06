// Shared per-domain control builders + per-entity camera views, used by both
// the device detail panel (ui.js) and the room focus panel (roompanel.js).
import { api } from './api.js';
import { getState, stateLabel, isOn, friendlyName } from './state.js';

const SNAPSHOT_REFRESH_MS = 10000;

let sliderActive = false; // block panel re-renders while a slider is being dragged

export function isSliderActive() {
  return sliderActive;
}

function debounce(fn, ms) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

// ---------------------------------------------------------------- controls

// Renders the control widgets for an entity into `container`.
// compact: fewer buttons so controls fit inside a room-panel tile.
// onError: called with a message when a service call fails.
export function renderControls(container, entityId, { compact = false, onError } = {}) {
  const s = getState(entityId);
  const a = s?.attributes || {};
  const domain = entityId.split('.')[0];

  const call = (service, data) =>
    api.control({ entity_id: entityId, domain, service, ...(data ? { data } : {}) })
      .catch((e) => onError?.(`Control failed: ${e.message}`));

  const svc = (label, service, cls = '') => {
    const btn = document.createElement('button');
    btn.textContent = label;
    if (cls) btn.className = cls;
    btn.onclick = async () => {
      btn.disabled = true;
      await call(service);
      btn.disabled = false;
    };
    container.appendChild(btn);
  };

  // labeled range input; keeps sliderActive true while dragging so live HA
  // echoes don't rebuild the panel under the user's thumb
  const slider = ({ label, min, max, step = 1, value, format, onCommit }) => {
    const wrap = document.createElement('div');
    wrap.className = 'dp-slider';
    const head = document.createElement('div');
    head.className = 'dp-slider-head';
    const lab = document.createElement('span');
    lab.textContent = label;
    const val = document.createElement('span');
    val.className = 'val';
    val.textContent = format(Number(value));
    head.append(lab, val);
    const inp = document.createElement('input');
    inp.type = 'range';
    inp.min = min; inp.max = max; inp.step = step; inp.value = value;
    const send = debounce(onCommit, 250);
    inp.addEventListener('pointerdown', () => { sliderActive = true; });
    inp.addEventListener('input', () => {
      const v = Number(inp.value);
      val.textContent = format(v);
      send(v);
    });
    const release = () => { sliderActive = false; };
    inp.addEventListener('pointerup', release);
    inp.addEventListener('pointercancel', release);
    inp.addEventListener('change', release);
    wrap.append(head, inp);
    container.appendChild(wrap);
  };

  // big live readout for pure data entities
  if (domain === 'sensor' || domain === 'binary_sensor') {
    const big = document.createElement('div');
    big.className = 'dp-bigvalue';
    big.textContent = stateLabel(entityId);
    if (a.device_class) {
      const sub = document.createElement('span');
      sub.textContent = a.device_class.replaceAll('_', ' ');
      big.appendChild(sub);
    }
    container.appendChild(big);
  }

  if (['light', 'switch', 'fan', 'input_boolean'].includes(domain)) {
    svc(isOn(entityId) ? 'Turn off' : 'Turn on', 'toggle');
    if (!compact) {
      svc('On', 'turn_on', 'secondary');
      svc('Off', 'turn_off', 'secondary');
    }
    if (domain === 'light' && isOn(entityId) && a.brightness != null) {
      slider({
        label: 'Brightness', min: 1, max: 255, value: a.brightness,
        format: (v) => `${Math.round((v / 255) * 100)}%`,
        onCommit: (v) => call('turn_on', { brightness: v }),
      });
    }
    if (domain === 'light' && isOn(entityId) && a.color_temp_kelvin != null &&
        a.min_color_temp_kelvin != null && a.max_color_temp_kelvin != null) {
      slider({
        label: 'Color temp', min: a.min_color_temp_kelvin, max: a.max_color_temp_kelvin,
        step: 50, value: a.color_temp_kelvin,
        format: (v) => `${v} K`,
        onCommit: (v) => call('turn_on', { color_temp_kelvin: v }),
      });
    }
  } else if (domain === 'cover') {
    svc('Open', 'open_cover');
    svc('Close', 'close_cover', 'secondary');
    svc('Stop', 'stop_cover', 'secondary');
    if (a.current_position != null) {
      slider({
        label: 'Position', min: 0, max: 100, value: a.current_position,
        format: (v) => `${v}%`,
        onCommit: (v) => call('set_cover_position', { position: v }),
      });
    }
  } else if (domain === 'lock') {
    svc('Lock', 'lock');
    svc('Unlock', 'unlock', 'secondary');
  } else if (domain === 'media_player') {
    svc('Play/Pause', 'media_play_pause');
    svc('⏮', 'media_previous_track', 'secondary');
    svc('⏭', 'media_next_track', 'secondary');
    if (a.volume_level != null) {
      slider({
        label: 'Volume', min: 0, max: 1, step: 0.01, value: a.volume_level,
        format: (v) => `${Math.round(v * 100)}%`,
        onCommit: (v) => call('volume_set', { volume_level: v }),
      });
    }
  } else if (domain === 'climate') {
    if (a.temperature != null) {
      const row = document.createElement('div');
      row.className = 'dp-temp';
      const step = a.target_temp_step || 0.5;
      const mkStep = (label, dir) => {
        const btn = document.createElement('button');
        btn.className = 'secondary';
        btn.textContent = label;
        btn.onclick = () => {
          let next = a.temperature + dir * step;
          if (a.min_temp != null) next = Math.max(a.min_temp, next);
          if (a.max_temp != null) next = Math.min(a.max_temp, next);
          call('set_temperature', { temperature: Math.round(next * 10) / 10 });
        };
        return btn;
      };
      const readout = document.createElement('span');
      readout.className = 'dp-temp-value';
      readout.textContent = `${a.temperature}°`;
      row.append(mkStep('−', -1), readout, mkStep('+', 1));
      container.appendChild(row);
    }
    if (Array.isArray(a.hvac_modes)) {
      const chips = document.createElement('div');
      chips.className = 'dp-chips';
      for (const mode of a.hvac_modes) {
        const chip = document.createElement('button');
        chip.className = 'chip' + (s?.state === mode ? ' active' : '');
        chip.textContent = mode.replaceAll('_', '/');
        chip.onclick = () => call('set_hvac_mode', { hvac_mode: mode });
        chips.appendChild(chip);
      }
      container.appendChild(chips);
    }
  } else if (domain === 'script' || domain === 'scene') {
    svc('Run', 'turn_on');
  }
}

// ---------------------------------------------------------------- camera view

// A self-contained camera <img> with its own snapshot timer / MJPEG stream,
// so any number of cameras can be shown at once. In snapshot mode the image
// refreshes every 10s; in live mode the <img> holds an MJPEG connection
// (one backend worker thread each) until destroy() blanks the src.
export function createCameraView(entityId, { live = false, onError } = {}) {
  const el = document.createElement('div');
  el.className = 'cam-view';
  const img = document.createElement('img');
  img.alt = `Camera: ${friendlyName(entityId)}`;
  const hint = document.createElement('span');
  hint.className = 'cam-hint muted hidden';
  hint.textContent = 'starting live stream…';
  el.append(img, hint);

  let isLive = false;
  let key = null;   // `${entityId}|${isLive}` applied to the <img>
  let timer = null; // snapshot refresh interval

  const snap = () => { img.src = `/api/camera/${entityId}/snapshot?t=${Date.now()}`; };
  img.onload = () => hint.classList.add('hidden');
  img.onerror = () => {
    hint.classList.add('hidden');
    if (isLive) {
      // stream refused (e.g. too many simultaneous streams over Nabu Casa) —
      // fall back to snapshot polling instead of leaving a dead tile
      onError?.(`Live stream failed for ${friendlyName(entityId)} — showing snapshots`);
      isLive = false;
      apply();
      view.onModeChange?.(false);
    } else {
      // Nabu Casa drops connections in short bursts — retry sooner than the
      // regular interval, but only while this view is still current
      const k = key;
      setTimeout(() => { if (key === k && !isLive) snap(); }, 2500);
    }
  };

  // Idempotent per mode: repeated calls must not touch the <img>, or the
  // MJPEG stream would reconnect on every state echo.
  const apply = () => {
    const k = `${entityId}|${isLive}`;
    if (key === k) return;
    key = k;
    clearInterval(timer);
    timer = null;
    if (isLive) {
      hint.classList.remove('hidden'); // HA spins up ffmpeg — first frame takes a few seconds
      img.src = `/api/camera/${entityId}/stream?t=${Date.now()}`;
    } else {
      hint.classList.add('hidden');
      snap();
      timer = setInterval(snap, SNAPSHOT_REFRESH_MS);
    }
  };

  const view = {
    el,
    entityId,
    onModeChange: null, // set by the owner to keep its live/pause button in sync
    isLive: () => isLive,
    setLive(v) {
      isLive = !!v;
      apply();
    },
    destroy() {
      clearInterval(timer);
      timer = null;
      key = null;
      img.onload = null;
      img.onerror = null;
      img.src = ''; // aborts an in-flight MJPEG connection
      img.removeAttribute('src');
      el.remove();
    },
  };
  view.setLive(live);
  return view;
}
