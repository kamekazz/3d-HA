# Frontend (`frontend/js/`)

Native ES modules, Three.js via CDN importmap — no npm, no bundler, no build step. What each module
does is readable from the files themselves; below is the part the code can't tell you.

`house.js` loads the whole-house shell GLB; when that fetch/parse fails it dispatches
`shellLoadFailed` and `ui.js` raises a persistent banner — a silently missing house reads as a
render bug rather than the deploy problem it usually is (see `docs/TROUBLESHOOTING-house-shell.md`).

**The boot curtain** (`frontend/js/boot.js`): the app assembles itself over seconds — ~200 furniture
GLBs, the DRACO house shell, wall/floor textures, then the room-card thumbnails — and every one of
those used to land on screen as its own pop-in, with the camera visibly re-framing when the shell
arrived (`house.js` `refitStage`). `#boot-screen` covers all of it and lifts once. Eight things about
it are not readable from the code:

- **The markup is static in `index.html`, deliberately.** `<head>` blocks on socket.io and the
  three.js importmap from a CDN before `main.js` is even parsed, so a JS-created overlay would flash
  the empty chrome first.
- **`DefaultLoadingManager` drives the progress bar; `models.js modelsIdle()` is the gate.** Every
  loader in the app is constructed with no explicit manager (`models.js` GLTFLoader/DRACOLoader,
  `textures.js` TextureLoader), so the manager sees GLBs, the DRACO decoder and textures alike — but
  its counts dip to zero between bursts, so it cannot be the completion signal on its own, and its
  `itemsLoaded`/`itemsTotal` are closure locals that are **not** readable off the instance (boot.js
  mirrors them from the callbacks). `modelsIdle()` counts inside `getInstance`, not `loadModel`, so
  it covers the clone/material work after the fetch — and the shell and device markers for free.
- **Never wait on a bare `requestAnimationFrame` in the gate.** Chrome pauses rAF whenever the tab is
  backgrounded, occluded or not being composited, so a bare rAF hangs the curtain until the watchdog
  — measured, not theoretical. `boot.js nextFrame()` races rAF against a 100 ms timer, and
  `finishBoot` uses it too. `main().catch` reveals first and *then* banners, or a boot error would be
  an unreadable black screen. `window.__boot.state()` says which gate is holding during a hang, and
  `window.__boot.timeline()` gives the per-stage wall clock.
- **The watchdog reveals on a STALL, never on a clock.** It used to be a flat 15 s failsafe, and that
  was a bug, not a safety net: assembly here takes 8-20 s, so the timer fired *inside*
  `settleLoaders` and lifted the curtain at 633/640 items — measured. Everything downstream of that
  await (the shell's `refitStage`, `compileAsync`, the cutaway/daylight/light settles, and the
  room-card snapshots, which had not even started) therefore ran in full view. That is the
  "two or three things pop up after the loading screen" report. `boot.js` now tracks `progressAt`,
  bumped by both `DefaultLoadingManager` callbacks and a sampled `modelsPending()`, and re-arms
  every 500 ms for as long as either the house is missing or *something moved* within `STALL_MS`
  (8 s), up to a 120 s `HARD_CAP_MS`. `settleLoaders` correspondingly carries **no deadline of its
  own** — a second independent clock racing the watchdog is what created the gap — and it races
  `modelsIdle()` against a 250 ms poll so a wedged GLB cannot park it past the watchdog's decision.
- **The failsafe will not reveal an empty stage.** `main()` spends its first phase awaiting three
  fetches, and if HA is still connecting they can outlast any timer — at which point `buildHouse` has
  not run and an unconditional reveal lifts the curtain onto nothing, which reads as "the app opened
  and the house doesn't render". `main()` calls `bootHouseBuilt()` the moment geometry is in the
  scene; until then the watchdog relabels the curtain "Waiting for Home Assistant…".
- **The house is loaded first, and alone.** `main()` awaits `houseShellReady()` immediately after
  `buildHouse`, *before* `buildDevices`/`buildObjects` fire ~271 furniture loads. It is the first
  thing you see so it should be the first thing loaded — but it is also the shell that pays for
  sharing: it is DRACO-compressed, and the decoder (763 KB over three files in `vendor/draco/gltf/`)
  is only requested once GLTFLoader has parsed the shell and met the extension, so issued after the
  furniture it queues behind all of it on a 6-connection pool. Doing it first also means
  `setEnvironmentData` measures a shell that already exists, so the yard is planted correctly once
  instead of being built and replanted on the shell's `levelChanged`. `houseShellReady()` resolves
  immediately when there is no shell or it failed, so a 404 shell cannot hang the boot.
  (`settleLoaders` alone was never sufficient for this: `getInstance` drops its in-flight count in a
  `finally`, so `modelsIdle()` can resolve a microtask *before* `loadHouseShell`'s continuation has
  added, masked and framed anything.)
