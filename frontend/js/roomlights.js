// Home Assistant lights -> light in the 3D scene. Three sources feed one pool:
//
//   FIXTURES   a furniture object bound to an HA entity (objects.entity_id) --
//              a lamp GLB that IS light.bedside. Light comes from the fixture
//              itself, and the fixture's own materials glow.
//   EXTERIORS  a light PLACEMENT in an outdoor room -- the porch sconces and
//              garage floodlights, which hang on the shell and have no
//              furniture to bind to. The marker's position is the source.
//   ROOMS      the fallback for a room with no VISIBLE bound fixture and no
//              lit exterior: the whole-room glow, from its placed lights and
//              its HA area's.
//
// Fixtures and exteriors outrank rooms for a pool slot. A room keeps its record
// either way -- roomcards.js and dashboard.js read the room->lights sets through
// the accessors below, and those must not change meaning.
import * as THREE from 'three';
import { scene, controls, renderer, onFrame } from './scene.js';
import { roomMeshes, floorBaseY, getLevel, isOutdoorRoom } from './house.js';
import { getState, isOn, onStateApplied, paintModelState } from './state.js';
import { getNightFactor } from './daylight.js';
import { objects3d } from './objects.js';
import { getFocusedRoomId } from './focus.js';

// The pool is fixed-size and its lights are never added/removed/HIDDEN.
// `lights.point.length` is baked into three's program cache key, so changing
// the count -- including via light.visible = false -- recompiles every
// MeshStandardMaterial in the scene. Driving intensity to 0 costs nothing:
// WebGLLights.setup does no intensity culling, so a dark light keeps its slot.
// Never set castShadow on one either; that is a second cache-key term.
// The size is therefore decided ONCE, in initRoomLights, which main.js calls
// before renderer.compileAsync -- so the one real compile stays behind the
// boot curtain.
let POOL_SIZE = 12;

function decidePoolSize() {
  let wanted = 12;
  try {
    if (window.matchMedia('(pointer: coarse)').matches) wanted = 8;
  } catch { /* no matchMedia */ }
  // three has no per-object light culling: every point light is evaluated on
  // every lit fragment, and each costs ~4 uniform vectors. Stay well inside the
  // driver's budget or the program fails to link on mobile GLES.
  try {
    const gl = renderer?.getContext?.();
    const maxVec = gl?.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS);
    if (maxVec) wanted = Math.min(wanted, Math.max(4, Math.floor((maxVec - 96) / 4)));
  } catch { /* no context yet — keep the default */ }
  return wanted;
}

const GLOW_COLOR = 0xffb466;       // fallback tint when HA reports no colour
const SLAB_GLOW = new THREE.Color(0xffa64d);
const SLAB_INTENSITY = 0.45;

// Candela, with decay 2 and the world unit = 1 FOOT. r160 uses physically
// correct falloff (useLegacyLights is gone), so illuminance is intensity / d^2
// -- at 5 ft that is a 25x divisor. The old value of 2.2 put ~0.06 on a surface
// from a room centre, which is why lights read as doing nothing at all.
const FIXTURE_BASE = 45;
const CENTRE_BASE = 90;            // a room centre sits further from every surface
const FIXTURE_RANGE = 22;          // ft; the light.distance cutoff
// An exterior throws further than a table lamp and has no ceiling to bounce
// off: a porch sconce has to read across a whole facade, a floodlight further.
// 70 cd blew the siding round every sconce to white and, once scene.js's
// night bloom landed, fogged the whole upper frame off the garage floods.
// 18 cd puts ~150/255 on the wall a foot under the lamp, like the photograph.
const EXTERIOR_BASE = 80;
const EXTERIOR_RANGE = 30;         // ft
// The coach lamps and floods on the facade are ~3000K in every photograph; a
// white bulb reports rgb 255,255,255 to HA, which lit them 6500K here.
const EXTERIOR_WARM = new THREE.Color(0xffb46b);
const EMISSIVE_MAX = 1.6;          // glow on the fixture's own materials
const SMOOTH_TAU = 0.4;

