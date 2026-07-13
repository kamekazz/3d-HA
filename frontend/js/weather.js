// Visible weather driven by the HA weather entity: rain streaks, snowfall,
// drifting low-poly clouds, lightning flashes, and wet/snowy lawn tinting.
// Follows daylight.js's resolved condition (so mode overrides and
// __daylight.simulate() drive this too). Particle pools are allocated once at
// max size and throttled with setDrawRange; intensities ease so condition
// changes fade instead of snap. Nothing here adds/removes lights — that would
// recompile every MeshStandard shader (see roomlights.js); lightning flashes
// modulate renderer.toneMappingExposure instead.
import * as THREE from 'three';
import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';
import { scene, renderer, onFrame } from './scene.js';
import { onDaylightChanged, getDaylight } from './daylight.js';
import { getEnvironmentCenter, setGroundSnow, setGroundWet } from './environment.js';

// HA condition -> effect levels (0..1). Anything missing means 0/false.
const EFFECTS = {
  'partlycloudy':    { cloud: 0.45 },
  'cloudy':          { cloud: 1.0, grey: 0.45 },
  'fog':             { cloud: 0.8, grey: 0.55 },
  'windy':           { wind: 1 },
  'windy-variant':   { wind: 1, cloud: 0.35 },
  'rainy':           { rain: 0.5, cloud: 1, grey: 0.65, wet: 1 },
  'pouring':         { rain: 1.0, cloud: 1, grey: 0.8, wet: 1 },
  'hail':            { rain: 1.0, cloud: 1, grey: 0.8, wet: 1 },
  'lightning':       { rain: 0.25, cloud: 1, grey: 0.85, lightning: true, wet: 0.5 },
  'lightning-rainy': { rain: 0.8, cloud: 1, grey: 0.85, lightning: true, wet: 1 },
  'snowy':           { snow: 1.0, cloud: 1, grey: 0.3, snowGround: 1 },
  'snowy-rainy':     { snow: 0.6, rain: 0.4, cloud: 1, grey: 0.55, snowGround: 0.6, wet: 0.5 },
};

const R = 170;        // precip volume half-extent (ft) around the house
const TOP = 110;      // precip spawn height
const RAIN_LEN = 2.2; // streak length
const MAX_RAIN = 1500;
const MAX_SNOW = 900;
const N_CLOUDS = 9;
const CLOUD_WRAP = 280;
const EXPOSURE_BASE = 1.15; // must match scene.js

let weatherRoot;
let target = { rain: 0, snow: 0, cloud: 0, grey: 0, wind: 0, wet: 0, snowGround: 0, lightning: false };
// eased levels (ground effects ease slower — snow settles, lawn dries)
const level = { rain: 0, snow: 0, cloud: 0, grey: 0, wind: 0, wet: 0, snowGround: 0 };

let rainMesh, rainPos, rainSpeed;
let snowMesh, snowPos, snowSpeed, snowPhase;
const clouds = []; // { mesh, speed, opacity }
const _grey = new THREE.Color(0x8b95a3);
const _white = new THREE.Color(0xffffff);

let flash = 0;        // current lightning brightness, decays each frame
let nextBolt = 5;     // seconds until the next flash
let time = 0;

function makeRain() {
  rainPos = new Float32Array(MAX_RAIN * 6);
  rainSpeed = new Float32Array(MAX_RAIN);
  for (let i = 0; i < MAX_RAIN; i++) {
    const x = (Math.random() * 2 - 1) * R, z = (Math.random() * 2 - 1) * R;
    const y = Math.random() * TOP;
    rainSpeed[i] = 55 + Math.random() * 25;
    rainPos.set([x, y, z, x, y - RAIN_LEN, z], i * 6);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position',
    new THREE.BufferAttribute(rainPos, 3).setUsage(THREE.DynamicDrawUsage));
  geo.setDrawRange(0, 0);
  rainMesh = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({
    color: 0xa8c0d8, transparent: true, opacity: 0.55 }));
  rainMesh.frustumCulled = false;
  rainMesh.visible = false;
  return rainMesh;
}

