# Rear deck material, round 5

Only `addRearDeckDetail` and private rear-deck material/evidence files changed.
The existing scan is attenuated and masked into irregular patches, with broad
neutral wear, shorter scuffs, pale grit and dark pits. The wear fields use a
periodic Fourier filter so the existing 1.5 m texture repeat has no transverse
join. The matching normal strength drops from .20 to .045.

The shallow step's top uses the same worn composite, darkened with vertex tint,
on exactly the existing nosing box. Its vertical riser is dark neutral gray.
The nosing remains a child of the same rear-deck editor group. Deck footprints,
heights, pitch, board orientation, bevels, joints, stairs, rails, furniture,
source-instance coupling and front geometry are preserved.

Runtime private textures: albedo 42,862 bytes + normal 4,430 = 47,292 bytes.
The shared nosing map adds no asset payload. CC0 attribution is preserved in
`frontend/textures/backyard/DECK-ATTRIBUTION.md`; deterministic build recipe is
`scratchpad/backyard4k/deck_material_r5.py`.

R5 self-capture revealed transverse repeat seams and a flat-painted step top.
R5b corrected the seams; R5c adds the worn texture to the existing step top.
Actual-app capture command:

`node scratchpad/backyard4k/workflow_capture.cjs deck-material-r5c photo14 --pose-file scratchpad/backyard4k/deck_layout_poses.json`

The capture uses the current registered rolled photo14 camera and native
3840 x 2880 canvas. Its diagnostic JSON is the authoritative load/error and
front-fingerprint record. R5c loaded 293/293 with no page errors and front
signature 482260 triangles, xor 166137678, sum 3351587226.

Builder assessment: grain is less continuous and lower contrast; broad wear
remains visible with faint short scuffs. It still has very regular straight
board edges and may be too smooth relative to the reference's scattered dirt.
R5c full preview and native floor crop were visually inspected: the transverse
repeat joins are gone and the nosing now has a dark worn surface. No blind-critic
pass is claimed. A fresh focused and full-frame critic should judge R5c.
