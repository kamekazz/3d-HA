// App-wide undo/redo: buttons in the 3D topbar and the planner topbar, plus
// Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z. The backend owns the history (full layout
// snapshots per edit); this module just triggers undo/redo and re-fetches.
// Note: other browser tabs won't see an undo until their next reload — there
// is no layout-change relay over SocketIO (only state_changed).
import { api, onLayoutMutation } from './api.js';
import { canEdit } from './route.js';

const UNDO_BTNS = ['btn-undo', 'pl-undo'];
const REDO_BTNS = ['btn-redo', 'pl-redo'];

let refreshFn = null; // context: reloadHouse (3D) or the planner's rehydrate
let busy = false;     // a held-down Ctrl+Z must not overlap undo calls

// Swap the post-undo refresh handler (planner does this while open).
// Returns the previous handler so the caller can restore it.
export function setUndoHandler(fn) {
  const prev = refreshFn;
  refreshFn = fn;
  return prev;
}

function paint({ can_undo, can_redo }) {
  for (const id of UNDO_BTNS) {
    const el = document.getElementById(id);
    if (el) el.disabled = !can_undo;
  }
  for (const id of REDO_BTNS) {
    const el = document.getElementById(id);
    if (el) el.disabled = !can_redo;
  }
}

export async function refreshUndoUI() {
  try { paint(await api.getHistory()); } catch { /* backend unreachable */ }
}

async function run(action) {
  if (busy) return;
  busy = true;
  try {
    const res = await action(); // {ok, can_undo, can_redo}
    paint(res);
    if (res.ok) await refreshFn?.();
  } catch (e) {
    console.warn('undo/redo failed:', e);
  } finally {
    busy = false;
  }
}

export function initUndo({ defaultRefresh }) {
  if (!canEdit) return; // no editing on the viewer, so no undo/redo either
  refreshFn = defaultRefresh;
  for (const id of UNDO_BTNS) {
    const el = document.getElementById(id);
    if (el) el.onclick = () => run(api.undo);
  }
  for (const id of REDO_BTNS) {
    const el = document.getElementById(id);
    if (el) el.onclick = () => run(api.redo);
  }
  window.addEventListener('keydown', (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    const tag = document.activeElement?.tagName;
    // typing: browser-native text-field undo wins
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    const k = e.key.toLowerCase();
    if (k === 'z' && !e.shiftKey) { e.preventDefault(); run(api.undo); }
    else if (k === 'y' || (k === 'z' && e.shiftKey)) { e.preventDefault(); run(api.redo); }
  });
  onLayoutMutation(refreshUndoUI);
  refreshUndoUI();
}
