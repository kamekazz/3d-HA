# Ground R9 candidate

Prepared after native R8 self-review: pale mint, stiff rectangular ribbons and angular tips were still visibly synthetic. Reference focus has tapered curved blades and less blue exposed vegetation. Source changes are confined to the grass geometry/material portion of `addRearGroundDetail`; root-owned bed outlines, expanded lawn, substrate, litter and lighting are untouched.

The same 35 triangles per tuft now form five blades with seven triangles each, instead of seven blades with five. Four cross-sections follow a smooth parabolic centreline, rolling slightly across the width and narrowing continuously through the upper half to a fine point. Explicit shared analytic normals prevent independent triangular facets producing hard diagonal highlights. Peak blade heights remain in the previous range; no instance placement or random sequence changes were made. Total blade triangles remain5.6M.

Upper vertex reflectance ramps smoothly to1.10 rather than an abrupt1.30 at a broad tip. Blade species tint changes from6a8061×2.025 to6e8252×1.95 to reduce the pale blue/mint component. This is a local material hypothesis, not a measured final color match. Lower strand count can expose more substrate, so final native image must assess coverage and mean before acceptance.

`node --check frontend/js/environment.js` passes. No browser/capture launched; awaiting root's serialized capture queue. R8 remains a failed realism candidate, and R9 has not yet been visually validated.
