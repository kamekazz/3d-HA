// Loads uploaded .glb/.gltf library models and hands out per-instance clones.
// glTF is authored in METERS; the world unit is FEET, so every instance is
// wrapped in a pivot scaled by 3.28084 — user scale and state scale live on
// the caller's outer group and never touch that factor.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { getEnvIntensity } from './scene.js';

const FEET_PER_METER = 3.28084;

const dracoLoader = new DRACOLoader();
// decoder WASM is only fetched if a DRACO-compressed mesh actually shows up.
// Served from our own static root (frontend/vendor/), NOT the CDN: the house
// shell GLB is DRACO-compressed, so a CDN-blocked or air-gapped deploy would
// render the whole scene except the house. Mirror of
// three@0.160.0/examples/jsm/libs/draco/gltf/ — re-copy it if three is bumped.
dracoLoader.setDecoderPath('/vendor/draco/gltf/');
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

const cache = new Map(); // model_id -> Promise<{scene, box}>

// ------------------------------------------------------------ readiness gate
// Nothing else in the app knows when the scene has finished assembling: every
// caller of getInstance() below throws its promise away (objects.js:makeObject,
// devices.js, house.js:loadHouseShell), so the house used to build itself
// piecemeal on screen. boot.js awaits this to hold the loading curtain.
//
// The count lives on getInstance, NOT on loadModel, so it also covers the
// clone/traverse/material work that runs after the fetch resolves — and it
// covers the house shell and model-backed device markers for free, since both
// go through getInstance too.
let inFlight = 0;
const idleWaiters = new Set();

export function modelsIdle() {
  if (inFlight === 0) return Promise.resolve();
  return new Promise((resolve) => idleWaiters.add(resolve));
}

export function modelsPending() { return inFlight; }

function releaseIfIdle() {
  if (inFlight > 0 || !idleWaiters.size) return;
  const waiters = [...idleWaiters];
  idleWaiters.clear();
  for (const resolve of waiters) resolve();
}

function loadModel(modelId) {
  let entry = cache.get(modelId);
  if (!entry) {
    entry = gltfLoader.loadAsync(`/api/house/model/${modelId}/file`)
      .then((gltf) => ({
        scene: gltf.scene,
        box: new THREE.Box3().setFromObject(gltf.scene),
      }))
      .catch((err) => {
        cache.delete(modelId); // let a later attempt retry (e.g. re-upload)
        throw err;
      });
    cache.set(modelId, entry);
  }
  return entry;
}

// Drop a model from the cache (library delete/re-upload).
export function invalidateModel(modelId) {
  cache.delete(modelId);
}

/**
 * A fresh scene-graph instance of a library model, ready to add to an
 * outer group that owns position/rotation/user scale.
 *
 * anchor: 'center' — bbox centered on the origin (device markers, which are
 *         centered on their placement point like the primitives);
 *         'bottom' — bbox XZ-centered, min Y at 0 (furniture sits on the slab).
 *
 * Geometries/textures are shared with the cached original (cheap instances);
 * materials are cloned per instance so state styling can tint one marker
 * without repainting every clone. Original material params are stashed in
 * child.userData.__orig for state.js to restore.
 */
export async function getInstance(modelId, anchor = 'bottom') {
  inFlight += 1;
  try {
    return await buildInstance(modelId, anchor);
  } finally {
    inFlight -= 1;
    releaseIfIdle();
  }
}

async function buildInstance(modelId, anchor) {
  const { scene, box } = await loadModel(modelId);
  const inst = scene.clone(true);
  inst.traverse((child) => {
    if (!child.isMesh) return;
    child.material = Array.isArray(child.material)
      ? child.material.map((m) => m.clone())
      : child.material.clone();
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    // instances load async, possibly after the last applyEnvIntensity() sweep
    for (const m of mats) if ('envMapIntensity' in m) m.envMapIntensity = getEnvIntensity();
    child.userData.__orig = mats.map((m) => ({
      color: m.color ? m.color.getHex() : null,
      emissive: m.emissive ? m.emissive.getHex() : null,
      emissiveIntensity: m.emissiveIntensity ?? 1,
    }));
  });

  const pivot = new THREE.Group();
  pivot.userData.part = 'model'; // not pickable on its own; owner root is
  const center = box.getCenter(new THREE.Vector3());
  inst.position.set(
    -center.x,
    anchor === 'bottom' ? -box.min.y : -center.y,
    -center.z);
  pivot.scale.setScalar(FEET_PER_METER);
  pivot.add(inst);
  return pivot;
}

// Native footprint of a model in feet (for UI hints), after unit conversion.
export async function getModelSize(modelId) {
  const { box } = await loadModel(modelId);
  const size = box.getSize(new THREE.Vector3());
  return {
    width: size.x * FEET_PER_METER,
    height: size.y * FEET_PER_METER,
    depth: size.z * FEET_PER_METER,
  };
}
