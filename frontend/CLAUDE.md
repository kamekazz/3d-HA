# Frontend (`frontend/js/`)

Native ES modules, Three.js via CDN importmap — no npm, no bundler, no build step. What each module
does is readable from the files themselves; below is the part the code can't tell you.

`house.js` loads the whole-house shell GLB; when that fetch/parse fails it dispatches
`shellLoadFailed` and `ui.js` raises a persistent banner — a silently missing house reads as a
render bug rather than the deploy problem it usually is (see `docs/TROUBLESHOOTING-house-shell.md`).

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

**Dynamic lighting** follows Home Assistant's sun and weather — frontend-only, no backend changes.
`frontend/js/daylight.js` reads `sun.sun` (`elevation`/`azimuth`) and the first `weather.*` entity
(via `state.js findEntities`), maps elevation through a keyframe ramp (night/dusk/golden/day) and
the weather condition through a dim/desaturate table, and eases `scene.js`'s exported
`sunLight`/`hemiLight` plus background+fog color toward the target each frame (~1s settle;
`onFrame(fn)` tick registry in scene.js — fog near must stay > controls.maxDistance 300; HA azimuth
0=N maps to scene north = −Z). Renderer uses ACESFilmic tone mapping; shadows stay off (translucent
walls). Topbar `☀ auto` button cycles auto/day/night (persisted in `localStorage['3dha.lightMode']`);
`window.__daylight.simulate({elevation, azimuth, condition})` fakes states for testing,
`simulate(null)` reverts. `frontend/js/roomlights.js` makes rooms glow at night when their HA
`light.*` entities are on (placed devices ∪ the linked HA area's lights): slab emissive tint per lit
room, plus a **fixed pool of 6 PointLights** (never added/removed — changing the scene's light count
recompiles every MeshStandard shader; only intensities animate, scaled by `getNightFactor()`).
When >6 rooms are lit, the ones nearest `controls.target` on visible levels win.
`setRoomLightsData({house, structure})` must be re-called after every house rebuild
(`main.js reloadHouse`) because slabs get fresh materials.

**Outdoor environment & weather** (frontend-only): `frontend/js/environment.js` builds the yard —
a grass disc reaching past fog-far, merged low-poly trees/bushes (two draw calls, vertex-colored
foliage, seeded RNG so the yard never reshuffles) laid out to mirror the real property's satellite
view (dense west treeline, treeline across the back, open east lawn, shrubs flanking the driveway
entrance), plus a fake-AO contact shadow. Plants anchor to the house-shell GLB's **measured**
footprint when one is loaded — re-measured on `levelChanged` since the shell loads async, with flat
hardscape meshes (<3 ft tall, e.g. the driveway) excluded from the bounds — and never grow on a
room rect (`onPad`). `setEnvironmentData(house)` re-runs on every `reloadHouse`.
`frontend/js/weather.js` renders the HA weather condition: rain streaks (LineSegments) + snow
(Points) from fixed max-size pools throttled with `setDrawRange`, ~9 drifting cloud meshes,
lightning as `renderer.toneMappingExposure` flashes (never add/remove lights — shader recompile),
and eased wet/whitened lawn tinting via `setGroundWet/Snow`. It follows daylight.js's resolved
sun+weather through `onDaylightChanged`, so the mode button and `__daylight.simulate({condition})`
drive it too; `window.__weather.step(secs)` advances the easing manually for testing (rAF pauses in
hidden tabs, so nothing eases while the tab is backgrounded). Both hide in edit mode
(`appModeChanged`), where the grid/dark ground shows instead, and in single-floor view (below).

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
