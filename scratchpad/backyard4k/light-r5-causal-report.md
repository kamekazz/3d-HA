# Rear LIGHT R5 — final causal diagnosis

**No production files changed. Exact scoped patch proposed in `light-r5-response-proposal.patch`.** The missing direct lawn term is explained by actual near-tree shadows at canonical335°/42°, not by grass self-shadowing or broken normals. The dominant indoor environment IBL masks those shadows. A geometry-selected195°/30° sun casts the house's real shadow over the photo09 foreground while leaving all sampled photo12 foreground points sunlit. Final ephemeral validation of the proposed four-material lighting response plus living-grass pigment correction brings both foreground mean RGBs within4.3levels/channel of their references. Source lifecycle/native verification and an independent critic remain for root.

The bounded runtime response `ground directional sun ×4, ground IBL ×0.02, hemisphere unchanged` recovers the two references' light/dark separation. A separately validated1.425linear blue-pigment factor on living grass resolves most of the resulting yellow cast. The facade remains too dark under the southern sun, and an upper-right lawn shadow is visible in photo12. Do not promote mean-color agreement as a final photorealism pass.

## What causes the canonical zero direct term

Corrected1200×900 photo12 component renders:

| Runtime condition | Foreground mean RGB |
|---|---|
| Canonical335/42 direct only |0.01 /0.01 /0.00 |
| Grass/clover/litter castShadow disabled |0.01 /0.01 /0.00 |
| Near oak leaves castShadow disabled |26.29 /28.82 /13.11 |
| Far oak leaves castShadow disabled |0.01 /0.01 /0.00 |
| Near/far oak leaves and bark castShadow disabled |45.77 /49.73 /24.41 |
| All receiveShadow disabled |45.97 /49.97 /24.53 |
| House shell castShadow disabled |0.01 /0.01 /0.00 |

Thus the near oak leaves and bark account for essentially all suppression. The actual blade normal Y components range0..0.9598 before the existing upward shading bias; the positive no-receive direct render proves the material responds to the sun.

At canonical335/42, three exact-camera turf points are approximately[-0.023,0.223,-87.812], [3.645,0.209,-83.855], [8.193,0.216,-80.722]. Sun rays launched0.35ft above them hit alpha-solid `rear-scanned-oak-leaves` at distances14.87,15.02,17.87ft and heights10.53,10.61,12.52ft. Near leaf bounds are[-43.45,0.647,-113.85]..[79.15,39.62,-77.56]. Far leaf bounds are[-246.55,-0.818,-435.22]..[282.89,43.75,-336.83]; they do not affect these lawn rays.

The first blocker probe's `renderer.shadowMap.enabled=false` was ineffective at invalidating the already compiled receiver shader programs; those rows are **inconclusive**, not evidence of broken normals. The corrected probe uses each mesh's actual `receiveShadow=false` uniform and restores it afterward. The first canonical ray batch also ran after camera drift and returned null; corrected rays reassert position, target, up, FOV and matrices immediately before sampling. Use the corrected evidence.

## Geometry establishes a sun that separates the two lawns

South180°/25° casts the house shadow across both foregrounds: all three photo12 rays hit `Root_Node` at y26.8..30.1ft. South180°/42° clears all photo12 rays but also clears two of three photo09 rays. Intermediate directions/elevations were then chosen from a ray scan before any candidate rendering.

Eight actual turf samples per photo cover two screen rows380/420 at x90/230/370/510 in600×450 coordinates. The central pair of columns is scored separately from the edges. The scan uses azimuths165/180/195/210 and elevations30/33/36. It respects actual loaded leaf alphaTest textures and all visible non-grass casters. Grass/litter are excluded after raising ray origins0.35ft; their independent render ablation above establishes that this exclusion does not hide the main problem.

| Sun | Photo09 central shaded | Photo09 all shaded | Photo12 clear |
|---|---:|---:|---:|
|195/30 |4/4 |8/8 |8/8 |
|195/33 |4/4 |7/8 |8/8 |
|195/36 |4/4 |6/8 |8/8 |
|180/36 |2/4 |4/8 |7/8 |
|180/30 |4/4 |6/8 |2/8 |
|180/33 |3/4 |5/8 |4/8 |
|210/30 |1/4 |3/8 |8/8 |
|165/30 |0/4 |1/8 |8/8 |

Selected195/30 shade points in photo09 span world x4.48..28.48, z−71.54..−64.10. All first blockers are actual house `Root_Node`, at facade/roof x−6.62..17.85, y24.26..28.71, z≈−24.45. Even the right-of-house-width sample[28.48,0.202,−64.10] is shadowed by the shifted ray reaching[17.85,24.26,−24.44]. Photo12 points span x−0.918..9.585,z−89.02..−79.93 and all have clear rays. No missing neighbor, invisible blocker, painted shadow or position-based darkening was added. Sparse samples do not prove that every lawn pixel is clear; the full diagnostic image retains a real shaded patch in photo12's upper-right lawn.

## Bounded ground-material response

Only after the geometry scan met the75% shade/clear gate did the probe change the four dedicated rear ground materials in its ephemeral page: turf, grass blades, clover and fallen leaves. It multiplied the actual shadowed directional-light color in the directional-light shader loop, leaving point/HA light terms alone. An onBeforeRender wrapper scaled those materials' current daylight-owned envMapIntensity. Hemisphere, all other materials, global light/weather/exposure state and source remained unchanged. No shadow or AO field was painted.

All means use the unchanged1200×900 camera rendered down to600×450, foreground ROI[60,365,540,450]. They are tone-mapped sRGB bytes and are not linearly additive.

