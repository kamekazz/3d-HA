// Per-floor 2D floor-plan editor (top-down, feet). Draw rooms as rectangles,
// carve them into rectilinear polygons by dragging edges/vertices, drag whole
// rooms, and assign HA areas. Persists through the existing room endpoints;
// the 3D scene is rebuilt once, when the planner closes.
import { api } from './api.js';
import { getLevel } from './house.js';
import { fillTextureSelect } from './textures.js';
import { setUndoHandler } from './undo.js';

const $ = (id) => document.getElementById(id);

const PALETTE = ['#8fa8bf', '#b98fbf', '#8fbf9c', '#bfae8f',
                 '#bf8f8f', '#8fbfbd', '#a3bf8f', '#9a8fbf'];
const HANDLE_PX = 8;   // vertex handle size
const MID_PX = 6;      // edge-midpoint handle size
const HIT_PX = 7;      // edge hit tolerance
const MIN_ROOM_FT = 1.5;

let getStructure = () => null;
let onCloseCb = null;

let canvas, ctx;
let isOpen = false;
let house = null;          // planner's own copy of /api/house
let activeFloorId = null;
let mode = 'select';       // 'select' | 'draw' | 'draw-stairs'
let selectedRoomId = null;
let selectedStairId = null;
let selectedVertex = null; // vertex index in the selected room's polygon
let drag = null;           // transient gesture state
let lastPointerDownTime = 0; // manual double-click tracking
let spaceHeld = false;
let view = { x: -5, z: -5, pxPerFt: 14 }; // world coords of top-left + zoom

// floor-plan tracing image (per floor, drawn under the grid)
const planImages = new Map(); // floorId -> HTMLImageElement
let imgOpacity = 0.4;
let moveImage = false; // "Move image" toggle: empty-canvas drags slide the image

// ------------------------------------------------------------------ helpers

const snapStep = () => Number($('pl-snap').value) || 0.5;
const snap = (v, bypass) => bypass ? v : Math.round(v / snapStep()) * snapStep();
const round2 = (v) => Math.round(v * 100) / 100;

function worldToScreen(wx, wz) {
  return { x: (wx - view.x) * view.pxPerFt, y: (wz - view.z) * view.pxPerFt };
}
function screenToWorld(px, py) {
  return { x: view.x + px / view.pxPerFt, z: view.z + py / view.pxPerFt };
}

function floorsSorted() {
  return [...(house?.floors || [])].sort((a, b) => a.level - b.level);
}
function activeFloor() {
  return (house?.floors || []).find((f) => f.id === activeFloorId) || null;
}
function activeRooms() {
  return activeFloor()?.rooms || [];
}
function selectedRoom() {
  return activeRooms().find((r) => r.id === selectedRoomId) || null;
}

function floorBelowActive() {
  const sorted = floorsSorted();
  const i = sorted.findIndex((f) => f.id === activeFloorId);
  return i > 0 ? sorted[i - 1] : null;
}

// stairs visible on this tab: ones starting here (going up) and ones coming
// up from the floor below (going down from here)
function activeStairs() {
  const own = (activeFloor()?.stairs || []).map((st) => ({ st, up: true }));
  const below = (floorBelowActive()?.stairs || []).map((st) => ({ st, up: false }));
  return [...own, ...below];
}

function selectedStair() {
  return activeStairs().find(({ st }) => st.id === selectedStairId)?.st || null;
}

function stairRect(st) {
  return [[st.x, st.z], [st.x + st.width, st.z],
          [st.x + st.width, st.z + st.depth], [st.x, st.z + st.depth]];
}

// working polygon: absolute world [x, z] vertices, derived once per load
function absPoly(room) {
  const fp = room.footprint;
  const rel = fp.points || [[0, 0], [fp.width, 0], [fp.width, fp.depth], [0, fp.depth]];
  return rel.map(([px, pz]) => [fp.x + px, fp.z + pz]);
}

function bboxOf(pts) {
  const xs = pts.map((p) => p[0]), zs = pts.map((p) => p[1]);
  const minX = Math.min(...xs), minZ = Math.min(...zs);
  return { minX, minZ, w: Math.max(...xs) - minX, h: Math.max(...zs) - minZ };
}

function signedArea(pts) {
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x1, z1] = pts[i], [x2, z2] = pts[(i + 1) % pts.length];
    a += x1 * z2 - x2 * z1;
  }
  return a / 2;
}

function pointInPolygon([px, pz], pts) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, zi] = pts[i], [xj, zj] = pts[j];
    if ((zi > pz) !== (zj > pz)
        && px < ((xj - xi) * (pz - zi)) / (zj - zi) + xi) inside = !inside;
  }
  return inside;
}

function distToSegment(p, a, b) {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  const len2 = dx * dx + dz * dz;
  let t = len2 ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / len2 : 0;
  t = Math.max(0, Math.min(1, t));
  const cx = a[0] + t * dx, cz = a[1] + t * dz;
  return { d: Math.hypot(p[0] - cx, p[1] - cz), t, x: cx, z: cz };
}

function segmentsCross(a, b, c, d) {
  const orient = (p, q, r) => {
    const v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
    return Math.abs(v) < 1e-12 ? 0 : (v > 0 ? 1 : -1);
  };
  const o1 = orient(a, b, c), o2 = orient(a, b, d);
  const o3 = orient(c, d, a), o4 = orient(c, d, b);
  return o1 !== o2 && o3 !== o4 && o1 !== 0 && o2 !== 0 && o3 !== 0 && o4 !== 0;
}

function isSelfIntersecting(pts) {
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if ((j + 1) % n === i || (i + 1) % n === j) continue; // adjacent
      if (segmentsCross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n])) return true;
    }
  }
  return false;
}