function makeSnowSprite() {
  const c = document.createElement('canvas');
  c.width = c.height = 32;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(16, 16, 2, 16, 16, 16);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 32, 32);
  return new THREE.CanvasTexture(c);
}

function makeSnow() {
  snowPos = new Float32Array(MAX_SNOW * 3);
  snowSpeed = new Float32Array(MAX_SNOW);
  snowPhase = new Float32Array(MAX_SNOW);
  for (let i = 0; i < MAX_SNOW; i++) {
    snowPos.set([(Math.random() * 2 - 1) * R, Math.random() * TOP,
                 (Math.random() * 2 - 1) * R], i * 3);
    snowSpeed[i] = 3.5 + Math.random() * 3.5;
    snowPhase[i] = Math.random() * Math.PI * 2;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position',
    new THREE.BufferAttribute(snowPos, 3).setUsage(THREE.DynamicDrawUsage));
  geo.setDrawRange(0, 0);
  snowMesh = new THREE.Points(geo, new THREE.PointsMaterial({
    size: 0.45, map: makeSnowSprite(), transparent: true,
    depthWrite: false, opacity: 0.9 }));
  snowMesh.frustumCulled = false;
  snowMesh.visible = false;
  return snowMesh;
}

function makeCloud(i) {
  const geos = [];
  const puffs = 4 + Math.floor(Math.random() * 3);
  for (let p = 0; p < puffs; p++) {
    const g = new THREE.IcosahedronGeometry(4 + Math.random() * 5, 1);
    g.scale(1.6, 0.55 + Math.random() * 0.2, 1);
    g.translate((p - puffs / 2) * 6 + Math.random() * 3,
                (Math.random() - 0.5) * 2, (Math.random() - 0.5) * 6);
    geos.push(g);
  }
  const mesh = new THREE.Mesh(
    BufferGeometryUtils.mergeGeometries(geos, false),
    new THREE.MeshStandardMaterial({
      color: 0xffffff, roughness: 1, flatShading: true,
      transparent: true, opacity: 0, depthWrite: false }));
  mesh.position.set((i / N_CLOUDS * 2 - 1) * CLOUD_WRAP,
                    92 + Math.random() * 40,
                    (Math.random() * 2 - 1) * 200);
  mesh.visible = false;
  mesh.frustumCulled = false;
  return { mesh, speed: 2 + Math.random() * 4, opacity: 0 };
}

function retarget({ condition }) {
  const fx = EFFECTS[condition] || {};
  target = {
    rain: fx.rain || 0, snow: fx.snow || 0, cloud: fx.cloud || 0,
    grey: fx.grey || 0, wind: fx.wind || 0, wet: fx.wet || 0,
    snowGround: fx.snowGround || 0, lightning: !!fx.lightning,
  };
}

