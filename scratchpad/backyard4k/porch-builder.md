# Rear porch detail builder

Scope: the rear porch/sliding door only. No database/model writes, interior edits, front changes, global lighting or shared RNG changes.

Read the roomkit skill, RESUME, ROOM-BRIEF, STYLE-BAR, frontend contract and EDITABLE YARD identity contract. Viewed reference 14, 07, 09 and 02, and live native baseline rear_elevation.png. Reference 14's filename establishes north looking south; 02/07 establish the northeast porch viewpoint.

## Live evidence

`porch_probe.cjs` launches the real app at http://127.0.0.1:5001, imports its house module, and reads live transformed shell vertices and +Z ray hits. It writes `porch_probe.json`; it has no mutation API calls. Browser network escalation was necessary for the app's Three.js CDN dependency.

Door panes: left world X 9.5793..12.6804, Z -24.3278; right X 13.0083..16.1094, Z -24.2280. Both world Y 2.2966..11.1080. Siding ray hits at Z -24.487. The existing source shell already includes the grilles and frame; baseline showed saturated blue, nearly uniform glass.

## Source change and integration

Only added helper `addRearPorchDetail(L, props, masses)` to frontend/js/environment.js. Parent integrates the call after existing backyard generation:

```js
addRearPorchDetail(L, props, masses);
```

Append a factory entry so these additions own a discrete editable item:

```js
['building', 'Rear porch detail', () => addRearPorchDetail,
 (f) => (addRearPorchDetail = f)],
```

The helper adds two dark neutral glass skins placed 0.02 ft outward of their measured glass faces; narrow physical three-column/six-row grille bars; perimeter gaskets; a black recessed backplate and raised pull; aluminium sill rails and a dark recessed track; the continuous grey nosing at the existing upper/lower platform junction. All nonemissive. Uses existing bucket materials, deterministic analytic vertex color, no new texture or RNG draws. Fixed measured coordinates track L.blockE/L.blockN translations, matching the existing yard landmark contract. Live iteration showed the source fine grille disappears behind the opaque skins (it belongs to the source glass appearance), so physical bars were added in front.

## Validation and limits

`node --check frontend/js/environment.js` passes. Native baseline and edited `renders/porch_r1/porch_photo14.png` visually inspected. Final edited capture is 3840x2880, loads 293/293 objects, zero page errors, shadowMap enabled/type2. The door grid, handle and threshold render after correction. Parent received integration and critic received the locked pose path/key. Fresh critic pending; no indistinguishability or completion claim.

Registered reference pose in `porch_poses.json`, key `porch_photo14`: position [18,8.4,-38], target [6,4,-27], FOV 85, 3840x2880 (4:3 to match photo14), level all, sun elevation42/azimuth335, no cutaway/markers, matching the current workflow lighting. It places the door in the left third and preserves a broad deck foreground. Existing misplaced furniture remains visible and limits whole-photo matching.

The glass uses the shared props material and a restrained value field, so does not recreate true scene reflections or the photograph's visible interior. Those remain a fidelity limit. Existing deck platform placement, furniture placement, and grade conflict were not repaired by this helper. The existing deck's rear stair has one riser against shell grade Y2.13; reference09 shows roughly four. Resolving that requires a coordinated rear terrain/deck change rather than lifting this detail above the existing door threshold. The shell-door proportions remain those of the measured source opening.