// Interior light is no longer gated to darkness. It reads at DAY_FLOOR of full
// strength at noon and full strength at night, so switching a light on is
// visible at any hour -- the whole point of the feature.
const DAY_FLOOR = 0.35;
// The single-floor dollhouse view swaps the sky for a dark studio backdrop and
// hides the yard, so the same spill blows a whole floor plan out. Pull it back
// there -- but NOT in room focus, which also sits on a floor level and is the
// one view where you are close enough to want a lamp to read properly.
const FLOORVIEW_SPILL = 0.4;

function spillScale() {
  const base = DAY_FLOOR + (1 - DAY_FLOOR) * getNightFactor();
  const dollhouse = getLevel() !== 'all' && getFocusedRoomId() === null;
  return dollhouse ? base * FLOORVIEW_SPILL : base;
}

let rooms = [];                     // [{roomId, level, center, radius, lightIds, lit, glow, fixtures}]
let fixtures = [];                  // [{objectId, entityId, roomId, level, on, level01, color, glow}]
let exteriors = [];                 // [{placementId, entityId, roomId, level, pos, on, level01, color, glow}]
const byEntity = new Map();         // entity_id -> [room records]    (rooms only)
const fixturesByEntity = new Map(); // entity_id -> [fixture records]
const exteriorsByEntity = new Map(); // entity_id -> [exterior records]
const pool = [];                    // [{light, owner}] owner = fixture | room | null
let assignmentDirty = false;
// Shot/debug override: every exterior renders as ON, night only, off by
// default. The night photograph the exterior is judged against has every
// sconce and flood lit; HA usually has them off at the hour a shot is taken.
let forceExt = false;
let lastLevel = null;

// entity_ids a fixture now represents. devices.js uses this to suppress the
// floating auto-generated marker for the same entity -- frontend-only, so
// unbinding restores the marker with no DB write.
export const boundEntities = new Set();

// fixture records carry objectId, exteriors carry placementId, rooms neither
const isFixture = (owner) => owner != null && owner.objectId !== undefined;
const isExterior = (owner) => owner != null && owner.placementId !== undefined;

// Does a bound piece actually EMIT? Binding is also how a fan, a TV or a lock
// becomes clickable in the 3D view, and a Dyson fan glowing lamp-amber when you
// switch it on is just wrong. Lights emit; so do switches, because a
// switch-controlled lamp is the common case here (switch.edwin_bedside_light...).
// light_cfg.emit overrides in either direction.
const EMITTING_DOMAINS = new Set(['light', 'switch']);

function emitsLight(rec) {
  if (rec.cfg.emit !== undefined && rec.cfg.emit !== null) return !!rec.cfg.emit;
  return EMITTING_DOMAINS.has(rec.entityId.split('.')[0]);
}

// An object root can be hidden by objects.js (House mode, room focus, a
// cut-away wall) OR by its parent floor group (the level selector). Walk the
// chain, exactly as main.js pick() does.
function isShown(o) {
  for (let n = o; n; n = n.parent) if (!n.visible) return false;
  return true;
}

function fixtureShown(rec) {
  const root = objects3d.get(rec.objectId);
  return !!root && isShown(root);
}

// An exterior is NOT gated on its marker the way a fixture is gated on its
// model. Device markers are edit-only chrome (devices.js) and House mode hides
// every one of them -- gating on the marker would switch the porch light off in
// the one view the porch is ever seen from. What gates it is the room: hidden
// by the user, or scoped out by a focus on some OTHER room (a point light is
// occluded by nothing, so a yard light left burning during an indoor focus
// shines straight through the wall you are looking at).
function exteriorLive(rec) {
  if (rec.hidden) return false;
  const focused = getFocusedRoomId();
  return focused === null || focused === rec.roomId;
}

