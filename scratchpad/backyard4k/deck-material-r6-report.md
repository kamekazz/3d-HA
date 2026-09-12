# Rear deck material round 6

Scope: only private deck textures, their generation/attribution/evidence files,
and `addRearDeckDetail` material wiring. Geometry, board UVs, dimensions,
position, bevels, substrate, fascia, rails, steps, source-instance coupling,
root contact shading, ground and front geometry are unchanged.

R5's blind critic identified smooth cloudy board faces. R6 reduces the smooth
low-frequency field and uses thresholded multiscale chalk abrasion, source
high-frequency scratches, localized dark pits and clustered fine grit. Grain
contrast stays substantially below R4's continuous dark-fibre treatment.
The 1K source remains the CC0 Poly Haven Wood Planks Grey diffuse scan; no
house reference photograph is used as a projected image or material input.

The matching 512px normal derives from the new surface, replacing the previous
original scan normal. A 512px roughness map varies dry chalk and exposed wear.
Only albedo is sRGB; normal and roughness use Three's default NoColorSpace.
The existing shallow-step nosing shares this material and retains its dark
vertex tint and exact existing UVs. Outdoor stair boxes remain unchanged.

Runtime maps: albedo 183,024 bytes; normal 46,764; roughness 16,184.
Total 245,972 bytes, below the 300 KB material-piece budget. The deterministic
recipe `deck_material_r6.py` enforces a 300,000 byte limit. Attribution is in
`frontend/textures/backyard/DECK-ATTRIBUTION.md`.

Static validation: `node --check frontend/js/environment.js` passed. First
coordinated real-app capture (`deck-material-r6 photo14`, registered deck poses)
timed out before `window.__scene3d` appeared after 60 seconds. Its browser was
closed and capture slot returned; no image/diagnostic JSON was produced. Real-app
visual validation is pending startup diagnosis and a coordinated retry.
