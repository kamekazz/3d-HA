# Light gauntlet — shared plan

Goal: every room has a light fixture bound to a real HA entity, and a room whose
lights are on **reads as lit** — warm pool on the floor, wash up the walls,
falloff — while a room whose lights are off stays genuinely dark.

Bar: The Sims 4 night interiors with lamps on. References in `ref/`.

## Rules everyone follows

1. **Never call Home Assistant to turn a light on.** This is the user's real
   house. `POST /api/control` would physically switch their lamps. Every test
   forces state *client-side* via `state.js applyState()` — that is what
   `tools/roomkit/lightshot.py` does. No exceptions.
2. **All layout writes go through the HTTP API**, never straight into
   `house.db`. The routes are `@undoable`, so an API write is undoable and a
   direct SQLite write silently desynchronises history:
   - `POST /api/house/room/<id>/object` — add furniture (model_id, name, x/y/z,
     rot_y, scale)
   - `PATCH /api/house/object/<id>` — set `entity_id`, `light_cfg`, geometry
   - `POST /api/house/model` — upload a `.glb` (multipart)
3. **Feet everywhere.** World unit = 1 ft. Object x/y/z are room-LOCAL feet,
   measured from the room's x/z anchor (bbox min corner), y from the floor.
4. A binding that does not emit is a failure. `roomlights.js EMITTING_DOMAINS`
   is `light` + `switch`; a `fan.*` binding is click-only. If you bind a fan or
   anything else that must glow, set `light_cfg.emit = true`.

## The shot rig

```
cd tools
../backend/.venv/Scripts/python.exe -m roomkit.lightshot --room <id> --level <0|1|2> \
    --out ../scratchpad/lightgauntlet/shots/r<id>_<tag>
```

Writes `<out>_on.png` and `<out>_off.png` and prints JSON: the entities it
forced, per-slot light intensities, and `delta` (centre-box luminance on minus
off). It uses room focus for scoping and takes the camera itself from inside
the room's air volume.

`--day` shoots at noon instead of the default 22:00 night.

## Room → entity map

`level` is the FLOOR LEVEL that `--level` wants, not the floor id.

| room | id | level | entity to bind | fixture object |
|---|---|---|---|---|
| Movie Room | 1 | 0 | `light.movie_room_lamp` | none yet |
| Arcade Room | 2 | 0 | `light.game_room_downlights` | none yet |
| Dining | 4 | 1 | `switch.dining_room` (TP-Link HS210 dimmer) | **146 Dining Chandelier** |
| Living Room | 5 | 1 | `light.living_room_livingroom` | none yet (113 is a fan) |
| Kitchen | 6 | 1 | `switch.kitchen` | none yet |
| Garage | 7 | 1 | `light.garage` | none yet |
| Office | 8 | 1 | `light.work_office_desk` | none yet |
| Laundry | 9 | 1 | `switch.laundry_room` | none yet |
| Pantry | 10 | 1 | `switch.pantry` | none yet |
| First floor hallway | 12 | 1 | — none exists in HA — | none yet |
| Office printers | 22 | 1 | `switch.office_closet` | none yet |
| Bathroom 1F | 23 | 1 | — none exists in HA — | **181 Bath1F Vanity** |
| Guest Room | 13 | 2 | `light.guest_room` | none yet |
| Master Bed | 14 | 2 | bound already (13, 203) | 13, 203 |
| Rios Room | 15 | 2 | bound already (125) | 125 |
| Master Bath | 16 | 2 | `light.2nd_floor_master_bathroom_light` | **155 Master Bath Vanity** |
| Hallway 2F | 17 | 2 | `light.2nd_floor_2nd_floor_hallway` | none yet |
| Master Closet | 27 | 2 | `light.rosemarys_closet` | none yet |
| bath 2F | 26 | 2 | — none exists in HA — | **163 Bath2F Vanity** |
| Bathroom closet | 24 | 2 | — none exists — | none |
| Room 7 | 25 | 2 | — none exists — | none |
| Stairwell | 28 | 2 | — none exists — | none |

