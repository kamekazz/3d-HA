# Round 2 blind verdicts — 4 critics, 4 FAILs, all "obvious"

Each critic saw one blind side-by-side, labels stripped, order shuffled, and was told not to
read anything else. All four correctly identified the photograph. None found it hard.

## The five themes they converged on, in priority order

**1. No texture anywhere — every material is flat tinted plastic.** Named by all four.
The floor is one uniform value from camera to far wall: no grain, no per-plank tonal
variation, no specular sheen picking up the ceiling fixtures. The walls are poster-flat
colour fields per plane. The photo's floor sheen running down the hall is most of what
makes the hall read as long, and we have none of it.

**2. Nothing touches the ground.** Named by three. No contact shadow or AO under the
runner (it floats as a pale decal), the plant stands, the door bottoms, or in the door
panel rebates — one critic noted the corner where a bevel meets the panel field is exactly
as bright as the open door face, "physically impossible".

**3. Repeat artefacts read as tiling.** The hall runner shows identical hard-edged blocks
marching down its length with crisp 90° corners; the stair runner shows the same as
rectangular blocks across the lower treads; the floor's butt-lines read as UV seams.

**4. No light falloff.** Walls are near-uniform top to bottom. The stairwell has no bright
pool at the bottom from the front door and no gradient up the walls. Light pools under the
ceiling cans are perfect circular gradients on a matte plane.

**5. Every white is the same white.** Door face, casing and skirting share two values total.
In the photo the door face blows out near the light and drops to warm mid-grey in the
reveal, and the skirting reads brighter than the door above it.

## Specific geometry called out

- **Stair runner does not wrap.** It is a lighter quad painted on the tread tops, stopping
  dead at each nosing. It must wrap over the nosing and down each riser as a continuous
  band, inset ~4-5 in from each side, with thickness and a small radius at the nosing.
- **Handrail assembly.** The black rail is a chunky faceted low-poly bar, floating without
  brackets where the photo has two clearly bracketed mounts; the balusters terminate in
  air with no cap, no base and no connection to the string.
- **Door panel bevels are flat chamfers.** Each sloped face is a single constant fill, so
  the panel reads as a paper cut-out pyramid. Real raised panels have a COVE — a curved
  sweep whose tone ramps continuously from field to shoulder, with a specular smear on the
  top bevel and a soft shadow on the bottom.
- **Ceiling dome is enormous** — roughly two feet across at that distance.
- **Snake plants** are three fat rubbery blades instead of a dense fan.
- **Wall sculpture** rods hover unattached with no cast shadow and no backing raft.
- **Doors** show no leaf-to-frame reveal shadow; the handle is a floating stub with no rose.
- **Bottom of the stairwell** is a backdrop, not a room.

## What is NOT fixable in this engine, and must not be chased

`roomkit.glb` has **no image-texture API** — "tiled texture" in this repo means per-cell or
vertex tone authored in geometry. So "add a scanned albedo + normal map" cannot be done for
a GLB piece. The app renders **no shadow maps for generated geometry** (only the house
shell casts sun shadows), so true cast shadows and AO are not available either — which is
exactly why `STYLE-BAR.md` requires a baked contact-shadow decal under every piece instead.

Do not read these as excuses. The available levers are: material roughness/metalness for
sheen, vertex/cell tone for grain and gradients, baked contact-shadow decals, baked light
falloff in the wall skins, differentiated albedo per trim element, and better geometry.
Every one of the five themes above can be pushed a long way with those.
