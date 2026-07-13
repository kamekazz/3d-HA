// Floor presentation mode: viewing a single level swaps the outdoor world for
// a dark studio backdrop (radial-gradient texture, no fog), flies the camera
// in to frame just that floor, and locks zoom-out to that framing shot —
// so a lone floor never floats over the lawn. Selecting House ('all')
// restores the daylight sky, the house zoom cap, and the pose you left from.
// The yard/weather meshes hide themselves on the same levelChanged event
// (environment.js / weather.js); daylight.js skips background/fog writes
// while the backdrop texture is installed.
import * as THREE from 'three';
import { scene, camera, controls, flyTo, getViewPose, setMaxZoom, MIN_ZOOM, MAX_ZOOM } from './scene.js';
import { roomMeshes } from './house.js';
import { repaintSky } from './daylight.js';

let backdropTex = null;
let savedBg = null;   // daylight-owned background Color while overridden
let savedFog = null;
let housePose = null; // camera pose captured when leaving the House view
let houseMax = null;  // MAX_ZOOM captured when leaving the House view
let activeLevel = 'all';

// vertical-ish radial gradient: a lifted slate glow behind the model fading
// to near-black at the corners — reads as a product-viewer studio sweep
function makeBackdrop() {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(256, 210, 60, 256, 256, 350);
  grad.addColorStop(0, '#33405a');
  grad.addColorStop(0.55, '#1b2232');
  grad.addColorStop(1, '#0a0d14');
  g.fillStyle = grad;
  g.fillRect(0, 0, 512, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function enterBackdrop() {
  if (savedBg) return; // already in floor mode (floor -> floor switch)
  backdropTex = backdropTex || makeBackdrop();
  savedBg = scene.background;
  savedFog = scene.fog;
  scene.background = backdropTex;
  scene.fog = null; // nothing distant to hide; the gradient carries the depth
}

function exitBackdrop() {
  if (!savedBg) return;
  scene.background = savedBg; // daylight.js resumes driving it
  scene.fog = savedFog;
  savedBg = null;
  savedFog = null;
  repaintSky(); // push current sky/fog values — they eased while we hid them
}

function floorCenter(level) {
  const box = new THREE.Box3();
  const mb = new THREE.Box3();
  for (const mesh of roomMeshes.values()) {
    if (mesh.userData.level !== level) continue;
    box.union(mb.setFromObject(mesh));
  }
  return box.isEmpty() ? null : box;
}

// Fly to a ~50°-elevation dollhouse shot that fits the floor's rooms, keeping
// the user's current azimuth so the switch doesn't spin the world. The sphere
// fit overestimates for a flat slab, so the padding leans tight (0.92) — the
// floor should fill the frame, not float in it.
function frameFloor(level) {
  const box = floorCenter(level);
  if (!box) return; // empty floor: keep the current pose/zoom cap
  const center = box.getCenter(new THREE.Vector3());
  const radius = 0.5 * box.getSize(new THREE.Vector3()).length();
  const vFov = THREE.MathUtils.degToRad(camera.fov);
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const fit = Math.min(vFov, hFov);
  const dist = Math.max(0.92 * radius / Math.sin(fit / 2), MIN_ZOOM * 1.5);
  const az = Math.atan2(camera.position.x - center.x, camera.position.z - center.z);
  const polar = 0.68; // angle from vertical
  flyTo(new THREE.Vector3(
    center.x + dist * Math.sin(polar) * Math.sin(az),
    center.y + dist * Math.cos(polar),
    center.z + dist * Math.sin(polar) * Math.cos(az)), center);
  setMaxZoom(dist * 1.12); // barely past the framing shot — that's max zoom-out
}

// Rebuilds re-fire setLevel with the same level after re-targeting the orbit
// at the whole-house center (house.js focusOn) — swing the view back onto the
// floor without flying the camera anywhere.
function recenterFloor(level) {
  const box = floorCenter(level);
  if (!box) return;
  const center = box.getCenter(new THREE.Vector3());
  if (controls.target.distanceTo(center) > 0.5) {
    flyTo(camera.position, center);
  }
}

export function initFloorView() {
  window.addEventListener('levelChanged', (e) => {
    const level = e.detail.level;
    if (level !== 'all') {
      enterBackdrop();
      if (activeLevel === 'all') {
        housePose = getViewPose();
        houseMax = MAX_ZOOM;
      }
      // panning would drift the floor off-center; orbit + zoom is enough here
      controls.enablePan = false;
      if (level !== activeLevel) frameFloor(level);
      else recenterFloor(level); // rebuild on the same level — recenter only
    } else {
      exitBackdrop();
      controls.enablePan = true;
      if (activeLevel !== 'all') {
        if (houseMax != null) setMaxZoom(houseMax);
        // focus-mode exits fly to their own saved pose right after this and
        // simply override the goal — both were captured at the same moment
        if (housePose) flyTo(housePose.position, housePose.target);
        housePose = null;
        houseMax = null;
      }
    }
    activeLevel = level;
  });
}
