# Deck and north steps — bounded first build

This subtask follows fresh porch critic r1: the largest gap was a pale smooth deck with regular seams rather than irregularly weathered grey boards. Lake work is frozen during this subtask.

Read/inspected references 02, 09 and 14, actual `renders/porch_r1/porch_photo14_preview.jpg`, room3's measured landmarks, `scratchpad/ext/b_deck.py`, and `kit.py`. The roomkit and frontend contracts were already read during this agent's preceding lake task.

Only new `addRearDeckDetail(L, props, masses)` at EOF of `frontend/js/environment.js` was authored in this subtask. No database/model source file, front, room, global lighting/weather or lake helper changes.

## Geometry and material

Upper: world X3..20, Z-32.6..-24.43, surface Y2.744 (0.024ft above source). Lower: X3..27.5, Z-42.2..-32.6, Y2.424. Separate strips are polygon-clipped on a 0.48ft pitch with 0.032ft physical gaps and 0.025ft thickness. Upper/lower diagonal fields are opposite, inferred from the direction change across the separator visible in photos02/14. The old source used the same diagonal on both platforms.

A private seeded 256×1024 canvas texture has fine lengthwise fibre, larger whitening/weather patches and fine grain. Each board receives independent grey variation and lengthwise texture offset. Standard nonemissive material, roughness0.91, slight bump, receives the app's real shadows. Its material dispose event explicitly disposes the texture; its mesh has ownGeometry=true for yard teardown. This layer is a fixed environmental detail over the existing placed deck and does not independently track subsequent moves of that source model.

Continuous white rail caps follow all eight existing runs. Source `kit.py railing` accidentally made vertical-run top rails 0.34ft deep, leaving isolated balusters in the live render. The new caps restore the spans while retaining the existing openings.

North stair flight: X8..12.6 (center10.3), Z-42.2..-46.4, four risers from2.424 down to L.lo+0.027≈0.217, coordinated with ground_builder. This is the actual source stair center/railing opening; the room3 note incorrectly calls10.3 the west edge. Added tread noses, grey risers/stringers, white end posts/sloped handrails and unlit dark recessed housing geometry. No new light emitters.

## Integration dependencies

Parent must call `addRearDeckDetail(L, props, masses)` and register it as a scoped factory. The source one-step north tread/riser must be masked: wholly inside X7.9..12.7, Z-43.5..-42.25, Y1.8..2.4. Otherwise its old high tread protrudes through the new flight. Parent/ground builder handle removal of the old raised procedural rear lawn; actual shell under the north steps already lies at Y0.164.

## Actual first-build self-inspection

Syntax: `node --check frontend/js/environment.js` passed. Parent integrated call/factory. Captured actual app through the standard workflow in native3840×2880: `renders/deck-build1/porch_photo14.png`, independently inspected its `porch_photo14-preview.jpg` reduction. Camera exactly `[18,8.4,-38]` toward `[6,4,-27]`, FOV85, House/all, no markers/cutaway, sun42° / azimuth335 / sunny.

The render loads293/293 models with zero JavaScript errors, shadows enabled/type2. Front geometry fingerprint matches baseline exactly:482260 triangles,xor166137678,sum3351587226. The boards now carry visible grain/scuffs and per-board grey variation; upper/lower directions and continuous top rails render correctly without a visible raised sheet edge. Existing furniture placement, box-shaped grill and plain siding remain outside this subtask and dominate the unmatched scene. The grain remains more regular than the photograph's broad dirt/weather patches; an independent critic should judge it.

North steps require the separate old-tread/terrain masking integration and an elevation capture, which ground_builder and parent own. This close-up verifies the new deck finish and rail spans only. Bounded first build complete; no photograph-match claim and no fresh deck critic verdict yet.
