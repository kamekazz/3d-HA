// Fetch wrappers to the Flask backend. The browser only ever talks to Flask.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  let body = null;
  try { body = await res.json(); } catch { /* no body */ }
  if (!res.ok) {
    const err = new Error(body?.error || `${res.status} ${res.statusText}`);
    err.status = res.status;
    err.detail = body?.detail;
    throw err;
  }
  return body;
}

const get = (p) => request(p);
const post = (p, data) => request(p, { method: 'POST', body: JSON.stringify(data ?? {}) });
const patch = (p, data) => request(p, { method: 'PATCH', body: JSON.stringify(data ?? {}) });
const del = (p) => request(p, { method: 'DELETE' });

export const api = {
  getStructure: () => get('/api/ha/structure'),
  getStates: () => get('/api/ha/states'),
  getStatus: () => get('/api/ha/status'),
  refreshHA: () => post('/api/ha/refresh'),

  getHouse: () => get('/api/house'),
  generateHouse: () => post('/api/house/generate'),
  syncHouse: () => post('/api/house/sync'),
  createRoom: (data) => post('/api/house/room', data),
  updateRoom: (id, data) => patch(`/api/house/room/${id}`, data),
  deleteRoom: (id) => del(`/api/house/room/${id}`),
  placeDevice: (roomId, data) => post(`/api/house/room/${roomId}/device`, data),
  updatePlacement: (id, data) => patch(`/api/house/device/${id}`, data),
  deletePlacement: (id) => del(`/api/house/device/${id}`),

  control: (payload) => post('/api/control', payload),
};