- **The model files are cached, and that is most of the boot time.** Werkzeug defaults to
  `Cache-Control: no-cache`, so every one of the ~270 GLBs was revalidated on every single page load
  — 12.3 MB and ~10.6 s, measured. `models.js` now appends `?v=<mtime>` from the `model_versions`
  map on `GET /api/house` (`setModelVersions`, called before any `getInstance` in both `main()` and
  `reloadHouse`), and `house/routes.py` serves a versioned request `immutable` for a year. The id
  alone cannot be the version — uploads reuse the `model_<id>.<ext>` filename, and the roomkit tools
  rewrite those files in place — which is why it is keyed on mtime. An unversioned request keeps the
  old revalidate-every-time behaviour. Warm boot: 8.5 s → 1.7 s.
- **The bar has to arrive at 100% before the fade starts.** `#boot-fill` animates its width over
  0.3 s, so lifting the curtain one frame after `paint(1)` cut that animation off around 90% — the
  bar visibly never finished. `finishBoot` waits on `barFull()` (transitionend raced against the
  computed `transition-duration`, since transitionend never fires under `prefers-reduced-motion` or
  in a backgrounded tab) before adding `body.booted`.

The render loop keeps running behind the curtain **on purpose**: `snapshots.js` captures the room
cards off the live canvas, and `scene.js`'s pose solve needs real renders. Because the shell now
lands before the user can touch the camera, `refitStage({onlyIfUntouched: true})` always wins and the
opening shot is the shell-measured one. `reloadHouse` (planner close, undo, sync) gets no curtain —
models are already cached.

**The stage, and how the house gets framed** (`frontend/js/stage.js` + `scene.js`): the canvas is
full-bleed (`#scene-container` is `inset:0`) but chrome covers part of it, so the house is framed
into the *unobstructed* rect — "the stage" — and that rect is owned by **CSS, not JS**. `#stage-rect`
is an invisible fixed div inset by the `--stage-*` tokens; `stage.js` measures it with one
`getBoundingClientRect()`, which resolves `calc()`, `env()`, every media query, the orientation and
any `body.*` override at once (`getComputedStyle` on an unregistered custom property returns its
token *stream*, the literal `calc(...)` string, so it cannot do this). Move the tokens — including
the `--stage-spill` knob, which is how far the house may tuck behind 80%-opaque glass — and the 3D
re-frames itself. `visibility:hidden`, never `display:none`: the latter would not fire the
`ResizeObserver` that drives everything.

`stage.js` is also the app's **single layout bus**. `onStageChanged` (camera) fires before
`onLayoutChanged` (panel capacity); it coalesces on a double `requestAnimationFrame`, because iOS
reports a stale `innerWidth/innerHeight` for one frame after a rotation. It replaces the three
private 150 ms debounces `roomcards.js`/`cameras.js` used to keep, and it listens to `visualViewport`
too — the only signal when Safari's URL bar collapses or the keyboard opens. Each rail additionally
has its own `ResizeObserver`: a `display:none` rail measures 0 so `computeCapacity()` bails, and a
`window.resize` that fired while it was hidden is never repeated — which is exactly why rotating
during room focus or edit mode used to leave a capacity computed for the old orientation.

`scene.js applyStage` re-centres the **frustum** on the stage with `camera.setViewOffset`, treating
the canvas as a window onto a larger virtual frame. `camera.fov`/`camera.aspect` therefore describe
that **virtual** frame, not the visible one — so nothing may read them to compute a fit. Everything
routes through `fitDistance(radius, pad)` instead (`focus.js` ×2, `floorview.js`); reading fov
directly yields a larger fit, a shorter distance, and a cropped subject. `snapshots.js` is exempt and
must stay so: `snapCam` is a separate camera that never gets the offset. Two consequences worth
knowing: `controls.panSpeed = H/fullH` cancels the fov inflation for OrbitControls' pan, and picking
needs no change *only because* the canvas is `inset:0` (`Raycaster.setFromCamera` unprojects through
`projectionMatrixInverse`, which includes the offset).

