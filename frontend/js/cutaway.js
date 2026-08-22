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
// Architecture: pieces that ARE part of a wall rather than things standing in
// front of one — skins and trim runs (wall wash, wainscot, baseboards, crown),
// the openings cut through it (window units, door leaves, linings, casings) and
// applied panels. They bind per wall, so a room keeps the trim and the doors on
// the walls it still shows: per sub-mesh where the GLB has one per wall, and
// otherwise by splitting the merged run per triangle (splitMerged).
//
// Two things follow from being architecture rather than furniture, and both are
// the point of having a separate list. Architecture skips the MOUNT_MIN_Y gate
// below: a door lining or a garage door starts at the floor and still has to
// leave with its wall, where a dresser pushed against that wall must not. And
// it is measured by geometry rather than by its anchor, because a piece like
// "Dining Windows" is five units on four different walls in one model, anchored
// nowhere near any of them.
//
// Deliberately NOT objects.js's SURFACE_RE, which is about pickability and also
// catches "Ceiling Fan" and "Floor Vent" — real furniture, which has to fade as
// a whole object or not at all. Note `floor` is absent here on purpose: a floor
// plane in a narrow room measures within SURFACE_MAX_DIST of every wall and
// would be shredded across all of them.
// Every noun takes an optional plural: the pieces that exposed this bug are
// named "Dining Openings", "Dining Windows" and "Rios Closet Doors", and \b
// after a singular fails on all three.
const WALL_ARCH_RE = /\b(walls?|wainscots?|baseboards?|crowns?|mou?ldings?|trims?|openings?|casings?|jambs?|linings?|windows?|doors?|sliders?|panels?)\b/i;
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
// are one GLB per room covering every wall. Fading them as whole objects would
// strip a room of all its trim at once, so they bind and fade per wall:
// { mesh, roomId, edgeIndex }, where mesh is a sub-mesh of the GLB or one of
// the per-wall buckets splitMerged carved out of it.
let surfaceParts = [];
// Surfaces whose GLB has not resolved yet; drained by the tick, because the
// bind needs real geometry to measure.
let pendingSurfaces = [];