function isAxisAlignedRect(pts) {
  if (pts.length !== 4) return false;
  for (let i = 0; i < 4; i++) {
    const [x1, z1] = pts[i], [x2, z2] = pts[(i + 1) % 4];
    if (Math.abs(x1 - x2) > 1e-9 && Math.abs(z1 - z2) > 1e-9) return false;
  }
  const bb = bboxOf(pts);
  return Math.abs(Math.abs(signedArea(pts)) - bb.w * bb.h) < 1e-6;
}

function areaName(areaId) {
  const structure = getStructure();
  if (!structure || !areaId) return null;
  for (const f of structure.floors || []) {
    const a = (f.areas || []).find((a) => a.area_id === areaId);
    if (a) return a.name;
  }
  return areaId;
}

function setStatus(msg) {
  $('pl-status').dataset.msg = msg || '';
  renderStatus();
}
function renderStatus(cursor) {
  const parts = [];
  if (cursor) parts.push(`${cursor.x.toFixed(1)} ft, ${cursor.z.toFixed(1)} ft`);
  const msg = $('pl-status').dataset.msg;
  if (msg) parts.push(msg);
  else if (mode === 'draw') parts.push('Drag to draw a room · Esc to cancel');
  else if (mode === 'draw-stairs') parts.push('Drag out the stairwell — stairs connect down to the floor below · Esc to cancel');
  else if (selectedStair()) parts.push('Drag to move · corners resize · arrow select sets which way they go up · Del removes');
  else if (selectedRoom()) parts.push('Drag corners/edges to reshape · Dbl-click an edge to add a corner · Dbl-click or Del a corner to remove');
  else parts.push('Click a room to edit · "+ Draw room" to add one · drag to pan, wheel to zoom');
  $('pl-status').textContent = parts.join('  ·  ');
}

// ------------------------------------------------------------------ persist

async function persistStair(st) {
  const payload = { floor_id: st.floor_id, name: st.name || 'Stairs',
                    x: round2(st.x), z: round2(st.z),
                    width: round2(st.width), depth: round2(st.depth),
                    direction: st.direction };
  try {
    if (st.id) {
      await api.updateStairs(st.id, payload);
    } else {
      const res = await api.createStairs(payload);
      st.id = res.id;
    }
    setStatus('');
  } catch (err) {
    setStatus(`Save failed: ${err.message}`);
  }
}

async function persistRoom(room) {
  const pts = room._poly;
  const bb = bboxOf(pts);
  const rect = isAxisAlignedRect(pts);
  const payload = {
    name: room.name,
    ha_area_id: room.ha_area_id || null,
    floor_id: room.floor_id,
    height: room.height,
    color: room.color,
    // full payload per gesture: omitting these would revert appearance edits
    // on the next drag (undefined keys are fine — JSON drops them)
    wall_color: room.wall_color,
    wall_texture: room.wall_texture || null,
    floor_color: room.floor_color,
    floor_texture: room.floor_texture || null,
    footprint: {
      x: round2(bb.minX), z: round2(bb.minZ),
      width: round2(bb.w), depth: round2(bb.h),
      points: rect ? null
        : pts.map(([x, z]) => [round2(x - bb.minX), round2(z - bb.minZ)]),
    },
  };
  try {
    if (room.id) {
      await api.updateRoom(room.id, payload);
    } else {
      const res = await api.createRoom(payload);
      room.id = res.id;
      if (selectedRoomId === null) selectedRoomId = res.id;
    }
    room.footprint = payload.footprint;
    setStatus('');
  } catch (err) {
    setStatus(`Save failed: ${err.message}`);
  }
}

// ------------------------------------------------------------------ drawing

function resizeCanvas() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function fitView() {
  const rooms = activeRooms();
  let bb = { minX: 0, minZ: 0, w: 40, h: 30 };
  if (rooms.length) {
    const all = rooms.flatMap((r) => r._poly);
    bb = bboxOf(all);
  }
  const cw = canvas.clientWidth, ch = canvas.clientHeight;
  view.pxPerFt = Math.max(2, Math.min(
    (cw * 0.8) / Math.max(bb.w, 10), (ch * 0.8) / Math.max(bb.h, 10), 40));
  view.x = bb.minX + bb.w / 2 - cw / 2 / view.pxPerFt;
  view.z = bb.minZ + bb.h / 2 - ch / 2 / view.pxPerFt;
}

function drawGrid() {
  const cw = canvas.clientWidth, ch = canvas.clientHeight;
  const x0 = Math.floor(view.x), z0 = Math.floor(view.z);
  const x1 = Math.ceil(view.x + cw / view.pxPerFt);
  const z1 = Math.ceil(view.z + ch / view.pxPerFt);
  const drawLines = (step, style) => {
    ctx.strokeStyle = style;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = Math.ceil(x0 / step) * step; x <= x1; x += step) {
      const s = worldToScreen(x, 0).x;
      ctx.moveTo(s, 0); ctx.lineTo(s, ch);
    }
    for (let z = Math.ceil(z0 / step) * step; z <= z1; z += step) {
      const s = worldToScreen(0, z).y;
      ctx.moveTo(0, s); ctx.lineTo(cw, s);
    }
    ctx.stroke();
  };
  if (view.pxPerFt >= 6) drawLines(1, '#1c232d');   // 1 ft minor lines
  drawLines(5, '#2a3340');                           // 5 ft major lines
}

