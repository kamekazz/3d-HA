# Rear clipped planting, round 3

Changed only `addRearPlantingDetail` in `frontend/js/environment.js`. The root
coordinator synchronized the matching rear grass exclusion polygons separately.
The existing grass material and added 20-foot yard depth are retained.

References inspected: 09 (rear elevation), 08 (east gravel return), 10 (deck
planting detail), plus the recorded planting-r2 blind FAIL verdict. East is the
left side of photo 09, west its right side. Main crowns sit outside the measured
deck footprints x3..20.6 / x20.6..42.2.

Both mature clipped canopies grow approximately 1.55 times in diameter. East
center/radii: [50.4,-41.2] / [7.60,5.35,6.74] feet. West center/radii:
[-4.4,-38.5] / [6.67,4.81,6.05] feet. Centers move outward only for deck clearance.
Their shape uses broad clipped shoulders, a subtly flattened dome, continuous
low-amplitude irregular lobes, dense individually folded small leaves, and
forked woody stems beneath the lower crown. Low shrubs under the rail now meet
into a spreading hedge. Gravel beds and cobble borders expand around the crowns.

All 11 shrub keys and both bed/cobble pairs retain their original authored pivots.
`planting-r3-before-items.json` records the previous live pivots;
`planting-r3-pivot-check.json` verifies all 15 rear items with no differences
at tolerance 1e-7. This preserves saved Outside-editor transformations.

The registered `elevation_poses.json` photo09 camera remains unchanged. The
coordinator rejected an experimental 105-degree gable fit because it distorted
foreground deck framing. Under the registered camera, the round-3 candidate's
right crown diameter is about 107 pixels normalized to a 600-pixel-wide image,
compared with approximately 100 pixels in photo09. The frame still has house/
deck registration limitations, particularly the partly cropped left crown.

Validation: `node --check frontend/js/environment.js` passed. Candidate actual-app
capture is `renders/planting-r3-candidate/photo09.png` (3840x2880), with 293/293
models loaded, zero page errors, no failed requests or shader/runtime errors,
and unchanged front triangle guard 482260 / xor166137678 / sum3351587226. Four
HTTP 502/503 resource messages remain in the candidate's console diagnostics.

Final synchronized-bed capture: `renders/planting-r3-final/photo09.png`
(3840x2880), visually inspected through its 1200x900 QA preview. It again loads
293/293 models with zero page errors, no failed requests or shader/runtime
errors, and the same front guard. The same four HTTP 502/503 console resource
messages remain. Grass no longer grows through the expanded gravel beds.
No blind critic has judged this round; no visual pass is claimed.
