// Floating value labels: one hidden canvas-sprite pill per placed device
// (name + live value, e.g. "Hall sensor · 21.5 °C"). Shown for the hovered
// marker, or for a whole room in focus mode. Redrawn on state changes.
import * as THREE from 'three';
import { floorGroups } from './house.js';
import { friendlyName, stateLabel, onStateApplied } from './state.js';

const labels = new Map(); // entity_id -> sprite

const CANVAS_W = 512, CANVAS_H = 128;

function drawLabel(sprite) {
  const { canvas, ctx, entityId } = sprite.userData;
  const name = friendlyName(entityId);
  const value = stateLabel(entityId);

  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

  ctx.font = '600 44px system-ui, "Segoe UI", sans-serif';
  const valueW = ctx.measureText(value).width;
  ctx.font = '28px system-ui, "Segoe UI", sans-serif';
  const nameW = ctx.measureText(name).width;
  const pillW = Math.min(CANVAS_W, Math.max(valueW, nameW) + 48);
  const x = (CANVAS_W - pillW) / 2;

  // pill background, matching the tooltip look
  ctx.fillStyle = 'rgba(29, 29, 31, 0.92)';
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(x, 4, pillW, CANVAS_H - 8, 16);
  ctx.fill();
  ctx.stroke();

  ctx.textAlign = 'center';
  ctx.fillStyle = '#cccccc';
  ctx.font = '28px system-ui, "Segoe UI", sans-serif';
  ctx.fillText(name, CANVAS_W / 2, 46, pillW - 32);
  ctx.fillStyle = '#ffffff';
  ctx.font = '600 44px system-ui, "Segoe UI", sans-serif';
  ctx.fillText(value, CANVAS_W / 2, 100, pillW - 32);

  sprite.material.map.needsUpdate = true;
}

function makeLabel(dev, room, floor, yOffset = 0.7) {
  const canvas = document.createElement('canvas');
  canvas.width = CANVAS_W;
  canvas.height = CANVAS_H;
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: texture, transparent: true, depthTest: false,
  }));
  sprite.renderOrder = 10;
  sprite.center.set(0.5, 0); // anchor at bottom so it floats above the marker
  sprite.scale.set(6, 1.5, 1);
  sprite.raycast = () => {}; // labels must never steal picks
  const fp = room.footprint;
  sprite.position.set(
    fp.x + dev.position.x,
    dev.position.y + yOffset,
    fp.z + dev.position.z);
  sprite.visible = false;
  sprite.userData = {
    entityId: dev.entity_id,
    roomId: room.id,
    level: floor.level,
    hiddenByUser: dev.visible === 0,
    canvas,
    ctx: canvas.getContext('2d'),
  };
  return sprite;
}

// Flip an entity's user-hidden flag without rebuilding (room panel edit mode).
export function setLabelHidden(entityId, hidden) {
  const sprite = labels.get(entityId);
  if (!sprite) return;
  sprite.userData.hiddenByUser = hidden;
  if (hidden) sprite.visible = false;
}

export function buildLabels(house) {
  for (const sprite of labels.values()) {
    sprite.parent?.remove(sprite);
    sprite.material.map.dispose();
    sprite.material.dispose();
  }
  labels.clear();

  for (const floor of house.floors || []) {
    const group = floorGroups.get(floor.level);
    if (!group) continue;
    for (const room of floor.rooms || []) {
      for (const dev of room.devices || []) {
        const sprite = makeLabel(dev, room, floor);
        group.add(sprite);
        labels.set(dev.entity_id, sprite);
      }
      // A furniture piece bound to an entity IS that entity, and devices.js
      // stands its floating marker down — so the label has to move to the
      // fixture too, or hovering the lamp pops a pill over empty air where the
      // marker used to be. Built second so it wins the map slot. Sits near the
      // bulb: the object anchor is at its base (models.js 'bottom').
      for (const o of room.objects || []) {
        if (!o.entity_id) continue;
        const y = (o.light_cfg?.offset_y ?? 1.0) + 0.7;
        const sprite = makeLabel({ ...o, visible: 1 }, room, floor, y);
        group.add(sprite);
        labels.set(o.entity_id, sprite);
      }
    }
  }
}

export function showLabel(entityId) {
  const sprite = labels.get(entityId);
  if (!sprite) return;
  drawLabel(sprite);
  sprite.visible = true;
}

export function hideLabel(entityId) {
  const sprite = labels.get(entityId);
  if (sprite) sprite.visible = false;
}

export function showRoomLabels(roomId) {
  for (const sprite of labels.values()) {
    if (sprite.userData.roomId === roomId && !sprite.userData.hiddenByUser) {
      drawLabel(sprite);
      sprite.visible = true;
    }
  }
}

export function hideAllLabels() {
  for (const sprite of labels.values()) sprite.visible = false;
}

// keep visible labels live as states stream in
onStateApplied((entityId) => {
  if (entityId === null) {
    for (const sprite of labels.values()) if (sprite.visible) drawLabel(sprite);
  } else {
    const sprite = labels.get(entityId);
    if (sprite?.visible) drawLabel(sprite);
  }
});
