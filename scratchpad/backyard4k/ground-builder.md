# Rear ground first build

Owned source: `addRearGroundDetail` appended at end of `frontend/js/environment.js`. Parent integrated its call. Independent seed 0x47524f55. Custom 512px procedural six-foot grass blade tile, nonrepeating spatial wear, subtle mower direction, curled lobed fallen-leaf geometry concentrated at shore. No photo texture, lighting change, global grass change, or database edit.

Read roomkit skill, RESUME, ROOM-BRIEF, STYLE-BAR and frontend contracts. Viewed actual references 09,12,13 and filename descriptions. Inspected baseline lake render plus lake-build3 photo12. Actual scene shadows are enabled, PCFSoft; stale documentation about shadows was not followed.

First actual capture: `renders/ground-build1/photo09.png` and `photo12.png`, native 3840x2880. Both load 293/293 objects and report zero page errors. Exact front geometry checksum unchanged: 482260 triangles / xor166137678 / sum3351587226. Inspected both downscaled previews: rear turf is green and finer than former grey grain; real fallen leaves are visible. Still visibly a rendered field; needs critic and microstructure judgement. First selfcheck found occasional old shoreline apron triangles showing through eased slope; changed turf shore height to the same straight ramp as the lake apron. This tiny fix awaits next integrated screenshot.

Prepared neutral blind pair `ground-critic-r1/pair.png` for fresh critic, based on first native photo12 shot versus actual reference12 downsampled only to photograph size. Builder did not inspect random key. No independent verdict yet. Parent's later larger-lawn request moves yardN north by20ft through rear-only copied landmarks; helper formulas automatically follow it, no separate offset required.

## Lower grade dependency

Current default lowGrade=false conforms old procedural raised lawn. Helper accepts `{lowGrade:true}` to lower all rear turf to L.lo=.19ft; surface is ~.217ft with ±.018ft variation. North four stairs x10.3..14.9 z-42..-46 can land at .19. Actual downward shell raycast already gives .164 here, so old procedural raised lawn is primary obstruction at these stairs.

Before lowGrade=true, remove only rear-specific four g calls and three bank quads in addGroundCover. Preserve its base sheet and all front/side calls. The east kerb rear-only quad at end also represents raised grade and needs removal if east rear lowers. Existing rear beds anchored L.hi may float and need their owner to re-seat.

Actual live shell inspection is in `ground-probe.cjs` and `ground-probe.json`. Imported raised pad is Root_Node, PaletteMaterial001, y2.1338; base is y.164. Top triangles at index offsets k84210,84213,84216,84219 span front/interior and MUST NOT be deleted whole. Spatially clip only their rear exterior portions beyond z=-24.5107 for x<20.5973, and beyond z=-10.9445 for x>=20.5973. Full rear top triangles k84255,84258 span x20.5973..47.3597 z-29.4951..-10.8983; preserve the narrow south boundary (z>-10.9445) to avoid wall sill. Associated west vertical pad faces k84204,84207 cross the house side and need same spatial clipping; north face k84252 at z-51.0327 can clip wholly if identified as pad; east face k84261 and north-east face200775 bound raised rear east pad. Actual triangle coordinates in probe support exact validation before mutation. Never clip other low-y wall details based on height alone. Ground builder did not modify shell.

## Lifecycle

Turf material is registered with yardGrassMats; its per-mesh onBeforeRender composes current wetF and snowF from rear-specific base so global front colour is never used as rear base. Geometry/material are yard-owned and disposed on rebuild; material dispose listener releases own canvas texture. No onFrame registration or model-cache geometry. Turf is fixed unpickable terrain like the base surface; fallen leaves are fixed attached ground detail.


## Second build: low grade and exact imported-pad surgery

Implemented `lowerRearShellPad`: 13 validated source triangle signatures on Root_Node / PaletteMaterial001, then clips the rear exterior portions at x20.5973 and z-24.5107 / -10.9445. All retained attributes interpolate; original attribute values and noncandidate triangle indices remain unchanged. Works on a clone owned by this live shell, never modifies/disposes source cache geometry. Idempotent per shell; old owned clone disposed when replaced by a new shell instance. Changed source signatures fail closed.

