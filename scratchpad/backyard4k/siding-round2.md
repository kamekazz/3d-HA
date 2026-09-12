# Rear siding — bounded critic follow-up

The independent siding-r1 critic identified the photograph with 100% confidence. Its single largest siding finding was a flat, uniformly grey gable with mechanically thin, even lines, compared with the photograph's stronger overlapping clapboard relief and uneven local shading. This follow-up owns only `addRearSidingDetail()` in `frontend/js/environment.js`.

Inspected actual reference09, the first builder's report, `renders/siding-build3/photo09.png`, and the exact critic verdict. Previously read repository roomkit SKILL, RESUME, ROOM-BRIEF, STYLE-BAR, frontend CLAUDE and actual live shadows/daylight contracts. No front, other elevation, source shell material, trim, glazing, room, global lighting, weather or exposure change was made. Existing source-facing triangle selection and true window/door openings are unchanged.

The lapped faces now have approximately 0.047ft (0.56in) butt projection instead of 0.026ft, with a shallow bow across the face. Three physical profile facets per course and four-foot horizontal sections let the real daylight shade the profile and a restrained 0.007ft longitudinal bow. The edges are still clipped to the measured source triangle outlines. Courses remain at the existing 0.481ft reveal. They do not cast sub-inch shadows into the low-resolution global sun map; the retained source shell continues casting the house silhouette.

A private-seeded 512x256 material tile supplies subtle chalking and a broader underside dirt/occlusion transition, with a narrow dark return and slight variation along the run. No photograph pixels enter this tile. The existing texture lifecycle/dispose hook is retained. Subtle per-course and low-frequency vertex colour variation replace the almost uniform prior surface; material roughness is 0.84. These changes keep the material nonemissive and responsive to the actual app lighting.

## Actual self-capture

`renders/siding-round2/photo09.png` is a native3840x2880 real-app5001 capture using unchanged `elevation_poses.json` photo09: position [15,5.7,-68], target [13,18,-24.5], FOV80. House/all, markers/cutaway off, capture-only sunny elevation42/azimuth335, PCFSoft shadows enabled/type2. 293/293 models loaded, zero page errors or shader failures. The native image was reduced without retouching to `photo09-preview.jpg` (1600x1200) for visual inspection.

The lap profile is now legible across the main gable and wing as wider local shadow/highlight transitions. Subtle surface waviness and course variation break up the earlier nearly flat area. The result still looks cleaner and more mechanically regular than the photograph. Sky/context and blank glazing remain obvious scene differences, outside this piece. Simultaneous parent-owned deck/ground work appears in this capture, so it is evidence for the final current app and a bounded siding check, not a pixel-isolated whole-frame before/after.

Front environment fingerprint exactly matches workflow_front_baseline: 482260 triangles, xor166137678, sum3351587226. `node --check frontend/js/environment.js` passed. No independent critic has judged this round yet; no photo-match pass is claimed.
