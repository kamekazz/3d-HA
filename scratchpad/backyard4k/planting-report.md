# Planting builder, bounded pass (2026-09-12)

Scope: rear north exterior planting only. Read actual reference images 03, 08, 09, 10, 12, 13, manifest camera descriptions, roomkit SKILL/RESUME/ROOM-BRIEF/STYLE-BAR and frontend documentation. Shadows confirmed enabled in real capture; older prose saying shadows off is stale.

## Implementation

Canonical implementation: `frontend/js/environment.js` `addRearPlantingDetail` at end of file; call replaces former addBackYard sections 2/3. Lake, porch, ground helper bodies were not edited by this worker. Parent integrated `rearFoliage` material split in bucketMesh.

- Eleven editable shrub items, with two clipped dark evergreen crowns flanking porch, two upright clipped shrubs and a rear east specimen, four low hedge lobes under north rail, two low west bed accents.
- All ground anchors now L.lo to match ground builder's lowered rear lawn. Actual north stair x8..12.6 stays clear.
- Dark 64x40 tessellated inner crowns, folded individual geometric leaf surfaces around 0.16..0.29ft tip-to-tip, exposed branching only beneath larger specimens, near-ground foliage for low hedge.
- Core and leaves carry `userData.rearFoliage`; parent splits them to matte roughness .95 / nonmetal foliage material with real casting/receiving shadows while ordinary props retain original material.
- Two scalloped gravel beds use existing scoped river-pebble factories. Bed rim scaled .45, pebble radius capped .18. No photo-derived image or billboard.
- Fixed private RNG 0x504c414e. No edits to front/shared factory definitions or global RNG before rear construction. Lake and ground calls survive.

## Identity and limitations

New items use existing shrub kind, scoped item ownership and position-derived keys; editing, clone and deletion follow the standard buckets. Geometry carries UVs, normals and colors for safe merging. Old section2/3 mixed mound/photinia/weeper/grass placements were retired in this photo arrangement. Their original position-derived keys were not migrated to the relocated new shrubs; no saved yard_edits rows were deleted. The prior photinia's general east position is retained but leaf silhouette and exact centre changed. Parent suppressed the separate generic rear scatter using a discard bucket while preserving its RNG consumption.

`planting_build.py` and `planting_refine.py` are one-time patch records, not repeatable generators; canonical generator is the JS helper.

## Real app checks

- node --check frontend/js/environment.js passed after changes.
- `renders/planting-build1/photo09.png` and `photo03.png`: 3840x2880, real http://127.0.0.1:5001, all 293/293 models loaded, zero page errors. Both inspected for technical/visual outcomes (photo03 file did not successfully decode for a separate view_image read; it is not claimed as visually approved).
- Build1 photo09 revealed excessive specular shine and bare hedge stalks. Corrected to matte material, reduced fold ridge, near-ground low foliage and lower final grade.
- `renders/planting-build2/photo09.png`: 3840x2880, 293/293 models loaded, zero page errors, renderer shadowMap.enabled=true/type2. Inspected actual image: matte fine leaf surface, low hedge seated, two main shrubs flank porch and stair remains clear.
- Exact camera poses in planting_poses.json. photo09 pos [15,5.7,-68], target [13,18,-24.5], fov80; photo03 pos [62,6.2,-87], target [13,16,-24.5], fov64. Same fixed daylight42/335/sunny as shared capture.
- Front geometry unchanged against workflow_front_baseline.json: 482260 triangles; xor166137678; sum3351587226 in both rounds.

## Honest open findings

This is a bounded build/self-check, not a blind critic pass or photoreal completion claim. Crown outlines remain highly regular and leaf distribution deserves fresh criticism; near white gravel still reads lighter/coarser than the photos. Real photo09 includes natural irregular shrub bottoms and a denser mixed low hedge. Build2 reveals legacy pale stairs/site slabs in foreground and an unskirted porch underside after grade lowering; these are separate ground/porch work, reported to parent. The exact matched photo framing still differs from source and should be rechecked after facade/lighting work. Shore plants are owned by lake helper and were not added to the middle lawn.
