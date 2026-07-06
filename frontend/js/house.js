// Builds floors + rooms from /api/house. Levels stack on Y, rooms on the X-Z grid.
import * as THREE from 'three';
import { scene, focusOn } from './scene.js';

export const floorGroups = new Map();  // level -> THREE.Group
export const roomMeshes = new Map();   // roomId -> mesh
export const floorBaseY = new Map();   // level -> world Y of the floor slab

let houseRoot = null;
let currentLevel = 'all';

export function buildHouse(house) {
  if (houseRoot) scene.remove(houseRoot);
  floorGroups.clear();
  roomMeshes.clear();
  floorBaseY.clear();

  houseRoot = new THREE.Group();
  scene.add(houseRoot);

  const floors = [...(house.floors || [])].sort((a, b) => a.level - b.level);
  let y = 0;
  let center = null;

  for (const floor of floors) {
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
    y += floor.floor_height || 10.0;
  }

  if (center) focusOn(center.x, 5, center.z);
  setLevel(currentLevel);
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