function tick(dt) {
  dt = Math.min(dt, 0.1);
  time += dt;
  const k = 1 - Math.exp(-dt / 2.0);   // sky/precip settle ~2 s
  const kg = 1 - Math.exp(-dt / 12.0); // ground snow/wet settle much slower
  for (const key of ['rain', 'snow', 'cloud', 'grey', 'wind']) {
    level[key] = THREE.MathUtils.lerp(level[key], target[key], k);
  }
  level.wet = THREE.MathUtils.lerp(level.wet, target.wet, kg);
  level.snowGround = THREE.MathUtils.lerp(level.snowGround, target.snowGround, kg);
  setGroundWet(level.wet);
  setGroundSnow(level.snowGround);

  const c = getEnvironmentCenter();
  weatherRoot.position.set(c.x, 0, c.z);

  // --- rain
  const nRain = Math.floor(MAX_RAIN * level.rain);
  rainMesh.visible = nRain > 0 && weatherRoot.visible;
  rainMesh.geometry.setDrawRange(0, nRain * 2);
  if (rainMesh.visible) {
    for (let i = 0; i < nRain; i++) {
      let y = rainPos[i * 6 + 1] - rainSpeed[i] * dt;
      if (y < 0) y += TOP;
      rainPos[i * 6 + 1] = y;
      rainPos[i * 6 + 4] = y - RAIN_LEN;
    }
    rainMesh.geometry.attributes.position.needsUpdate = true;
  }

  // --- snow
  const nSnow = Math.floor(MAX_SNOW * level.snow);
  snowMesh.visible = nSnow > 0 && weatherRoot.visible;
  snowMesh.geometry.setDrawRange(0, nSnow);
  if (snowMesh.visible) {
    const sway = 1 + level.wind * 3;
    for (let i = 0; i < nSnow; i++) {
      let y = snowPos[i * 3 + 1] - snowSpeed[i] * dt;
      if (y < 0) y += TOP;
      snowPos[i * 3 + 1] = y;
      let x = snowPos[i * 3] + Math.sin(time * 0.8 + snowPhase[i]) * dt * 1.5 * sway;
      if (x > R) x -= 2 * R; else if (x < -R) x += 2 * R;
      snowPos[i * 3] = x;
    }
    snowMesh.geometry.attributes.position.needsUpdate = true;
  }

  // --- clouds: the first N*cloud clouds fade in, the rest fade out
  const shown = Math.ceil(N_CLOUDS * level.cloud);
  clouds.forEach((cl, i) => {
    cl.opacity = THREE.MathUtils.lerp(cl.opacity, i < shown && target.cloud > 0.01 ? 0.8 : 0, k);
    cl.mesh.visible = cl.opacity > 0.01 && weatherRoot.visible;
    if (!cl.mesh.visible) return;
    cl.mesh.material.opacity = cl.opacity;
    cl.mesh.material.color.copy(_white).lerp(_grey, level.grey);
    let x = cl.mesh.position.x + cl.speed * (1 + level.wind * 2.5) * dt;
    if (x > CLOUD_WRAP) x -= 2 * CLOUD_WRAP;
    cl.mesh.position.x = x;
  });

  // --- lightning: random flashes via tone-mapping exposure (a uniform — no
  // shader recompile, unlike touching the light count)
  if (target.lightning && weatherRoot.visible) {
    nextBolt -= dt;
    if (nextBolt <= 0) {
      flash = 0.8 + Math.random() * 0.5;
      nextBolt = 3 + Math.random() * 8;
    }
  }
  if (flash > 0.001) {
    flash *= Math.exp(-dt / 0.12);
    renderer.toneMappingExposure = EXPOSURE_BASE * (1 + flash * 1.4);
  } else if (renderer.toneMappingExposure !== EXPOSURE_BASE) {
    renderer.toneMappingExposure = EXPOSURE_BASE;
  }
}

export function initWeather() {
  weatherRoot = new THREE.Group();
  weatherRoot.name = 'weather';
  scene.add(weatherRoot);

  weatherRoot.add(makeRain());
  weatherRoot.add(makeSnow());
  for (let i = 0; i < N_CLOUDS; i++) {
    const cl = makeCloud(i);
    clouds.push(cl);
    weatherRoot.add(cl.mesh);
  }

  window.addEventListener('appModeChanged', (e) => {
    weatherRoot.visible = e.detail.mode === 'view';
  });

  onDaylightChanged(retarget);
  retarget(getDaylight());
  onFrame(tick);

  window.__weather = {
    state: () => ({ target, level }),
    // manual clock for testing: rAF pauses in hidden tabs, so easing stalls;
    // step(10) advances the weather sim by 10 seconds worth of frames
    step: (secs) => { for (let i = 0; i < secs * 10; i++) tick(0.1); },
  };
}