function drawRoom(room, isSel) {
  const pts = room._poly;
  if (!pts?.length) return;
  ctx.beginPath();
  pts.forEach(([x, z], i) => {
    const s = worldToScreen(x, z);
    i ? ctx.lineTo(s.x, s.y) : ctx.moveTo(s.x, s.y);
  });
  ctx.closePath();
  const bad = drag?.room === room && drag.invalid;
  ctx.fillStyle = room.color || '#8fa8bf';
  ctx.globalAlpha = isSel ? 0.35 : 0.2;
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = bad ? '#d64545' : (room.color || '#8fa8bf');
  ctx.lineWidth = isSel ? 2.5 : 1.5;
  ctx.stroke();

  // name + linked HA area at the bbox center
  const bb = bboxOf(pts);
  const c = worldToScreen(bb.minX + bb.w / 2, bb.minZ + bb.h / 2);
  ctx.textAlign = 'center';
  ctx.fillStyle = '#e6e9ee';
  ctx.font = '600 13px system-ui, sans-serif';
  ctx.fillText(room.name, c.x, c.y - 2);
  const area = areaName(room.ha_area_id);
  ctx.fillStyle = '#8b95a5';
  ctx.font = '11px system-ui, sans-serif';
  ctx.fillText(area || 'no HA area', c.x, c.y + 13);

  // device placement dots (red when outside the room's shape)
  const fp = room.footprint;
  for (const dev of room.devices || []) {
    const wx = fp.x + dev.position.x, wz = fp.z + dev.position.z;
    const s = worldToScreen(wx, wz);
    ctx.beginPath();
    ctx.arc(s.x, s.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = pointInPolygon([wx, wz], pts) ? '#4a9eff' : '#d64545';
    ctx.fill();
  }

  if (!isSel) return;
  // vertex handles (squares) + edge midpoint handles (hollow)
  for (let i = 0; i < pts.length; i++) {
    const s = worldToScreen(pts[i][0], pts[i][1]);
    ctx.fillStyle = i === selectedVertex ? '#e0b100' : '#e6e9ee';
    ctx.strokeStyle = '#2b6cb0';
    ctx.lineWidth = 1.5;
    ctx.fillRect(s.x - HANDLE_PX / 2, s.y - HANDLE_PX / 2, HANDLE_PX, HANDLE_PX);
    ctx.strokeRect(s.x - HANDLE_PX / 2, s.y - HANDLE_PX / 2, HANDLE_PX, HANDLE_PX);
  }
  for (let i = 0; i < pts.length; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[(i + 1) % pts.length];
    const s = worldToScreen((ax + bx) / 2, (az + bz) / 2);
    ctx.beginPath();
    ctx.arc(s.x, s.y, MID_PX / 2 + 1, 0, Math.PI * 2);
    ctx.fillStyle = '#161b23';
    ctx.fill();
    ctx.strokeStyle = '#2b6cb0';
    ctx.stroke();
  }
}

function drawPlanImage() {
  const floor = activeFloor();
  const img = floor && planImages.get(floor.id);
  if (!img?.complete || !img.naturalWidth) return;
  const s = worldToScreen(floor.plan_x || 0, floor.plan_z || 0);
  const scale = (floor.plan_scale || 0.05) * view.pxPerFt; // ft/px -> screen px
  ctx.globalAlpha = imgOpacity;
  ctx.drawImage(img, s.x, s.y, img.naturalWidth * scale, img.naturalHeight * scale);
  ctx.globalAlpha = 1;
}

function drawStair({ st, up }, isSel) {
  const a = worldToScreen(st.x, st.z);
  const b = worldToScreen(st.x + st.width, st.z + st.depth);
  ctx.fillStyle = '#aab4c4';
  ctx.globalAlpha = 0.18;
  ctx.fillRect(a.x, a.y, b.x - a.x, b.y - a.y);
  ctx.globalAlpha = 1;
  ctx.strokeStyle = isSel ? '#e0b100' : '#aab4c4';
  ctx.lineWidth = isSel ? 2.5 : 1.5;
  ctx.strokeRect(a.x, a.y, b.x - a.x, b.y - a.y);

  // treads perpendicular to the ascent axis
  const alongX = st.direction === 'e' || st.direction === 'w';
  const run = alongX ? st.width : st.depth;
  const treads = Math.max(2, Math.round(run / 1)); // ~1 ft per tread line
  ctx.strokeStyle = '#8b95a5';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 1; i < treads; i++) {
    const t = i / treads;
    if (alongX) {
      const x = a.x + (b.x - a.x) * t;
      ctx.moveTo(x, a.y); ctx.lineTo(x, b.y);
    } else {
      const y = a.y + (b.y - a.y) * t;
      ctx.moveTo(a.x, y); ctx.lineTo(b.x, y);
    }
  }
  ctx.stroke();

  // ascent arrow through the middle of the run
  const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
  const half = { n: [0, 1, 0, -1], s: [0, -1, 0, 1],
                 e: [-1, 0, 1, 0], w: [1, 0, -1, 0] }[st.direction] || [0, 1, 0, -1];
  const lenX = Math.abs(b.x - a.x) / 2 - 6, lenY = Math.abs(b.y - a.y) / 2 - 6;
  const sx = cx + half[0] * lenX, sy = cy + half[1] * lenY;
  const ex = cx + half[2] * lenX, ey = cy + half[3] * lenY;
  ctx.strokeStyle = isSel ? '#e0b100' : '#e6e9ee';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(sx, sy); ctx.lineTo(ex, ey);
  const ang = Math.atan2(ey - sy, ex - sx);
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - 7 * Math.cos(ang - 0.45), ey - 7 * Math.sin(ang - 0.45));
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - 7 * Math.cos(ang + 0.45), ey - 7 * Math.sin(ang + 0.45));
  ctx.stroke();

  ctx.textAlign = 'center';
  ctx.fillStyle = '#e6e9ee';
  ctx.font = '600 11px system-ui, sans-serif';
  ctx.fillText(up ? '▲ up' : '▼ down', cx, cy + 4);

  if (!isSel) return;
  const pts = stairRect(st);
  for (const [px, pz] of pts) {
    const s = worldToScreen(px, pz);
    ctx.fillStyle = '#e6e9ee';
    ctx.strokeStyle = '#e0b100';
    ctx.lineWidth = 1.5;
    ctx.fillRect(s.x - HANDLE_PX / 2, s.y - HANDLE_PX / 2, HANDLE_PX, HANDLE_PX);
    ctx.strokeRect(s.x - HANDLE_PX / 2, s.y - HANDLE_PX / 2, HANDLE_PX, HANDLE_PX);
  }
  for (let i = 0; i < 4; i++) {
    const [ax, az] = pts[i], [bx, bz] = pts[(i + 1) % 4];
    const s = worldToScreen((ax + bx) / 2, (az + bz) / 2);
    ctx.beginPath();
    ctx.arc(s.x, s.y, MID_PX / 2 + 1, 0, Math.PI * 2);
    ctx.fillStyle = '#161b23';
    ctx.fill();
    ctx.strokeStyle = '#e0b100';
    ctx.stroke();
  }
}

