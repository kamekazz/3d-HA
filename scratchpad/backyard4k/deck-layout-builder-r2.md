# Deck layout round 2 — corrected structural arrangement

Independent derivation read ROOM-BRIEF orientation contract, room3 landmarks and original b_deck.py, then inspected actual refs02/09/14 and both user drone attachments. The main rear wall is world Z-24.436, east edge X20.6; the wing rear/TV wall is Z-10.898. Reference02 puts the lounge against the wing and beside the main east wall; reference09 puts slider/stairs west and lounge east; the drone fixes a north/south separator between side-by-side platforms. The former source stacked them north/south with an east/west separator and furnished the open landing. This was a structural error, not a camera defect.

The new physical deck has upper X3..20.6 Z-42.2..-24.43 topY2.744, lower X20.6..42.2 Z-42.2..-10.91 topY2.424. The common edge at X20.6 is one shallow step. Upper north stairs are X8..12.6 Z-42.2..-46.4, four risers to low grade. East lounge stairs are X42.2..46.4 Z-19..-14.4, four risers. Footprint dimensions beyond the measured house anchors remain photo-derived estimates, especially the long lower platform required by the imported shell's wing setback.

Only environment.js was changed: addRearDeckDetail now generates weathered boards, substrate/fascia/posts, continuous rails and both flights as one group; configureRearDeckInstances attaches that actual group beneath the named Backyard Deck root, masks only its original model child, and applies model-child matrix corrections to the seven existing rear furniture roots. The old porch separator strips and redundant old-tread mask call were removed. Narrow light AO bounds now follow the two corrected rectangles and extend to wing Z-10.9. No database write, model-source file, interior or front code was changed by this builder.

Target object bottom centers/yaw degrees:

| Object | X | Y | Z | Yaw |
|---|---:|---:|---:|---:|
| Grill | 5.4 | 2.744 | -38.5 | 178 |
| Sofa | 28 | 2.424 | -40.15 | 0 |
| Lounge | 33 | 2.424 | -31.6 | 0 |
| Chaise | 40.15 | 2.424 | -33 | 0 |
| Parasol | 40.1 | 2.424 | -39.5 | 200 |
| Planter | 40.5 | 2.424 | -13.1 | 0 |
| Planter Two | 4.55 | 2.744 | -29.9 | 0 |

Actual native 3840x2880 real-app captures: renders/deck-layout2/photo14.png, photo02.png, photo09.png. Poses in deck_layout_poses.json, provenance beside each PNG. All loaded293/293, zero page errors, shadows enabled/type2; front geometry checksum exactly baseline (482260 triangles, xor166137678, sum3351587226). Small preview JPEGs were inspected. The drone test camera hit the roof and is explicitly NOT valid geometry evidence.

Photo14 now has open foreground, the north/south separator, slider left and grill right. Photo02 now connects correctly to the TV wall. It also exposes severe pre-existing shrub collisions with the corrected lounge: crown centers (34.7,-36.5), (35,-19.8), (40,-30.2), (39,-22.5). These were sent to parent to relocate east of X42.2 by at least each crown radius. No obvious grass tufts appear on visible deck boards; beneath those crowns remains occluded. Existing sparse/wrong furniture detail, box-shaped grill, missing upper cabinet and overly smooth materials remain visibly unlike photographs. No independent critic pass or photograph-match claim.

Lifecycle validation in deck-layout-verify.cjs/json uses only ephemeral display edits. Actual deck root +2ft and sofa root +1ft survive yard rebuild exactly. Reset/rebuild restores both bounds exactly. Fresh buildObjects with those offsets in an in-memory copy of GET/api/house preserves +2/+1 after complete root replacement. Exactly one replacement child survives each case, source model remains hidden, and zero page errors occur. Fixed source pose baselines measured from the pre-refit current API rows ensure future saved offsets do not disappear on reload. Cleanup restores child matrices/visibility and reparents the replacement to old yard before normal geometry/material disposal. Standard root visibility and picking carry through the actual child hierarchy. Existing editor rotation pivots remain the original object root anchors; this environment-only correction does not rewrite editor/DB pivot semantics.