export function initRoomLights() {
  POOL_SIZE = decidePoolSize();
  for (let i = 0; i < POOL_SIZE; i++) {
    const light = new THREE.PointLight(GLOW_COLOR, 0, 10, 2);
    scene.add(light);
    pool.push({ light, owner: null });
  }

  onStateApplied((entityId) => {
    if (entityId === null) {
      for (const r of rooms) refreshLit(r);
      for (const f of fixtures) refreshFixture(f);
      for (const e of exteriors) refreshFixture(e);
    } else {
      for (const r of byEntity.get(entityId) || []) refreshLit(r);
      for (const f of fixturesByEntity.get(entityId) || []) refreshFixture(f);
      for (const e of exteriorsByEntity.get(entityId) || []) refreshFixture(e);
    }
    assignmentDirty = true;
  });

  // Anything that changes what is on screen changes who deserves a slot. NOT
  // the wall cutaway: it re-scores every wall every frame during an orbit and
  // would thrash the pool at 60Hz — the per-frame goal covers that instead.
  for (const ev of ['levelChanged', 'focusChanged', 'appModeChanged']) {
    window.addEventListener(ev, () => { assignmentDirty = true; });
  }

  onFrame(tick);

  if (window.__daylight) {
    window.__daylight.rooms = () => rooms.map((r) => ({
      roomId: r.roomId, level: r.level, lit: r.lit,
      lights: [...r.lightIds],
      pooled: pool.some((p) => p.owner === r),
    }));
  }
  window.__roomlights = {
    poolSize: () => POOL_SIZE,
    forceExteriors: (v) => {
      forceExt = !!v;
      for (const e of exteriors) refreshFixture(e);
      assignmentDirty = true;
    },
    fixtures: () => fixtures.map((f) => ({
      objectId: f.objectId, entityId: f.entityId, roomId: f.roomId,
      level: f.level, on: f.on, emits: f.emits, level01: +f.level01.toFixed(3),
      glow: +f.glow.toFixed(3), shown: fixtureShown(f),
      color: f.color.getHexString(),
      pooled: pool.some((p) => p.owner === f),
    })),
    exteriors: () => exteriors.map((e) => ({
      placementId: e.placementId, entityId: e.entityId, roomId: e.roomId,
      level: e.level, on: e.on, glow: +e.glow.toFixed(3), live: exteriorLive(e),
      color: e.color.getHexString(),
      pos: [+e.pos.x.toFixed(2), +e.pos.y.toFixed(2), +e.pos.z.toFixed(2)],
      pooled: pool.some((p) => p.owner === e),
    })),
    slots: () => pool.map((p) => ({
      owner: p.owner
        ? (isFixture(p.owner) ? `object ${p.owner.objectId}`
          : isExterior(p.owner) ? `exterior ${p.owner.placementId}`
            : `room ${p.owner.roomId}`)
        : null,
      intensity: +p.light.intensity.toFixed(2),
    })),
    bound: () => [...boundEntities],
  };
}

