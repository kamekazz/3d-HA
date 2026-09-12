# Rear deck round 7 — orientation diagnosis

Read roomkit skill, RESUME, ROOM-BRIEF, STYLE-BAR, frontend CLAUDE, the editable
yard contract, current addRearDeckDetail, reference manifest and camera fit.
Inspected actual photographs 14/02 and BOTH user overhead screenshots:
codex-clipboard-0a26a656-b67d-4b8d-8e39-ae01a7099398.png and
codex-clipboard-a84d2dac-6312-424d-b3fb-13b42472198b.png in the user's Temp.
Also inspected actual R6 photo14 capture preview and its matched blind crop.

Both overheads show upper slider-landing boards parallel to the north railing,
east–west in world coordinates. Current upper boards are diagonal. Lower
lounge boards run southwest–northeast; current lower boards use the opposite
diagonal. Proposed correction is upper platform angle PI/4 → PI/2 and lower
-PI/4 → PI/4. Angles describe ACROSS boards in the current generator, so the
resulting upper ALONG direction is -X and lower ALONG direction is (-X,+Z).
Keep the existing .48 ft pitch / .462 ft face width and R6 maps initially.

The registered camera also contributes to the apparent density gap. Analytic
projection using its actual no-view-offset camera state gives the following
pitch intervals across x220..500 at a 600×450 comparison size, on upper y2.744:

| image y | current diagonal | corrected east–west |
|---|---:|---:|
| 300 | 33.8 | 28.6 |
| 350 | 24.7 | 22.0 |
| 400 | 19.5 | 18.0 |

This is camera mathematics, not a rendered validation. Orientation alone
reduces count by only 8–18%, rather than the ~2× gap identified by the critic.
The photograph's strong actual seam minima at y350 are x229,260,290,320,350,
380,409,438,467,495. Tracking them to y380 gives x229,264,298,332,366,399,432,
465,497 (the leftmost seam leaves the sampled interval). Their convergence is
approximately x480–490/y125, whereas corrected world-X projects to
x393.6/y135.6 under the registered camera. Its upper-deck camera height is
10.0805−2.744 = 7.3365 model units. This does not independently establish
physical eye height: the source slider is about 9 model units tall. The
existing slider-only camera fit has 9.81px RMSE
and hits the x22 bound, so it does not establish a precise deck scale match.

Do not double physical board width solely to compensate for that camera.
This diagnosis does not alter deck perimeter, elevations, steps, furniture,
editor coupling, or material maps. Root retains camera/lighting ownership.
An actual native capture and fresh blind critic remain required after editing.

Root subsequently granted the two angle changes. They are applied with a
two-line explanatory comment; node --check passed. No width/material change.

The separately saved experimental camera fit uses seam convergence together
with four slider and two perimeter anchors, with no imposed board pitch or
camera height. It reduces predicted horizontal intervals at image y350 from
22.0 to 15.6, and matches the observed world-X vanishing point within 4px. Its
house/separator anchor remains 38.6px off, so full-frame alignment is imperfect.
It remains a candidate, with the canonical pose unchanged.

## Actual native validation

Captured both cameras from the real app at 3840×2880 using reference-light-r5
(sun elevation 30, azimuth 195), in renders/deck-r7-orientation/. Both completed
with 293/293 assets, zero page errors, enabled type2 shadows and unchanged front
checksum: 482260 triangles, xor166137678, sum3351587226. Browser closed exit0
before inspection, and the GPU slot was returned to root.

Inspected both actual full-frame progress previews. The corrected canonical
view now has the intended upper east–west board direction; lower visible boards
have the corrected diagonal. Upper seams remain visibly denser than photograph14.
The experimental camera improves upper seam convergence but makes the separator
nearly vertical, unlike the photograph's strongly diagonal separator. It is not
recommended for promotion. Canonical pose files remain unchanged; candidate
entries automatically added by the generic capture helper were removed from the
public progress renders/previews/renderSizes maps, while its evidence files stay.

This is an orientation correction, not a photographic-match claim. Fresh blind
critic required; width remains .48 pending evidence that separates model scale
and perimeter/camera fit from the physical board pitch.
