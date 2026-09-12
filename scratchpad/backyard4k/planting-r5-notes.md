# Rear planting R5

Reference 09 shows a broad evergreen canopy behind and to image-right of the
west clipped crown. Reference 04 confirms the open lower trunk and irregular
horizontal boughs along that west side of the house. Reference 03 supports its
position beyond the rear deck planting, while reference 08 documents the
opposite, east return and does not justify adding this tree there.

`addRearLayeredConifer` adds one scoped, independently seeded tree after the
existing planting sequence. It is anchored at world (-20.5, 0.12, -29.5), behind
the west clipped crown at (-4.4, -38.5). Twenty-two unequal boughs form four
horizontal tiers, widest at mid-height, with 132 secondary twigs and 1,056
individual needle triangles. Another 264 fixed crossing planes carry fine
needle masks, generated deterministically by `build_conifer_spray.py`. Their
orientation follows the branchlets rather than the camera. There is no
spherical or conical canopy core.

The new item's key is `tree:-205:-295`; its current bounds are x -28.65..-12.14,
y 0.18..12.68, z -36.62..-23.12 feet. All geometry is in the rear half. Its
1,942 triangles occupy 256,344 bytes for position, color, UV and normal
attributes. The new synthetic needle PNG is 37,164 bytes, for 293,508 bytes
total, below the 300 KB piece budget even after flattening. No external model
assets or photographic textures are added. The tagged props material split
only affects this new tree. Its map is disposed with the material; a failed
map load hides the planes while retaining the actual woody/needle geometry.
Three r160's standard shadow depth pass inherits the map and alphaTest, so
the needle mask also defines its shadows.

`planting-r5-audit.mjs` executes the before/after planting code using the
project's exact Three.js r160. All 15 previous keys, authored pivots, geometry
hashes and bed/cobble factory arguments are identical. A second generation
matches byte for byte. The grass exclusion code is untouched. Node syntax
validation passes. Other workers' lighting, grill and unrelated edits are
outside this patch.

The first actual app capture (`renders/planting-r5-candidate/photo09.png`,
3840 x 2880) loaded 293/293 models with zero page errors and the unchanged
front geometry guard. Browser closed with exit 0. Builder review rejected
its sparse branch-comb silhouette, prompting the fine needle spray revision.
The refined capture is `renders/planting-r5-final/photo09.png`, 3840 x 2880.
It loaded 293/293 models with zero page errors, zero failed requests, and the
same front geometry guard (482260 triangles, xor 166137678, sum 3351587226).
The browser closed with exit 0. Four existing HTTP 502/503 console messages
remain; no shader or runtime errors were reported.

Builder review confirms the missing planting now has a broad layered canopy
behind/right of the main clipped crown. However, the horizontal shoots still
look too regular and their needle clusters read as stiff dark fans at this
viewing scale. This is a remaining visual weakness for the fresh critic and
the next refinement, not a photoreal pass. No source change followed this
final capture.
