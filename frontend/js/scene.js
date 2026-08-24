// Three.js scene, camera, controls, lights, render loop.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { getStageRect, onStageChanged } from './stage.js';

export let scene, camera, renderer, controls;
export let hemiLight, sunLight; // driven live by daylight.js (sun/weather)

export const MIN_ZOOM = 10;
// The zoom-out cap. It belongs to the SCENE, not to any one shot: it used to be
// pinned to the opening-shot distance, so a bad framing could never be pulled
// back from — and on a portrait iPad the framing distance is itself larger than
// the old cap, so the clamp truncated the very shot it was computing.
// `let` on purpose — importers (focus.js) track the live binding.
export let MAX_ZOOM = 300;
let zoomTarget = 0; // desired camera↔target distance; eased toward each frame
// live touch points on the canvas — pinch tracking, and the gate that stops a
// two-finger pinch from also registering as a tap in main.js's picking
const touchPoints = new Map();
export function wasMultiTouch() { return touchPoints.size > 1; }
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
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(container.clientWidth, container.clientHeight);
  // filmic tone mapping so the daylight ramp (bright noon → dim night) rolls
  // off instead of clipping; no shadow maps — the FrontSide dollhouse walls
  // (outside-facing faces culled) would cast broken shadows, and enabling
  // shadows would recompile every MeshStandard shader
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  // Real sun shadows: only the opaque house-shell GLB casts and only the lawn
  // receives (see house.js / environment.js) — the FrontSide dollhouse walls
  // never opt in, so the "broken translucent walls" reason shadows were off no
  // longer applies. Enabling here folds the shadow shader variants into the
  // same one-time startup compile as the PMREM pass below (no runtime hitch).
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  // IBL: GLB models ship PBR (often metallic) materials that render black
  // without an environment map. Generated once at startup — the one-time
  // shader recompile happens before the first frame.
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();

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

  // Pinch-to-zoom. OrbitControls' own zoom stays OFF (above): its dolly writes
  // the camera distance directly, and the eased loop below would lerp it right
  // back toward the stale zoomTarget on the next frame — the pinch would
  // rubber-band on release. Drive zoomTarget instead, exactly like `wheel`.
  //
  // controls.touches.TWO stays TOUCH.DOLLY_PAN on purpose: with enableZoom
  // false its dolly half is a no-op and only its pan half runs, which follows
  // the two fingers' CENTROID while we follow their SPREAD. Orthogonal, so
  // pinch and two-finger pan compose (iOS Maps). In floor view and room focus
  // enablePan is false too, so OrbitControls ignores the gesture entirely.
  let pinchStart = 0, pinchZoom = 0;
  const spread = () => {
    const [a, b] = [...touchPoints.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  };
  const el = renderer.domElement;
  el.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'touch') return;
    touchPoints.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (touchPoints.size === 2) { pinchStart = spread(); pinchZoom = zoomTarget; }
  });
  el.addEventListener('pointermove', (e) => {
    if (e.pointerType !== 'touch' || !touchPoints.has(e.pointerId)) return;
    touchPoints.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (touchPoints.size !== 2 || !pinchStart || poseGoal) return; // a fly-to owns the camera
    const d = spread();
    if (d < 10) return;
    zoomTarget = THREE.MathUtils.clamp(pinchZoom * (pinchStart / d), MIN_ZOOM, MAX_ZOOM);
    userTookCamera = true;
  });
  const endTouch = (e) => {
    if (!touchPoints.delete(e.pointerId)) return;
    if (touchPoints.size < 2) pinchStart = 0; // survivor becomes a fresh rotate anchor
  };
  el.addEventListener('pointerup', endTouch);
  el.addEventListener('pointercancel', endTouch);

  // iOS Safari has ignored user-scalable=no since iOS 10. touch-action:none
  // (set by OrbitControls on the canvas) only covers gestures that START on
  // the canvas — a pinch beginning on the glass rail and sliding over it would
  // otherwise page-zoom the whole dashboard.
  for (const t of ['gesturestart', 'gesturechange', 'gestureend']) {
    document.addEventListener(t, (e) => e.preventDefault(), { passive: false });
  }

  hemiLight = new THREE.HemisphereLight(0xdfe8ff, 0x30363f, 1.0);
  scene.add(hemiLight);
  sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
  sunLight.position.set(60, 90, 36);
  scene.add(sunLight);
  // daylight.js moves the light to sunDir*150 every frame and aims it at the
  // origin (house center ≈ (13,5,13), only ~18 ft off), so a fixed, generous
  // ortho frustum covers every sun angle without moving/resizing per frame.
  // Leave sunLight.target at the origin — daylight.js sets an absolute position,
  // so re-targeting to house center would tilt the true sun angle.
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.set(2048, 2048);
  const shadowCam = sunLight.shadow.camera; // OrthographicCamera
  shadowCam.left = -140; shadowCam.right = 140;
  shadowCam.top = 140; shadowCam.bottom = -140;
  shadowCam.near = 1; shadowCam.far = 400;
  shadowCam.updateProjectionMatrix();
  sunLight.shadow.bias = -0.0005;   // kills acne
  sunLight.shadow.normalBias = 1.0; // ~1 ft — kills peter-panning on thick shell walls

  // 1 ft grid cells — the world unit is one foot
  const grid = new THREE.GridHelper(200, 200, 0x2a3340, 0x1c232d);
  grid.name = 'editGrid'; // named so snapshots.js can hide it during captures
  grid.position.y = -0.01;
  scene.add(grid);

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(2000, 2000),
    new THREE.MeshStandardMaterial({ color: 0x141a22, roughness: 1, transparent: true, opacity: 0.8 }));
  ground.name = 'editGround';
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

  // Layout is the resize signal, not the window: stage.js observes an invisible
  // CSS-inset probe, so a rotation, a breakpoint flip, a safe-area change, an
  // iPadOS Split View resize and a body-class flip all arrive here identically.
  onStageChanged(applyStage);
  applyStage();

  // Remember whether the user has taken the camera, so a layout change can
  // re-fit without yanking them back to the canned pose.
  controls.addEventListener('start', () => { userTookCamera = true; });

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