The whole-house shot (`scene.js frameAll`, which the Home button also re-runs) is **solved, not
estimated**. A bounding sphere is badly wrong for a house, and because perspective is not affine,
aiming at a box's 3D centre does not centre its silhouette. `solveHousePose` bisects the distance
around an inner `aimFor(dist)` loop that slides the aim point until the projected outline sits on the
stage centre — alternating a full rescale with a full recentre in one loop *oscillates* (measured:
111 → 80 → 92 → 78 ft, never settling), which is why it is two nested solves and not one. It frames
`getBuildingBox()` (the shell's mass) when a shell is loaded, because House mode hides every room
mesh and the shell is all you see. `Vector3.project()` reads `matrixWorldInverse`, which only
`renderer.render()` refreshes — the solve must invert it by hand each pass.

**The one content rail** (`frontend/js/siderail.js`): rooms and cameras used to be two 380px columns
flanking the house, covering 64% of an iPad Air's width with 19 photo tiles at equal weight. They now
share one glass rail and only one grid shows at a time. `cameras.js` and `roomcards.js` are otherwise
unchanged and still own `#left-dash`/`#room-cards`. Visibility is a `data-panel` attribute on
`#sr-body`, not `.hidden` on the grids, because `cameras.js` already writes a `no-cams` class on the
rail for "HA has no cameras" and two writers of `.hidden` would fight; CSS resolves both. In portrait
the same rail lies down as a bottom filmstrip (`--rail-h`, `auto-fill` columns) — a side rail there
leaves the house a 480px stage and pushes the framing to ~209 ft. Room-card brightness is the rail's
hierarchy: `.lit` (lights on) keeps the photo at full brightness, everything else recedes.
**Rail order is earned**: every card tap and card light-toggle scores that room a point in a
localStorage table (`roomUse:v1`) whose scores halve every 14 days, and the rail sorts by that —
so the rooms this house actually uses hold the top slots and the rest fall past the "All rooms"
button. Ties and never-used rooms keep the natural floor order, so a fresh install looks exactly
as it did before. Two things are deliberate: the re-rank is applied only while the rail is
off-screen (otherwise a tap would slide the grid out from under the finger that made it, and a
toggle would move its own card mid-gesture), and it is triggered by `onFocusChanged`, not by the
`ResizeObserver` on `#room-cards` — Chrome reports *nothing* for an element with no box, so that
observer never fires on a `display:none` transition (measured). The all-rooms overlay stays
grouped by floor: that view exists to find the room you rarely open.

**Dynamic lighting** follows Home Assistant's sun and weather — frontend-only, no backend changes.
`frontend/js/daylight.js` reads `sun.sun` (`elevation`/`azimuth`) and the first `weather.*` entity
(via `state.js findEntities`), maps elevation through a keyframe ramp (night/dusk/golden/day) and
the weather condition through a dim/desaturate table, and eases `scene.js`'s exported
`sunLight`/`hemiLight` plus background+fog color toward the target each frame (~1s settle;
`onFrame(fn)` tick registry in scene.js — fog near must stay > controls.maxDistance 300; HA azimuth
0=N maps to scene north = −Z). Renderer uses ACESFilmic tone mapping; shadows stay off (translucent
walls). Topbar `☀ auto` button cycles auto/day/night (persisted in `localStorage['3dha.lightMode']`);
`window.__daylight.simulate({elevation, azimuth, condition})` fakes states for testing,
`simulate(null)` reverts. `frontend/js/roomlights.js` turns HA lights into scene light, from **three sources feeding one pool**:

- **Fixtures** — an `objects` row carrying an `entity_id` (see the root `CLAUDE.md`). The lamp's own
  GLB materials glow (`state.js paintModelState`, factored out of `applyStyle` — a fixture must
  *not* go through `applyStyle`, which also rescales and would pop the lamp 1.25× when it turns on),
  and a pool light sits at the fixture.
- **Exteriors** — a `light.*` **placement** (a device marker, not an object) in a room whose name
  matches `house.js OUTDOOR_RE`. The porch sconces and garage floodlights hang on the shell GLB, so
  there is no lamp furniture to bind them to, and House mode hides the yard's room mesh along with
  every other room — which left the two sources below unable to light the exterior *at all* in the
  only view the exterior is ever seen from. The marker the user dragged onto the facade is where
  that light really hangs, so the placement is the source (`EXTERIOR_BASE` 70, range 34 ft). Two
  things do not carry over from fixtures: it is **outdoor rooms only** (a point light is occluded by
  nothing, so an indoor placement promoted the same way would shine straight out through the shell
  onto the lawn), and it is **not** gated on its marker being visible — markers are edit-only chrome
  that House mode hides outright, so `exteriorLive` gates on the *room* instead (user-hidden, or
  scoped out by a focus on some other room). Like a fixture, a lit exterior suppresses its room's
  centre fallback.
- **Rooms** — the old whole-room fallback, for any room with no *visible* bound fixture. The room
  record is kept for **every** room regardless: `getRoomLightIds`/`getRoomsForEntity`/
  `getAllHouseLightIds` are what `roomcards.js` counts and toggles off and what `dashboard.js`
  scopes its tile to, so a fixture must never become a second `rooms[]` entry — `Array.find` would
  return a 1-light set for a 5-light room and "all off" would turn one light off. Fixtures live in
  their own array, and `getAllHouseLightIds` stays `light.*`-only because a fixture may be bound to
  a `switch.*` (`roomcards.js toggleRoomLights` hardcodes `domain: 'light'`).

Four things are load-bearing and not guessable:

- **The pool is fixed-size and its lights are never added, removed *or hidden*.** `lights.point.length`
  is baked into three's program cache key, so changing it — `light.visible = false` included —
  recompiles every `MeshStandardMaterial`. Intensity 0 is free. The size is chosen **once**, in
  `initRoomLights`, which `main.js` calls before `renderer.compileAsync`, so the one real compile
  stays behind the boot curtain: 12 desktop / 8 coarse-pointer, capped by `MAX_FRAGMENT_UNIFORM_VECTORS`.
  Never `castShadow` a pool light either — that is a second cache-key term.
- **Intensities are candela under r160's physically-correct falloff** (`useLegacyLights` is gone),
  with decay 2 and the world unit = 1 **foot**, so illuminance is `intensity / d²` — a 25× divisor
  at 5 ft. The old `POOL_INTENSITY = 2.2` put ~0.06 on a surface, which is why lights read as doing
  nothing at all; `FIXTURE_BASE` is 45 and `CENTRE_BASE` 90. Colour must go through
  `setRGB(..., THREE.SRGBColorSpace)`: `Color.setRGB` defaults to the **linear** working space
  (only `setHex` defaults to sRGB), and HA's `rgb_color` bytes are sRGB.
- **Spill is no longer night-gated to zero** — `DAY_FLOOR + (1 - DAY_FLOOR) * getNightFactor()`, so
  a light that is on reads as on at noon. Consequences: `settleRoomLights()` exists and is called
  beside `settleDaylight()` (or the curtain lifts onto a dozen lamps ramping up), `snapshots.js`
  brackets its capture with `suspendRoomLights()` (cards are keyed by *geometry* and persisted, so a
  card shot while a lamp was on would bake it in forever — and the restore must be intensity-only,
  see the pool rule above), and the single-floor dollhouse view scales spill by `FLOORVIEW_SPILL`
  but **room focus does not**, being the one view close enough to want a lamp to read properly.
- **A fixture's world position is computed, not read.** `getWorldPosition` is wrong here twice over:
  frame callbacks run before `renderer.render` refreshes `matrixWorld`, and at `setRoomLightsData`
  time it is still the identity. `houseRoot` is untransformed and a floor group carries only a Y
  offset, so `floorBaseY.get(level) + root.position.y` is exact and synchronous — which is also what
  makes the light follow a gizmo drag for free. Emission follows the *mesh* (`isShown` ancestor
  walk, so House mode / focus / level all count) but deliberately **not** `wallFade`: the cutaway
  binds any piece within 2 ft of a wall above 1.2 ft, which catches a table lamp, and dimming the
  room's light because a wall dissolved defeats what the dissolve is for.

`setRoomLightsData({house, structure})` must be re-called after every house rebuild
(`main.js reloadHouse`) because slabs and object roots get fresh materials.

**The transform gizmo** (`frontend/js/drag.js`) is three's `TransformControls`. In r160 it *is* an
`Object3D` — `scene.add(tc)`, there is no `getHelper()`. Four non-obvious things:
`applyStage` inflates `camera.fov` to describe the virtual frame and TransformControls sizes its
handles straight off `camera.fov`, so `tc.size` is corrected by `getStageFovScale()` (the same
`H/fullH` that `controls.panSpeed` already cancels) — picking needs no correction, since
`setFromCamera` unprojects through `projectionMatrixInverse`. The capture-phase `pointerdown`
pre-disable is kept from the old plane-drag: `dragging-changed` alone lets OrbitControls fire its
`start` event first, which `scene.js` reads as "the user took the camera" and which would kill
`refitStage` forever. `main.js`'s pointerup click handler runs *before* the gizmo's, so it guards on
`isTransforming()` — otherwise a ≤5 px nudge on an arrow reads as a click on the room behind it.
And the readback is normalised in `objectChange`: scale mode writes axes independently and goes
negative past the pivot, while **rotation must be read off the quaternion, never `rotation.y`** —
XYZ Euler decomposition expresses a 180° yaw as `(π, 0, π)`, so `rotation.y` reads exactly 0 and
every half-turn-or-more was silently thrown away on save.

**Outdoor environment & weather** (frontend-only): `frontend/js/environment.js` builds the yard —
a grass disc reaching past fog-far, merged low-poly trees/bushes (two draw calls, vertex-colored
foliage, seeded RNG so the yard never reshuffles) laid out to mirror the real property's satellite
view (dense west treeline, treeline across the back, open east lawn, shrubs flanking the driveway
entrance), plus a fake-AO contact shadow. Plants anchor to the house-shell GLB's **measured**
footprint when one is loaded — re-measured on `levelChanged` since the shell loads async, with flat
hardscape meshes (<3 ft tall, e.g. the driveway) excluded from the bounds — and never grow on a
room rect (`onPad`). `setEnvironmentData(house)` re-runs on every `reloadHouse`, and re-measures the
shell a few times over the first half second before trusting it (`settleShellAnchors` — the rect the
boot build sees is not the rect a frame later, and the whole yard hangs off it; see "Editing the
outside" in the root CLAUDE.md). The yard also carries per-piece identity so the **Outside editor**
(`yard.js`) can move, scale, erase and duplicate individual trees, beds, slabs and props — the
generated yard is never stored, only the deltas against it, and it is drawn per-item only while that
editor is open. Read the "EDITABLE YARD" banner comment in `environment.js` before touching any
`add*` factory: the item boundaries are the factory calls themselves, so adding, renaming or
reordering one moves the keys that every saved edit is filed under.
`frontend/js/weather.js` renders the HA weather condition: rain streaks (LineSegments) + snow
(Points) from fixed max-size pools throttled with `setDrawRange`, ~9 drifting cloud meshes,
lightning as `renderer.toneMappingExposure` flashes (never add/remove lights — shader recompile),
and eased wet/whitened lawn tinting via `setGroundWet/Snow`. It follows daylight.js's resolved
sun+weather through `onDaylightChanged`, so the mode button and `__daylight.simulate({condition})`
drive it too; `window.__weather.step(secs)` advances the easing manually for testing (rAF pauses in
hidden tabs, so nothing eases while the tab is backgrounded). Both hide in edit mode
(`appModeChanged`), where the grid/dark ground shows instead, and in single-floor view (below) — the
one exception being the yard while the Outside editor is open, since that is what is being edited.

**The dollhouse cutaway** (`frontend/js/cutaway.js`): the walls between you and a room fade out, so
every room reads like a Sims-4 build-mode shot — two far walls, no near walls, no ceiling. This used
to be free: walls were zero-thickness `ShapeGeometry` fins wound with inward normals and drawn
`side: THREE.FrontSide`, so the GPU backface-culled whichever ones the camera stood behind. That
popped at exactly 90 degrees, and it only ever hid the wall *surface* — the art and windows mounted
on it are separate GLB objects and were left hanging in mid-air.

Walls now have a body (`house.js WALL_THICKNESS`, 0.35 ft, extruded **outward** so the inner face
stays on the old plane — every one of the hand-placed furniture pieces is flush against it, and an
inward extrusion would embed them). Each polygon edge is its own child `Mesh` of the room mesh with
its own **cloned** material and `userData { part:'wall', edgeIndex, nx, nz (inward normal), fade,
hx, hz }`; the room mesh itself now carries empty geometry and is just the identity + parent
(`roomMeshes`, picking, `userData.kind`). Each wall's shape runs from `u = -t` to `len + t` so
neighbours overlap in a `t x t` block at every corner instead of leaving a notch. Each wall also
carries its own `part:'plinth'` skirt and `part:'edges'` accent rim as children, so both fade with
it — a room-wide version of either left a colored kerb and a bright outline tracing walls that had
dissolved. The skirt is a bare quad on the wall's **outer** face, not a solid: the outer face is the
only part of a kerb you can ever see, and a solid's end cap points along its wall, so at a corner
whose neighbour had faded it jutted into the open side as a colored nub. One `part:'plinthCap'`
(the polygon at `-PLINTH_DEPTH`, **BackSide**) closes the underside; BackSide is load-bearing —
faced up, its projection slides out past the slab's along the near edges and repaints the kerb.

One `onFrame` tick scores every wall by `dot(inward normal, horizontal direction to the camera)` and
eases opacity across a **wide** band (`FADE_LO 0.02 .. FADE_HI 0.55` — these are cosines, so that is
~33 degrees of orbit; the first attempt at 0.05..0.30 spanned barely 15 and still read as the pop it
replaced). The score is horizontal-only: folding in camera height would fade every wall at once from
overhead. `house.js applyWallOpacity` is the single writer, multiplying `userData.fade` by the room's
`baseOpacity` so focus-mode ghosting composes; `setRoomOpacity`/`setRoomEmissive`/`paintRoomEmissive`
fan out over the wall children (`paintRoomEmissive` deliberately does *not* touch `baseEmissive` —
hover needs to add a boost and put the stored level back).

It runs in **every** view that draws rooms, not just room focus: a solid wall does not backface-cull,
so a focus-only fade would turn the single-floor view into a row of sealed boxes.

Things mounted on a wall go with it. Door/window hinges carry `edgeIndex`. Furniture binds whole-object
when it is within 2 ft of a wall **and** its anchor is above 1.2 ft — the height gate is what keeps a
sofa pushed against a wall in place while the art above it leaves. **Architecture** (`WALL_ARCH_RE`:
wall/wainscot/baseboard/crown/moulding/trim, plus the openings through it — window, door, opening,
casing, jamb, lining, slider, panel; every noun takes an optional plural, since the pieces that
exposed this were named "Dining Openings"/"Dining Windows"/"Rios Closet Doors") takes a different
route from furniture in two ways that are the whole point of the split list: it **skips the 1.2 ft
height gate** (a door lining or a garage door starts at the floor and still has to leave with its
wall) and it is measured **by geometry, not by its anchor** ("Dining Windows" is five units on four
walls in one model, anchored near none of them). `floor` is deliberately absent — a floor plane in a
narrow room measures within `SURFACE_MAX_DIST` of every wall and would be shredded across all of
them. Not objects.js's `SURFACE_RE`, which is about pickability and also matches "Ceiling Fan".
Architecture is one GLB per room and binds **per wall**: by sub-mesh
where the GLB happens to have one per wall, and otherwise by `splitMerged`, which sorts the merged
run's triangles by nearest wall and rebuilds it as one child mesh per wall (buckets share the source
attribute buffers, differ only in their index, and each needs its **own** material clone, since
`fadeSubtree` tracks the transparent flag per material). That split is what the whole thing turns
on: `glb.py` groups primitives **by material, never by wall**, so a `for w in "nswe"` trim run lands
in a single primitive whose bbox centre is mid-room — it bound to nothing and kept full opacity
forever, leaving skirting, wainscot, casings and door leaves standing in the gap. Fixing it here and
not in the GLBs means every already-uploaded room is covered with no rebuild. The bind is lazy (GLBs
resolve late) and must `root.updateWorldMatrix(true, true)` first, because `Box3.setFromObject`
refreshes only the object's own matrix and a stale parent chain makes every panel measure to the
room origin; collect the sub-meshes before splitting, or `traverse` walks into the buckets it just
made. Ceilings (`CEILING_RE`, name *ending* in "Ceiling") always fade to 0 — crown authored inside
a `* Ceiling` piece therefore goes with it even on walls still shown.
Anything faded gets `transparent: true` set once (flipping that flag is what recompiles a shader).
`objects.js` stays the single writer of object *visibility*; the fade goes through its `wallFade` map.
`window.__cutaway` exposes `settle()` (jump every fade to its target — roomkit's `shot.py` and
`dollhouse.py` call it before grabbing the canvas), `setEnabled(b)` and `debug()`. Snapshot cards
render from their own camera, so `snapshots.js` brackets its render with `scoreForCamera(snapCam)`.
Room focus also hides stairs, which live on the house root and would otherwise hang in the backdrop.

**Single-floor presentation mode** (`frontend/js/floorview.js`): picking a floor in the level
selector shouldn't leave one slab hovering over the lawn, so on `levelChanged` to a floor it swaps
the sky for a dark studio-gradient backdrop (a radial CanvasTexture as `scene.background`, fog
nulled — daylight.js guards its background/fog writes behind `scene.background.isColor`/`scene.fog`
and exposes `repaintSky()` for the restore, since its tick early-returns once converged), flies the
camera to a centered ~50°-elevation dollhouse shot of that floor's rooms (keeps the current
azimuth), locks zoom-out just past that framing shot (`scene.js setMaxZoom` retunes the live
`MAX_ZOOM` cap), and disables pan so the floor stays centered; environment.js and weather.js hide
their roots on the same event. Selecting House ('all') restores the daylight sky, the house zoom
cap, and the pose you left from (focus-mode exits then override with their own saved pose — both
were captured at the same moment). Same-level re-fires (rebuilds) only re-center the orbit target
— buildHouse's `focusOn` points it at the whole-house center otherwise — without moving the camera.

