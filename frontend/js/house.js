import * as THREE from 'three';
import { scene, focusOn, frameInitialView } from './scene.js';
import { getTiledTexture, textureSize } from './textures.js';
import { onStateApplied, isOn } from './state.js';
import { getInstance } from './models.js';

export const floorGroups = new Map();  // level -> THREE.Group
export const roomMeshes = new Map();   // roomId -> mesh
export const openingMeshes = new Map(); // opId -> THREE.Group (hinge)
export const floorBaseY = new Map();   // level -> world Y of the floor slab
export const stairGroups = [];         // stairs span two levels, so they live
                                       // outside the floor groups

let houseRoot = null;
let currentLevel = 'all';

// The whole-house shell model: when configured, the "House" (level 'all') view
// hides the generated geometry and shows this single model instead. Loads
// async; until it resolves (or if it fails) the view falls back to the normal
// stacked all-floors geometry. See setLevel below.
let houseShell = null;    // loaded shell root Group, or null (not loaded/failed)
let shellConfig = null;   // { model_id, x, y, z, rot_y, scale } from the payload

// The opening camera shot is set once, from the first build that has rooms;
// later rebuilds (edits, undo, sync) must not yank the camera around.
let initialViewDone = false;

export function buildHouse(house) {
  if (houseRoot) scene.remove(houseRoot);
  floorGroups.clear();
  roomMeshes.clear();
  openingMeshes.clear();
  floorBaseY.clear();
  stairGroups.length = 0;
  houseShell = null; // the old shell went away with the old houseRoot

  houseRoot = new THREE.Group();
  scene.add(houseRoot);

  const floors = [...(house.floors || [])].sort((a, b) => a.level - b.level);
  let y = 0;
  let bbox = null; // whole-house footprint across all floors

  floors.forEach((floor, i) => {
    floorBaseY.set(floor.level, y);
    const group = new THREE.Group();
    group.position.y = y;
    group.userData = { level: floor.level, name: floor.name };
    floorGroups.set(floor.level, group);
    houseRoot.add(group);

    for (const room of floor.rooms || []) {
      const mesh = buildRoom(room, floor);
      group.add(mesh);
      roomMeshes.set(room.id, mesh);
      const fp = room.footprint;
      if (!bbox) {
        bbox = { minX: fp.x, minZ: fp.z, maxX: fp.x + fp.width, maxZ: fp.z + fp.depth };
      } else {
        bbox.minX = Math.min(bbox.minX, fp.x);
        bbox.minZ = Math.min(bbox.minZ, fp.z);
        bbox.maxX = Math.max(bbox.maxX, fp.x + fp.width);
        bbox.maxZ = Math.max(bbox.maxZ, fp.z + fp.depth);
      }
    }

    // stairs rise from this floor's base up to the next floor's base; they
    // belong to both levels, so they sit on the root, not in a floor group
    const upperLevel = floors[i + 1] ? floors[i + 1].level : floor.level;
    for (const st of floor.stairs || []) {
      const stairs = buildStairs(st, floor, upperLevel, y);
      houseRoot.add(stairs);
      stairGroups.push(stairs);
    }

    y += floor.floor_height || 10.0;
  });

  if (bbox) {
    const cx = (bbox.minX + bbox.maxX) / 2;
    const cz = (bbox.minZ + bbox.maxZ) / 2;
    if (!initialViewDone) {
      initialViewDone = true;
      frameInitialView(cx, cz, bbox.maxX - bbox.minX, bbox.maxZ - bbox.minZ, y);
    } else {
      focusOn(cx, 5, cz);
    }
  }
  setLevel(currentLevel);

  // Kick off the whole-house shell (async). setLevel re-runs once it resolves.
  shellConfig = house.house_shell && house.house_shell.model_id
    ? { ...house.house_shell } : null;
  if (shellConfig) loadHouseShell(shellConfig);
}

function applyShellTransform(root, cfg) {
  root.position.set(cfg.x || 0, cfg.y || 0, cfg.z || 0);
  root.rotation.y = cfg.rot_y || 0;
  root.scale.setScalar(cfg.scale || 1); // multiplies the pivot's meters->feet
}