// (Re)build records after any house rebuild — buildHouse disposes the old slab
// materials and buildObjects the old object roots, so records must repoint at
// the fresh meshes.
export function setRoomLightsData({ house, structure }) {
  rooms = [];
  fixtures = [];
  exteriors = [];
  byEntity.clear();
  fixturesByEntity.clear();
  exteriorsByEntity.clear();
  boundEntities.clear();
  for (const p of pool) p.owner = null;

  // ha_area_id -> Set(light entity_ids) from the HA registry tree, so rooms
  // glow even for lights that were never placed as 3D markers
  const areaLights = new Map();
  for (const f of structure?.floors || []) {
    for (const a of f.areas || []) {
      const set = new Set();
      for (const e of a.entities || []) {
        if (e.entity_id?.startsWith('light.')) set.add(e.entity_id);
      }
      if (set.size) areaLights.set(a.area_id, set);
    }
  }

  for (const floor of house?.floors || []) {
    for (const room of floor.rooms || []) {
      // --- fixtures: furniture carrying an entity ---
      const roomFixtures = [];
      for (const o of room.objects || []) {
        if (!o.entity_id) continue;
        boundEntities.add(o.entity_id);
        const rec = {
          objectId: o.id,
          entityId: o.entity_id,
          roomId: room.id,
          level: floor.level,
          cfg: o.light_cfg || {},
          on: false,
          level01: 0,
          color: new THREE.Color(GLOW_COLOR),
          glow: 0,      // eased 0..1, drives both emissive and spill
          painted: -1,  // last emissive level written; repaint only on change
        };
        rec.emits = emitsLight(rec);
        fixtures.push(rec);
        roomFixtures.push(rec);
        if (!fixturesByEntity.has(o.entity_id)) fixturesByEntity.set(o.entity_id, []);
        fixturesByEntity.get(o.entity_id).push(rec);
      }

      // --- exteriors: a light PLACEMENT in a yard ---
      // Outdoor rooms have no lamp furniture to bind, and House mode hides
      // their room mesh along with every other room -- so neither source above
      // could ever light one, and every porch sconce and floodlight in the
      // house did nothing at all in the only view the exterior is seen from.
      // The marker the user dragged onto the facade is where that light really
      // hangs, so the placement itself is the source. Outdoor rooms ONLY: a
      // point light is occluded by nothing, so an indoor placement promoted the
      // same way would shine straight out through the shell onto the lawn.
      const roomExteriors = [];
      if (isOutdoorRoom(room.name)) {
        const fpo = room.footprint;
        const yBase = floorBaseY.get(floor.level) ?? 0;
        for (const dev of room.devices || []) {
          if (!dev.entity_id?.startsWith('light.')) continue;
          const rec = {
            placementId: dev.id,
            entityId: dev.entity_id,
            roomId: room.id,
            level: floor.level,
            hidden: dev.visible === 0,
            cfg: {},           // refreshFixture reads it; placements carry none
            pos: new THREE.Vector3(
              fpo.x + dev.position.x,
              yBase + dev.position.y,
              fpo.z + dev.position.z),
            on: false,
            level01: 0,
            color: new THREE.Color(GLOW_COLOR),
            glow: 0,
            wasLit: false,     // tracks the pool-candidacy threshold crossing
          };
          exteriors.push(rec);
          roomExteriors.push(rec);
          if (!exteriorsByEntity.has(dev.entity_id)) {
            exteriorsByEntity.set(dev.entity_id, []);
          }
          exteriorsByEntity.get(dev.entity_id).push(rec);
        }
      }

      // --- room record: kept for EVERY room, fixtures or not ---
      const lightIds = new Set();
      for (const dev of room.devices || []) {
        if (dev.entity_id?.startsWith('light.')) lightIds.add(dev.entity_id);
      }
      for (const id of areaLights.get(room.ha_area_id) || []) lightIds.add(id);
      // a bound light that was never placed as a marker still belongs to the
      // room, or the card count and the dashboard tile would miss it
      for (const f of roomFixtures) {
        if (f.entityId.startsWith('light.')) lightIds.add(f.entityId);
      }
      if (!lightIds.size) continue;

      const fp = room.footprint;
      const baseY = floorBaseY.get(floor.level) ?? 0;
      const rec = {
        roomId: room.id,
        level: floor.level,
        center: new THREE.Vector3(
          fp.x + fp.width / 2,
          baseY + (room.height || 8) * 0.6,
          fp.z + fp.depth / 2),
        radius: Math.hypot(fp.width, fp.depth) / 2,
        lightIds,
        lit: false,
        glow: 0, // eased slab emissive intensity
        // The room-centre fallback yields to a fixture only while that fixture
        // is actually ON SCREEN — tested per frame, not decided here. House
        // mode hides all indoor furniture, and a room whose only candidate was
        // a fixture would otherwise go dark in the one view where warm windows
        // at night are the entire point.
        fixtures: roomFixtures,
        exteriors: roomExteriors,
      };
      rooms.push(rec);
      for (const id of lightIds) {
        if (!byEntity.has(id)) byEntity.set(id, []);
        byEntity.get(id).push(rec);
      }
    }
  }

  for (const r of rooms) refreshLit(r);
  for (const f of fixtures) refreshFixture(f);
  for (const e of exteriors) refreshFixture(e);
  assignmentDirty = true;
}