Removed four rear-only lawn slabs, three rear banks and the rear east bank in addGroundCover; original shared base sheet, front and side calls retained. Rear detail uses lowGrade:true; parent copied rearSite still adds 20 feet lawn depth. Planting builder notified to seat rear vegetation at L.lo.

`maskRearSourceTread` finds the exact Backyard Deck object through objects3d; deferred model retries are bounded and cancelled on yard/shell replacement. Only triangles wholly within x7.89..12.71, z-43.51..-42.24, y1.79..2.41 are removed from cloned instance geometry. Verified 12 triangles from mesh_0, 2 from mesh_0_1. Original geometry is restored before disposing old owned clones at a yard rebuild.

Ground outer boundary now fades through vertex RGBA across 4.5 ft at east/west/south boundaries; depthWrite false. It still reads as a greener rectangular plot in aerial view because existing global grass is grey; no global colour changed.

Real selfshots: ground-lowered1/photo09 (earlier narrow camera), ground-lowered2/rear_site (expanded spacious lawn, after alpha), ground-lowered3/photo09 (full-house 80-degree camera). All native4K, all293 objects loaded, zero page errors, exact frontgeometry checksum unchanged. Ground-lowered3 exposed pale old pad stairs below the previous high turf. Pixel-ray audit ground-artifact-probe.json identified Root_Node faces; measured their actual positions in ground-legacy-steps.json. `clearMeasuredRearPadRemnants` removes only24 exact triangle signatures for the obsolete north stair hollow faces and east return strip; two unrelated residual fence triangles intentionally retained. Final capture ground-lowered4/photo09 verifies this cleanup.

Actual low-grade ray grid (ground-lowered-verify.json) x5..25,z-55..-25 now has no high rear pad hits. 13 pad candidates became retained clipped portions, source68144/result68154 before24remnant removal; final expected68130. `ground-source-audit.json` confirms full addFrontYard, makeGrassTexture, repaintGrass and GRASS_BASE unchanged against HEAD. No builder edits to global scene/daylight/weather/textures files.


## Grass round 2 after independent critic FAIL

Fresh critic identified flat carpet instead of upright mown grass. Added camera-independent physical sward entirely inside addRearGroundDetail: 120,000 instanced four-blade tufts, each blade tapered and bent, blade heights before per-instance scaling .09-.156ft, narrow .008-.012ft full widths. Variable yaw, lean, dimensions, patch-level pigment and density at the outer fade; 2,400 instances of three-leaf low clover appear in nonrepeating patches. Excludes current upper/lower deck geometry, north stair landing, eastern lounge stair and gravel return beds. Ground material patch contrast increased locally; all shared grass constants/textures unchanged.

First selfshot ground-tufts1 showed excessively broad sparse sprouts. Narrowed blades, raised density and softened dark root pigment. Self-inspected ground-tufts2/photo12 preview: finer upright structure visible throughout foreground, no longer coarse broad sprouts. It remains recognizably rendered, so no photo-match claim. Final close/wide captures in ground-sward-r2 use workflow camera poses and parent instance-aware audit.

Cost: two extra draws, 1,490,400 triangles instanced over the full rear lawn. Actual close capture reports 12draws and2,135,077 rendered triangles total. Instance matrix/color GPU data roughly9.3MB; no external models/textures/assets downloaded. Both geometries/materials are yard-owned; material dispose events also dispose InstancedMesh buffers so yard rebuilds release their instance resources.

Actual world-bounds/weather verification ground-sward-verify.json: grass maximumZ=-11.6044, clover maximumZ=-11.9916, both whollyrear. Existing wet input darkens both material bases by.7; snow converges both to existing GRASS_SNOW. No global weather/rendering change. The old workflow frontchecksum incorrectly counted16 local tuft/clover triangles at localZ>=0; parent corrected capture to account for instance matrices, with whollyrear world-bounds early rejection. Earlier ground-tufts1/2 rawchecksums are therefore invalid as front audits; use final ground-sward-r2 instance-aware results.
