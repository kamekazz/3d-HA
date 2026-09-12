# Rear siding and roof detail — build 3

Implemented `addRearSidingDetail()` at the end of `frontend/js/environment.js`; parent integrated the call beside the other rear helpers. No shell geometry/material mutation, database writes, GLB writes, renderer, house.js, sky or front edits.

Read roomkit skill, RESUME/ROOM-BRIEF/STYLE-BAR and frontend lighting/weather/stage documentation. Inspected actual references 01/04/07/09/10 and baseline `elevation-fit2/photo09.png` before building. Measured the live app shell through `siding-probe.cjs`; raw world triangles and UV signatures are retained in `siding-probe.json`.

Measured north-facing backing planes:

| plane | world Z | X bounds | Y bounds used |
|---|---:|---|---|
| main gabled rear | -24.436689 | -7.2841..20.5973 | 2.1338..40.5944 |
| lower rear wing | -10.8983 | 20.5973..47.3597 | 2.14..12.9627 |
| recessed upper wing | -8.1702 | 20.5973..40.4796 | 14.8492..22.9131 |

Selects only exact planar north-facing `Root_Node` backing triangles with the measured siding palette UV, then clips them into 0.481-ft courses. Their real door/window cutouts and gable outline remain. Courses have 0.026-ft physical projection over a 0.095-ft forward layer. Fine lower edges use a private-seeded mipmapped texture to prevent the subpixel dashed artifacts seen with tiny explicit returned lips. Siding receives scene shadows; the retained source shell supplies building cast shadows. No scene-wide shadow setting changes.

Rear-facing original white window/corner/fascia/gutter triangles are copied 0.10 ft outward, so they stay ahead of the new cladding. Neutral upper glass overlays preserve the source windows, grille divisions and frames. All direct geometry owns its teardown, and the siding texture disposes with its material. Per-yard duplicate guard prevents overlays stacking across repeated calls.

Self-shot and inspected `renders/siding-build3/photo09.png` using `elevation_poses.json` photo09, position [15,5.7,-68], target [13,18,-24.5], FOV80, native3840x2880. Existing app5001, all floors, cutaway/markers off, sun42/335 sunny, shadowMap enabled type2. 293/293 models loaded, zero page errors. Front environment fingerprint unchanged: triangles482260, xor166137678, sum3351587226.

Visible improvement: cool-grey fine horizontal siding, white casings and fascia, dark neutral upstairs glazing replace warm-grey coarse black lines/blue panes. Known fidelity gaps remain: the glass lacks the reference's reflected trees/interior variation; the black TV remains its flat source model without cover pleats; the roof itself retains source shingle/silhouette geometry. No photorealism pass claimed. Fresh independent critic pending through parent coordination.
