# Rear planting R4

The R3 blind verdict identified the four shrubs beneath the deck rail as
separate smooth ellipsoids. Reference 09 and the actual R3 full-frame pair were
inspected before rebuilding those four pieces.

Only the four under-rail shrubs use the new spreading form. Each consists of
28 irregular woody shoots carrying 868 small folded leaves, with branch forks,
overlapping sprays, varying shoot heights, and olive/dark-green foliage.
There is no closed spherical core. The mesh is tagged `rearFoliage`, so the
existing contact system measures its current geometry and editable transform.
The top heights range from approximately 3.3 to 4.3 feet at grade 0.12 feet.
The backmost vertex is limited to z -42.42, outside the deck front at -42.2.

The existing scoped `Clipped evergreen` factory and authored pivots remain.
The two mature clipped crowns, east return shrubs, west accents, bed outlines,
cobble edges, and all unrelated rear and front features are unchanged by this
patch. The original shared random stream is advanced by exactly the same
number of draws so the later west accents remain identical.

Offline validation: `planting-r4-audit.mjs` executes the before/after planting
functions using exact Three.js r160. All 15 item keys/pivots match. Bed/cobble
factory arguments match exactly. Only four geometry hashes differ; the seven
other shrub geometries are identical. Each changed piece has 2,128 triangles
and 280,896 bytes including positions, colors, UVs, and generated normals,
below 300 KB even after flattening. No new textures or external model assets.
`node --check frontend/js/environment.js` passes.

This is builder evidence. A fresh blind critic has not judged R4; no pass is
claimed. Capture diagnostics are recorded separately with the canonical image.

The initial candidate capture loaded 293/293 models with zero page errors and
an unchanged front guard (482260 triangles, xor 166137678, sum 3351587226).
Builder review found overly bare V-shaped shrub bases; the final source adds
low shoots and staggered origins, retaining the exact same geometry budget.

Final canonical capture: `renders/planting-r4-final/photo09.png`, 3840 x 2880.
The browser closed successfully before builder image review. It loaded 293/293
models with zero page errors, zero failed requests, and the same front guard.
Four pre-existing HTTP 502/503 console resource messages remain; there are no
shader/runtime errors. The saved preview was inspected: foliage now reaches
the bed and overlaps into a continuous irregular strip. Leaf-scale fidelity
and the overall photo match remain for the independent critic to judge.
