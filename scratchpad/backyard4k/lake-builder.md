# Lake edge builder — first build, awaiting fresh critic

Scope: north/rear lake edge and its horizon only, implemented by `addRearLakeDetail` in `frontend/js/environment.js`. The parent integrates the call and suppresses conflicting old rear content. No front helper, global lighting/weather/stage setting, database, shell, or interior was edited by this builder.

Read: `.claude/skills/roomkit/SKILL.md`, `tools/roomkit/RESUME.md`, `ROOM-BRIEF.md`, `STYLE-BAR.md`, and the frontend lighting/weather/stage plus editable-yard contracts. Actual `scene.js` is authoritative: shadows are on, PCFSoft, and retained.

## Photo evidence and orientation

Personally inspected actual converted references 05, 06, 11, 12 and 13 with their filename camera notes. North is -Z. The water is visible through spaced mature broadleaf trunks under a connected overhead canopy. A curved grey gravel strip has two irregular pale cobble courses against the grass. The opposite bank is low with pale reeds, followed by mixed trees; it is not a row of houses.

The old app baseline was personally inspected at `renders/baseline/lake_center.png`: it showed only flat grey-green lawn, a level sky boundary and large faceted shrubs. There was no lake or mature trunk frame.

## Implementation

- `addRearLakeDetail(L, leaves, beds, props, lawns, trunks, masses)` uses private seed `0x4c414b45` and local scoped yard items. It does not advance the front RNG.
- Curved shoreline near `L.yardN`, grey gravel and paired cobble edge. A mesh apron slopes from the lawn to the raised gravel; earth slopes back down to the water.
- Nine individually branching mature trees. Folded, arbitrarily rotated leaf geometry occupies 3D crown volumes; there are no photo textures or camera-facing cards.
- Actual horizontal water mesh above the pre-existing submerged low lawn by 0.018 ft. Bank geometry rises above it. A MeshStandardMaterial keeps standard lights, with slight procedural ripple normals and Fresnel sky colour taken from the live `scene.background`. The lake does not yet provide scene-object reflections.
- Opposite-bank terrain, low reeds and volumetric woodland close the horizon from multiple viewpoints.
- Water geometry/material are owned by the normal yard teardown (`ownGeometry=true`). There is no retained frame callback, custom texture or render target. Water is a fixed environmental mesh; shoreline and trees use editable yard items.

## Integration

The parent has placed the helper call at the end of `addBackYard`. Suppress the old straight north bed and old rear sections 4/4b/5 (dense tree ranks, understory and north houses). The earlier large mounds near z=-50 remain a separate rear-planting dependency; they obstruct the baseline lake camera and do not resemble the supplied references.

## Verification

`node --check frontend/js/environment.js` passed. First attempted integrated capture `renders/lake-build1/photo11.png` was invalid because a parallel integration temporarily removed `addRearPorchDetail`; the console recorded that ReferenceError at `installItemScopes`. This is not a lake visual verdict. It must not be used as a final screenshot.

Exact intended reference-facing camera: position `[16,5.7,-57]`, target `[16,4,-110]`, fov 65, House level, cutaway false, no markers, sunny elevation 42 / azimuth 335, native 3840×2880. Capture uses `workflow_capture.cjs ... photo11 --pose-file workflow_matched_poses.json` and roomkit's actual setup.

## Final first-build self-inspection

Personally inspected `renders/lake-build3/photo11.png` and `renders/lake-build3/photo12-preview.jpg` (the second is a viewing reduction of the native `photo12.png`, not a generated image). Both native captures are 3840×2880. The first valid local capture exposed the crown being above the frame and faceted distant crown balls; the bounded correction lowered the crown skirt, increased individual leaf coverage, and replaced the far crown balls with volumetric folded-leaf geometry.

Both final captures loaded 293/293 models with zero JavaScript errors. Console resource failures were existing 502/503 camera/API requests, not shader or yard merge errors. The front geometry fingerprint remained **exactly identical** to baseline in both views: 482260 triangles, xor 166137678, sum 3351587226. Photo11 reports eight draw calls / 561399 visible triangles, with shadowMap enabled, type 2.

Second exact camera: photo12 position `[-2,5.7,-60]`, target `[26,4.2,-90]`, fov 68, same lighting and level. These poses are useful reproducible views, not a mathematically solved camera registration to the photographs.

The 3D water, curved shore and tree frame are now present across both viewpoints. Still visibly unfinished: trunks/branch forks are too mechanical, leaf silhouettes are angular, water has no object reflections, and the shoreline gravel is too even/bright. Photo12 also reveals old green low-poly shrubs stranded over the water toward the east; these are pre-existing rear planting which the next ground/planting builder must suppress or relocate. A large flat sky gap remains between the near canopy and opposite shore. These are honest self-observations, not an independent critic verdict.

This is a bounded first build. It has not received a fresh independent critic verdict and is not claimed to match the photographs.