function redraw() {
  if (!isOpen) return;
  const cw = canvas.clientWidth, ch = canvas.clientHeight;
  ctx.fillStyle = '#10141a';
  ctx.fillRect(0, 0, cw, ch);
  drawPlanImage();
  drawGrid();

  const sel = selectedRoom();
  for (const room of activeRooms()) {
    if (room !== sel) drawRoom(room, false);
  }
  if (sel) drawRoom(sel, true); // selected on top

  for (const entry of activeStairs()) {
    drawStair(entry, entry.st.id === selectedStairId);
  }

  if (drag?.type === 'draw' && drag.moved) {
    const a = worldToScreen(Math.min(drag.ax, drag.bx), Math.min(drag.az, drag.bz));
    const b = worldToScreen(Math.max(drag.ax, drag.bx), Math.max(drag.az, drag.bz));
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = '#3182ce';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(a.x, a.y, b.x - a.x, b.y - a.y);
    ctx.setLineDash([]);
    ctx.fillStyle = '#8b95a5';
    ctx.font = '11px system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(
      `${Math.abs(drag.bx - drag.ax).toFixed(1)} × ${Math.abs(drag.bz - drag.az).toFixed(1)} ft`,
      b.x + 8, b.y);
  }
}

// ------------------------------------------------------------------ hit test

function hitTest(w) {
  const tol = HIT_PX / view.pxPerFt;
  const selSt = selectedStair();
  if (selSt) {
    const pts = stairRect(selSt);
    for (let i = 0; i < 4; i++) {
      if (Math.hypot(w.x - pts[i][0], w.z - pts[i][1]) <= (HANDLE_PX + 2) / view.pxPerFt) {
        return { kind: 'stair-corner', st: selSt, i };
      }
    }
    for (let i = 0; i < 4; i++) {
      const [ax, az] = pts[i], [bx, bz] = pts[(i + 1) % 4];
      if (Math.hypot(w.x - (ax + bx) / 2, w.z - (az + bz) / 2) <= (MID_PX + 3) / view.pxPerFt) {
        return { kind: 'stair-edge', st: selSt, i };
      }
    }
  }
  const sel = selectedRoom();
  if (sel) {
    const pts = sel._poly;
    for (let i = 0; i < pts.length; i++) { // vertex handles first
      if (Math.hypot(w.x - pts[i][0], w.z - pts[i][1]) <= (HANDLE_PX + 2) / view.pxPerFt) {
        return { kind: 'vertex', room: sel, i };
      }
    }
    for (let i = 0; i < pts.length; i++) { // then edge midpoints
      const [ax, az] = pts[i], [bx, bz] = pts[(i + 1) % pts.length];
      if (Math.hypot(w.x - (ax + bx) / 2, w.z - (az + bz) / 2) <= (MID_PX + 3) / view.pxPerFt) {
        return { kind: 'edge', room: sel, i };
      }
    }
    for (let i = 0; i < pts.length; i++) { // then edge bodies (for Alt+insert)
      const hit = distToSegment([w.x, w.z], pts[i], pts[(i + 1) % pts.length]);
      if (hit.d <= tol) return { kind: 'segment', room: sel, i, at: hit };
    }
  }
  // stairs sit on top of rooms, so test them first
  for (const { st } of activeStairs()) {
    if (w.x >= st.x && w.x <= st.x + st.width
        && w.z >= st.z && w.z <= st.z + st.depth) {
      return { kind: 'stair', st };
    }
  }
  const rooms = activeRooms();
  for (let i = rooms.length - 1; i >= 0; i--) {
    if (pointInPolygon([w.x, w.z], rooms[i]._poly)) {
      return { kind: 'room', room: rooms[i] };
    }
  }
  return null;
}

// ------------------------------------------------------------------ gestures

