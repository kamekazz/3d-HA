// Three.js scene, camera, controls, lights, render loop.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export let scene, camera, renderer, controls;

const MIN_ZOOM = 3, MAX_ZOOM = 90;
let zoomTarget = 0; // desired camera↔target distance; eased toward each frame

export function initScene(container) {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x10141a);
  // fog must start beyond controls.maxDistance, or zooming out fades the whole house away
  scene.fog = new THREE.Fog(0x10141a, 110, 320);

  camera = new THREE.PerspectiveCamera(
    55, container.clientWidth / container.clientHeight, 0.1, 500);
  camera.position.set(14, 16, 14);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.set(4, 1.5, 4);
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

  scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x30363f, 1.0));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4);
  sun.position.set(20, 30, 12);
  scene.add(sun);

  const grid = new THREE.GridHelper(60, 60, 0x2a3340, 0x1c232d);
  grid.position.y = -0.01;
  scene.add(grid);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(200, 200),
    new THREE.MeshStandardMaterial({ color: 0x141a22, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.02;
  scene.add(ground);

  window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });

  renderer.setAnimationLoop(() => {
    const dist = camera.position.distanceTo(controls.target);
    const next = THREE.MathUtils.lerp(dist, zoomTarget, 0.15);
    if (Math.abs(next - dist) > 1e-4) {
      camera.position.sub(controls.target).multiplyScalar(next / dist).add(controls.target);
    }
    controls.update();
    renderer.render(scene, camera);
  });

  // debug handle (console): inspect the scene / renderer stats
  window.__scene3d = { scene, camera, renderer, controls };
}

export function focusOn(x, y, z) {
  controls.target.set(x, y, z);
  zoomTarget = camera.position.distanceTo(controls.target);
}