// envMapIntensity owner — daylight.js drives it with the day/night ramp so the
// IBL doesn't flatten nights (r160 has no scene.environmentIntensity; the
// per-material uniform never recompiles shaders). Lives here so devices/models
// can read it without an import cycle through daylight.js.
let envIntensity = 0.45;
export function getEnvIntensity() { return envIntensity; }
export function setEnvIntensity(v) {
  envIntensity = v;
  applyEnvIntensity();
}
// re-run after rebuilds: fresh room/marker materials default to intensity 1
export function applyEnvIntensity() {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) if (m && 'envMapIntensity' in m) m.envMapIntensity = envIntensity;
  });
}

export function focusOn(x, y, z) {
  controls.target.set(x, y, z);
  zoomTarget = camera.position.distanceTo(controls.target);
}

// ─────────────────────────── the stage ──────────────────────────────────────
// The canvas is full-bleed (#scene-container is inset:0) but the chrome covers
// part of it, so the house used to be centred behind the rail. Rather than
// inset the canvas, re-centre the FRUSTUM on the unobstructed rect: treat the
// canvas as a window onto a larger virtual frame centred on the stage.
//
// three derives `top` from fov and `width` from aspect*height for that VIRTUAL
// frame before narrowing to the sub-rect, so both are recomputed here and
// nothing else may ever write camera.aspect. fov is inflated by exactly the
// virtual frame's extra height, which pins the CANVAS's own vertical FOV at
// BASE_FOV: moving the chrome changes WHERE the optical axis lands, never how
// big the house is. That invariant is what makes it safe to re-run on every
// layout change.
export const BASE_FOV = 55;
let stagePx = 0;              // tan(half-angle) per CSS pixel — drives every fit
let lastW = 0, lastH = 0;

