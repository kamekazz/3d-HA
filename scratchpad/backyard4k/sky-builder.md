# Rear sky R4

Scope: `frontend/js/environment.js`, `addRearAtmosphereDetail()` plus the read-only `getDaylight` import. No light, exposure, weather, fog, global background, material, ground, neighbor, or scene-owner change.

## Diagnosis

The existing sky shader already applied `colorspace_fragment`, so color encoding was not the problem. The HA daytime background itself was flat slate: a clear photo14 render patch measured RGB 95/116/145 against 213/232/254 in the photograph; photo09 reference sky measured 185/203/234. Transparent cirrus alone could not lift the base sky.

The first R4 attempt added a background-derived directional blue/horizon gradient to the existing two planes. Real-app photo12 and photo09 exposed rectangular coverage/reflection edges; this candidate was rejected. The coordinator authorized replacing those bounded fields with a continuous north-only dome while retaining exact nonrear pixel isolation.

## Implementation

One small procedural sphere (radius 300 feet, center 16/0/-301) replaces the two sky planes. Its vertices remain entirely north: min [-284,-300,-601], max [316,300,-1]. The vertex shader places its fragments at background depth, so all real building, tree, land and water geometry occludes it normally. BackSide rendering, depth testing, no depth writes, early transparent render order, no shadows, no image asset. The existing yard teardown owns geometry/material disposal.

The gradient reads the actual linear `scene.background`, brightens its channels for directional scattering, and blends toward a pale horizon. Sparse stretched procedural cirrus uses a continuous projection of the view direction; an initial atan longitude seam seen in photo14 was removed before final captures. Sky output remains untonemapped with Three's sRGB conversion. The lake's existing reflection pass sees the real procedural sky.

The existing rear camera gate rejects south/front, primary side and interior cameras. The read-only resolved daylight accessor supplies condition/elevation: cloudy, fog, precipitation and snow disable this clear-sky artwork, partly cloudy retains 45%, full wetness disables it, and it fades away below daytime sun elevations. Night is exactly zero. This adds no frame subscriptions, timers, textures, rendering passes or global state writes.

## Validation

`sky-r4-verify.json`: front, west, east, interior each 0 changed pixels in 1,080,000 pixels when sky is disabled/enabled. Night, cloudy, rainy and fully wet rear comparisons are also exactly 0. Dry daytime rear changes 465,454 pixels. Bounds are entirely north. No page errors. Renderer still exposure 1.15, ACES tone mapping enum 4, output `srgb`.

Real-app previews at canonical camera angles: `renders/sky-r4-dome-preview/` photo09/photo11/photo14/photo12, all 293/293 objects. Photo11/photo12 confirm full lake coverage and continuous reflection. Photo14 in that preview directory is the rejected atan-noise seam version; final captures use the seam correction.

Final native captures: `renders/sky-r4-final/` photo09, photo11, photo14, photo12, and photo09_sun155, all 3840 x 2880, 293/293 objects, no page errors. All retain front triangle checksum 482260 / xor166137678 / sum3351587226. Matching `-progress.jpg` previews are 1600 x 1200. The final photo14 cloud longitude seam is gone.

The shared-page capture helper now resets camera.up to [0,1,0] before each pose and records it. Photo12 and photo09_sun155 were retaken after this correction and their state.up is [0,1,0]. Photo09/photo11 were captured before the first rolled pose; photo14 applied its own canonical roll correctly. No camera registry was modified.

The pixel probe above ran on the closed-dome version before the final noise-coordinate seam correction; the camera gate, background depth, geometry, weather/night uniforms and opacity were unchanged by that correction. A repeat probe was stopped to release the single-browser slot for the queued ground critic. Its runnable script remains `sky-r4-verify.cjs`.

Final photo14 sky patch is RGB171/200/236 versus prior95/116/145; photo11 is182/205/232 versus94/115/143. `sky-r4-color-metrics.json` records exact crop rectangles and means. The sky is brighter and continuous, though still bluer/darker than the reference14 sky213/232/254.

The requested alternate azimuth155 comparison is an unpromoted capture only. It darkens the rear facade: upper siding RGB160/164/167 at335 becomes104/112/125 at155. It does not darken the foreground lawn; that patch rises from129/146/101 to140/155/111. `sky-r4-sun-comparison.json` records those samples. Production sun settings and canonical capture lighting remain untouched; all capture lighting used the app's existing test override.

No critic has judged the final sky. No browser remains open from this builder.