function refreshLit(rec) {
  rec.lit = [...rec.lightIds].some((id) => getState(id) && isOn(id));
}

// Does this room still need its whole-room fallback light?
function needsCentre(rec) {
  if (rec.fixtures.some((f) => f.emits && fixtureShown(f))) return false;
  // a lit exterior replaces the centre wash for the same reason a fixture does:
  // both light from where the light actually is
  return !rec.exteriors.some((e) => e.glow > 0.01 && exteriorLive(e));
}

function paintFixture(f, root) {
  // NOT applyStyle: that also rescales the marker, and a lamp must not grow
  // 1.25x when it turns on. Glow is never night-gated — a lamp that is on
  // reads as on at noon.
  paintModelState(root, {
    emissiveHex: f.color.getHex(),
    emissiveIntensity: EMISSIVE_MAX * f.glow,
    grey: false,
  });
}

// Repaint one fixture's emissive from its current eased glow. main.js calls
// this to drop a hover boost: roomlights only repaints when the glow MOVES, so
// a fixture sitting at a steady level would otherwise keep the boost forever.
export function repaintFixture(objectId) {
  const f = fixtures.find((x) => x.objectId === objectId);
  const root = f && objects3d.get(objectId);
  if (!root) return;
  // a non-emitting binding (a fan, a lock) still hovers — restore its AUTHORED
  // materials rather than painting a glow it never had
  if (f.emits) paintFixture(f, root);
  else paintModelState(root, { emissiveHex: null, grey: false });
}

// Warm white for a colour temperature: HA reports kelvin, three wants RGB.
// Approximation of the Planckian locus — good enough for a lamp glow.
// ColorManagement is on in r160 and Color.setRGB defaults to the LINEAR working
// space, so every call here must name sRGB explicitly or the colour washes out.
// (Color.setHex defaults to sRGB, which is why GLOW_COLOR needs no argument.)
function kelvinToColor(k, out) {
  const t = THREE.MathUtils.clamp(k, 1500, 12000) / 100;
  let r;
  let g;
  let b;
  if (t <= 66) {
    r = 255;
    g = 99.47 * Math.log(t) - 161.12;
  } else {
    r = 329.7 * Math.pow(t - 60, -0.1332);
    g = 288.12 * Math.pow(t - 60, -0.0755);
  }
  if (t >= 66) b = 255;
  else if (t <= 19) b = 0;
  else b = 138.52 * Math.log(t - 10) - 305.04;
  return out.setRGB(
    THREE.MathUtils.clamp(r, 0, 255) / 255,
    THREE.MathUtils.clamp(g, 0, 255) / 255,
    THREE.MathUtils.clamp(b, 0, 255) / 255,
    THREE.SRGBColorSpace);
}

