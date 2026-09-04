// Home Assistant lights -> light in the 3D scene. Three sources feed one pool:
//
//   FIXTURES   a furniture object bound to an HA entity (objects.entity_id) --
//              a lamp GLB that IS light.bedside. Light comes from the fixture
//              itself, and the fixture's own materials glow.
//   EXTERIORS  a light PLACEMENT in an outdoor room -- the porch sconces and
//              garage floodlights, which hang on the shell and have no
//              furniture to bind to. The marker's position is the source.
//   ROOMS      two different whole-room lights, never both (roomLightMode):
//              CENTRE, the fallback for a room with no VISIBLE bound fixture
//              and no lit exterior -- the whole-room glow, from its placed
//              lights and its HA area's; and FILL, the warm indirect term a
//              room gets *while its own fixtures are lit*.
//
// Fixtures and exteriors outrank rooms for a pool slot, and a centre (a room's
// only light) outranks a fill (a room that is already lit). A room keeps its
// record either way -- roomcards.js and dashboard.js read the room->lights sets
// through the accessors below, and those must not change meaning.
import * as THREE from 'three';
import { scene, controls, renderer, onFrame } from './scene.js';
import { roomMeshes, floorBaseY, getLevel, isOutdoorRoom, setRoomWallFill } from './house.js';
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
// 45 used to be this number, back when a fixture was the ONLY light in its room
// and so had to fill the whole room single-handed. Everything past a few feet of
// the bulb then came out of the 1/d^2 divisor, which gave a big room a hot patch
// and a black remainder and a small one a flat wash: measured in the guest room,
// wall 194 behind the lamp -> 45 at the far end, and a floor reading 0-7 with the
// light ON. Nearly half that budget now goes to the fill below, which is what
// buys the direct term the headroom to fall off steeply and still leave a room
// standing behind it.
// FIXTURE_BASE / FILL_BASE / SLAB_FILL are `let` only because
// window.__roomlights.tune() writes them -- see the note on tune(). Nothing in
// the module itself assigns them.
let FIXTURE_BASE = 24;
const CENTRE_BASE = 90;            // a room centre sits further from every surface
const FIXTURE_RANGE = 22;          // ft; the light.distance cutoff

