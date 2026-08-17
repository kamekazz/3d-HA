// The Sims-4 dollhouse cutaway: the walls between you and a room fade away, so
// you always look into it over two far walls and never at the back of a near
// one, and there is never a ceiling in the way.
//
// This replaces a trick that used to be free. Walls were zero-thickness fins
// wound with inward normals and drawn FrontSide, so the GPU backface-culled
// whichever ones the camera stood behind. That cost nothing but it flipped at
// exactly 90 degrees (a hard pop every time you orbited past a corner), and it
// only ever hid the wall surface — the art, windows and cabinets mounted on
// that wall are separate GLB objects and were left hanging in mid-air.
//
// Walls have a body now (house.js WALL_THICKNESS), which does not backface-cull
// at all, so the cutaway has to be explicit. That is this module: one onFrame
// tick that scores every wall against the camera azimuth, eases its opacity,
// and drags the wall's mounted furniture along with it.
//
// It runs in EVERY view that draws rooms, not just room focus. It has to: solid
// walls mean the single-floor view would otherwise be a row of sealed boxes.
import * as THREE from 'three';
import { scene, camera, onFrame } from './scene.js';
import { roomMeshes, openingMeshes, wallParts, applyWallOpacity } from './house.js';
import { objects3d, setObjectWallFade, fadeSubtree } from './objects.js';

// Facing score = dot(wall's inward normal, horizontal direction to the camera).
// 1 = looking straight at the painted face, 0 = edge-on, -1 = behind it.
// The band is deliberately wide: these are cosines, so 0.02..0.55 is a ~33
// degree arc of orbit to cross. Tighter values (0.05..0.30, the first attempt)
// span barely 15 degrees, which at any real orbit speed still reads as the pop
// this replaced. Fully transparent by the time the wall goes edge-on.
const FADE_LO = 0.02;
const FADE_HI = 0.55;
// Easing time constant, seconds. ~0.18s to settle — fast enough to feel
// attached to the drag, slow enough that nothing snaps.
const TAU = 0.09;

// A room-spanning ceiling slab, e.g. "Kitchen Ceiling". Deliberately anchored
// to the end of the name so "Ceiling Fan" — a fixture, not a surface — is not
// caught by it.
const CEILING_RE = /\bceilings?\s*$/i;
// Room-spanning wall skins and trim runs: one GLB per room holding a separate
// sub-mesh per wall. They fade per sub-mesh, so a room keeps the trim on the
// walls it still shows. Deliberately NARROWER than objects.js's SURFACE_RE,
// which is about pickability and also catches "Ceiling Fan" and "Floor Vent" —
// real furniture, which has to fade as a whole object or not at all.
const WALL_SKIN_RE = /\b(wall wash|wall panel|wainscot|baseboards?|crown|molding)\b/i;
// Mounted furniture must be off the floor: a dresser pushed against a wall is
// bottom-seated at y~0 and stays put when that wall goes, exactly as it does in
// the Sims. Art, windows, curtains, sconces and wall cabinets all sit higher.
const MOUNT_MIN_Y = 1.2;
// ...and within arm's reach of the wall line, in feet.
const MOUNT_MAX_DIST = 2.0;
// Wall skins sit ON the wall plane, so this can be much tighter than the
// mounted-furniture radius — it has to be, or a narrow room's floor plane
// measures close enough to a wall to be dragged into the fade.
const SURFACE_MAX_DIST = 1.0;

let enabled = true;
// objectId -> { roomId, edgeIndex } for wall-mounted furniture, and
// objectId -> { roomId, edgeIndex: null } for ceilings (always faded out).
let mounted = new Map();
let lastSent = new Map(); // objectId -> last opacity pushed to objects.js
// Room-spanning surface pieces — the wall-wash skin, baseboard and crown runs —
// are one GLB per room holding a separate sub-mesh per wall. Fading them as
// whole objects would strip a room of all its trim at once, so they bind and
// fade per sub-mesh: { mesh, roomId, edgeIndex }.
let surfaceParts = [];
// Surfaces whose GLB has not resolved yet; drained by the tick, because the
// bind needs real geometry to measure.
let pendingSurfaces = [];

