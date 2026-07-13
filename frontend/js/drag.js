// Drag-move for the selected device marker or furniture object.
// Selection-gated: only the object picked via a panel (or 3D click) drags, so
// grabbing anywhere else still orbits the camera. Movement happens on the
// horizontal plane through the object's own height — no network traffic until
// the pointer is released, then a single PATCH.
import * as THREE from 'three';
import { api } from './api.js';
import { scene, camera, renderer, controls } from './scene.js';
import { appMode } from './ui.js';

let selected = null;  // root Object3D with userData.kind 'device' | 'object'
let helper = null;    // selection highlight
let dragging = false;

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const plane = new THREE.Plane();
const hit = new THREE.Vector3();
const grabOffset = new THREE.Vector3();
const movedListeners = new Set();

// fn({kind, id, x, z}) with ROOM-RELATIVE x/z, called after the PATCH lands —
// ui.js uses it to refresh open panel inputs and its cached house copy.
export function onDragMoved(fn) {
  movedListeners.add(fn);
}

export function setSelected(obj) {
  if (helper) {
    scene.remove(helper);
    helper.dispose();
    helper = null;
  }
  if (appMode === 'view') {
    selected = null;
    return;
  }
  selected = obj || null;
  if (selected) {
    helper = new THREE.BoxHelper(selected, 0x4a9eff);
    scene.add(helper);
  }
}

export function getSelected() {
  return selected;
}

function castAt(event) {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
}

export function initDrag() {
  const el = renderer.domElement;

  // capture phase: runs before OrbitControls' own pointerdown handler, so
  // disabling controls here stops the camera from orbiting mid-drag
  el.addEventListener('pointerdown', (e) => {
    if (e.button !== 0 || !selected || !selected.visible) return;
    castAt(e);
    if (!raycaster.intersectObject(selected, true).length) return;
    dragging = true;
    controls.enabled = false;
    el.style.cursor = 'grabbing';
    const worldPos = selected.getWorldPosition(new THREE.Vector3());
    // horizontal plane through the object's own height, so wall-mounted
    // devices drag without pointer-offset skew
    plane.set(new THREE.Vector3(0, 1, 0), -worldPos.y);
    raycaster.ray.intersectPlane(plane, hit);
    grabOffset.copy(hit).sub(worldPos);
  }, true);

  el.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    castAt(e);
    if (!raycaster.ray.intersectPlane(plane, hit)) return;
    // floor groups only offset Y, so world XZ maps straight onto local XZ
    selected.position.x = hit.x - grabOffset.x;
    selected.position.z = hit.z - grabOffset.z;
    helper?.update();
  });

  const endDrag = async () => {
    if (!dragging) return;
    dragging = false;
    controls.enabled = true;
    el.style.cursor = '';
    const ud = selected.userData;
    // The house shell sits on the house root (no room footprint offset); its
    // position IS world XZ, saved through the shell endpoint.
    if (ud.kind === 'house-shell') {
      const x = +selected.position.x.toFixed(2);
      const z = +selected.position.z.toFixed(2);
      try {
        await api.setHouseShell({ x, z });
        for (const fn of movedListeners) fn({ kind: 'house-shell', x, z });
      } catch (err) {
        console.warn('shell drag save failed:', err);
      }
      return;
    }
    const x = +(selected.position.x - ud.fpX).toFixed(2);
    const z = +(selected.position.z - ud.fpZ).toFixed(2);
    try {
      if (ud.kind === 'device') await api.updatePlacement(ud.placementId, { x, z });
      else await api.updateObject(ud.objectId, { x, z });
      const id = ud.kind === 'device' ? ud.placementId : ud.objectId;
      for (const fn of movedListeners) fn({ kind: ud.kind, id, x, z });
    } catch (err) {
      console.warn('drag save failed:', err);
    }
  };
  el.addEventListener('pointerup', endDrag);
  el.addEventListener('pointercancel', endDrag);
}