const _v = new THREE.Vector3();
const _box = new THREE.Box3();
const _c = new THREE.Vector3();
const _p = new THREE.Vector3();
const _inv = new THREE.Matrix4();  // world -> room-local
const _m = new THREE.Matrix4();    // sub-mesh local -> room-local

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
        if (WALL_ARCH_RE.test(name)) {
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

// Sort a sub-mesh's triangles by the wall each one sits against, in room-local
// space. Returns Map(edgeIndex -> vertex indices), with -1 collecting whatever
// is not near any wall, or null if the geometry can't be read.
function triangleBuckets(geo, walls, toLocal) {
  const pos = geo.attributes?.position;
  if (!pos) return null;
  const index = geo.index;
  const count = index ? index.count : pos.count;
  if (count < 3 || count % 3 !== 0) return null;
  const buckets = new Map();
  for (let t = 0; t < count; t += 3) {
    let cx = 0, cz = 0;
    for (let k = 0; k < 3; k++) {
      _p.fromBufferAttribute(pos, index ? index.getX(t + k) : t + k);
      _p.applyMatrix4(toLocal);
      cx += _p.x; cz += _p.z;
    }
    const edge = nearestWall(walls, cx / 3, cz / 3, SURFACE_MAX_DIST);
    const key = edge === null ? -1 : edge;
    let arr = buckets.get(key);
    if (!arr) buckets.set(key, arr = []);
    for (let k = 0; k < 3; k++) arr.push(index ? index.getX(t + k) : t + k);
  }
  return buckets;
}

// Split a sub-mesh that skins several walls into one child per wall.
//
// roomkit's glb.py groups primitives BY MATERIAL, never by wall, so a trim run
// authored as `for w in "nswe"` lands in a single primitive whose bbox centre
// sits in the middle of the room — nowhere near a wall. It therefore bound to
// nothing and kept full opacity forever while the walls it skinned faded away.
// That is the leftover "frame" of a cutaway: skirting, chair rail, wainscot,
// casings and door leaves left standing in the gap. Splitting here rather than
// re-authoring the GLBs fixes every already-uploaded room with no rebuild.
//
// Buckets share the source attribute buffers and differ only in their index, so
// this costs one index array per wall, not a copy of the mesh. Each bucket does
// need its OWN material clone: fadeSubtree tracks the transparent flag per
// material, so a shared one would fade every wall together — the bug again.
// Returns true if the mesh was split.
function splitMerged(o, walls, roomId, owner) {
  // A multi-material mesh carries draw groups keyed to index ranges; reindexing
  // would silently repaint it. Not something roomkit emits — leave it alone.
  if (Array.isArray(o.material)) return false;
  const src = o.geometry;
  const buckets = triangleBuckets(src, walls, _m);
  if (!buckets) return false;
  const edges = [...buckets.keys()].filter((k) => k !== -1);
  // Nothing wall-adjacent at all: a genuine room-wide piece — a floor plane, a
  // contact-shadow decal. Leave it whole and opaque, as before.
  if (edges.length === 0) return false;
  // All of it on one wall the bbox centre happened to miss: bind it whole, no
  // need to rebuild any geometry.
  if (buckets.size === 1) {
    surfaceParts.push({ mesh: o, roomId, edgeIndex: edges[0], owner });
    return true;
  }

  for (const [key, idx] of buckets) {
    const g = new THREE.BufferGeometry();
    for (const name of Object.keys(src.attributes)) {
      g.setAttribute(name, src.attributes[name]);
    }
    g.setIndex(idx);
    const part = new THREE.Mesh(g, key === -1 ? o.material : o.material.clone());
    part.name = `${o.name || 'skin'}#${key}`;
    o.add(part);
    if (key !== -1) surfaceParts.push({ mesh: part, roomId, edgeIndex: key, owner });
  }
  // The parent keeps the identity and the transform and stops drawing — the
  // same trick house.js uses for the room mesh. Children sit at identity, so
  // the split geometry lands exactly where the merged mesh did.
  o.geometry = new THREE.BufferGeometry();
  return true;
}

// Measure a loaded surface GLB and bind each of its sub-meshes to the wall it
// skins. A sub-mesh that measures to the middle of the room is handed to
// splitMerged, which either sorts it per wall or leaves it whole and opaque.
function bindSurface(entry) {
  const root = objects3d.get(entry.objectId);
  if (!root || root.children.length === 0) return false;
  const mesh = roomMeshes.get(entry.roomId);
  if (!mesh) return true; // room is gone; drop it
  const walls = wallParts(mesh);
  // getWorldPosition refreshes mesh.matrixWorld, which the inverse below needs.
  mesh.getWorldPosition(_v);
  const ox = _v.x, oz = _v.z;
  _inv.copy(mesh.matrixWorld).invert();
  // Box3.setFromObject measures off matrixWorld and refreshes only the object's
  // own matrix, not its parent chain. A GLB that resolved since the last render
  // still carries stale ancestors, and every panel then measures to the room's
  // origin and binds to nothing — which is how three of a wall-wash's four
  // panels silently kept blocking the cutaway. Force the subtree current first.
  root.updateWorldMatrix(true, true);
  // Collected up front, not handled inside traverse(): splitMerged adds
  // children to the mesh it is splitting, and traverse would walk straight into
  // them and try to split each bucket again.
  const subMeshes = [];
  root.traverse((o) => { if (o.isMesh) subMeshes.push(o); });
  for (const o of subMeshes) {
    _box.setFromObject(o);
    if (_box.isEmpty()) continue;
    _box.getCenter(_c);
    const edge = nearestWall(walls, _c.x - ox, _c.z - oz, SURFACE_MAX_DIST);
    if (edge !== null) {
      surfaceParts.push({ mesh: o, roomId: entry.roomId, edgeIndex: edge, owner: root.userData.name });
      continue;
    }
    _m.multiplyMatrices(_inv, o.matrixWorld);
    if (splitMerged(o, walls, entry.roomId, root.userData.name)) continue;
    // Nothing of it lies on a wall plane, so it is not a skin or an opening —
    // it is architecture standing a little off the wall: art on deep frames, a
    // window unit with a proud stool. Those used to reach here through the
    // furniture path and bind at its roomier radius, so keep binding them that
    // way rather than silently dropping them now that the name routes here.
    const near = nearestWall(walls, _c.x - ox, _c.z - oz, MOUNT_MAX_DIST);
    if (near !== null) {
      surfaceParts.push({ mesh: o, roomId: entry.roomId, edgeIndex: near, owner: root.userData.name });
    }
  }
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

// Undo every fade this module has applied: walls, the panels in their openings,
// the per-wall surface skins and anything mounted on a wall. Used by
// setEnabled(false) so a photo-matched interior shot sees all four walls and
// the ceiling, the way someone standing in the room does.
function restoreAll() {
  for (const mesh of roomMeshes.values()) {
    const base = mesh.userData.baseOpacity ?? 1;
    for (const wall of wallParts(mesh)) {
      wall.userData.fade = 1;
      applyWallOpacity(wall, base);
    }
  }
  for (const hinge of openingMeshes.values()) {
    hinge.visible = true;
    const op = hinge.userData.baseOpacity ?? 1;
    for (const child of hinge.children) {
      if (child.material) child.material.opacity = op;
    }
  }
  for (const part of surfaceParts) {
    part.last = 1;
    fadeSubtree(part.mesh, 1);
    part.mesh.visible = true;
  }
  for (const objectId of mounted.keys()) {
    lastSent.set(objectId, 1);
    setObjectWallFade(objectId, 1);
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
    setEnabled: (v) => {
      enabled = v;
      // tick() early-returns while disabled, so flipping the flag alone would
      // freeze whatever was already faded out -- including every ceiling, which
      // CEILING_RE holds at 0 permanently. Disabling the cutaway has to mean
      // "show the room as built", so put everything back to full.
      if (!v) restoreAll();
    },
    debug: () => ({ pending: pendingSurfaces.length,
      parts: surfaceParts.map((p) => [p.owner, p.mesh.name, p.roomId, p.edgeIndex, p.last]),
      mounted: mounted.size }),
  };
}
