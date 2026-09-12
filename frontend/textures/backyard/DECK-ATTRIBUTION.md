# Rear deck scanned grain

Wood Planks Grey, Poly Haven, CC0 1.0.

Source and license: https://polyhaven.com/a/wood_planks_grey

`deck-grain-albedo.webp` derives from the 1K diffuse map. It is neutralized
to cool grey with broken chalk abrasion, clustered grit and short scuffs. The
source's continuous grain is attenuated; its high-frequency detail is retained
in irregular patches. `deck-wood-normal.webp` is a matching generated OpenGL
micro-relief normal, and `deck-roughness.webp` varies the dry worn response.

The runtime maps five separate scan interiors to individual modeled boards.
Scanned board joints are excluded from their UV regions; the actual physical
joints and beveled edges remain geometry. The scan repeats every 1.5 metres
along a board, with independent longitudinal offsets and strip choices.

Build recipe: `scratchpad/backyard4k/deck_material_r6.py`.
These assets apply only to the rear deck. No house reference image is projected.
