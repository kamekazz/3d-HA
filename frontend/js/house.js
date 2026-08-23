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

// The Frontyard and Backyard are not rooms — they are the outside of the house,
// carrying the porch, deck, driveway and the outdoor cameras and lights. Three
// modules need to know that and would otherwise each keep their own copy of the
// test (environment.js had the only one), so it lives here with the geometry:
//
//  * focus.js keeps the whole house on screen when you tap one, instead of
//    isolating it the way it isolates a bedroom,
//  * objects.js lets their furniture through the House-mode sweep, because a
//    deck that vanishes on the whole-house view is a deck you can never see,
//  * environment.js excludes their pads from the building bbox it plants around.
const OUTDOOR_RE = /yard|patio|deck|outdoor|garden/i;

export function isOutdoorRoom(name) {
  return OUTDOOR_RE.test(name || '');
}

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

// Props baked into the shell that the real house does not have, cut by world
// box at load time.
//
// The shell carries a garden set the photographs contradict: a ground-level
// terrace behind the garage wing with a lounge suite and a big OPEN cantilever
// parasol, where the real house has a raised deck against the back wall with a
// CLOSED parasol on it. Most of that set is separate meshes and environment.js
// hides those. The parasol's frame and ribs are not — they are 5,631 triangles
// merged into `Root_Node`, the shell's 79k-triangle catch-all, so hiding the
// object would take the siding with it. Left in, they hang over the back lawn
// as a black spiked star, and it is the first thing the eye finds in the view
// the app flies to when you tap the Backyard.
//
// So the triangles go, not the object. They separate cleanly by height: below
// y 5.5 in this footprint is terrace slab and boundary fence, which stay; above
// it there is nothing but the parasol. Measured off the loaded shell — see the
// y-histogram in the commit message.
const SHELL_CUTS = [
  { name: 'parasol frame', min: [30, 5.5, -48], max: [45, 14, -36] },
  // The back garden's boundary fence. It encloses the whole rear lot — a closed
  // rectangle with its west line at x ~ -5, its east at x ~ 45 and its back run
  // at z ~ -50 — and there is no fence in any photograph of this garden: the
  // lawn runs to a curved rock border and a treeline, and the only fence on the
  // property is a dark wood neighbour panel at the far line. It is three times
  // the deck's footprint standing in open grass, and it was the first thing a
  // critic named in the view the app flies to when you tap the Backyard.
  //
  // The floor of the box is y 1.0, which keeps the terrace slab and the grade;
  // the near face is z -26, which keeps the rear elevation (its wall is at
  // -24.5) and the garage wing (-10.9). Measured on a 5 ft grid: the perimeter
  // cells carry 90-740 triangles each and the interior cells 1-13, which is how
  // you can tell it is a fence and not a lawn.
  { name: 'rear boundary fence', min: [-8, 1.0, -80], max: [48, 9, -26] },
  // ...and its east line, which carries on north up the side of the garage
  // wing. Kept to y 7 and to z -11: the wing's own rear wall is at z -10.9 and
  // rises past y 11, and the fence run never goes above 6.5.
  { name: 'fence east return', min: [42, 1.0, -27], max: [48, 7, -11] },
  // The same fence's bottom rails, left behind when the boxes above took its
  // pickets: four thin bars at y 0.654-0.765, about 0.6 ft proud of the lawn,
  // rendering as white lines lying on the grass. Boxes measured off the loaded
  // shell by the exterior builder and re-verified here. Safe at this height:
  // the terrain there sits at 0.16 and the raised pad at 2.13, so neither is
  // inside them, and the only other things they touch are legs of props
  // environment.js already hides.
  { name: 'fence rails, rear run', min: [24.5, 0.45, -51.6], max: [48.0, 1.05, -29.5] },
  { name: 'fence rail, west strip', min: [2.8, 0.45, -54.6], max: [14.8, 1.05, -52.8] },
];

