# Rear siding and measured north roof — R4

Scope: only the existing `addRearSidingDetail()` material/course construction and the private `addMeasuredRearRoofFinish()` tile in `frontend/js/environment.js`. The exact source plane, normal, UV, opening, trim, glass, roof mesh and triangle-offset guards remain unchanged. No front, interior, other primary elevation, source GLB/cache material, renderer, sun, sky, shadow map, or daylight behavior edits.

Read frontend/CLAUDE.md, repository roomkit SKILL, RESUME/ROOM-BRIEF/STYLE-BAR and reference manifest; visually inspected references03/09 and the actual siding-r3 blind pair/verdict. The prior critic's largest component gap was mechanical uniformly grey courses; roof was weakly mottled with a hard diagonal scene shadow.

Changes:
- Four physical profile facets per 0.481ft course: rounded butt, gently concave broad face and tucked top. Peak butt depth is 0.0665ft before the restrained per-course multiplier, with a 0.010ft longitudinal bow. These respond to the real app light. Fine courses still do not cast subpixel sun shadows; the retained source shell casts the building silhouette.
- Connected broad chalk-tone variation plus restrained course-batch variation, instead of random dirt spots. Adjusted the private vinyl tile's grain/chalking and overlap transition, base albedo and roughness to retain a cool grey facade while giving its relief a brighter face.
- The existing four north wing/dormer roof triangles now carry multi-scale mineral aggregate variation and independently varying tab tones. Roof geometry and the real diagonal cast shadow remain unchanged.
- No new texture downloads or external assets; the existing canvas texture lifecycle and owned geometry cleanup remain.

Verification: `node --check frontend/js/environment.js` passes. Real app5001 capture `renders/siding-r4-final/photo09.png` is native3840x2880, canonical photo09 position[18,5.7,-86], target[13.5,16,-24.5], FOV66, sunny42/335, all floors, markers/cutaway off, sun shadows enabled/type2. All293 models loaded; zero page errors or shader errors. Four existing backend502/503 console resource messages are in the JSON report; no failed requests were reported. The first sandboxed captures could not load CDN dependencies; the final network-capable capture succeeded.

Inspected the full-frame1600px preview and native siding crop; both are unretouched derivatives of the actual4K capture. The laps and broader face variation survive the full frame, and north roof shingles are visibly mottled. Front environment fingerprint stays exactly482260 triangles / xor166137678 / sum3351587226.

Largest remaining component gap: the two upstairs rear windows remain nearly uniform black panes rather than the photograph's varied tree/sky reflections. Existing pane/frame geometry is retained; references03/09 do not resolve enough evidence for a confidently placed AC detail. The siding also remains more even than the real facade and the roof keeps the hard scene-sun shadow. No photographic-match or blind-critic pass is claimed.