**App shell, not web page** — the things that make this read as an installed app rather than a
site in a tab, and the rules that keep it that way:

- **Never call `window.alert` / `confirm` / `prompt`.** They are the browser's dialogs, styled by the
  OS and titled with the origin ("127.0.0.1:5000 says"), the loudest web-page tell there is.
  `js/dialog.js` `showAlert(msg, {title})` / `showConfirm(msg, {title, okLabel, danger})` are the
  replacements: one `<dialog>` in the top layer (so no z-index against the planner at 60 or the
  model library at 70), awaited where the natives were (`if (!await showConfirm(...)) return;`),
  queued so a loop of failures shows them in turn. Esc, the backdrop and Cancel resolve `false`; a
  `danger` confirm focuses Cancel. The global `* { margin: 0 }` reset kills the UA's `margin: auto`,
  which is the whole of how a modal dialog centres — `#app-dialog` restates it.
- **Chrome slides, it doesn't pop.** `.hidden` is still `display:none`, but `style.css` "Motion"
  rides `transition-behavior: allow-discrete` + `@starting-style` so display flips only when the
  fade ends and an element returning from `none` starts from its exit pose. Opacity/transform only,
  so nothing that measures layout (`roomcards.js`/`cameras.js` capacity, the stage tokens) sees any
  difference; `pointer-events:none` on the way out so a fading panel can't eat the tap that
  dismissed it; every resting state is `transform:none`. `#banner`/`#gizmo-bar`/`#focus-exit` carry
  a centring translate and restate it in their exit pose, same rule as their `:active`. On browsers
  without `allow-discrete` the block is inert and everything pops as before — it is never
  load-bearing. One consequence for tests: `dash.offsetWidth` / `getComputedStyle(el).display` read
  "shown" for ~260 ms after the class flips, and the Browser pane throttles transitions while it is
  hidden, so a check right after a toggle can catch the in-flight state.
- **Nothing in the chrome is prose.** `body` is `user-select:none; cursor:default`; fields, the
  device panel's `#dp-entity`/`.attrs` readouts and the dialog message opt back in. Images are
  `-webkit-user-drag:none`, scrollbars are thin/translucent (`scrollbar-*` inherits from `html`),
  `js/appshell.js` suppresses the context menu outside fields and image `dragstart`, ticks
  `navigator.vibrate` under touch taps (Android only), and holds a **screen wake lock in view mode
  only** — re-requested on every `visibilitychange`, dropped on `appModeChanged` to edit, silent if
  unsupported or refused.
- **Installable**: `manifest.webmanifest` + `icons/` (PNG sizes rendered by the same geometry as
  `icon.svg`; the maskable one is full-bleed with the glyph in the 80% safe zone, and the
  apple-touch-icon is square because iOS rounds it itself) + the standalone/theme-color metas in
  `index.html`. `app.py` registers the `.webmanifest` MIME type, since Windows has no registry entry
  for it and an `octet-stream` manifest is silently ignored. **Deliberately no service worker**:
  js/css are edited live against this server, and a cached module is a change that silently
  doesn't apply.