export function applyStage(rect = getStageRect()) {
  if (!camera || !renderer) return;
  const W = Math.max(1, window.innerWidth);
  const H = Math.max(1, window.innerHeight);
  const cx = rect.x + rect.w / 2;
  const cy = rect.y + rect.h / 2;
  const fullW = 2 * Math.max(cx, W - cx);
  const fullH = 2 * Math.max(cy, H - cy);

  const tanBase = Math.tan(THREE.MathUtils.degToRad(BASE_FOV) / 2);
  camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(tanBase * fullH / H));
  camera.aspect = fullW / fullH;
  if (fullW <= W + 0.5 && fullH <= H + 0.5) {
    // Symmetric chrome (or none): the offset is a no-op, so drop it entirely.
    // aspect MUST already be assigned — clearViewOffset() calls
    // updateProjectionMatrix() itself, using whatever aspect is current.
    camera.clearViewOffset();
  } else {
    camera.setViewOffset(fullW, fullH, fullW / 2 - cx, fullH / 2 - cy, W, H);
  }
  camera.updateProjectionMatrix();

  // OrbitControls' perspective pan is `targetDistance *= tan(fov/2)` over
  // element.clientHeight and knows nothing about the view offset, so the
  // inflated fov would make a pan drag travel fullH/H too far. Cancel it.
  controls.panSpeed = H / fullH;
  stageFovScale = H / fullH;

  // Pixels are square in tangent space, so one scalar drives every fit.
  stagePx = 2 * tanBase / H;

  if (W !== lastW || H !== lastH) {
    // Never re-set the same size: setSize writes canvas.width, which CLEARS the
    // drawing buffer, and snapshots.js reads that buffer back synchronously.
    lastW = W; lastH = H;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setSize(W, H);
  }
}

// Same correction, for anything else that has to undo the inflated fov.
// TransformControls sizes its gizmo from camera.fov directly, so without this
// the handles render fullH/H too large — ~40% in portrait, where the bottom
// filmstrip pushes the stage furthest off-centre.
let stageFovScale = 1;
export function getStageFovScale() { return stageFovScale; }

// Distance at which a bounding sphere of `radius` exactly fills the stage rect.
// THE single fit primitive. With a view offset in play camera.fov/camera.aspect
// describe the VIRTUAL frame, so any hand-rolled `fit = min(vFov, hFov)` now
// computes a larger fit, lands on a shorter distance, and crops its subject —
// focus.js and floorview.js must route through here. Reduces to
// min(vFov,hFov)/2 exactly when the stage is the whole canvas, so this
// generalises the old math rather than replacing it.
export function fitDistance(radius, pad = 1.0) {
  const r = getStageRect();
  const half = Math.atan(Math.min(r.w, r.h) * 0.5 * stagePx);
  return pad * radius / Math.sin(half);
}

// Retune the zoom-out cap live (floorview.js tightens it per floor, then
// restores the house cap). Importers of MAX_ZOOM track the live binding.
export function setMaxZoom(d) {
  MAX_ZOOM = d;
  controls.maxDistance = d;
  if (zoomTarget > d) zoomTarget = d;
}