async function loadHouseShell(cfg) {
  const root = houseRoot; // the root this shell belongs to
  let pivot;
  try {
    pivot = await getInstance(cfg.model_id, 'bottom'); // floor seated at Y=0
  } catch (err) {
    console.warn(`house shell model ${cfg.model_id} failed to load:`, err);
    // Loudly, not just in the console: a missing shell looks like "the house
    // vanished" with the rest of the scene intact, which reads as a render bug
    // rather than the deploy problem it usually is (see
    // docs/TROUBLESHOOTING-house-shell.md). ui.js turns this into a banner —
    // an event, not a direct call, because ui.js already imports this module.
    window.dispatchEvent(new CustomEvent('shellLoadFailed', {
      detail: { modelId: cfg.model_id, error: err },
    }));
    return; // stay in the generated-geometry fallback
  }
  if (houseRoot !== root) return; // a newer rebuild superseded this one
  const shell = new THREE.Group();
  // kind lets drag.js recognise it; pickable:false keeps pick() from selecting
  // it as a click target (it's a backdrop). drag.js uses its own reference.
  shell.userData = { kind: 'house-shell', pickable: false };
  shell.add(pivot);
  // The shell is the only real sun-shadow caster (generated FrontSide walls
  // never opt in — see scene.js). receiveShadow self-shadows eaves/dormers.
  shell.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  applyShellTransform(shell, cfg);
  root.add(shell);
  houseShell = shell;
  setLevel(currentLevel); // a shell now exists — apply House mode if on 'all'
}

function buildStairs(st, floor, upperLevel, baseY) {
  const rise = floor.floor_height || 10.0;
  const group = new THREE.Group();
  group.position.set(st.x, baseY, st.z);
  group.userData = { levels: [floor.level, upperLevel] };

  const mat = new THREE.MeshStandardMaterial({ color: 0x8b95a5, roughness: 0.8 });
  const shared = { kind: 'stairs', roomName: st.name || 'Stairs', level: floor.level };
  const alongX = st.direction === 'e' || st.direction === 'w';
  const run = alongX ? st.width : st.depth;   // length in the ascent axis
  const across = alongX ? st.depth : st.width;
  const steps = Math.max(2, Math.round(rise / 0.6)); // ~7 in per riser
  const tread = run / steps;

  for (let i = 0; i < steps; i++) {
    const h = (rise * (i + 1)) / steps;
    const geo = alongX
      ? new THREE.BoxGeometry(tread, h, across)
      : new THREE.BoxGeometry(across, h, tread);
    const step = new THREE.Mesh(geo, mat);
    // step 0 (lowest) sits at the start of the run, ascending toward the
    // direction the arrow points: n = -Z, s = +Z, e = +X, w = -X
    const along = st.direction === 'n' || st.direction === 'w'
      ? run - (i + 0.5) * tread   // ascending toward the min edge
      : (i + 0.5) * tread;        // ascending toward the max edge
    step.position.set(
      alongX ? along : across / 2,
      h / 2,
      alongX ? across / 2 : along);
    step.userData = shared;
    group.add(step);
  }
  return group;
}

// BoxGeometry UVs run 0..1 per face; stretch them to world feet so a wall
// texture tiles at its preset ft-per-repeat regardless of room size. Faces
// come in the fixed order +X,-X,+Y,-Y,+Z,-Z, 4 vertices each.
function worldScaleBoxUVs(geo, w, h, d) {
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  const uv = geo.attributes.uv;
  for (let face = 0; face < 6; face++) {
    const [su, sv] = dims[face];
    for (let i = face * 4; i < face * 4 + 4; i++) {
      uv.setXY(i, uv.getX(i) * su, uv.getY(i) * sv);
    }
  }
  uv.needsUpdate = true;
}

// Wall body thickness, feet. Walls extrude OUTWARD from the footprint line so
// the inner face stays exactly where the old zero-thickness fins were: every
// hand-placed furniture piece is flush against that plane and would end up
// embedded in the wall if the mass grew inward.
const WALL_THICKNESS = 0.35;
// How far the floor plinth drops below the slab. This is the chunky colored
// rim you see along the open sides of a Sims-style cutaway.
const PLINTH_DEPTH = 0.5;