function onPointerDown(e) {
  if (!isOpen) return;
  const now = Date.now();
  const isDblClick = (now - lastPointerDownTime < 400);
  lastPointerDownTime = now;
  try { canvas.setPointerCapture(e.pointerId); } catch { /* synthetic event */ }
  const rect = canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const w = screenToWorld(px, py);

  if (e.button === 1 || spaceHeld) {
    drag = { type: 'pan', startView: { ...view }, startPx: { x: px, y: py } };
    return;
  }
  if (e.button !== 0) return;

  if (mode === 'draw' || mode === 'draw-stairs') {
    const ax = snap(w.x, e.shiftKey), az = snap(w.z, e.shiftKey);
    drag = { type: 'draw', stairs: mode === 'draw-stairs',
             ax, az, bx: ax, bz: az, moved: false };
    return;
  }

  const hit = hitTest(w);
  if (hit?.kind === 'stair-corner') {
    drag = { type: 'stair-corner', st: hit.st, i: hit.i,
             before: { ...hit.st }, moved: false };
  } else if (hit?.kind === 'stair-edge') {
    drag = { type: 'stair-edge', st: hit.st, i: hit.i,
             before: { ...hit.st }, orig: { ...hit.st }, startW: w, moved: false };
  } else if (hit?.kind === 'stair') {
    if (selectedStairId !== hit.st.id) {
      selectedStairId = hit.st.id;
      selectedRoomId = null;
      selectedVertex = null;
      updatePropsPanel();
    }
    drag = { type: 'stair-move', st: hit.st, before: { ...hit.st },
             orig: { ...hit.st }, startW: w, moved: false };
    redraw();
  } else if (hit?.kind === 'vertex') {
    if (isDblClick && hit.room._poly.length > 3) {
      const room = hit.room;
      const before = room._poly.map((p) => [...p]);
      room._poly.splice(hit.i, 1);
      selectedVertex = null;
      if (isSelfIntersecting(room._poly)) {
        room._poly = before;
        setStatus('Removing that corner would make edges cross.');
      } else {
        persistRoom(room).catch(console.error);
      }
      redraw();
      return;
    }
    selectedVertex = hit.i;
    drag = { type: 'vertex', room: hit.room, i: hit.i,
             before: hit.room._poly.map((p) => [...p]), moved: false };
  } else if (hit?.kind === 'edge') {
    if (isDblClick) {
      const room = hit.room;
      drag = { type: 'vertex', room, i: hit.i + 1,
               before: room._poly.map((p) => [...p]), moved: true };
      const [ax, az] = room._poly[hit.i];
      const [bx, bz] = room._poly[(hit.i + 1) % room._poly.length];
      room._poly.splice(hit.i + 1, 0,
        [snap((ax + bx)/2, e.shiftKey), snap((az + bz)/2, e.shiftKey)]);
      selectedVertex = hit.i + 1;
      redraw();
      return;
    }
    drag = { type: 'edge', room: hit.room, i: hit.i,
             before: hit.room._poly.map((p) => [...p]),
             orig: hit.room._poly.map((p) => [...p]),
             startW: w, moved: false };
  } else if (hit?.kind === 'segment' && (e.altKey || isDblClick)) {
    // insert a vertex on the edge and start dragging it
    const room = hit.room;
    drag = { type: 'vertex', room, i: hit.i + 1,
             before: room._poly.map((p) => [...p]), moved: true };
    room._poly.splice(hit.i + 1, 0,
      [snap(hit.at.x, e.shiftKey), snap(hit.at.z, e.shiftKey)]);
    selectedVertex = hit.i + 1;
    redraw();
  } else if (hit?.kind === 'segment' || hit?.kind === 'room') {
    if (selectedRoomId !== hit.room.id) {
      selectedRoomId = hit.room.id;
      selectedStairId = null;
      selectedVertex = null;
      updatePropsPanel();
    }
    const bb = bboxOf(hit.room._poly);
    drag = { type: 'room', room: hit.room,
             before: hit.room._poly.map((p) => [...p]),
             orig: hit.room._poly.map((p) => [...p]),
             origMin: { x: bb.minX, z: bb.minZ }, startW: w, moved: false };
    redraw();
  } else {
    if (selectedRoomId !== null || selectedStairId !== null) {
      selectedRoomId = null;
      selectedStairId = null;
      selectedVertex = null;
      updatePropsPanel();
      redraw();
    }
    const floor = activeFloor();
    if (moveImage && floor && planImages.get(floor.id)) {
      drag = { type: 'img', floor, startW: w,
               orig: { x: floor.plan_x || 0, z: floor.plan_z || 0 } };
    } else {
      drag = { type: 'pan', startView: { ...view }, startPx: { x: px, y: py } };
    }
  }
  renderStatus(w);
}

function onPointerMove(e) {
  if (!isOpen) return;
  const rect = canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const w = screenToWorld(px, py);
  renderStatus(w);
  if (!drag) return;

  if (drag.type === 'pan') {
    view.x = drag.startView.x - (px - drag.startPx.x) / view.pxPerFt;
    view.z = drag.startView.z - (py - drag.startPx.y) / view.pxPerFt;
    redraw();
    return;
  }
  if (drag.type === 'img') {
    drag.floor.plan_x = drag.orig.x + (w.x - drag.startW.x);
    drag.floor.plan_z = drag.orig.z + (w.z - drag.startW.z);
    drag.moved = true;
    redraw();
    return;
  }
  drag.moved = true;

  if (drag.type === 'draw') {
    drag.bx = snap(w.x, e.shiftKey);
    drag.bz = snap(w.z, e.shiftKey);
  } else if (drag.type === 'stair-corner') {
    // resize keeping the opposite corner fixed
    const st = drag.st;
    const opp = stairRect(drag.before)[(drag.i + 2) % 4];
    const nx = snap(w.x, e.shiftKey), nz = snap(w.z, e.shiftKey);
    st.x = Math.min(nx, opp[0]);
    st.z = Math.min(nz, opp[1]);
    st.width = Math.max(2, Math.abs(nx - opp[0]));
    st.depth = Math.max(2, Math.abs(nz - opp[1]));
  } else if (drag.type === 'stair-edge') {
    // edges in stairRect order: 0 top, 1 right, 2 bottom, 3 left
    const st = drag.st, o = drag.orig;
    const nx = snap(w.x, e.shiftKey), nz = snap(w.z, e.shiftKey);
    if (drag.i === 0) {
      st.z = Math.min(nz, o.z + o.depth - 2);
      st.depth = o.z + o.depth - st.z;
    } else if (drag.i === 2) {
      st.depth = Math.max(2, nz - o.z);
    } else if (drag.i === 3) {
      st.x = Math.min(nx, o.x + o.width - 2);
      st.width = o.x + o.width - st.x;
    } else {
      st.width = Math.max(2, nx - o.x);
    }
  } else if (drag.type === 'stair-move') {
    const dx = snap(drag.orig.x + (w.x - drag.startW.x), e.shiftKey) - drag.orig.x;
    const dz = snap(drag.orig.z + (w.z - drag.startW.z), e.shiftKey) - drag.orig.z;
    drag.st.x = drag.orig.x + dx;
    drag.st.z = drag.orig.z + dz;
  } else if (drag.type === 'vertex') {
    drag.room._poly[drag.i] = [snap(w.x, e.shiftKey), snap(w.z, e.shiftKey)];
    drag.invalid = isSelfIntersecting(drag.room._poly);
  } else if (drag.type === 'edge') {
    // rectilinear edge drag: a horizontal edge only moves in Z, a vertical
    // edge only in X; diagonal edges move freely
    const pts = drag.room._poly;
    const i = drag.i, j = (drag.i + 1) % pts.length;
    const [ax, az] = drag.orig[i], [bx, bz] = drag.orig[j];
    const dx = w.x - drag.startW.x, dz = w.z - drag.startW.z;
    const horizontal = Math.abs(az - bz) < 1e-9;
    const vertical = Math.abs(ax - bx) < 1e-9;
    pts[i] = [
      vertical || !horizontal ? snap(ax + dx, e.shiftKey) : ax,
      horizontal || !vertical ? snap(az + dz, e.shiftKey) : az,
    ];
    pts[j] = [
      vertical || !horizontal ? snap(bx + dx, e.shiftKey) : bx,
      horizontal || !vertical ? snap(bz + dz, e.shiftKey) : bz,
    ];
    drag.invalid = isSelfIntersecting(pts);
  } else if (drag.type === 'room') {
    const dx = snap(drag.origMin.x + (w.x - drag.startW.x), e.shiftKey) - drag.origMin.x;
    const dz = snap(drag.origMin.z + (w.z - drag.startW.z), e.shiftKey) - drag.origMin.z;
    drag.room._poly = drag.orig.map(([x, z]) => [x + dx, z + dz]);
  }
  redraw();
}