function refreshFixture(rec) {
  const st = getState(rec.entityId);
  rec.on = !!st && isOn(rec.entityId);
  const a = st?.attributes || {};
  // HA sends brightness: null (not absent) for a light that supports it but is
  // off, and a switch-backed lamp has no such attribute at all — so this must
  // test for null too, or `null / 255` silently pins the lamp at zero. Floored
  // at 0.15 so a bulb dimmed to 1 still reads as on rather than as broken.
  const b = a.brightness;
  rec.level01 = rec.on
    ? (b === null || b === undefined ? 1 : 0.15 + 0.85 * (b / 255))
    : 0;
  if (forceExt && isExterior(rec) && getNightFactor() > 0.5) {
    rec.on = true;
    rec.level01 = 1;
  }

  if (rec.cfg.color) {
    rec.color.set(rec.cfg.color);
  } else if (Array.isArray(a.rgb_color) && a.rgb_color.length === 3) {
    rec.color.setRGB(a.rgb_color[0] / 255, a.rgb_color[1] / 255,
                     a.rgb_color[2] / 255, THREE.SRGBColorSpace);
  } else if (a.color_temp_kelvin) {
    kelvinToColor(a.color_temp_kelvin, rec.color);
  } else {
    rec.color.setHex(GLOW_COLOR);
  }
}

// --- accessors: the single source of truth for "which lights are in a room" --
// roomcards.js counts and toggles off these, and dashboard.js scopes its tile
// to them, so they cover ROOMS only and stay light.* — a fixture may be bound
// to a switch.* entity, which must not land in a "lights on" count whose
// toggle calls light.turn_off on everything it holds.

export function getRoomLightIds(roomId) {
  return rooms.find((r) => r.roomId === roomId)?.lightIds ?? new Set();
}

// entity_id -> [roomId] so a light's state change can update just its cards
export function getRoomsForEntity(entityId) {
  const ids = (byEntity.get(entityId) || []).map((r) => r.roomId);
  // a fixture's room repaints too, even if the entity was never placed there
  for (const f of fixturesByEntity.get(entityId) || []) {
    if (!ids.includes(f.roomId)) ids.push(f.roomId);
  }
  return ids;
}

// Every light that belongs to some room of the house. The dashboard's
// "N lights on / all off" tile scopes to these — HA instances can hold
// hundreds of light entities (virtual/decor integrations) that aren't
// house lighting.
export function getAllHouseLightIds() {
  return new Set(byEntity.keys());
}

// A fixture's world position. Deliberately NOT getWorldPosition: frame
// callbacks run before renderer.render, which is what refreshes matrixWorld, so
// that would read a stale matrix (and the identity on the very first pass).
// houseRoot is untransformed and a floor group carries ONLY a Y offset, so the
// exact world position is available synchronously from the live root.position —
// which also means the light follows a drag for free.
const _p = new THREE.Vector3();

function fixtureWorldPos(rec, out) {
  const root = objects3d.get(rec.objectId);
  if (!root) return null;
  const base = floorBaseY.get(rec.level) ?? 0;
  return out.set(
    root.position.x,
    base + root.position.y + (rec.cfg.offset_y ?? 1.0), // bulb above the base
    root.position.z);
}

function distToTarget(f) {
  return fixtureWorldPos(f, _p) ? _p.distanceToSquared(controls.target) : Infinity;
}

// Give the pool to the best-ranked owners: fixtures first (they light from the
// right place), then whole-room fallbacks, both restricted to visible levels
// and ordered by distance to what the camera is looking at.
function reassignPool() {
  const level = getLevel();
  const onLevel = (l) => level === 'all' || l === level;

  const fixCands = fixtures
    .filter((f) => f.emits && f.glow > 0.01 && onLevel(f.level) && fixtureShown(f))
    .sort((a, b) => distToTarget(a) - distToTarget(b));
  const extCands = exteriors
    .filter((e) => e.glow > 0.01 && onLevel(e.level) && exteriorLive(e))
    .sort((a, b) => a.pos.distanceToSquared(controls.target)
      - b.pos.distanceToSquared(controls.target));
  const roomCands = rooms
    .filter((r) => r.lit && onLevel(r.level) && needsCentre(r)
      && isShown(roomMeshes.get(r.roomId) || { visible: false }))
    .sort((a, b) =>
      a.center.distanceToSquared(controls.target) -
      b.center.distanceToSquared(controls.target));

  const winners = [...fixCands, ...extCands, ...roomCands].slice(0, POOL_SIZE);

  // keep already-assigned winners on their light so they don't blink
  for (const p of pool) if (!winners.includes(p.owner)) p.owner = null;
  for (const owner of winners) {
    if (pool.some((p) => p.owner === owner)) continue;
    const slot = pool.find((p) => !p.owner);
    if (!slot) break;
    slot.owner = owner;
  }
  // position every slot now that ownership has settled
  for (const p of pool) {
    if (!p.owner) continue;
    if (isFixture(p.owner)) {
      if (fixtureWorldPos(p.owner, _p)) p.light.position.copy(_p);
      p.light.distance = p.owner.cfg.range ?? FIXTURE_RANGE;
    } else if (isExterior(p.owner)) {
      p.light.position.copy(p.owner.pos);
      p.light.distance = EXTERIOR_RANGE;
    } else {
      p.light.position.copy(p.owner.center);
      p.light.distance = p.owner.radius * 2.5;
    }
  }
}