// ───────────────────────── the whole-house shot ─────────────────────────────
// 20 degrees, not the 3 this used to sit at. The old curb-level view was chosen
// when this was a desktop model viewer; on a wall tablet the house IS the
// subject, and at 3° the roof plane is invisible and the far half of the lot
// hides behind the near half. 20° reads as an architectural model while the
// facade still holds — flatter than room focus (~30°) and much flatter than
// floorview's ~51°, which looks straight down at a bare slab.
//
// The front of this house faces ~+Z; the azimuth sits left of face-on so the
// facade reads in 3D instead of flat.
//
// The target height is NOT a fraction of anything — it is the fit sphere's own
// centre. That is what makes dist = R/sin(half) exact, and it is what removes
// the old `topY * 0.58` (topY summed floor heights INCLUDING the junk HA
// "error" floor, 37.8ft on a ~22ft house, so the camera aimed at open sky).
const HOUSE_ELEV = THREE.MathUtils.degToRad(20);
const HOUSE_AZ = THREE.MathUtils.degToRad(-18);
// Fraction of the stage the house should fill. Not a sphere pad — the shot is
// solved against the house's real projected outline (see frameAll), so this is
// literally "leave 8% of the stage as margin".
const HOUSE_FILL = 0.92;
// Hard ceiling on any zoom cap: daylight.js's fog near is 320 (foggy) / 360
// (clear), and a maxDistance past it fades the whole house out.
const HOUSE_MAX = 300;

let houseBox = null;        // THREE.Box3 of the building — set by house.js
let userTookCamera = false;

/** house.js hands us the measured bounds of the building after every build. */
export function setHouseBounds(box) {
  houseBox = box.clone();
}

function applyHouseZoomCap(frameDist) {
  setMaxZoom(Math.min(HOUSE_MAX, Math.max(frameDist * 1.8, 120)));
}