async function onPointerUp(e) {
  if (!isOpen || !drag) return;
  const d = drag;
  drag = null;

  if (d.type === 'pan') { redraw(); return; }

  if (d.type === 'img') {
    if (d.moved) {
      try {
        await api.updateFloor(d.floor.id, {
          plan_x: round2(d.floor.plan_x), plan_z: round2(d.floor.plan_z),
        });
      } catch (err) {
        setStatus(`Image move failed: ${err.message}`);
      }
    }
    redraw();
    return;
  }

  if (d.type === 'draw') {
    mode = 'select';
    $('pl-draw').classList.remove('active');
    $('pl-stairs').classList.remove('active');
    canvas.style.cursor = '';
    const wFt = Math.abs(d.bx - d.ax), hFt = Math.abs(d.bz - d.az);
    if (d.moved && wFt >= MIN_ROOM_FT && hFt >= MIN_ROOM_FT) {
      const floor = activeFloor();
      const x = Math.min(d.ax, d.bx), z = Math.min(d.az, d.bz);
      if (d.stairs) {
        // stairs descend: they connect this floor to the one below (unless
        // this is the lowest floor, which can only connect upward)
        const lower = floorBelowActive() || floor;
        const st = {
          id: null, floor_id: lower.id, name: 'Stairs',
          x, z, width: wFt, depth: hFt,
          direction: hFt >= wFt ? 'n' : 'e',
        };
        (lower.stairs ||= []).push(st);
        await persistStair(st);
        selectedStairId = st.id;
        selectedRoomId = null;
      } else {
        const room = {
          id: null, floor_id: floor.id,
          name: `Room ${(floor.rooms?.length || 0) + 1}`,
          ha_area_id: null, height: 8,
          color: PALETTE[(floor.rooms?.length || 0) % PALETTE.length],
          devices: [],
          footprint: { x, z, width: wFt, depth: hFt, points: null },
        };
        room._poly = [[x, z], [x + wFt, z], [x + wFt, z + hFt], [x, z + hFt]];
        floor.rooms.push(room);
        await persistRoom(room);
        selectedRoomId = room.id;
        selectedStairId = null;
      }
      selectedVertex = null;
      updatePropsPanel();
    }
    redraw();
    return;
  }

  if (d.type.startsWith('stair-')) {
    if (d.moved) await persistStair(d.st);
    redraw();
    return;
  }

  // vertex / edge / room gestures
  if (!d.moved) { redraw(); return; }
  if (d.invalid || isSelfIntersecting(d.room._poly)) {
    d.room._poly = d.before; // revert, never persist a crossing polygon
    setStatus('Edges cannot cross — change undone.');
  } else if (Math.abs(signedArea(d.room._poly)) < 0.5) {
    d.room._poly = d.before;
    setStatus('Room got too small — change undone.');
  } else {
    await persistRoom(d.room);
  }
  redraw();
}

function onWheel(e) {
  if (!isOpen) return;
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const before = screenToWorld(px, py);
  view.pxPerFt = Math.max(2, Math.min(60, view.pxPerFt * Math.pow(1.0015, -e.deltaY)));
  view.x = before.x - px / view.pxPerFt;
  view.z = before.z - py / view.pxPerFt;
  redraw();
}

async function onKeyDown(e) {
  if (!isOpen) return;
  const tag = document.activeElement?.tagName;
  const typing = tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA';

  if (e.key === 'Escape') {
    if (drag && drag.type !== 'pan' && drag.before) {
      if (drag.type.startsWith('stair-')) Object.assign(drag.st, drag.before);
      else drag.room._poly = drag.before;
      drag = null;
      redraw();
    } else if (mode === 'draw' || mode === 'draw-stairs') {
      mode = 'select';
      $('pl-draw').classList.remove('active');
      $('pl-stairs').classList.remove('active');
      canvas.style.cursor = '';
      drag = null;
      redraw();
    } else if (selectedRoomId !== null || selectedStairId !== null) {
      selectedRoomId = null;
      selectedStairId = null;
      selectedVertex = null;
      updatePropsPanel();
      redraw();
    } else {
      closePlanner();
    }
    renderStatus();
    return;
  }
  if (typing) return;

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedStair()) {
      await deleteSelectedStair();
      return;
    }
    const room = selectedRoom();
    if (!room) return;
    if (selectedVertex !== null && room._poly.length > 3) {
      const before = room._poly.map((p) => [...p]);
      room._poly.splice(selectedVertex, 1);
      selectedVertex = null;
      if (isSelfIntersecting(room._poly)) {
        room._poly = before;
        setStatus('Removing that corner would make edges cross.');
      } else {
        await persistRoom(room);
      }
      redraw();
    } else if (selectedVertex === null) {
      await deleteSelectedRoom();
    }
  } else if (e.key === 'd' || e.key === 'D') {
    $('pl-draw').click();
  }
  if (e.key === ' ') spaceHeld = true;
}