function slotGoal(p, spill) {
  if (isFixture(p.owner)) {
    const f = p.owner;
    // A fixture in a hidden room or on a hidden level must stop emitting --
    // it would light the scene from a lamp you cannot see. But deliberately NOT
    // scaled by userData.wallFade: the cutaway binds any piece within 2 ft of a
    // wall and above 1.2 ft, which catches a table lamp standing next to one,
    // and dimming the room's light because a wall dissolved defeats the very
    // thing the dissolve is for. objects.js hides the piece outright once the
    // fade bottoms out, and isShown catches that.
    const root = objects3d.get(f.objectId);
    if (!root || !isShown(root)) return 0;
    return FIXTURE_BASE * (f.cfg.intensity ?? 1) * f.glow * spill;
  }
  if (isExterior(p.owner)) {
    return exteriorLive(p.owner) ? EXTERIOR_BASE * p.owner.glow * spill : 0;
  }
  // Same for the whole-room fallback: room focus hides the sibling rooms, and
  // point lights are not occluded by anything, so an ungated one would spill
  // straight through the wall into the room you are looking at.
  if (p.owner) {
    return p.owner.lit && isShown(roomMeshes.get(p.owner.roomId) || { visible: false })
      ? CENTRE_BASE * spill : 0;
  }
  return 0;
}

function roomGoal(r, night) {
  return r.lit && needsCentre(r) ? SLAB_INTENSITY * night : 0;
}

function paintSlab(r) {
  const slab = roomMeshes.get(r.roomId)?.children
    .find((c) => c.userData.part === 'slab');
  if (!slab) return;
  slab.material.emissive.copy(SLAB_GLOW);
  slab.material.emissiveIntensity = r.glow;
}

// Jump every ease to its target. main.js calls this beside settleDaylight() so
// the boot curtain doesn't lift onto a dozen lights visibly ramping up — the
// spill is no longer night-gated to zero, so that ramp would always show.
export function settleRoomLights() {
  const spill = spillScale();
  const night = getNightFactor();
  for (const f of fixtures) {
    f.glow = f.level01;
    f.painted = f.glow;
    const root = objects3d.get(f.objectId);
    if (root && f.emits) paintFixture(f, root);
  }
  for (const e of exteriors) { e.glow = e.level01; e.wasLit = e.glow > 0.01; }
  // AFTER the glows above, not before: candidacy is tested on glow, so a pool
  // handed out against the pre-settle zeros wins nothing and every light ramps
  // in from 0 on the first frame after the curtain lifts -- the exact ramp this
  // function exists to skip.
  reassignPool();
  for (const r of rooms) { r.glow = roomGoal(r, night); paintSlab(r); }
  for (const p of pool) p.light.intensity = slotGoal(p, spill);
}

