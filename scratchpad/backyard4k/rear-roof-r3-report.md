# Rear roof finish — round 3

The siding-r2 critic identified the photograph at 99% confidence and named the warm pale roof with regular coarse shingles as the largest remaining siding/roof gap. Checked the actual reference09 and blind pair, plus root/frontend CLAUDE and the roomkit skill, RESUME, ROOM-BRIEF and STYLE-BAR.

Changed only `addRearSidingDetail()` by adding a call to the new private `addMeasuredRearRoofFinish(shell, group)` immediately below it in `frontend/js/environment.js`. The siding, trim and glass from round2 remain as authored. No other helper, source GLB, shared roof material, cache, room, database, front/east/west roof plane, camera registry, exposure, global lighting or renderer was changed.

The real-app scene raycast identifies lower roof mesh `90809`, material `Roofing Shingles Asphalt`, at photo09 normalized pixel (0.315,0.545), point [36.2304,13.6101,-10.9121]. A broad geometry probe located the corresponding dormer source in the same shell. Retained roofing-only world geometry and ray evidence in `rear-roof-probe.json`; `rear-roof-probe.cjs` reproduces this measurement against app5001.

Exactly four source triangles are copied into the additive finish:

| Roof | Mesh/index offsets | World X | World Y | World Z | Normal |
|---|---|---|---|---|---|
| Lower north wing | 90809 / 6,9 | 20.6017..48.0164 | 13.0456..23.3238 | -12.0861..9.2881 | [0,.9012,-.4334] |
| North dormer | 92051 / 33,36 | 20.1535..41.2329 | 22.9423..27.6506 | -9.5151...2848 | [0,.9014,-.4331] |

The positive-Z end of each selected plane is its true north-slope ridge, largely hidden beneath the dormer. The opposite slopes are excluded. Mesh identity, material identity, exact offsets, measured bounds and normal gates guard the selection. Vertices are copied 0.018ft along the normal, with no source mutation. The original shell retains cast shadows; the overlay receives shadows and normal scene illumination.

The finish uses a private-seeded 1024² material tile covering 12×8ft of roof slope: cool charcoal asphalt granules, subtle uneven shingle tone, fine staggered courses and low-contrast joints. No photo pixels are used. Roughness .96, metalness0, emissive0, fine bump .007ft. Geometry owns teardown and the texture disposes with the owned material. One mesh, four triangles, one material/tile.

## Actual render verification

`node --check frontend/js/environment.js` passed. Captured and visually inspected `renders/rear-roof-r3/photo09.png` at native3840×2880, plus its1600×1200 preview and unscaled `roof-native-crop.png`. Uses the corrected registered photo09 camera [18,5.7,-86], target[13.5,16,-24.5], FOV66, all floors, markers/cutaway off and canonical sunny42/335. Actual app5001, PCFSoft shadows enabled/type2, 293/293 assets loaded, zero page errors or shader failures.

The lower and dormer roofs now read dark neutral/cool charcoal instead of pale taupe. Their fine softened staggered texture no longer dominates the roof. The native crop still shows clean regular roof boundaries and some periodic material mottling; this is a bounded improvement awaiting an independent verdict, not a photorealism pass. Other scene changes from concurrent ground/deck work are present in the full capture.

The capture's front environment geometry fingerprint exactly matches `workflow_front_baseline.json`: 482260 triangles, xor166137678, sum3351587226. The source shell and shared roofing material are preserved by construction; there are no GLB/source geometry assignments in this helper.