// ------------------------------------------------------------------ props

function fillAreaOptions() {
  const sel = $('pl-area');
  sel.innerHTML = '<option value="">— no HA area —</option>';
  const structure = getStructure();
  if (!structure) return;
  for (const f of structure.floors || []) {
    for (const a of f.areas || []) {
      const opt = document.createElement('option');
      opt.value = a.area_id;
      opt.textContent = `${a.name} (${f.name})`;
      sel.appendChild(opt);
    }
  }
}

function updatePropsPanel() {
  const room = selectedRoom();
  const panel = $('pl-props');
  panel.classList.toggle('hidden', !room);
  if (room) {
    $('pl-name').value = room.name;
    $('pl-area').value = room.ha_area_id || '';
    $('pl-color').value = room.color || '#8fa8bf';
    $('pl-height').value = room.height;
    $('pl-wall-color').value = room.wall_color || '#f2ede3';
    $('pl-wall-tex').value = room.wall_texture || '';
    $('pl-floor-color').value = room.floor_color || '#e5decf';
    $('pl-floor-tex').value = room.floor_texture || '';
  }
  const st = selectedStair();
  const spanel = $('pl-sprops');
  spanel.classList.toggle('hidden', !st);
  if (st) $('pl-sdir').value = st.direction;
}

async function deleteSelectedStair() {
  const st = selectedStair();
  if (!st) return;
  try {
    if (st.id) await api.deleteStairs(st.id);
    for (const f of house.floors || []) {
      if (f.stairs) f.stairs = f.stairs.filter((s) => s !== st);
    }
    selectedStairId = null;
    updatePropsPanel();
    redraw();
  } catch (err) {
    setStatus(`Delete failed: ${err.message}`);
  }
}

async function deleteSelectedRoom() {
  const room = selectedRoom();
  if (!room) return;
  if (!confirm(`Delete room "${room.name}"? Its device placements go with it.`)) return;
  try {
    if (room.id) await api.deleteRoom(room.id);
    const floor = activeFloor();
    floor.rooms = floor.rooms.filter((r) => r !== room);
    selectedRoomId = null;
    selectedVertex = null;
    updatePropsPanel();
    redraw();
  } catch (err) {
    setStatus(`Delete failed: ${err.message}`);
  }
}

// ------------------------------------------------------------------ floors

function buildFloorTabs() {
  const nav = $('pl-floors');
  nav.innerHTML = '';
  for (const f of floorsSorted()) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = `${f.level} · ${f.name}`;
    btn.classList.toggle('active', f.id === activeFloorId);
    btn.onclick = () => setActiveFloor(f.id);
    nav.appendChild(btn);
  }
}

function loadPlanImage(floor, bustCache) {
  if (!floor?.plan_image) return;
  if (planImages.has(floor.id) && !bustCache) return;
  const img = new Image();
  img.onload = redraw;
  img.src = `/api/house/plan/${floor.id}` + (bustCache ? `?t=${Date.now()}` : '');
  planImages.set(floor.id, img);
}

function updateImgControls() {
  const floor = activeFloor();
  const hasImg = !!floor?.plan_image;
  document.querySelectorAll('.pl-img-ctl').forEach((el) =>
    el.classList.toggle('hidden', !hasImg));
  if (hasImg) $('pl-img-scale').value = floor.plan_scale || 0.05;
  if (!hasImg && moveImage) {
    moveImage = false;
    $('pl-img-move').classList.remove('active');
  }
}

function setActiveFloor(floorId) {
  activeFloorId = floorId;
  selectedRoomId = null;
  selectedStairId = null;
  selectedVertex = null;
  drag = null;
  buildFloorTabs();
  updatePropsPanel();
  loadPlanImage(activeFloor());
  updateImgControls();
  fitView();
  redraw();
  renderStatus();
}

// ------------------------------------------------------------------ open/close

// After an undo/redo while the planner is open: re-fetch the house and
// rebuild the planner's working state, keeping the current floor, selection
// and pan/zoom where still valid. Deliberately NOT setActiveFloor — that
// clears the selection and fitView() would reset the zoom on every undo.
// Cached plan images are reused (files survive undo); after undoing a plan
// re-upload the old cached bitmap may show until the planner is reopened.
async function rehydrate() {
  const keepFloor = activeFloorId;
  const keepRoom = selectedRoomId;
  const keepStair = selectedStairId;
  house = await api.getHouse();
  for (const f of house.floors || []) {
    for (const r of f.rooms || []) r._poly = absPoly(r);
  }
  drag = null; // never let a live gesture reference stale room objects
  selectedVertex = null;
  const floors = floorsSorted();
  activeFloorId = floors.some((f) => f.id === keepFloor)
    ? keepFloor : floors[0]?.id ?? null;
  selectedRoomId = activeRooms().some((r) => r.id === keepRoom) ? keepRoom : null;
  selectedStairId = activeStairs().some(({ st }) => st.id === keepStair)
    ? keepStair : null;
  buildFloorTabs();
  updatePropsPanel();
  loadPlanImage(activeFloor()); // restores an undone plan-image pointer
  updateImgControls();
  redraw();
  renderStatus();
}

let prevUndoHandler = null;

export async function openPlanner(initialLevel) {
  house = await api.getHouse();
  for (const f of house.floors || []) {
    for (const r of f.rooms || []) r._poly = absPoly(r);
  }
  fillAreaOptions();

  const floors = floorsSorted();
  if (!floors.length) return;
  const lvl = initialLevel ?? getLevel();
  const match = floors.find((f) => f.level === lvl);
  activeFloorId = (match || floors[0]).id;

  isOpen = true;
  $('planner').classList.remove('hidden');
  resizeCanvas();
  setActiveFloor(activeFloorId);
  prevUndoHandler = setUndoHandler(rehydrate);
}

