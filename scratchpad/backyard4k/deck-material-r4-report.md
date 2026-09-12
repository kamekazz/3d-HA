# Rear deck material, round 4

Changed only `addRearDeckDetail` in `frontend/js/environment.js` and dedicated
rear deck texture/build/evidence files. Both platform footprints, heights,
diagonal board directions, rails, stairs, furniture and source-instance
runtime/editor logic are preserved.

The cloudy CanvasTexture is replaced by a neutralized Poly Haven CC0 wood scan
and its matching OpenGL normal. Five safe scan-interior UV ranges each cover
one modeled board; no scanned joint falls inside a board. Independent strip
choices and longitudinal phases vary the boards. Repeat length is 1.5 m.
Physical pitch remains .48 ft; width is now .462 ft, giving .216 inch joints.
Edge bevel width/drop is .006 ft, with a milder edge tint. This addresses the
previous .432 inch uniform black grooves without changing platform layout.

Runtime texture payload: albedo 197,470 bytes; normal 4,430 bytes.
Attribution is in `frontend/textures/backyard/DECK-ATTRIBUTION.md`.
Rebuild the neutral albedo using `deck_material_r4.py`.

Actual application capture:

`node scratchpad/backyard4k/workflow_capture.cjs deck-material-r4 photo14 --pose-file scratchpad/backyard4k/deck_layout_poses.json`

Sandbox capture failed loading the CDN module. The authorized escalated
capture succeeded: 293/293 models, zero page errors, camera [22,8,-39],
3840 x 2880 pixels. Front geometry signature stayed at 482260 triangles,
xor 166137678, sum 3351587226.

Viewed full frame and the native-resolution floor crop in
`renders/deck-material-r4/`. The floor now has authentic directional grain,
fine streaking, scratches and fasteners; it no longer has the prior soft
cloud field. This is a builder assessment, not a blind pass. Straight uniform
edges and bright/busy scanned weathering can still expose the material, while
the unmatched camera and other scene elements remain obvious in the full frame.
Send to a fresh focused critic before any claim that it matches the photo.
