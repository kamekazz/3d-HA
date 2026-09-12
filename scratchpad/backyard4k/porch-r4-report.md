# Rear porch workstation R4

Scope: only the workstation subgroup in `addRearPorchDetail` and its live reflection probe attachment. No door dimensions, deck, landscaping, global lighting, shared shell material, model files, or database changes.

Read the roomkit skill, RESUME, ROOM-BRIEF, STYLE-BAR and frontend environment/editor contract. Inspected the actual converted references 14, 02 and 10 plus the supplied overhead clipboard PNG (`codex-clipboard-0a26a656-b67d-4b8d-8e39-ae01a7099398.png`).

## Reference evidence

The overhead photograph is decisive: the stainless countertop is a long strip against the outer west rail of the upper platform, extending outward from the house. Its doors face the middle of the deck. It is perpendicular to the house wall. Photo14 is consistent: the counter ends near the side rail and its front face crosses the siding perspective rather than following it. Photo10 locates this assembly beyond the slider's west side. Photo02 documents the other platform and slider boundary but does not independently expose the workstation.

R3 placed the 6.10 ft long cabinet parallel to the house wall. That gave the wrong projected silhouette in the registered photo14 view. R4 corrects orientation and position without changing the authored width, depth or height. This is a multi-view layout correction; no dimensions were enlarged to compensate for a camera angle.

## Source geometry

The existing `rear-porch-stainless-cabinet` remains the owner coupled to the editable `Rear porch detail` item. Its new child `rear-porch-workstation` contains the counter, body, sliding panels, legs and countertop pots. The wall box, lantern and speaker remain direct children of the original owner.

The workstation rotates -90 degrees around Y about its prior center `(6.10+dx, 0, -25.19+dz)` and moves that center to `(3.90+dx, 0, -28.00+dz)`. The original front normal -Z becomes +X (east); +90 degrees would incorrectly face west. Counter bounds before anchor offsets: X 3.125..4.675, Z -31.050..-24.950, Y 5.870..5.975. The work surface remains 6.10 x 1.55 ft. Feet remain on deck Y 2.744; rear lip top Y 6.135 gives the unchanged 3.391 ft main envelope, excluding pots/plants.

The material texture, steel/dark material values, physical panel bowing and mesh dimensions remain unchanged. The cube probe now transforms its existing sample point through the workstation subgroup matrix. Its canonical sample point is `(5.81+dx,4.9,-28.32+dz)`, in front of the east-facing doors. The existing recursion guards and disposal listeners remain intact. Planar glass reflection code is unchanged.

Root was notified that the prior floor planter position overlapped this corrected layout; root owns that separate instance placement.

## Verification status

`node --check frontend/js/environment.js` passes. Native registered photo14 capture is `renders/porch-r4/photo14.png` (3840 x 2880; 293/293 loaded; zero page errors), using the exact R3 critic pose copied into `porch-r4-poses.json`. Inspected `photo14-progress.jpg`, the capture workflow's downscaled preview: the corrected long face is visible, but stainless remains markedly darker than the reference. The native PNG itself exceeded the image reader's transport limit; the original full-resolution artifact is preserved. Capture initially could not load the app's CDN modules under network restriction; the same capture succeeded with network escalation.

`porch-r4-verify.cjs` completed successfully and wrote `porch-r4-verify.json`. The measured live anchor offsets are dx +0.120616 and dz -0.366601. Actual counter bounds are X 3.245616..4.795615, Z -31.416601..-25.316601, Y 5.870000..5.975000. Its front normal is `(1,0,0)` within floating-point tolerance. Editor owner translation +1.5 ft X shifts the workstation exactly +1.5 ft; rebuild restores identical counter bounds. Workstation and wall accessory parentage are correct, the steel has its cube environment map, steel/glass disposal listeners execute on rebuild, original shell material values remain unchanged, and there are zero page errors. These checks do not claim rendered reflection fidelity.

The root-owned floor planter at `(4.9,2.744,-32.5)` has measured Z bounds -33.660289..-31.339711 and overlaps the corrected workstation AABB by 0.07689 ft. Root was notified after the probe to move its center to Z -32.80, which would create 0.22311 ft clearance. That follow-up source change belongs to root and has not been recaptured here.

The single-browser capture/probe slot has been released to root and the queued siding builder. No critic has judged R4 and no fidelity pass is claimed.