const _v = new THREE.Vector3();
const _box = new THREE.Box3();
const _c = new THREE.Vector3();

// Squared distance from a room-local point to a wall, using the midpoint and
// half-vector house.js stashes on each wall child.
function distSqToWall(wall, px, pz) {
  const mx = wall.position.x, mz = wall.position.z;
  const hx = wall.userData.hx, hz = wall.userData.hz;
  const h2 = hx * hx + hz * hz;
  let s = h2 > 1e-6 ? ((px - mx) * hx + (pz - mz) * hz) / h2 : 0;
  s = Math.max(-1, Math.min(1, s)); // clamp to the segment
  const dx = px - (mx + s * hx), dz = pz - (mz + s * hz);
  return dx * dx + dz * dz;
}

// Nearest wall of a room to a room-local point, or null if none is close.
function nearestWall(walls, px, pz, maxDist) {
  let best = null, bestD = maxDist * maxDist;
  for (const wall of walls) {
    const d = distSqToWall(wall, px, pz);
    if (d < bestD) { bestD = d; best = wall.userData.edgeIndex; }
  }
  return best;
}

// Rebuild the object -> wall binding. Must run after every house rebuild:
// buildHouse/buildObjects throw away every mesh, so the old map points at
// meshes that are no longer in the scene.
export function setCutawayData(house) {
  mounted = new Map();
  lastSent = new Map();
  surfaceParts = [];
  pendingSurfaces = [];
  for (const floor of house?.floors || []) {
    for (const room of floor.rooms || []) {
      const mesh = roomMeshes.get(room.id);
      if (!mesh) continue;
      const walls = wallParts(mesh);
      for (const o of room.objects || []) {
        const name = o.name || o.model_name || '';
        if (CEILING_RE.test(name)) {
          mounted.set(o.id, { roomId: room.id, edgeIndex: null });
          continue;
        }
        if (WALL_SKIN_RE.test(name)) {
          pendingSurfaces.push({ objectId: o.id, roomId: room.id });
          continue;
        }
        if ((o.position?.y ?? 0) < MOUNT_MIN_Y) continue;
        // object anchors are room-relative, same frame as wall.position
        const best = nearestWall(walls, o.position.x, o.position.z, MOUNT_MAX_DIST);
        // Nothing close enough: a pendant light, a rug, a piece in the middle
        // of the room. Left alone — it keeps full opacity.
        if (best !== null) mounted.set(o.id, { roomId: room.id, edgeIndex: best });
      }
    }
  }
}

// Measure a loaded surface GLB and bind each of its sub-meshes to the wall it
// skins. A piece that measures to the middle of the room — a floor plane, a
// contact-shadow decal, a trim run authored as one merged loop — binds to
// nothing and keeps full opacity.
function bindSurface(entry) {
  const root = objects3d.get(entry.objectId);
  if (!root || root.children.length === 0) return false;
  const mesh = roomMeshes.get(entry.roomId);
  if (!mesh) return true; // room is gone; drop it
  const walls = wallParts(mesh);
  mesh.getWorldPosition(_v);
  const ox = _v.x, oz = _v.z;
  // Box3.setFromObject measures off matrixWorld and refreshes only the object's
  // own matrix, not its parent chain. A GLB that resolved since the last render
  // still carries stale ancestors, and every panel then measures to the room's
  // origin and binds to nothing — which is how three of a wall-wash's four
  // panels silently kept blocking the cutaway. Force the subtree current first.
  root.updateWorldMatrix(true, true);
  root.traverse((o) => {
    if (!o.isMesh) return;
    _box.setFromObject(o);
    if (_box.isEmpty()) return;
    _box.getCenter(_c);
    const edge = nearestWall(walls, _c.x - ox, _c.z - oz, SURFACE_MAX_DIST);
    if (edge !== null) surfaceParts.push({ mesh: o, roomId: entry.roomId, edgeIndex: edge, owner: root.userData.name });
  });
  return true;
}