Outdoor rooms (3 Backyard, 11 Frontyard) are already handled by the EXTERIORS
path in `roomlights.js` and are out of scope for this run.

**Do not bind a `*_led` switch.** `switch.kitchen_led`, `switch.pantry_led`,
`switch.hallway_led` etc. are the wall switch's own indicator LED, not the room
light. The bare `switch.kitchen` / `switch.pantry` / `switch.laundry_room` is
the light.

## Where the light engine's knobs are

`frontend/js/roomlights.js`:
- `FIXTURE_BASE = 45` candela, decay 2, world unit = 1 ft → illuminance is
  intensity / d². `light_cfg.intensity` multiplies it per fixture.
- `FIXTURE_RANGE = 22` ft cutoff; `light_cfg.range` overrides.
- `light_cfg.offset_y` (default 1.0 ft) lifts the emitter above the object's
  base — a ceiling fixture needs this to be roughly the object's own height.
- `light_cfg.color`, `light_cfg.emit`, `light_cfg.glow_part`.
- `POOL_SIZE = 12` point lights, handed to the nearest visible candidates.
  Fixtures outrank whole-room fallbacks. This is a hard cap — a house-wide view
  cannot light more than 12 sources at once.

## Findings from the first calibration shot (room 14, Master Bed)

- The rig is sound: identical framing between the on and off shot, off is
  genuinely dark (centre luminance 9.8), on reads 58.1, delta +48.3.
- ~~**The window blinds render blown-out white in an unlit night room.**~~ **FIXED** by
  `frontend/js/windowlight.js`: window emissive now follows `daylight.js`'s night factor, authored
  at day, `NIGHT_LUM` cool-blue at night. Room 14 unlit centre 12.7 -> 8.5, p95 45 -> 43, and the
  blinds meter (21,24,33) instead of clipping. Day renders are byte-identical. Original report:
  In
  `r14_master_off.png` the two windows are the brightest thing in a pitch-dark
  bedroom, which is backwards — at night an unlit room's window should be the
  DARK hole, or at most faintly moonlit. Whatever material the blinds carry is
  either emissive or unlit. This is not a binding problem and no `light_cfg`
  will fix it; it needs the blind material looked at. Any critic will flag it,
  so it is logged here rather than being rediscovered per room.
- Reference note: the five official Sims 4 screenshots on Steam
  (`ref_steam/`) are genuine but all DAYTIME. Use them for general material and
  scale calibration only. The night bar lives in `ref/`.

## The bar, measured (12 verified Sims 4 night interiors in `ref/`, notes in `ref/REF.md`)

These are measured off the reference images, not opinions. Build to them.

| what | Sims 4 | ours at round 0 (room 14) |
|---|---|---|
| unlit room at night | **L ≈ 28** — dark but never black, floor texture still readable | 9.8 — too dark |
| lit room | **L ≈ 124** | 58.1 — too dim |
| lit : unlit ratio | **≈ 4.5 : 1** | 5.9 : 1 |
| brightest thing in frame | **the fixture itself**, blown out to p99 ≈ 246 | the fixture is not the brightest thing |

Five rules the reference actually shows, several of which contradict the
obvious instinct:

1. **Wall wash is hot and tight; the floor pool is broad and weak.** Behind a
   torchiere the wall reads 242 at the shade, 180 one tile out, 99 at two, 25 in
   the far corner — while the floor directly under the same lamp peaks at only
   **66**. There is no bright disc on the floor. Do not tune for one.
2. **The fixture is far brighter than anything it lights.** Candles and bulbs
   read as blown-out emissive shapes while the wall a foot behind them sits at
   L 20–30. Self-illuminated first, light-casting second. This is what
   `glow_part` + `EMISSIVE_MAX` are for.
