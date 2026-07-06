// Builds floors + rooms from /api/house. Levels stack on Y, rooms on the X-Z grid.
import * as THREE from 'three';
import { scene, focusOn } from './scene.js';

export const floorGroups = new Map();  // level -> THREE.Group
export const roomMeshes = new Map();   // roomId -> mesh
export const floorBaseY = new Map();   // level -> world Y of the floor slab
const stairGroups = [];                // stairs span two levels, so they live
                                       // outside the floor groups

let houseRoot = null;
let currentLevel = 'all';

export function buildHouse(house) {
  if (houseRoot) scene.remove(houseRoot);
  floorGroups.clear();
  roomMeshes.clear();
  floorBaseY.clear();
  stairGroups.length = 0;

  houseRoot = new THREE.Group();
  scene.add(houseRoot);

  const floors = [...(house.floors || [])].sort((a, b) => a.level - b.level);
  let y = 0;
  let center = null;

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
      if (!center) center = { x: fp.x + fp.width / 2, z: fp.z + fp.depth / 2 };
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

  if (center) focusOn(center.x, 5, center.z);
  setLevel(currentLevel);
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

function buildRoom(room, floor) {
  const fp = room.footprint;
  const color = new THREE.Color(room.color || '#8fa8bf');
  const wallsMat = new THREE.MeshStandardMaterial({
    color, transparent: true, opacity: 0.18,
    side: THREE.DoubleSide, depthWrite: false,
  });
  const slabMat = new THREE.MeshStandardMaterial({
    color: color.clone().multiplyScalar(0.55), roughness: 0.9,
    transparent: true, opacity: 0.85,
  });

  let walls, slab;
  if (fp.points && fp.points.length >= 3) {
    // polygon footprint: Shape lives in XY, so map (x, z) -> (x, -z); after
    // rotateX(-PI/2) the extrusion (+shape Z) rises along +Y and shape Y maps
    // back onto +Z, putting the footprint flat on the XZ plane
    const shape = new THREE.Shape(
      fp.points.map(([px, pz]) => new THREE.Vector2(px, -pz)));
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: room.height, bevelEnabled: false,
    });
    geo.rotateX(-Math.PI / 2);
    walls = new THREE.Mesh(geo, wallsMat);
    walls.position.set(fp.x, 0, fp.z); // anchored at bbox min corner, not centered

    const slabGeo = new THREE.ShapeGeometry(shape);
    slabGeo.rotateX(-Math.PI / 2);
    slab = new THREE.Mesh(slabGeo, slabMat);
    slab.position.y = 0.01;
  } else {
    walls = new THREE.Mesh(
      new THREE.BoxGeometry(fp.width, room.height, fp.depth), wallsMat);
    walls.position.set(fp.x + fp.width / 2, room.height / 2, fp.z + fp.depth / 2);

    slab = new THREE.Mesh(new THREE.PlaneGeometry(fp.width, fp.depth), slabMat);
    slab.rotation.x = -Math.PI / 2;
    slab.position.y = -room.height / 2 + 0.01;
  }

  walls.userData = {
    kind: 'room', roomId: room.id, roomName: room.name,
    haAreaId: room.ha_area_id, level: floor.level,
    baseOpacity: 0.18,
  };

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(walls.geometry),
    new THREE.LineBasicMaterial({ color: color.clone().multiplyScalar(1.4) }));
  edges.userData.part = 'edges';
  walls.add(edges);

  slab.userData.part = 'slab';
  walls.add(slab);

  return walls;
}

export function setLevel(level) {
  currentLevel = level;
  for (const [lvl, group] of floorGroups) {
    group.visible = level === 'all' || lvl === level;
  }
  for (const g of stairGroups) { // stairs show on both levels they connect
    g.visible = level === 'all' || g.userData.levels.includes(level);
  }
}

export function getLevel() {
  return currentLevel;
}

// Single writer for room wall opacity: keeps userData.baseOpacity in sync so
// hover (which brightens then restores baseOpacity) never clobbers the
// editor highlight or focus-mode fades.
export function setRoomOpacity(mesh, value) {
  mesh.material.opacity = value;
  mesh.userData.baseOpacity = value;
}

export function highlightRoom(roomId) {
  for (const [id, mesh] of roomMeshes) {
    setRoomOpacity(mesh, id === roomId ? 0.38 : 0.18);
  }
}