// Current fade of one wall of one room, 0..1. Used to drive the room's mounted
// furniture and its door/window panels.
function fadeOf(mesh, edgeIndex) {
  const wall = mesh.userData.wallByEdge?.get(edgeIndex);
  return wall ? (wall.userData.fade ?? 1) : 1;
}

function tick(dt, instant = false, cam = camera) {
  if (!enabled) return;
  const k = instant ? 1 : 1 - Math.exp(-Math.max(dt, 0) / TAU);

  for (const mesh of roomMeshes.values()) {
    if (!mesh.visible) continue;
    const base = mesh.userData.baseOpacity ?? 1;
    for (const wall of wallParts(mesh)) {
      wall.getWorldPosition(_v);
      // Horizontal only. Walls are vertical, so what decides whether you see
      // the painted face is pure azimuth — folding in the camera's height would
      // fade every wall out at once from a top-down view.
      let dx = cam.position.x - _v.x, dz = cam.position.z - _v.z;
      const l = Math.hypot(dx, dz) || 1;
      dx /= l; dz /= l;
      const facing = wall.userData.nx * dx + wall.userData.nz * dz;
      const target = THREE.MathUtils.smoothstep(facing, FADE_LO, FADE_HI);
      const f = wall.userData.fade ?? 1;
      wall.userData.fade = f + (target - f) * k;
      applyWallOpacity(wall, base);
    }
  }

  // Door and window panels follow the wall they pierce, or they would be left
  // hanging in the gap where it was.
  for (const hinge of openingMeshes.values()) {
    const room = hinge.parent;
    if (!room || !room.visible) continue;
    const f = fadeOf(room, hinge.userData.edgeIndex);
    const op = (hinge.userData.baseOpacity ?? 1) * f;
    hinge.visible = op > 0.01;
    for (const child of hinge.children) {
      if (child.material) child.material.opacity = op;
    }
  }

  // Surface skins bind lazily: their GLBs resolve well after the house is built.
  if (pendingSurfaces.length) {
    pendingSurfaces = pendingSurfaces.filter((e) => !bindSurface(e));
  }
  for (const part of surfaceParts) {
    const mesh = roomMeshes.get(part.roomId);
    if (!mesh || !mesh.visible) continue;
    const f = fadeOf(mesh, part.edgeIndex);
    if (Math.abs((part.last ?? 1) - f) < 0.01) continue;
    part.last = f;
    fadeSubtree(part.mesh, f);
    part.mesh.visible = f > 0.01;
  }

  // ...and so does anything mounted on it.
  for (const [objectId, bind] of mounted) {
    const mesh = roomMeshes.get(bind.roomId);
    if (!mesh) continue;
    const f = bind.edgeIndex === null ? 0 : fadeOf(mesh, bind.edgeIndex);
    if (Math.abs((lastSent.get(objectId) ?? 1) - f) < 0.01) continue;
    lastSent.set(objectId, f);
    setObjectWallFade(objectId, f);
  }
}

// Snapshot cards render the scene from their own camera at a fixed azimuth
// (snapshots.js), and the cutaway is scored against the live one — so a card
// would otherwise be shot through the back of a solid wall. Re-score for that
// camera, then call the returned function to snap back to the live view.
export function scoreForCamera(cam) {
  tick(0, true, cam);
  return () => tick(0, true);
}

export function initCutaway() {
  onFrame((dt) => tick(dt));
  // Debug + screenshot handle. roomkit's shot.py / dollhouse.py fly the camera
  // and grab the canvas; without settle() they can catch a wall mid-fade.
  window.__cutaway = {
    settle: () => {
      // a rebuild leaves matrixWorld stale until the next render, and the fade
      // is scored off each wall's world position
      scene.updateMatrixWorld(true);
      tick(0, true);
    },
    setEnabled: (v) => { enabled = v; },
    debug: () => ({ pending: pendingSurfaces.length,
      parts: surfaceParts.map((p) => [p.owner, p.mesh.name, p.roomId, p.edgeIndex, p.last]),
      mounted: mounted.size }),
  };
}