3. **Colour temperature is the main cue that a light is on, not brightness.** In
   the one-lit-room dollhouse shot the lit room is only **1.7×** brighter than
   the unlit house — it reads as "on" purely because it is orange while
   everything else is neutral blue. A warm fixture colour is worth more than
   raw intensity.
4. **Warm interior against cool blue exterior is the whole night look.** Every
   moonlit outdoor surface measures cool blue (43,51,93); every lit interior
   patch measures warm yellow.
5. **Ceilings stay dark**, and a wall sconce lights the wall *below* it, not
   above. A chandelier lifts the counter under it to ~130 while the ceiling it
   hangs from stays at ambient.

Per-fixture colour temperature from the reference: torchiere ≈ near-white
(189,190,150); table lamp ≈ strong amber (126,85,42); candle chandelier ≈ yellow
(247,215,69); ceiling bathroom light ≈ neutral white (126,127,100).

**Both ends of our range are currently too dark.** Raising a single room's
`light_cfg.intensity` chases only half of it, and the unlit floor is a global
ambient question, not a per-room one — do not each invent a different fix for
that. Report what your room needs and it will be settled centrally.

## Rig correctness fix — every shot taken before this is suspect

`lightshot.py` runs its setup TWICE per shot (a re-assert after the settle, so a
late model load cannot leave a stale pose). On the second pass `house.setLevel()`
re-showed every room on the level, undoing the sibling-room hiding that room
focus had done on the first pass — and `enterFocus` then early-returned, because
it was already focused on that room. Sibling rooms therefore held pool slots at
`CENTRE_BASE` (90 cd), and **a point light is occluded by nothing**, so they lit
the subject straight through its walls.

Every "unlit" shot taken before this fix has a false ambient floor, and every
"lit" shot got fill it should not have had. Measured on the Dining room:

| | before | after |
|---|---|---|
| off, centre luminance | 17.0 | **6.2** |
| lights in the pool during the off shot | 4 sibling rooms at ~90 cd | **none** |
| delta | 47.7 | **51.5** |

**Consequence for anyone judging a room: take your own shots.** Do not trust a
screenshot a builder produced — re-shoot with the current rig and judge that.
A room tuned against the old leak may now be too dim.

## Calibration decision: do NOT chase the Sims absolute luminance numbers

The reference measures a lit Sims room at L≈124 and ours at L≈40, which looks
like a 3x shortfall. It is not one. The Movie Room at centre-luminance 39.5
(`shots/r1_round4_on.png`) is a convincingly lit warm media room by eye. The two
images come out of different renderers with different tone mapping — this app
uses ACESFilmic — so absolute 8-bit luminance does not transfer between them.

Judge on the **ratio** (lit vs unlit, target ≈4.5:1 and no worse than ~3:1),
on the reference's qualitative rules (warm against cool, fixture brightest,
tight wall wash, weak floor pool, dark ceilings), and above all on the blind
side-by-side. Do not globally rescale the renderer to hit an absolute number.

## Second rig fix: the camera moved between the ON and the OFF shot

The 8-direction clearance probe that picks where the eye stands was re-run on
every pass. It reads the live scene, and the scene is not the same on the second
pass — the first has already enabled the cutaway and hidden the device markers,
so the rays fly further and a different direction can win. In a near-square room
several directions sit within a foot of each other, so the winner flips: room 15
shot its ON frame from the east wall at `[10.32, 22.77, 28.55]` and its OFF frame
from a diagonal at `[-0.04, 22.77, 32.84]`, and reported the difference between
two different photographs as a delta.

The pose is now solved ONCE and pinned for every pass of both frames. Verified on
room 15: both frames now report `at [8.54, 22.77, 32.84]`, delta 67.7.

Together with the wall-leak fix, this means **any number produced before now is
unreliable, and any conclusion drawn from one should be re-taken.** The two
failure modes pushed in opposite directions — the leak inflated the off frame,
the roaming camera could inflate or deflate either — so they do not cancel.