function buildRoom(room, floor) {
  const fp = room.footprint;
  const isPoly = fp.points && fp.points.length >= 3;
  // room.color is the accent (edge outlines + plinth rim here, fill in the 2D
  // planner); wall/floor surfaces have their own color + optional preset texture
  const accent = new THREE.Color(room.color || '#8fa8bf');

  // Polygon geometry (Extrude/Shape) has UVs in shape coords = world feet,
  // so one repeat per `size` ft means repeat 1/size; rect geometry has 0..1
  // UVs, scaled to feet below (box) or via repeat = dims/size (plane slab).
  const ws = textureSize(room.wall_texture);
  const wallTex = getTiledTexture(room.wall_texture, 1 / ws, 1 / ws);
  const fs = textureSize(room.floor_texture);
  const floorTex = isPoly
    ? getTiledTexture(room.floor_texture, 1 / fs, 1 / fs)
    : getTiledTexture(room.floor_texture, fp.width / fs, fp.depth / fs);

  // Dollhouse walls. These used to be zero-thickness fins drawn FrontSide with
  // inward normals, so the GPU backface-culled whichever ones the camera stood
  // behind — free, but it popped at exactly 90 degrees and left mounted art
  // floating. Walls have a body now, which does NOT backface-cull, so
  // cutaway.js fades the near ones out per frame instead. That means one mesh
  // AND one material per edge: this is only the template, every wall gets a
  // clone (a shared material can't hold an independent opacity).
  // transparent stays true at opacity 1 so the fades never recompile the
  // shader; polygonOffset pushes wall triangles back so the slab and the
  // accent edge lines win the depth fight against the coincident wall caps.
  const wallsMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(room.wall_color || '#f2ede3'),
    map: wallTex,
    transparent: true, opacity: 1.0,
    side: THREE.FrontSide, depthWrite: true, roughness: 0.95,
    polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  });
  // Must stay MeshStandardMaterial on a child with userData.part === 'slab':
  // roomlights.js drives its emissive for the night glow.
  const slabMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(room.floor_color || '#e5decf'),
    map: floorTex, roughness: 0.9,
    polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
  });

  let walls, slab;
  const pts = isPoly ? fp.points.map(([px, pz]) => [px, pz])
    : [[0, 0], [fp.width, 0], [fp.width, fp.depth], [0, fp.depth]];

  const t = WALL_THICKNESS;
  const wallMeshes = [];
  for (let i = 0; i < pts.length; i++) {
    const ax = pts[i][0], az = pts[i][1];
    const bx = pts[(i + 1) % pts.length][0], bz = pts[(i + 1) % pts.length][1];
    const dx = bx - ax, dz = bz - az;
    const len = Math.hypot(dx, dz);
    if (len < 0.01) continue;

    // The run is extended by one thickness past each end so neighbouring walls
    // overlap in a t x t block at every corner — without it each convex corner
    // shows a square notch. The overshoot is buried inside the adjoining wall's
    // mass, so it costs nothing visually. Hole offsets share this u frame and
    // therefore need no shifting.
    const shape = new THREE.Shape();
    shape.moveTo(-t, 0);
    shape.lineTo(len + t, 0);
    shape.lineTo(len + t, room.height);
    shape.lineTo(-t, room.height);
    shape.lineTo(-t, 0);

    for (const op of room.openings || []) {
      if (op.edge_index === i) {
        let off = op.offset;
        if (off < 0) off = 0;
        if (off + op.width > len) off = Math.max(0, len - op.width);

        const hole = new THREE.Path();
        hole.moveTo(off, op.elevation);
        hole.lineTo(off + op.width, op.elevation);
        hole.lineTo(off + op.width, op.elevation + op.height);
        hole.lineTo(off, op.elevation + op.height);
        hole.lineTo(off, op.elevation);
        shape.holes.push(hole);

        // A `passage` is a cased opening — an arch or a doorway with no door in
        // it — so the hole above is the whole point and it gets no panel at all.
        // Without this it was handed the window material and every doorway
        // between two rooms carried a faint pane of glass across it.
        if (op.type === 'passage') continue;

        const isDoor = op.type === 'door';
        const depth = isDoor ? 0.2 : 0.3;
        // These panels fill the hole the shape above cuts. They used to be a
        // saddle-brown slab and a flat teal one; the teal read so unlike glass
        // that room builders avoided cutting openings at all and faked every
        // window as a flush decal on the wall. Glass is now a faint cool tint
        // at low opacity with a tight specular, and a door is painted white
        // like the real ones in this house — so a real opening is now the better
        // option, which is what the dollhouse view needs.
        // transparent is on even for an opaque door: the panel fades out with
        // its wall, and flipping that flag at runtime would recompile the shader.
        const panelMat = new THREE.MeshStandardMaterial({
          color: isDoor ? 0xf1ede6 : 0xdbe7ef,
          transparent: true,
          opacity: isDoor ? 1.0 : 0.22,
          roughness: isDoor ? 0.75 : 0.06,
          metalness: 0.0,
          side: THREE.DoubleSide
        });
        const panelGeo = new THREE.BoxGeometry(op.width, op.height, depth);
        const panel = new THREE.Mesh(panelGeo, panelMat);

        const hinge = new THREE.Group();
        panel.position.set(op.width / 2, op.height / 2, 0);
        hinge.add(panel);

        const angle = Math.atan2(-dz, dx);
        const u = [dx / len, dz / len];
        hinge.position.set(ax + u[0] * off, op.elevation, az + u[1] * off);
        hinge.rotation.y = angle;
        // edgeIndex + baseOpacity: cutaway.js fades a panel out with the wall
        // it pierces, otherwise a door hangs in the gap where its wall was.
        hinge.userData = {
          id: op.id, entityId: op.entity_id, type: op.type, baseAngle: angle,
          edgeIndex: i, baseOpacity: isDoor ? 1.0 : 0.22,
        };
        openingMeshes.set(op.id, hinge);
        // Will add to walls mesh after it's created
      }
    }

    // Extrude along the shape's local +Z (which the rotateY below aims INTO the
    // room), then pull it back a full thickness so the inner face lands on the
    // footprint line and the mass sits outside it.
    const geo = new THREE.ExtrudeGeometry(shape, { depth: t, bevelEnabled: false });
    geo.translate(0, 0, -t);
    const angle = Math.atan2(-dz, dx);
    geo.rotateY(angle);
    // Each wall is its own mesh anchored at the edge midpoint, so cutaway.js
    // can read a world position straight off it.
    const mx = (ax + bx) / 2, mz = (az + bz) / 2;
    geo.translate(ax - mx, 0, az - mz);

    const uv = geo.attributes.uv;
    for (let k = 0; k < uv.count; k++) {
      uv.setXY(k, uv.getX(k) / ws, uv.getY(k) / ws);
    }

    const wall = new THREE.Mesh(geo, wallsMat.clone());
    wall.position.set(mx, 0, mz);
    // nx/nz is the INWARD normal: the direction the painted face looks. The
    // wall is visible exactly when the camera sits on that side of it.
    wall.userData = {
      part: 'wall', edgeIndex: i, nx: -dz / len, nz: dx / len, fade: 1,
      hx: dx / 2, hz: dz / 2, // midpoint -> end b, for point-to-wall distance
    };
    wallMeshes.push(wall);
  }

  // The room mesh itself carries no geometry any more — it is the identity the
  // rest of the app holds (roomMeshes, picking, userData) and the parent of the
  // per-edge walls, the slab, the plinth and the accent outline.
  walls = new THREE.Mesh(new THREE.BufferGeometry(), wallsMat);
  walls.position.set(fp.x, 0, fp.z);
  for (const wall of wallMeshes) walls.add(wall);

  for (const [id, hinge] of openingMeshes) {
    if (room.openings?.some(o => o.id === id)) {
      walls.add(hinge);
    }
  }

  const slabShape = new THREE.Shape(pts.map(([px, pz]) => new THREE.Vector2(px, -pz)));
  const slabGeo = new THREE.ShapeGeometry(slabShape);
  slabGeo.rotateX(-Math.PI / 2);
  slab = new THREE.Mesh(slabGeo, slabMat);
  slab.position.y = 0.01;

  walls.userData = {
    kind: 'room', roomId: room.id, roomName: room.name,
    haAreaId: room.ha_area_id, level: floor.level,
    baseOpacity: 1.0, baseEmissive: 0, accent,
    // cutaway.js walks these every frame, so they are cached rather than
    // re-filtered out of children; wallByEdge is keyed by edge index, which
    // skips any degenerate edge the loop above dropped.
    wallList: wallMeshes,
    wallByEdge: new Map(wallMeshes.map((w) => [w.userData.edgeIndex, w])),
  };

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(slabGeo),
    new THREE.LineBasicMaterial({ color: accent.clone().multiplyScalar(1.4) }));
  edges.userData.part = 'edges';
  edges.position.y = 0.01;
  walls.add(edges);

  slab.userData.part = 'slab';
  walls.add(slab);

  // The plinth: the floor given a body, so a room whose near walls have faded
  // away still reads as a solid platform instead of a floating decal. Built
  // from the same polygon and dropped below the slab, so only its rim shows.
  // Deliberately a separate mesh from the slab — roomlights.js writes
  // slab.material.emissive directly and must keep meeting a single material.
  const plinthGeo = new THREE.ExtrudeGeometry(slabShape,
    { depth: PLINTH_DEPTH, bevelEnabled: false });
  plinthGeo.rotateX(-Math.PI / 2);
  plinthGeo.translate(0, -PLINTH_DEPTH, 0);
  const plinth = new THREE.Mesh(plinthGeo, new THREE.MeshStandardMaterial({
    color: accent.clone().multiplyScalar(0.85), roughness: 0.85,
  }));
  plinth.userData.part = 'plinth';
  walls.add(plinth);

  return walls;
}

