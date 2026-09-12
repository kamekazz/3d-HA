# Ground R8 candidate handoff

Scope: only `addRearGroundDetail` in `frontend/js/environment.js`. Enlarged lawn, exact root-owned planting-bed outlines, global light/shadow settings, and other helpers preserved. No photo-realism pass claimed.

## Evidence and candidate

Fixed native 3840×2880 photo12 camera from `lake_r2_poses.json`: position [-2,5.7,-77], target [26,3.1,-111], FOV68. `ground_base_probe.cjs` resets and records camera for every trial. Results in `renders/ground-r8-base-probe/metrics.json` use the same resized 600×450 ROI [60,300,540,450].

| Trial | Mean RGB | Adjacent luma gradient X/Y | Luma p10/p50/p90 |
|---|---|---|---|
| R7 whole | 128.05 / 142.04 / 111.11 | 14.03 / 13.09 | 110.49 / 137.57 / 161.73 |
| Base only | 131.31 / 139.39 / 104.51 | 9.42 / 11.28 | 117.29 / 135.63 / 152.98 |
| Base ×0.4, blades ×1.45 | 122.37 / 135.44 / 108.65 | 20.33 / 17.52 | 88.01 / 131.25 / 172.30 |
| Base ×0.6, blades ×1.35 | 127.19 / 140.81 / 111.82 | 17.09 / 15.18 | 103.06 / 135.16 / 170.23 |

Reference gradient is 22.71 / 20.31. The base-only trial supports the bright-substrate hypothesis. Selected the medium trial to retain mean while increasing visible dark gaps and bright strands. Source turf color now a4abd9 ×0.60; blade color 6a8061 ×2.025 (previous ×1.5). Density cell grew from 0.72 to 1.15ft; height/lay cell from 0.85 to 1.30ft. The final coarser grouping and oak litter were added after this isolated material probe, so the table is diagnostic evidence, not a final candidate measurement.

Grass budget remains 160,000 instances ×7 blades ×5 triangles =5.6M. No triangle inflation or shadow-bias shader is shipped.

## Fallen oak leaves

Replaced geometric star-fan litter with 1,350 curved 2×2 grids, eight triangles each (10,800 total). Real CC0 oak albedo RGBA and DirectX normal, full UVs, alphaTest0.45, normalScale(0.3,-0.3). Leaf lengths 0.35–0.69ft, varied curl/twist/burial, existing autumn palette. Shader converts sampled color to luminance detail before palette tint, retains alpha, and applies wet/snow behavior. Canvas lobed silhouette remains a safe request-failure fallback.

Existing parent-installed textures: `/textures/backyard/oak-leaf-albedo.webp` and `oak-leaf-normal-dx.webp`. Separate leaf map lifecycle guards prevent callbacks assigning disposed/rebuilt owners; default loader participates in boot manager.

## Validation and remaining work

`node --check frontend/js/environment.js` passed. Actual browser lifecycle results in `renders/ground-material-probe-r8/probe.json`: boot manager683/683 and pending0, turf768px/normal512px, litter384×655/normal256px, four texture disposals on rebuild, maps reloaded, blocked-request fallback verified, zero captured page errors. Inspected dry and snow1280×960 renders; snow neutralizes green texture and litter. This lifecycle probe uses the older camera and is not valid as the photo12 morphology gate.

Final native `ground-r8-oak` capture stalled amid four concurrent GPU captures. It produced no verified final candidate image. Parent requested serialized capture slots; on 2026-09-12 the verified node PID30872 and only its browser descendant tree were stopped. No replacement launched. Woodland subsequently completed a transient-memory patch; root will capture final photo12 in the next serialized group after deck.

Root then completed the serialized native capture successfully: `renders/spacing-verified/photo12.png`, metadata `photo12.json`, exact corrected camera, 293/293 models and zero reported page errors. Root reports identical front guard. Inspected full 1200×900 preview, native crop [1000,2000,2100,2800], and the exact reference/candidate focus crop. Derived images live beside the source with `ground-r8` in their filenames; final metrics are `ground-r8-final-metrics.json`.

Final source mean RGB is 127.98/141.82/112.94 versus reference133.34/145.42/110.64. Final adjacent gradient17.37/15.54 versus reference22.71/20.31. Final p10/p50/p90 is102.87/136.09/172.15 versus reference100.34/140.21/179.62. Open gaps and curved clump swaths are now visible. Native self-review still FAILS photorealism: stiff pale mint ribbons remain prominent, larger gaps expose smooth scanned substrate, and fallen leaves still look too uniformly pale/clean and numerous. Mean color agreement hides the blade/base color split. No additional source edits or capture launched after this inspection.

Required next step: fresh independent focus/full critic. Earlier R7 fresh critics failed; R8 remains an unapproved visual candidate despite verified rendering and improved local contrast.
