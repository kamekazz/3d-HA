// SocketIO client for live state updates, with a polling fallback.
import { api } from './api.js';

let pollTimer = null;

function startPolling(onBulkStates, onStatus) {
  if (pollTimer) return;
  onStatus('polling');
  pollTimer = setInterval(async () => {
    try {
      const states = await api.getStates();
      if (Array.isArray(states)) onBulkStates(states);
    } catch { onStatus('offline'); }
  }, 5000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

export function connectRealtime({ onStateChanged, onBulkStates, onStatus }) {
  if (typeof io === 'undefined') {
    // socket.io CDN blocked/unavailable — fall back to polling only
    startPolling(onBulkStates, onStatus);
    return;
  }
  const socket = io();
  socket.on('connect', () => { stopPolling(); onStatus('connected'); });
  socket.on('disconnect', () => startPolling(onBulkStates, onStatus));
  socket.on('connect_error', () => startPolling(onBulkStates, onStatus));
  socket.on('state_changed', (msg) => {
    if (msg?.entity_id) onStateChanged(msg.entity_id, msg.new_state);
  });
}