export function setLevel(level) {
  currentLevel = level;
  // House mode = the 'all' view WITH a shell loaded: hide the generated
  // geometry (walls/slabs/objects) + stairs and show the shell instead, but
  // keep device markers (kind 'device') visible/clickable. Without a shell,
  // 'all' behaves exactly as before (stacked floors).
  const houseMode = level === 'all' && !!houseShell;
  for (const [lvl, group] of floorGroups) {
    group.visible = houseMode ? true : (level === 'all' || lvl === level);
    for (const child of group.children) {
      // markers, label sprites and furniture own their own visibility
      // (devices.js / labels.js / objects.js) — objects.js needs to keep other
      // rooms' furniture hidden during room focus, which this sweep would undo
      if (child.userData.kind === 'device' || child.userData.kind === 'object'
          || child.isSprite) continue;
      child.visible = !houseMode; // rooms hidden only in House mode
    }
  }
  for (const g of stairGroups) { // stairs show on both levels they connect
    g.visible = houseMode ? false : (level === 'all' || g.userData.levels.includes(level));
  }
  if (houseShell) houseShell.visible = houseMode;
  // window event (not a callback registry) so devices.js/ui.js can react to
  // entering/leaving House mode without a circular import (house→state→devices)
  window.dispatchEvent(new CustomEvent('levelChanged', { detail: { level, houseMode } }));
}