// Room cards are captured off the live canvas and cached by GEOMETRY, then
// persisted — so a card shot while a lamp happened to be on bakes that in
// forever, and the pool lights are scene children the capture's per-room
// isolation sweep never hides. snapshots.js brackets its render with this.
//
// Intensity only, NEVER light.visible: dropping the count to 0 mid-capture
// recompiles every MeshStandardMaterial, twice per card, during a synchronous
// canvas readback. See the pool comment at the top of this file.
export function suspendRoomLights() {
  const saved = pool.map((p) => p.light.intensity);
  for (const p of pool) p.light.intensity = 0;
  const painted = fixtures.map((f) => f.painted);
  for (const f of fixtures) {
    const root = objects3d.get(f.objectId);
    // emissiveHex null restores the authored GLB materials (state.js)
    if (root && f.emits) paintModelState(root, { emissiveHex: null, grey: false });
  }
  return () => {
    pool.forEach((p, i) => { p.light.intensity = saved[i]; });
    fixtures.forEach((f, i) => {
      f.painted = painted[i];
      const root = objects3d.get(f.objectId);
      if (root && f.emits) paintFixture(f, root);
    });
  };
}

function tick(dt) {
  const level = getLevel();
  if (level !== lastLevel) {
    lastLevel = level;
    assignmentDirty = true;
  }

  const k = 1 - Math.exp(-dt / SMOOTH_TAU);

  // --- fixtures: ease the glow, repaint emissive only when it actually moved
  for (const f of fixtures) {
    const goal = f.level01;
    if (Math.abs(f.glow - goal) < 1e-3) f.glow = goal;
    else f.glow = THREE.MathUtils.lerp(f.glow, goal, k);
    if (!f.emits || Math.abs(f.glow - f.painted) < 5e-3) continue;
    // a fixture crossing in/out of "lit" changes who deserves a pool slot
    if ((f.glow > 0.01) !== (f.painted > 0.01)) assignmentDirty = true;
    f.painted = f.glow;
    const root = objects3d.get(f.objectId);
    if (root) paintFixture(f, root);
  }

  // --- exteriors: the same ease, with no emissive to paint -- the sconce is
  // part of the shell GLB, not a model this app owns ---
  for (const e of exteriors) {
    const goal = e.level01;
    if (Math.abs(e.glow - goal) < 1e-3) e.glow = goal;
    else e.glow = THREE.MathUtils.lerp(e.glow, goal, k);
    const lit = e.glow > 0.01;
    if (lit !== e.wasLit) {
      e.wasLit = lit;
      assignmentDirty = true;
    }
  }

  if (assignmentDirty) {
    assignmentDirty = false;
    reassignPool();
  }

  const spill = spillScale();

  // --- rooms: the slab wash stays a night-time mood cue ---
  const night = getNightFactor();
  for (const r of rooms) {
    const goal = roomGoal(r, night);
    // converge exactly, then stop writing. The old `&& r.glow === 0` guard let
    // a room settled at a non-zero glow rewrite its material every frame.
    if (Math.abs(r.glow - goal) < 1e-3) {
      if (r.glow === goal) continue;
      r.glow = goal;
    } else {
      r.glow = THREE.MathUtils.lerp(r.glow, goal, k);
    }
    paintSlab(r);
  }

  // --- the pool ---
  for (const p of pool) {
    const goal = slotGoal(p, spill);
    if (isFixture(p.owner)) {
      p.light.color.copy(p.owner.color);
      if (fixtureWorldPos(p.owner, _p)) p.light.position.copy(_p); // follows a drag
    } else if (isExterior(p.owner)) {
      p.light.color.copy(p.owner.color).lerp(EXTERIOR_WARM, 0.75);
    } else if (p.owner) {
      p.light.color.setHex(GLOW_COLOR);
    }
    p.light.intensity = THREE.MathUtils.lerp(p.light.intensity, goal, k);
    if (p.light.intensity < 1e-3 && goal === 0) p.light.intensity = 0;
  }
}