// Screen-space bounding rect of a Box3's eight corners, in CSS px. Uses the
// live projection, so the view offset is baked in.
const _c = new THREE.Vector3();
function projectBox(box) {
  const W = window.innerWidth, H = window.innerHeight;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (let i = 0; i < 8; i++) {
    _c.set(i & 1 ? box.max.x : box.min.x,
           i & 2 ? box.max.y : box.min.y,
           i & 4 ? box.max.z : box.min.z).project(camera);
    const px = (_c.x * 0.5 + 0.5) * W;
    const py = (-_c.y * 0.5 + 0.5) * H;
    if (px < minX) minX = px; if (px > maxX) maxX = px;
    if (py < minY) minY = py; if (py > maxY) maxY = py;
  }
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

function placeCamera(center, dist, target = controls.target) {
  const h = dist * Math.cos(HOUSE_ELEV);
  camera.position.set(center.x + Math.sin(HOUSE_AZ) * h,
                      center.y + dist * Math.sin(HOUSE_ELEV),
                      center.z + Math.cos(HOUSE_AZ) * h);
  target.copy(center);
  camera.lookAt(target);
  camera.updateMatrixWorld(true);
  // Vector3.project() reads matrixWorldInverse, which ONLY renderer.render()
  // refreshes — without this the solve below would measure the previous
  // frame's camera and never converge.
  camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
}

// Solve the pose that centres the house in the stage rect and fills
// HOUSE_FILL of it — against the real projected outline, not a bounding
// sphere. A sphere is badly wrong for a house: it wildly overestimates a wide
// low box, and because perspective is not affine, aiming at the box's 3D
// centre does NOT put its silhouette in the middle of the frame. Aiming at the
// 60x41x67ft centre of this house left it clipped off the bottom of the stage
// with 173px of dead sky above.
//
// Two nested solves, because the obvious single loop does not converge — a
// recentre changes the projected SIZE and a rescale changes its POSITION, so
// alternating full corrections oscillates (measured: 111 -> 80 -> 92 -> 78ft
// and no sign of settling):
//
//   aimFor(dist)  fixed distance, so only the aim point moves. Translating the
//                 aim translates the camera with it, so the view slides
//                 rigidly and this converges in two or three passes.
//   bisect        the projected size is monotonic in distance once the aim is
//                 solved, so bisection cannot oscillate and lands on the
//                 nearest distance that still fits.
//
// ~60 projections of 8 corners, once per framing. The aim point ends up at the
// house's VISUAL centre, which is also the point you want to orbit around, so
// nothing is traded away for the composition.
const _right = new THREE.Vector3();
const _up = new THREE.Vector3();
const _fwd = new THREE.Vector3();
const _aim = new THREE.Vector3();
const _probe = new THREE.Vector3();

// Where to aim, at a fixed distance, so the house's outline lands on the
// centre of the stage. Leaves the camera placed at that pose.
function aimFor(dist, sx, sy) {
  houseBox.getCenter(_aim);
  // Six passes, not two: translating the aim point translates the camera with
  // it, but the box has depth, so the projection does not slide by exactly the
  // requested amount and the residual only decays a few percent per pass.
  for (let pass = 0; pass < 6; pass++) {
    placeCamera(_aim, dist, _probe);
    const r = projectBox(houseBox);
    camera.matrixWorld.extractBasis(_right, _up, _fwd);
    // aim further right and the house slides left; aim lower and it rides up.
    // stagePx is tan-per-pixel, so a screen miss becomes world units at dist.
    _aim.addScaledVector(_right, (r.x + r.w / 2 - sx) * stagePx * dist)
        .addScaledVector(_up, -(r.y + r.h / 2 - sy) * stagePx * dist);
  }
  placeCamera(_aim, dist, _probe);
  return projectBox(houseBox);
}

function solveHousePose() {
  const stage = getStageRect();
  const sx = stage.x + stage.w / 2;
  const sy = stage.y + stage.h / 2;
  const maxW = stage.w * HOUSE_FILL;
  const maxH = stage.h * HOUSE_FILL;
  const savedPos = camera.position.clone();
  const savedTarget = controls.target.clone();

  let lo = MIN_ZOOM, hi = HOUSE_MAX;
  for (let i = 0; i < 14; i++) {
    const mid = (lo + hi) / 2;
    const r = aimFor(mid, sx, sy);
    if (r.w <= maxW && r.h <= maxH) hi = mid; else lo = mid;
  }
  aimFor(hi, sx, sy);            // leaves _aim at the solved aim point
  const center = _aim.clone();

  // leave the live camera exactly as we found it — this is a pure solve
  camera.position.copy(savedPos);
  controls.target.copy(savedTarget);
  camera.lookAt(controls.target);
  camera.updateMatrixWorld(true);
  camera.matrixWorldInverse.copy(camera.matrixWorld).invert();
  return { center, dist: hi };
}

// The canned opening shot, and what the Home button returns to. Unlike the
// one-shot frameInitialView it replaces, this is idempotent and safe to re-run
// on every rotation.
export function frameAll({ animate = false } = {}) {
  if (!houseBox) return;
  const { center, dist } = solveHousePose();
  applyHouseZoomCap(dist);
  const h = dist * Math.cos(HOUSE_ELEV);
  const pos = new THREE.Vector3(
    center.x + Math.sin(HOUSE_AZ) * h,
    center.y + dist * Math.sin(HOUSE_ELEV),
    center.z + Math.cos(HOUSE_AZ) * h,
  );
  userTookCamera = false;
  if (animate) { flyTo(pos, center); return; }
  controls.target.copy(center);
  camera.position.copy(pos);
  camera.lookAt(center);
  zoomTarget = dist;
}

// A layout change (rotation, breakpoint flip, rail switch) while the user owns
// the camera: keep the azimuth and elevation THEY chose and re-seat only the
// aim point and the distance. Snapping back to the canned pose here would feel
// like the app undoing their orbit.
export function refitStage({ onlyIfUntouched = false } = {}) {
  if (!houseBox) return;
  if (onlyIfUntouched && userTookCamera) return;
  if (!userTookCamera) { frameAll(); return; }   // still the canned shot — re-solve it
  const { center, dist } = solveHousePose();
  applyHouseZoomCap(dist);
  const dir = camera.position.clone().sub(controls.target);
  if (dir.lengthSq() < 1e-6) dir.set(0, 0, 1);
  dir.normalize();
  controls.target.copy(center);
  camera.position.copy(center).addScaledVector(dir, dist);
  camera.lookAt(controls.target);
  zoomTarget = dist;
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