export function getLevel() {
  return currentLevel;
}

// Live-update the shell's transform (numeric panel / drag) without a rebuild.
export function setShellTransform(t) {
  if (!shellConfig) return;
  Object.assign(shellConfig, t);
  if (houseShell) applyShellTransform(houseShell, shellConfig);
}

// The shell root Group (for drag.js), or null when no shell is loaded.
export function getShellRoot() {
  return houseShell;
}

// Current shell config { model_id, x, y, z, rot_y, scale }, or null.
export function getShellConfig() {
  return shellConfig ? { ...shellConfig } : null;
}

// The per-edge wall meshes of a room, in build order.
export function wallParts(mesh) {
  return mesh.userData.wallList
    || mesh.children.filter((c) => c.userData.part === 'wall');
}

// Single writer for a wall's final opacity. Two independent things dim a wall
// and they multiply: the room's ghost level (focus mode) and the camera-facing
// fade cutaway.js maintains in userData.fade. Both go through here so neither
// can clobber the other. depthWrite drops on a nearly-invisible wall so it
// stops occluding what is behind it.
export function applyWallOpacity(wall, baseOpacity) {
  const op = baseOpacity * (wall.userData.fade ?? 1);
  const mat = wall.material;
  if (Math.abs(mat.opacity - op) > 0.002) {
    mat.opacity = op;
    mat.depthWrite = op > 0.5;
  }
  wall.visible = op > 0.01;
}

// Single writer for room wall opacity (used by focus-mode fades): keeps
// userData.baseOpacity in sync and re-composites every wall against its
// current camera-facing fade.
export function setRoomOpacity(mesh, value) {
  mesh.userData.baseOpacity = value;
  for (const wall of wallParts(mesh)) applyWallOpacity(wall, value);
}

// Paint the accent glow onto a room's walls WITHOUT disturbing the stored
// level. Hover uses this: it needs to add a transient boost and then put the
// selection glow back, which it can't do if writing also rewrites the baseline.
export function paintRoomEmissive(mesh, intensity) {
  for (const wall of wallParts(mesh)) {
    wall.material.emissive.copy(mesh.userData.accent);
    wall.material.emissiveIntensity = intensity;
  }
}

// Single writer for the accent-tinted glow that marks hover/selection now
// that walls are opaque (opacity can't signal anymore). Hover reads
// userData.baseEmissive to restore, mirroring the baseOpacity pattern.
export function setRoomEmissive(mesh, intensity) {
  paintRoomEmissive(mesh, intensity);
  mesh.userData.baseEmissive = intensity;
}

export function highlightRoom(roomId) {
  for (const [id, mesh] of roomMeshes) {
    setRoomEmissive(mesh, id === roomId ? 0.35 : 0);
  }
}

onStateApplied((entityId) => {
  const targetAngleDelta = Math.PI / 2; // open 90 degrees inward
  for (const [id, mesh] of openingMeshes) {
    if (!mesh.userData.entityId) continue;
    if (entityId && mesh.userData.entityId !== entityId) continue;
    const active = isOn(mesh.userData.entityId);
    mesh.rotation.y = mesh.userData.baseAngle + (active ? targetAngleDelta : 0);
  }
});
