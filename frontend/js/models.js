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
// decoder WASM is only fetched if a DRACO-compressed mesh actually shows up
dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/draco/gltf/');
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(dracoLoader);

const cache = new Map(); // model_id -> Promise<{scene, box}>

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