function closePlanner() {
  if (!isOpen) return;
  isOpen = false;
  mode = 'select';
  drag = null;
  setUndoHandler(prevUndoHandler); // undo refreshes the 3D view again
  $('pl-draw').classList.remove('active');
  $('planner').classList.add('hidden');
  onCloseCb?.(); // one 3D rebuild for the whole editing session
}

export function initPlanner({ getStructure: gs, onClose }) {
  getStructure = gs;
  onCloseCb = onClose;
  canvas = $('pl-canvas');
  ctx = canvas.getContext('2d');

  $('btn-planner').onclick = () => openPlanner();
  $('pl-close').onclick = closePlanner;

  // floor-plan tracing image
  $('pl-img-btn').onclick = () => $('pl-img-file').click();
  $('pl-img-file').onchange = async () => {
    const file = $('pl-img-file').files[0];
    $('pl-img-file').value = '';
    const floor = activeFloor();
    if (!file || !floor) return;
    try {
      const res = await api.uploadFloorPlan(floor.id, file);
      floor.plan_image = res.plan_image;
      loadPlanImage(floor, true);
      updateImgControls();
      setStatus('Image uploaded — set ft/px so a known wall matches the grid, then "Move image" to line it up.');
    } catch (err) {
      setStatus(`Upload failed: ${err.message}`);
    }
  };
  $('pl-img-opacity').oninput = () => {
    imgOpacity = Number($('pl-img-opacity').value) / 100;
    redraw();
  };
  $('pl-img-scale').onchange = async () => {
    const floor = activeFloor();
    if (!floor) return;
    floor.plan_scale = Math.max(0.005, Number($('pl-img-scale').value) || 0.05);
    $('pl-img-scale').value = floor.plan_scale;
    redraw();
    try { await api.updateFloor(floor.id, { plan_scale: floor.plan_scale }); }
    catch (err) { setStatus(`Save failed: ${err.message}`); }
  };
  $('pl-img-move').onclick = () => {
    moveImage = !moveImage;
    $('pl-img-move').classList.toggle('active', moveImage);
    renderStatus();
  };
  $('pl-img-del').onclick = async () => {
    const floor = activeFloor();
    if (!floor?.plan_image) return;
    try {
      await api.deleteFloorPlan(floor.id);
      floor.plan_image = null;
      planImages.delete(floor.id);
      updateImgControls();
      redraw();
    } catch (err) {
      setStatus(`Delete failed: ${err.message}`);
    }
  };
  $('pl-draw').onclick = () => {
    mode = mode === 'draw' ? 'select' : 'draw';
    $('pl-draw').classList.toggle('active', mode === 'draw');
    $('pl-stairs').classList.remove('active');
    canvas.style.cursor = mode === 'draw' ? 'crosshair' : '';
    renderStatus();
  };
  $('pl-stairs').onclick = () => {
    mode = mode === 'draw-stairs' ? 'select' : 'draw-stairs';
    $('pl-stairs').classList.toggle('active', mode === 'draw-stairs');
    $('pl-draw').classList.remove('active');
    canvas.style.cursor = mode === 'draw-stairs' ? 'crosshair' : '';
    renderStatus();
  };
  $('pl-sdir').onchange = async () => {
    const st = selectedStair();
    if (!st) return;
    st.direction = $('pl-sdir').value;
    await persistStair(st);
    redraw();
  };
  $('pl-sdelete').onclick = deleteSelectedStair;

  canvas.addEventListener('pointerdown', onPointerDown);
  canvas.addEventListener('pointermove', onPointerMove);
  canvas.addEventListener('pointerup', onPointerUp);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('keyup', (e) => { if (e.key === ' ') spaceHeld = false; });
  window.addEventListener('resize', () => {
    if (!isOpen) return;
    resizeCanvas();
    redraw();
  });

  // properties panel — persist on change
  fillTextureSelect($('pl-wall-tex'));
  fillTextureSelect($('pl-floor-tex'));
  const roomPatch = (apply) => async () => {
    const room = selectedRoom();
    if (!room) return;
    apply(room);
    await persistRoom(room);
    redraw();
  };
  $('pl-name').onchange = roomPatch((r) => { r.name = $('pl-name').value.trim() || r.name; });
  $('pl-area').onchange = roomPatch((r) => { r.ha_area_id = $('pl-area').value || null; });
  $('pl-color').onchange = roomPatch((r) => { r.color = $('pl-color').value; });
  $('pl-height').onchange = roomPatch((r) => {
    r.height = Math.max(1, Number($('pl-height').value) || r.height);
  });
  $('pl-wall-color').onchange = roomPatch((r) => { r.wall_color = $('pl-wall-color').value; });
  $('pl-wall-tex').onchange = roomPatch((r) => { r.wall_texture = $('pl-wall-tex').value || null; });
  $('pl-floor-color').onchange = roomPatch((r) => { r.floor_color = $('pl-floor-color').value; });
  $('pl-floor-tex').onchange = roomPatch((r) => { r.floor_texture = $('pl-floor-tex').value || null; });
  $('pl-rect').onclick = roomPatch((r) => {
    const bb = bboxOf(r._poly);
    r._poly = [[bb.minX, bb.minZ], [bb.minX + bb.w, bb.minZ],
               [bb.minX + bb.w, bb.minZ + bb.h], [bb.minX, bb.minZ + bb.h]];
    selectedVertex = null;
  });
  $('pl-delete').onclick = deleteSelectedRoom;

  // debug handle (console): inspect planner state, map world ft -> screen px
  window.__planner = {
    worldToScreen, screenToWorld,
    rooms: () => activeRooms(),
    selected: () => selectedRoom(),
    view: () => ({ ...view }),
  };
}
