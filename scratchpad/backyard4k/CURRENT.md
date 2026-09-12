# Rear exterior work — current handoff

The original seven-piece build/shoot/blind-critic loop remains active. No piece has passed. Latest user steering (larger grass area) is implemented as rearSite.yardN = L.yardN - 20; keep this. Native spacing proof is renders/spacing-verified/lawn_spacing.png, now first card on http://127.0.0.1:8765/progress.html. App is http://127.0.0.1:5001.

## Capture discipline

Run one browser at a time. Four simultaneous 4K captures caused stalled multi-GB Chrome processes. Woodland now flushes temporary leaf arrays per tree; serialized captures succeed. Use initial exec require_escalated because existing Three.js CDN imports are denied in sandbox. workflow_capture.cjs now records early startup errors and logs phases. It generates lightweight *-progress.jpg previews while keeping native PNG links. Use canonical_poses.json; no camera-fit experiments.

## Current pieces

- Porch R4 failed blind review (100%): grill narrow/upright was largest gap. Cabinet long axis corrected to Z along west edge, front east. Planter Two (4.9, 2.744, -32.8) clears it. R5 builder changed only Grill target to (4.55, 2.744, -38.5), yaw270, based on both overhead refs; native capture next after light probe. Cover dimensions unchanged pending render.
- Siding R5: painted black lap stripes removed, six physical facets, restrained depth/material variation. Native renders/siding-r5/photo09.png; no page errors, 293/293. Fresh critic pending.
- Deck R6: finer chalk wear, grit, normal/roughness maps; 245972 bytes total. Native renders/spacing-verified/photo14.png. Fresh critic pending; R5 failed.
- Grass R9 failed blind review100% (tall wiry tufts/gaps). R10 uses11 shorter blades of3 triangles per clump,5.28M triangles. Native renders/ground-r10/photo12.png self-fails comb pattern and gaps. Pause new geometry until R5 lighting evidence considered. R8 lifecycle/weather/fallback passed.
- Plantings R3 failed blind review100%: four separate low ellipsoids. R4 replaces only those four with overlapping leafy branch sprays,280896 bytes/2128tris each. Native renders/planting-r4-final/photo09.png verified293/293, zero errors, unchanged front. All15 keys/pivots/beds and other7shrubs preserved. Fresh planting_critic_r4 waiting for browser slot after grill.
- Lake/woodland R6: far bank ~260ft across, smaller scanned far leaves, private haze and rough actual reflections. No rounded interior-volume trial retained. Native renders/spacing-verified/photo11.png. Far detail still too uniform; fresh critic pending.
- Sky R4 complete: continuous closed north sphere at background depth, rear camera/weather gate. sky-r4-verify.json has zero changed front/side/interior/night/cloudy/rain/wet pixels; sunny rear changes only. Native renders/sky-r4-final/photo09,11,12,14 verified. Alternate sun155 rejected. Fresh light R4 critic failed100%: shaded foreground and facade too uniformly bright.

## Active light R5 evidence

rear_light_builder_r5 owns the current serial browser for photo12 component ablation. No production light changes yet. photo09 canonical grass RGB121/138/95 is unchanged with sun disabled; disabling IBL gives36/50/28 vs reference38/48/33. Global getEnvIntensity1.15 is indoor fill, not permission to change globals. Existing shadows are enabled and house casts/receives. photo12 whole grass136/149/108 vs reference124/136/104: must evaluate components before any rear-local adjustment, no blanket darkening. Preserve addRearLightDetail contact transforms. Full report light-r5-report.md.

Porch R5 native renders/porch-r5-grill/photo14.png is complete, zero app errors and front signature unchanged; orientation correction retained, cloth still taut, critic pending.

Planting R4 fresh critic correctly identified photo LEFT at100%. Largest gap was missing layered conifer behind/right of west clipped shrub. R5 final adds Rear layered evergreen tree:-205:-295, at(-20.5,.12,-29.5),256344 geometry bytes/1942triangles plus37164-byte synthetic needle PNG=293508 total. Narrow rearConiferSprays props split with alpha-matched shadows and geometry-only fallback. All old15 keys/pivots/geometry identical; total now16 identities, preserve final new key too. Native renders/planting-r5-final/photo09.png passed293/293,zero runtime errors, front signature unchanged. Builder self-review still sees regular stiff fan sprays. Fresh critic pending.

Light R5 blockers prove canonical335/42 near oak leaves+bark shade photo12; grass self-shadowing is negligible. Corrected receiveShadow=false diagnostic recovers direct RGB46/50/25, same as disabling all trees. South180/42 clears photo12 but also most09 foreground; noIBL12=76/86/51,09=64/77/45. Next geometry visibility scan should test intermediate elevations30–35, azimuth180/195/210 (southwest rays can shift09 into main tall gable while12 misses west edge), then bounded ephemeral material response only if supported. No production light change yet. Do not use first shadowMap.enabled=false ablation: did not invalidate compiled materials. All probes restore state and close browser.

Light R5 visibility scan now found195/30: all8photo09 turf rays blocked by house and all8photo12 rays clear. Ephemeral rear-ground-only sun4/env.02 yields09RGB35/50/28 vsref38/48/33,12RGB128/134/86 vsref124/136/104. Physical contrast restored, blue balance deficient. rear_light_builder_r5 currently probes living grass blue1.4/1.45 while preserving snowwhite. Important: lighting response applies turf/tufts/clover/fallen leaves; pigment boost only living first3. First blue run accidentally omitted litter lighting, must corrected rerun selectedfactor before source proposal. No production lighting changes yet. Root added reference-light-r5.json (195/30) as explicit capture candidate; workflow default335/42 not changed.

Queue: rear_light_builder_r5 blue validation -> fresh deck_critic_r6 native photo14 (waiting explicit root GPU grant). Fresh deck critic successfully spawned after planting builder finalized. Earlier thread limit recurred when completed porch slot did not free; avoid repeated failed spawns, wait for active worker to finalize. Siding R5, lake R6, porch R5, planting R5 still need fresh critics.

## Root integration

addRearLightDetail measures actual clipped foliage bounds and follows live move/scale/delete; deck contact uses inverse actual replacement transform. contact-verify.cjs/json passed all11 crowns, deck +2ft move, scale/delete and rebuild with zero errors. Canopy sphere AO was removed; no global shadow bias tweak retained.

Front guard remains482260 triangles, xor166137678, sum3351587226 in all verified captures. scope_check.py confirms protected front builder/shared landmarks/global grass weather source unchanged. Main production changes environment.js plus private backyard textures. Do not touch unrelated .claude/settings.local.json. Source images/archives/native renders ignored locally; reports/scripts remain reviewable.

Use update_progress.py to update pieces; sync_review_status.py now only refreshes derived notes, no stale hardcoded statuses.