function maskShellProps(shell) {
  shell.updateWorldMatrix(true, true);
  // SketchUp exports its edge overlay as a LineSegments object beside the
  // meshes, and this shell carries one. It is invisible where it coincides with
  // a shaded face, so it costs nothing to keep — until you delete the faces it
  // was drawn over, and then the parasol's ribs are still there as bare white
  // lines radiating out of thin air. Nothing wants a wireframe over a shaded
  // model, so the whole overlay goes. Matched on type, not name: the names in
  // this file are SketchUp component ids a re-export would renumber.
  shell.traverse((o) => {
    if (o.isLineSegments || o.isLine || o.isLineLoop) o.visible = false;
  });
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  shell.traverse((o) => {
    if (!o.isMesh || !o.geometry?.attributes?.position) return;
    const geo = o.geometry;
    const pos = geo.attributes.position;
    const idx = geo.index;
    const count = idx ? idx.count : pos.count;
    if (count % 3 !== 0) return;
    const at = (i) => (idx ? idx.getX(i) : i);
    const keep = [];
    let cut = 0;
    for (let t = 0; t < count; t += 3) {
      a.fromBufferAttribute(pos, at(t)).applyMatrix4(o.matrixWorld);
      b.fromBufferAttribute(pos, at(t + 1)).applyMatrix4(o.matrixWorld);
      c.fromBufferAttribute(pos, at(t + 2)).applyMatrix4(o.matrixWorld);
      const x = (a.x + b.x + c.x) / 3;
      const y = (a.y + b.y + c.y) / 3;
      const z = (a.z + b.z + c.z) / 3;
      const hit = SHELL_CUTS.some((k) =>
        x >= k.min[0] && x <= k.max[0] && y >= k.min[1] && y <= k.max[1]
        && z >= k.min[2] && z <= k.max[2]);
      if (hit) { cut++; continue; }
      keep.push(at(t), at(t + 1), at(t + 2));
    }
    if (!cut) return;
    geo.setIndex(keep);
    geo.computeBoundingBox();
    geo.computeBoundingSphere();
    console.info(`shell: cut ${cut} prop triangles from ${o.name || '(unnamed)'}`);
  });
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
  // after the transform and the add, never before: SHELL_CUTS is expressed in
  // world feet, and until the shell is placed its matrixWorld is the identity
  maskShellProps(shell);
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
// How far the floor plinth drops below the slab. This is the chunky colored rim
// of the floor plate; it is built per edge as a child of that edge's wall, so it
// fades out with it and an open side of the cutaway shows no kerb at all.
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

    // An opening that spans its ENTIRE wall, floor to ceiling, means "there is
    // no wall here" — the case is a polygon room whose footprint notches around
    // a stairwell, where the two edges facing the void are not walls at all.
    // Cutting it as a hole cannot express that: the run below is extended by
    // one thickness past each end, and an opening's offset is clamped to
    // [0, len], so the overshoot always survives as a floor-to-ceiling post at
    // each end — two of them meeting in a solid column at the notch corner.
    // Pushing the hole wider instead makes ExtrudeGeometry triangulate garbage.
    // So skip the wall outright. Its plinth skirt and accent rim are its
    // children and go with it, which is what you want: they would otherwise
    // ring the void in saturated colour.
    if ((room.openings || []).some((op) => op.edge_index === i
        && op.offset <= 0 && op.offset + op.width >= len
        && op.elevation <= 0.01
        && op.elevation + op.height >= room.height - 0.02)) continue;

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

    // The plinth skirt and the accent rim belong to THIS edge, not to the room.
    // They used to be one room-wide mesh each and neither ever faded, so a room
    // whose near walls had dissolved still showed a colored kerb along the open
    // side and a bright outline tracing the wall that was gone — the leftover
    // "frame" of a cutaway. Parented to the wall, they share its local frame
    // (so the geometry math below is the wall's verbatim), inherit its
    // visibility, and applyWallOpacity fades them with it.
    //
    // The skirt is a bare quad on the wall's OUTER face, not a solid like the
    // wall: the outer face is the only part of a kerb you can ever see, and a
    // solid would also have end caps. Those caps are the whole problem — an end
    // cap faces along its wall, so at a corner where the neighbouring wall has
    // faded it is left pointing straight at the camera as a colored nub in the
    // open side, which is the artefact this rewrite exists to remove. A quad
    // has none, and it goes edge-on to nothing. The bottom cap below closes the
    // box. DoubleSide because the quad is hidden under the slab from inside the
    // room anyway, so which way it is wound never matters.
    const skirtGeo = new THREE.ShapeGeometry(new THREE.Shape([
      new THREE.Vector2(0, -PLINTH_DEPTH), new THREE.Vector2(len, -PLINTH_DEPTH),
      new THREE.Vector2(len, 0), new THREE.Vector2(0, 0),
    ]));
    skirtGeo.translate(0, 0, -t);
    skirtGeo.rotateY(angle);
    skirtGeo.translate(ax - mx, 0, az - mz);
    // transparent up front at opacity 1, like the wall material: flipping that
    // flag at runtime is what recompiles the shader.
    const skirt = new THREE.Mesh(skirtGeo, new THREE.MeshStandardMaterial({
      color: accent.clone().multiplyScalar(0.85), roughness: 0.85,
      side: THREE.DoubleSide, transparent: true, opacity: 1.0,
    }));
    skirt.userData = { part: 'plinth', edgeIndex: i };
    wall.add(skirt);
    wall.userData.skirt = skirt;

    const rim = new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(ax - mx, 0.01, az - mz),
        new THREE.Vector3(bx - mx, 0.01, bz - mz),
      ]),
      new THREE.LineBasicMaterial({
        color: accent.clone().multiplyScalar(1.4),
        transparent: true, opacity: 1.0,
      }));
    // part 'edges' is load-bearing: main.js pick() skips outlines when hunting
    // for the nearest opaque occluder.
    rim.userData = { part: 'edges', edgeIndex: i };
    wall.add(rim);
    wall.userData.rim = rim;

    wallMeshes.push(wall);
  }

  // The room mesh itself carries no geometry any more — it is the identity the
  // rest of the app holds (roomMeshes, picking, userData) and the parent of the
  // per-edge walls (each carrying its own plinth skirt and accent rim), the
  // slab and the plinth's bottom cap.
  walls = new THREE.Mesh(new THREE.BufferGeometry(), wallsMat);
  walls.position.set(fp.x, 0, fp.z);
  for (const wall of wallMeshes) walls.add(wall);

  for (const [id, hinge] of openingMeshes) {
    if (room.openings?.some(o => o.id === id)) {
      walls.add(hinge);
    }
  }

  // A void room (`is_void`) is a stairwell shaft: its footprint is a HOLE in
  // this floor, so it gets walls but no floor plate. Skipping the slab (and the
  // plinth cap below) is the only way to see down a well — the app draws one
  // opaque slab per footprint and a polygon cannot carry an interior hole, so
  // the shaft has to be its own room and that room has to be floorless.
  const isVoid = !!room.is_void;
  const slabShape = new THREE.Shape(pts.map(([px, pz]) => new THREE.Vector2(px, -pz)));
  if (!isVoid) {
    const slabGeo = new THREE.ShapeGeometry(slabShape);
    slabGeo.rotateX(-Math.PI / 2);
    slab = new THREE.Mesh(slabGeo, slabMat);
    slab.position.y = 0.01;
  }

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

  if (slab) {
    slab.userData.part = 'slab';
    walls.add(slab);
  }

  // The plinth gives the floor a body, so a room whose near walls have faded
  // still reads as a solid platform instead of a floating decal. Its rim is
  // built per edge above, with the wall it belongs to; this is only the bottom
  // cap that closes the box, so you never look up into the underside of a floor
  // plate in the stacked whole-house view (maxPolarAngle keeps the camera above
  // its target, but the target sits well below an upper floor). It belongs to
  // no single wall, so it never fades. Deliberately a separate mesh from the
  // slab — roomlights.js writes slab.material.emissive directly and must keep
  // meeting one material.
  //
  // BackSide is the load-bearing part: the cap sits half a foot under the slab,
  // so seen from above its projection slides out past the slab's along the near
  // edges and paints exactly the colored kerb the fading skirt just removed.
  // Facing it down means it only ever draws when you are actually beneath it.
  if (!isVoid) {
    const capGeo = new THREE.ShapeGeometry(slabShape);
    capGeo.rotateX(-Math.PI / 2);
    const cap = new THREE.Mesh(capGeo, new THREE.MeshStandardMaterial({
      color: accent.clone().multiplyScalar(0.85), roughness: 0.85,
      side: THREE.BackSide,
    }));
    cap.position.y = -PLINTH_DEPTH;
    cap.userData.part = 'plinthCap';
    walls.add(cap);
  }

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

