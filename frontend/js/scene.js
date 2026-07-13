// Three.js scene, camera, controls, lights, render loop.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export let scene, camera, renderer, controls;
export let hemiLight, sunLight; // driven live by daylight.js (sun/weather)

export const MIN_ZOOM = 10, MAX_ZOOM = 300;
let zoomTarget = 0; // desired camera↔target distance; eased toward each frame
let poseGoal = null; // {position, target} being flown to; suspends the zoom easing

// per-frame callbacks (fn(dt)) — lets daylight.js/roomlights.js animate
// without importing into the render loop and creating a module cycle
const frameCallbacks = new Set();
export function onFrame(fn) { frameCallbacks.add(fn); }

export function initScene(container) {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x10141a);
  // fog must start beyond controls.maxDistance, or zooming out fades the whole house away
  scene.fog = new THREE.Fog(0x10141a, 360, 1000);

  camera = new THREE.PerspectiveCamera(
    55, container.clientWidth / container.clientHeight, 0.1, 1600);
  camera.position.set(45, 50, 45);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  // filmic tone mapping so the daylight ramp (bright noon → dim night) rolls
  // off instead of clipping; no shadow maps — the BackSide dollhouse walls
  // (camera-facing faces culled) would cast broken shadows, and enabling
  // shadows would recompile every MeshStandard shader
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  container.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.set(13, 5, 13);
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.minDistance = MIN_ZOOM;
  controls.maxDistance = MAX_ZOOM;

  // OrbitControls zooms a fixed step per wheel *event* and ignores the scroll
  // amount, so mice that emit many events per notch zoom way too hard. Zoom
  // manually instead: proportional to the real scroll delta, eased per frame.
  controls.enableZoom = false;
  zoomTarget = camera.position.distanceTo(controls.target);
  renderer.domElement.addEventListener('wheel', (e) => {
    e.preventDefault();
    const px = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaMode === 2 ? e.deltaY * 120 : e.deltaY;
    zoomTarget = THREE.MathUtils.clamp(zoomTarget * Math.pow(1.001, px), MIN_ZOOM, MAX_ZOOM);
  }, { passive: false });

  hemiLight = new THREE.HemisphereLight(0xdfe8ff, 0x30363f, 1.0);
  scene.add(hemiLight);
  sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
  sunLight.position.set(60, 90, 36);
  scene.add(sunLight);

  // 1 ft grid cells — the world unit is one foot
  const grid = new THREE.GridHelper(200, 200, 0x2a3340, 0x1c232d);
  grid.position.y = -0.01;
  scene.add(grid);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(2000, 2000),
    new THREE.MeshStandardMaterial({ color: 0x141a22, roughness: 1, transparent: true, opacity: 0.8 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.02;
  scene.add(ground);
  
  // App mode toggle listener
  window.addEventListener('appModeChanged', (e) => {
    const isEdit = e.detail.mode === 'edit';
    grid.visible = isEdit;
    ground.visible = isEdit;
  });
  // Initial state for view mode
  grid.visible = false;
  ground.visible = false;

  window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });

  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const dt = clock.getDelta();
    for (const fn of frameCallbacks) fn(dt);
    if (poseGoal) {
      // fly-to tween: drive camera + target ourselves; controls are disabled so
      // damping momentum can't fight the flight path
      camera.position.lerp(poseGoal.position, 0.12);
      controls.target.lerp(poseGoal.target, 0.12);
      camera.lookAt(controls.target);
      zoomTarget = camera.position.distanceTo(controls.target);
      if (camera.position.distanceTo(poseGoal.position) < 0.05 &&
          controls.target.distanceTo(poseGoal.target) < 0.05) {
        camera.position.copy(poseGoal.position);
        controls.target.copy(poseGoal.target);
        zoomTarget = camera.position.distanceTo(controls.target);
        poseGoal = null;
        controls.enabled = true;
        controls.update();
      }
    } else {
      const dist = camera.position.distanceTo(controls.target);
      const next = THREE.MathUtils.lerp(dist, zoomTarget, 0.15);
      if (Math.abs(next - dist) > 1e-4) {
        camera.position.sub(controls.target).multiplyScalar(next / dist).add(controls.target);
      }
      controls.update();
    }
    renderer.render(scene, camera);
  });

  // debug handle (console): inspect the scene / renderer stats
  window.__scene3d = { scene, camera, renderer, controls, hemiLight, sunLight };
}

export function focusOn(x, y, z) {
  controls.target.set(x, y, z);
  zoomTarget = camera.position.distanceTo(controls.target);
}

// Smoothly fly the camera to a new pose (eased in the render loop above).
export function flyTo(position, target) {
  poseGoal = {
    position: new THREE.Vector3(position.x, position.y, position.z),
    target: new THREE.Vector3(target.x, target.y, target.z),
  };
  controls.enabled = false;
}

export function getViewPose() {
  return { position: camera.position.clone(), target: controls.target.clone() };
}