// --- the room fill -------------------------------------------------------
// A point light with decay 2 makes brightness nothing but a function of the
// distance to the bulb. Real rooms do not look like that, because most of what
// you can see is bounced light, which arrives from every direction at once --
// the Sims reference's floor sits on a 38-66 plateau under a lamp whose wall
// wash spans 242 -> 25 over the same span. This is that second term: one warm
// light at the room centre, alive only while the room's OWN fixtures are lit,
// with its DECAY FLATTENED so it reads as a plateau and not as a second hot
// spot at the ceiling. It is the only pool light that ever carries a decay
// other than 2.
//
// decay is a per-light UNIFORM in three (`struct PointLight { ... float decay; }`),
// not a program define like the pool's length or castShadow, so varying it per
// slot is free -- but every OTHER owner must set it back to 2, which
// reassignPool does. 0.45 holds ~1.4:1 across a 16 ft room. Exactly 0 is
// avoided on purpose: getDistanceAttenuation evaluates pow(lightDistance, decay)
// and pow(0.0, 0.0) is undefined in GLSL, and this light sits in mid-air where
// a headboard or a shelf may pass straight through it.
//
// FILL_BASE is NOT on the same scale as FIXTURE_BASE and must not be compared
// with it: with the 1/d^2 divisor gone this number is very nearly the
// irradiance it lands, not a candela at one foot.
// 2.0 was measured before the per-room ranges were tightened, and it turned out
// to spend almost exactly the contrast that tightening them bought: same room
// configs, far-wall modulation was 7.10 with the fill off and 1.96 with it at
// 2.0 (master bath), 29.25 -> 4.35 (master closet). Swept against the
// reference's own wall profile (242 -> 180 -> 99 -> 25, about 9.7:1) with
// everything else fixed:
//
//   fill  far-wall band                       ratio
//   0     247 210 126 108 47 16 17 21         15.4   dark end below the reference
//   0.4   247 211 129 114 56 25 28 33          9.9   <- the reference, near exactly
//   0.7   247 211 132 119 63 31 35 41          8.0
//   1.3   247 213 136 127 76 42 47 55          5.9
//   2.0   247 215 142 136 88 54 59 68          4.6   dark end 2.5x the reference
//
// The sweep also corrected the assumption this was built on: the guest room's
// floor reads 28-32 with the point fill at ZERO. SLAB_FILL below is what lifts
// a floor (it is the surface a point fill reaches worst, which is why the slab
// term exists) -- the point fill's real job is only the shadow side of
// furniture, and it does not need to be loud to do it. 0.5 sits just above the
// exact reference match to cover that.
let FILL_BASE = 0.5;
const FILL_DECAY = 0.45;
const FILL_RANGE = 1.8;            // x the room's own radius; the cutoff
// Bounce is warm whatever the bulb is -- it is the room's own walls and floor
// doing the bouncing, and the reference's night ambient measures a desaturated
// warm brown (28,24,18) even under a near-white torchiere. Deliberately not the
// fixture's HA colour: a lamp set to blue must not wash the whole room blue.
const FILL_COLOR = new THREE.Color(0xffb277);
// The floor is the surface a point fill reaches worst: its normal points at the
// ceiling while the fill hangs at eye height, so a plank two steps away takes
// the fill at a grazing angle and stays black. Measured in the guest room: the
// floor renders 108 at noon and 2 at night with the lamp ON. The reference's
// answer is not a brighter lamp -- under a torchiere its floor peaks at 66 and
// then PLATEAUS at 38 across the rest of the room, with no bright disc
// anywhere. A flat plateau is exactly what an emissive is, so the room's own
// slab carries the floor half of the indirect term and the point light carries
// the rest. Night-gated like the centre wash it sits beside: at noon the sun
// is already doing this.
let SLAB_FILL = 0.05;
// ...and the far WALL is the same argument one axis over. A point fill sits at
// the room centre, so illuminance on a vertical surface falls off with the
// distance to it AND with the cosine of the angle it is struck at -- the wall
// behind the lamp takes both penalties at once, which is why the shadow end of
// a lit room measured 4-16 while its bright end sat at 78-106. Every lit floor
// in the house metered below the Sims reference's UNLIT floor of 28, and its
// far corner is 25 against a peak of 242: the reference keeps every surface
// readable and gets its contrast out of the near end being hot, not the far end
// being black. Raising the direct term or widening a range is what produced the
// plateau the round before this one removed, so this lifts ONLY the surfaces
// the direct light does not reach, and by a flat amount, which is what an
// emissive is. Night-gated and fillFactor-gated exactly like SLAB_FILL: at noon
// the sun already does this (the day frame is byte-identical), and a room whose
// own fixtures are off gets exactly the nothing it got before.
//
// Composed with the accent hover/selection glow by house.js applyWallEmissive,
// because a material has one emissive and the two writers would otherwise
// clobber each other -- roomlights stops writing once its ease converges, so a
// hover would have erased the fill until the room's lights next moved.
// Sized against the reference's dark end: alone, an emissive of 0.055 in this
// colour tone-maps to about L 30 through ACESFilmic, and fillFactor takes ~0.63
// of that off a single-lamp room.
let WALL_FILL = 0.075;
const WALL_GLOW = new THREE.Color(0xffb277);   // the same bounce warm as FILL_COLOR
// ...but the generated wall shell is NOT what you are looking at in a furnished
// room. Every finished room here is skinned: `<Room> Wall Wash` is a run of
// full-height, edge-to-edge GLB planes, one per wall, sitting a hair inside the
// shell so each wall can carry its own albedo (see tools/roomkit/ROOM-BRIEF.md,
// "give each wall its own albedo"). They hide the shell completely -- measured
// by casting a 99-ray fan from the garage's own shot camera: `Garage Wall Wash`
// 15 hits, the room's wall mesh ZERO -- so an emissive on the shell alone
// rendered frames that were byte-identical to the ones before it. The fill
// therefore goes on the room's vertical room-scale surfaces, shell AND skin.
// SLAB_FILL has exactly this hole one axis over (its own comment notes a room
// floored with a `<Room> Floor` GLB gets nothing from it), and that is why every
// lit floor in this house meters below the Sims reference's UNLIT floor of 28.
// Deliberately only `wall wash`, the documented full-wall skin, and not every
// object with "wall" in its name: `Arcade TV Wall` and `Movie Screen Wall` are
// furniture that happens to stand against one, and painting a TV screen with the
// room's bounce is not what an indirect term is.
const WALL_SKIN_RE = /\bwall wash\b/i;
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
// Glow on the fixture's own materials. 1.6 left a dome lens measuring L=174
// against the wall beside it at 138-147 -- a margin of 1.2x, so you had to hunt
// the frame to find where the light was coming from. In every Sims 4 night
// reference the source is blown out (p99 ~246) against surfaces at 20-100, a
// margin of 2.5x to 10x: a lamp reads as ON because the lamp is the brightest
// thing in the room, not because the room got brighter. Under ACESFilmic a warm
// lens needs to be pushed well past 1.0 to clip, and the warm light_cfg.color
// costs blue channel on the way, so this sits high.
const EMISSIVE_MAX = 3.4;
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
            : `room ${p.owner.roomId} ${roomLightMode(p.owner)}`)
        : null,
      intensity: +p.light.intensity.toFixed(2),
      decay: p.light.decay,
      distance: +p.light.distance.toFixed(1),
    })),
    fills: () => rooms.filter((r) => fillFactor(r) > 0.001).map((r) => ({
      roomId: r.roomId, lit: r.lit, factor: +fillFactor(r).toFixed(3),
      pooled: pool.some((p) => p.owner === r),
      slab: +r.glow.toFixed(4), wall: +r.wallGlow.toFixed(4),
    })),
    // every room's two emissive terms, off rooms included — the off-state
    // check is "is this list all zeros", which `fills` above cannot answer
    // because it filters the off rooms out.
    surfaces: () => rooms.map((r) => ({
      roomId: r.roomId, mode: roomLightMode(r),
      slab: +r.glow.toFixed(4), wall: +r.wallGlow.toFixed(4),
    })),
    bound: () => [...boundEntities],
    // Sweep the three lighting budgets without a page reload. One shot per
    // value costs a browser boot and ~40 s of model loading, and the numbers
    // only mean anything compared against each other from the SAME scene --
    // the room's light_cfg is edited between rounds, so a shot taken an hour
    // ago is not a baseline. scratchpad/lightgauntlet/sweep.py drives this and
    // calls settleRoomLights() after each change.
    tune: (o) => { if (o.fixture !== undefined) FIXTURE_BASE = o.fixture;
                   if (o.fill !== undefined) FILL_BASE = o.fill;
                   if (o.slab !== undefined) SLAB_FILL = o.slab;
                   if (o.wall !== undefined) WALL_FILL = o.wall;
                   return { FIXTURE_BASE, FILL_BASE, SLAB_FILL, WALL_FILL }; },
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
      const roomWallSkins = [];
      for (const o of room.objects || []) {
        // ...and, in the same pass, the wall skins the fill has to reach. An
        // entity-bound piece is a fixture and never a surface, so this tests
        // the name only for the ones that fall through.
        if (!o.entity_id && WALL_SKIN_RE.test(o.name || '')) roomWallSkins.push(o.id);
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
      // A room with no light.* of its own still needs a record if it has an
      // emitting fixture, or the fill below has nothing to hang on: a
      // switch-controlled lamp (switch.dining_room driving the dining
      // chandelier -- five rooms here) is never in lightIds, because
      // roomcards.js toggles that set with light.turn_off and must not be
      // handed a switch. lightIds stays exactly as it was, so the record is
      // invisible to the accessors and to byEntity.
      if (!lightIds.size && !roomFixtures.some((f) => f.emits)) continue;

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
        glow: 0,     // eased slab emissive intensity
        wallGlow: 0, // eased wall-shell emissive intensity (the vertical half)
        // The room-centre fallback yields to a fixture only while that fixture
        // is actually ON SCREEN — tested per frame, not decided here. House
        // mode hides all indoor furniture, and a room whose only candidate was
        // a fixture would otherwise go dark in the one view where warm windows
        // at night are the entire point.
        fixtures: roomFixtures,
        exteriors: roomExteriors,
        wallSkins: roomWallSkins,
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

// How much of the room's own lighting is actually burning, as a sum of eased
// glows -- so it moves with the lamp's fade instead of popping, and is exactly
// 0 when every fixture in the room is off.
function litFixtureLoad(rec) {
  let sum = 0;
  for (const f of rec.fixtures) if (f.emits && fixtureShown(f)) sum += f.glow;
  return sum;
}

// Saturating, because bounce is not additive the way emitters are: a room with
// three lamps is not three times as bounced as a room with one. 1 lamp -> 0.63,
// 2 -> 0.86, 3 -> 0.95.
function fillFactor(rec) {
  const load = litFixtureLoad(rec);
  return load > 0 ? 1 - Math.exp(-load) : 0;
}

// Which whole-room light does this room want? Never both.
//   'centre'  no visible emitting fixture and no lit exterior -- the old
//             fallback wash, which is then the room's ONLY light.
//   'fill'    the room has a visible emitting fixture: the warm indirect term.
//             fillFactor decides whether it is actually burning, so a room
//             whose lamp is off but whose (unplaced) area light is on gets the
//             same nothing it always got.
//   null      a lit exterior is lighting the room from where the light really
//             is, same reason a fixture used to suppress the centre outright.
function roomLightMode(rec) {
  if (rec.fixtures.some((f) => f.emits && fixtureShown(f))) return 'fill';
  if (rec.exteriors.some((e) => e.glow > 0.01 && exteriorLive(e))) return null;
  return 'centre';
}

// light_cfg.glow_part narrows the emissive to the fixture's own lens. Without
// it the whole GLB glows, which is right for a lamp (it IS a shade on a stick)
// and badly wrong for anything where the bulb is one part of a larger piece --
// a bathroom vanity bound to its light bar is a 9 ft cabinet, mirror, basin and
// counter, and painting all of it lamp-amber turns the wall into a white slab.
// The pattern is matched case-insensitively against each mesh's MATERIAL name
// first (glb.py groups primitives by material, so a material is a part here)
// and then its own name. Compiled per fixture and cached: paintFixture runs on
// every frame the glow moves.
function glowFilter(f, root) {
  const pat = f.cfg.glow_part;
  if (!pat) return undefined;
  if (f.__glowRe?.src !== pat) {
    let re = null;
    try { re = new RegExp(pat, 'i'); } catch { /* bad pattern -> glow it all */ }
    f.__glowRe = { src: pat, re };
    f.__glowRoot = null;
  }
  const { re } = f.__glowRe;
  if (!re) return undefined;
  const test = (mesh) => {
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    return mats.some((m) => m?.name && re.test(m.name)) || re.test(mesh.name || '');
  };
  // A pattern that matches NOTHING would leave the filter rejecting every mesh,
  // and paintModelState restores whatever it rejects -- so one typo in
  // glow_part reads as a lamp that switches on and does not glow, with nothing
  // logged anywhere. Verify once per root (a rebuild hands over a new one) and
  // fall back to glowing the whole model, which is the pre-glow_part behaviour.
  // Re-tested while the answer is still "nothing matches", NOT once per root:
  // the GLB loads into an object root that already exists, and settleRoomLights
  // paints at boot -- so a check cached on the first paint measures an EMPTY
  // root, decides the pattern matches nothing, and falls back to glowing the
  // whole model for the life of the page. That is exactly what a bound vanity
  // looked like: a 9 ft white slab. A positive answer is cached; a negative one
  // costs a traverse of a few dozen meshes, and only on the frames the glow is
  // actually moving.
  if (f.__glowRoot !== root || !f.__glowAny) {
    f.__glowRoot = root;
    f.__glowAny = false;
    root.traverse((c) => {
      if (!f.__glowAny && c.isMesh && c.userData.__orig && test(c)) f.__glowAny = true;
    });
  }
  return f.__glowAny ? test : undefined;
}

function paintFixture(f, root) {
  // NOT applyStyle: that also rescales the marker, and a lamp must not grow
  // 1.25x when it turns on. Glow is never night-gated — a lamp that is on
  // reads as on at noon.
  paintModelState(root, {
    emissiveHex: f.color.getHex(),
    emissiveIntensity: EMISSIVE_MAX * f.glow,
    grey: false,
    partFilter: glowFilter(f, root),
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

// Give the pool to the best-ranked owners, in four bands, each ordered by
// distance to what the camera is looking at (so the room you are looking at
// outranks one you are not):
//   1 fixtures   they light from the right place
//   2 exteriors  same, for the facade
//   3 centres    a room whose ONLY light this is; losing the slot blacks it out
//   4 fills      a room that is already lit by its own fixtures, so the worst a
//                lost slot costs is the indirect term
// With ~41 bound fixtures against a pool of 12 the fills only ever get a slot
// once the fixtures on screen have taken theirs -- which is the whole-house
// view, seen from outside, where nobody is looking at a floor anyway. In room
// focus and on a single floor, where the fill is what the room is judged on,
// there is always room.
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
  const centreCands = [];
  const fillCands = [];
  for (const r of rooms) {
    if (!onLevel(r.level)) continue;
    if (!isShown(roomMeshes.get(r.roomId) || { visible: false })) continue;
    const mode = roomLightMode(r);
    // `lit` is the right test for the centre wash -- those ARE the entities it
    // stands in for -- and the wrong one for the fill, which follows the
    // fixtures themselves so a switch-bound lamp still bounces.
    if (mode === 'centre') { if (r.lit) centreCands.push(r); }
    else if (mode === 'fill' && fillFactor(r) > 0.01) fillCands.push(r);
  }
  const byTarget = (a, b) =>
    a.center.distanceToSquared(controls.target) -
    b.center.distanceToSquared(controls.target);
  centreCands.sort(byTarget);
  fillCands.sort(byTarget);

  // ...except that fixtures do not outrank fills WITHOUT LIMIT. Measured on
  // this house's second floor with every light forced on: 12 lit fixtures took
  // all 12 slots and not one room got its fill, so a whole floor went back to
  // black floors the moment the sixth lamp came on. Reserve a quarter of the
  // pool for the NEAREST fills, and pay for it out of the FURTHEST direct
  // owners -- the ones least likely to be what the camera is looking at. In
  // room focus there are only ever a handful of direct owners, so this changes
  // nothing in the view a room is judged in.
  const direct = [...fixCands, ...extCands, ...centreCands];
  const reserved = Math.min(Math.max(1, Math.round(POOL_SIZE / 4)), fillCands.length);
  const keep = Math.max(0, POOL_SIZE - reserved);
  const winners = [
    ...direct.slice(0, keep),
    ...fillCands.slice(0, reserved),
    ...direct.slice(keep),        // if the direct list was short, take it back
    ...fillCands.slice(reserved),
  ].slice(0, POOL_SIZE);

  // keep already-assigned winners on their light so they don't blink
  for (const p of pool) if (!winners.includes(p.owner)) p.owner = null;
  for (const owner of winners) {
    if (pool.some((p) => p.owner === owner)) continue;
    const slot = pool.find((p) => !p.owner);
    if (!slot) break;
    slot.owner = owner;
  }
  // position every slot now that ownership has settled. decay is set on every
  // branch, not only the fill's: a slot that held a fill last frame carries
  // FILL_DECAY, and handing it to a lamp without putting it back would give
  // that lamp no falloff at all.
  for (const p of pool) {
    if (!p.owner) continue;
    if (isFixture(p.owner)) {
      if (fixtureWorldPos(p.owner, _p)) p.light.position.copy(_p);
      p.light.distance = p.owner.cfg.range ?? FIXTURE_RANGE;
      p.light.decay = 2;
    } else if (isExterior(p.owner)) {
      p.light.position.copy(p.owner.pos);
      p.light.distance = EXTERIOR_RANGE;
      p.light.decay = 2;
    } else if (roomLightMode(p.owner) === 'fill') {
      p.light.position.copy(p.owner.center);
      p.light.distance = p.owner.radius * FILL_RANGE;
      p.light.decay = FILL_DECAY;
    } else {
      p.light.position.copy(p.owner.center);
      p.light.distance = p.owner.radius * 2.5;
      p.light.decay = 2;
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
  // Same for either whole-room light: room focus hides the sibling rooms, and
  // point lights are not occluded by anything, so an ungated one would spill
  // straight through the wall into the room you are looking at.
  if (p.owner) {
    const r = p.owner;
    if (!isShown(roomMeshes.get(r.roomId) || { visible: false })) return 0;
    const mode = roomLightMode(r);
    if (mode === 'centre') return r.lit ? CENTRE_BASE * spill : 0;
    if (mode === 'fill') return FILL_BASE * fillFactor(r) * spill;
    return 0;
  }
  return 0;
}

function roomGoal(r, night) {
  const mode = roomLightMode(r);
  if (mode === 'centre') return r.lit ? SLAB_INTENSITY * night : 0;
  if (mode === 'fill') return SLAB_FILL * fillFactor(r) * night;
  return 0;
}

// Deliberately NOT folded into roomGoal: the centre wash has no wall term. A
// centre-lit room is one whose only light is the whole-room point light itself,
// which already sits in the middle of the room throwing at every wall equally;
// there is no shadow side for a fill to rescue, and adding one there would lift
// every room in the house that has no fixture at all.
function wallFillGoal(r, night) {
  return roomLightMode(r) === 'fill' ? WALL_FILL * fillFactor(r) * night : 0;
}

function paintSlab(r) {
  const slab = roomMeshes.get(r.roomId)?.children
    .find((c) => c.userData.part === 'slab');
  if (!slab) return;
  slab.material.emissive.copy(SLAB_GLOW);
  slab.material.emissiveIntensity = r.glow;
}

// The authored-material record for one mesh, or null. Same fallback
// windowlight.js needs and for the same reason: cutaway.js splitMerged rebuilds
// a run that skins several walls as one child mesh PER WALL with its own
// material clone and empties the parent's geometry, so the mesh carrying
// `__orig` is the one that stopped drawing -- and `<Room> Wall Wash` is exactly
// that shape (one GLB, four walls) AND matches cutaway's WALL_ARCH_RE, so it is
// always split. The split children are single-material by construction, so the
// parent's index 0 is theirs.
function origFor(child) {
  if (child.userData.__orig) return child.userData.__orig;
  const p = child.parent;
  return p?.isMesh && p.userData.__orig ? p.userData.__orig : null;
}

// Paint the fill onto a wall skin. Only materials the GLB authored as NON
// emissive are touched, which does three jobs at once: it needs no restore
// bookkeeping (intensity 0 writes black, which IS the authored value), it keeps
// this off anything that is a light source rather than a surface, and it settles
// the one collision this could have had -- windowlight.js writes the same
// property on glazing materials wherever they turn up, and a pane is authored
// emissive.
function paintSkin(root, intensity) {
  root.traverse((child) => {
    if (!child.isMesh) return;
    const origs = origFor(child);
    if (!origs) return;
    const mats = Array.isArray(child.material) ? child.material : [child.material];
    mats.forEach((m, i) => {
      const orig = origs[i] ?? origs[0];
      if (!m.emissive || !orig || orig.emissive) return;
      m.emissive.copy(WALL_GLOW).multiplyScalar(intensity);
      m.emissiveIntensity = 1;
    });
  });
}

function paintWalls(r) {
  const mesh = roomMeshes.get(r.roomId);
  if (mesh) setRoomWallFill(mesh, WALL_GLOW, r.wallGlow);
  for (const id of r.wallSkins) {
    const root = objects3d.get(id);
    if (root) paintSkin(root, r.wallGlow);
  }
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
  for (const r of rooms) {
    r.glow = roomGoal(r, night);
    paintSlab(r);
    r.wallGlow = wallFillGoal(r, night);
    paintWalls(r);
  }
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
  // The slab wash is not a pool light and was never covered here, so a card
  // captured after dark baked the room's warm floor glow in forever. The fill
  // added a second, quieter writer of it (SLAB_FILL), so close it now. Material
  // `emissiveIntensity` is a plain uniform, not a program define -- writing it
  // costs no recompile, unlike the light.visible the note above forbids.
  // The wall shell is the same hole one axis over, and it is a bigger one: a
  // room card frames a room's walls, not its floor. Same reasoning, same fix.
  const slabs = rooms.map((r) => r.glow);
  const wallGlows = rooms.map((r) => r.wallGlow);
  for (const r of rooms) {
    r.glow = 0;
    paintSlab(r);
    r.wallGlow = 0;
    paintWalls(r);
  }
  const painted = fixtures.map((f) => f.painted);
  for (const f of fixtures) {
    const root = objects3d.get(f.objectId);
    // emissiveHex null restores the authored GLB materials (state.js)
    if (root && f.emits) paintModelState(root, { emissiveHex: null, grey: false });
  }
  return () => {
    pool.forEach((p, i) => { p.light.intensity = saved[i]; });
    rooms.forEach((r, i) => {
      r.glow = slabs[i];
      paintSlab(r);
      r.wallGlow = wallGlows[i];
      paintWalls(r);
    });
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

  // --- rooms: the wall shell's half of the same indirect term ---
  // Its own loop, not a second write inside the one above: the two eases share
  // a goal shape but not a value, and they do not stop on the same frame.
  //
  // The converge-and-stop the slab uses does NOT carry over here, and this is
  // the one place where holding a settled value costs a per-frame write. A lit
  // room keeps repainting because the materials it is painting can arrive AFTER
  // it settled: a wall-skin GLB resolves async (an object root exists from
  // buildObjects, empty, long before its meshes do), and cutaway.js splitMerged
  // then rebuilds that run as one FRESH material clone per wall the first time
  // the room is scored. Either event hands over a material with the authored
  // black emissive, and a room that had stopped writing would leave it there for
  // the life of the page. A settled DARK room still stops dead — that is the
  // common case, and it is the one the off-state guarantee rests on.
  for (const r of rooms) {
    const goal = wallFillGoal(r, night);
    if (Math.abs(r.wallGlow - goal) < 1e-4) {
      if (r.wallGlow === goal && goal === 0) continue;
      r.wallGlow = goal;
    } else {
      r.wallGlow = THREE.MathUtils.lerp(r.wallGlow, goal, k);
    }
    paintWalls(r);
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
      if (roomLightMode(p.owner) === 'fill') p.light.color.copy(FILL_COLOR);
      else p.light.color.setHex(GLOW_COLOR);
    }
    p.light.intensity = THREE.MathUtils.lerp(p.light.intensity, goal, k);
    if (p.light.intensity < 1e-3 && goal === 0) p.light.intensity = 0;
  }
}