// The BUILDING's world box, as opposed to the shell's whole-lot bounds. The
// shell is one merged mesh per material, so its lot pad, driveway and fences
// share a bbox with the house and a plain setFromObject lands on the lot line —
// 113 x 152 ft here, against a house about half that. The roof masses are the
// exception: they are separate meshes that start a storey up, so "elevated and
// thick" isolates them, and a roof outline is the building outline. Returned
// dropped to the ground (min.y = 0) because every caller wants the mass, not
// the roof. Null when there is no shell, or no mesh that reads as a roof.
//
// environment.js anchors the foundation beds and driveway props off this, and
// focus.js frames the yards against it.
export function getBuildingBox() {
  if (!houseShell) return null;
  houseShell.updateWorldMatrix(true, true);
  const box = new THREE.Box3();
  const mb = new THREE.Box3();
  houseShell.traverse((o) => {
    if (!o.isMesh) return;
    mb.setFromObject(o);
    if (mb.min.y >= 8 && mb.max.y - mb.min.y >= 5) box.union(mb);
  });
  if (box.isEmpty()) return null;
  box.min.y = 0;
  return box;
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
    // The edge's plinth skirt and accent rim go with it. They are children of
    // the wall, so visibility follows for free, but opacity lives on the
    // material and has to be written.
    const { skirt, rim } = wall.userData;
    if (skirt) {
      skirt.material.opacity = op;
      skirt.material.depthWrite = op > 0.5;
    }
    if (rim) rim.material.opacity = op;
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