|195/30 diagnostic | Photo09 foreground RGB | Photo12 foreground RGB |
|---|---|---|
|Reference |37.66 /48.45 /33.49 |124.27 /136.19 /103.89 |
|Normal material response |119.74 /136.98 /93.76 |146.80 /157.82 /115.53 |
|Direct only |0.16 /0.16 /0.08 |42.42 /44.74 /18.71 |
|Ground IBL0 |31.97 /47.10 /26.30 |65.68 /75.84 /42.37 |
|Ground IBL0, directional ×3 |32.16 /47.27 /26.43 |111.25 /118.40 /72.03 |
|Ground IBL0.02, directional ×4 |35.09 /50.42 /28.39 |128.24 /134.30 /85.65 |

The last diagnostic is close in red/green illumination levels and materially improves the sky-to-lawn contrast in photo09. It still misses photo12 blue by18.24 levels. Inspection confirms a warmer yellow lawn than the reference, and southern lighting leaves the rear facade darker than the reference. This is evidence for separately calibrating exterior direct and environment response, not permission to install the coefficients or modify another builder's grass albedo. A blanket all-indirect AO adjustment remains unsupported.

## Artifacts and validation

- `light-r5-blockers.cjs` / `renders/light-r5-blockers/probe.json`: independent caster ablations and initial low-sun rays; heed the two invalid diagnostic rows described above.
- `light-r5-blockers.cjs --corrected` / `renders/light-r5-blockers-corrected/probe.json`: actual receiveShadow control, corrected near-tree rays, south42 evidence.
- `light-r5-threshold.cjs` / `renders/light-r5-threshold/visibility.json`: complete192-ray scan, world points, first blockers and candidate ranking.
- `renders/light-r5-threshold/probe.json` and ten PNGs: selected195/30 and the bounded material response diagnostics.

Every run was serialized in root-granted GPU slots, against the real app at127.0.0.1:5001, with escalated CDN access. Each final render reports293/293 loaded object roots and no page errors. Captures preserve exact canonical position/target/FOV, explicitly reset camera.up=(0,1,0), and use1200×900 only as diagnostic resolution. HTTP failures were existing HA structure503, states502 and calendar502 responses, not rendering assets. Scripts syntax-check successfully. Every browser closed in finally and its process exited0 before the slot was released.

No production source, canonical registry, database, saved yard transform, ground geometry, contact transform logic, sky dome, front/interior lighting, or weather contract changed. No fresh critic verdict or photorealism pass is claimed.

## Final blue-balance validation and exact proposed source patch

Root requested a separate pigment correction after inspecting the lighting response. First tested living blue factors1.40/1.45; selected1.425 as a compromise between the shaded09 and lit12 blue errors. That first run accidentally exempted litter from the lighting response; it was used only to choose the pigment coefficient and is not the final candidate. The corrected run restored the exact earlier lighting semantics: sun×4 and IBL×0.02 on turf, tufts, clover **and litter**; blue pigment×1.425 only on turf, tufts and clover. Control means exactly reproduce the earlier four-material response.

| Final four-material lighting response | Photo09 RGB | Photo12 RGB |
|---|---|---|
|Reference |37.66 /48.45 /33.49 |124.27 /136.19 /103.89 |
|Blue1 control |35.09 /50.42 /28.39 |128.24 /134.30 /85.65 |
|Blue1.425 proposed |35.21 /50.49 /37.73 |128.28 /134.36 /99.91 |

Inspected both actual corrected images. They retain the physical shadow separation and photo12's grass reads less yellow. Residuals: photo09 grass is slightly cooler than its reference; photo12 remains slightly deficient in blue, and underlying blade anatomy still reads procedural. The facade and upper-right photo12 shade issues above remain. No further fit or render was launched after the corrected run.

Snow is explicitly excluded from the pigment change. For turf, the correction is inserted after its existing snow-detail luminance calculation and before its snow-color interpolation. For tufts/clover, the render callback subtracts the snow-white contribution before multiplying the remaining grass blue. Full-snow control and blue1.425 have identical recorded material colors and foreground RGB. Native foreground ROI[120,730,1080,900] is **pixel-identical**:0different pixels, maxdifference0. Whole frames have11765different pixels outside the ROI, maximum9 and overall mean absolute difference0.00716; no whole-frame invariance is claimed. Evidence: `renders/light-r5-blue-final/snow-invariance.json`.

`light-r5-blue.cjs --include-litter` captured the final six1200×900 images in `renders/light-r5-blue-final`. Its ownership audit finds each of the four edited materials used exclusively by its named rear mesh. The JSON field `fallenUnchanged:false` is expected in this corrected run because litter's **lighting shader** changes; its pigment does not receive the blue multiplier. No page errors; existing HA response failures only. Browser closed in finally, process exited0, GPU slot released before this report.

The proposed unified diff appends one scoped response block **inside `addRearLightDetail`, after its existing `settle(120)` call**. It composes the current contact shader/onBeforeRender callbacks; does not alter their root transform calculations; adds no lights, textures, camera hooks, timers or world-position masks; and leaves global source unchanged. It scales only the actual directional-light shader term, so HA point-light terms retain their existing response. Environment intensity still follows `getEnvIntensity()` from daylight/weather. The four ground materials own their normal existing disposal lifecycle. `light-r5-response-proposal.js` is the same insertion block for review.

No canonical preset or registry change is included.195/30 is the **reference-supported photographic illumination state**, recorded separately from the generic rear335/42 preset and from live HA sunlight. Root should use explicit195/30 when judging this reference-specific candidate, then perform scoped lifecycle/native checks before requesting fresh criticism. The proposed patch has not been applied by this builder.
