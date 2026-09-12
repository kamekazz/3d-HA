Rear turf geometry round 5

Corrected reference camera from lake_r2_poses.json: eye[-2,5.7,-77], target[26,3.1,-111], fov68, 3840x2880. The earlier eye z=-60 predated the enlarged lawn; moving it17ft north puts the foreground into the actual leaf-fall band near the shoreline. Unchanged-source baseline is renders/ground-r5-pose/photo12.png.

Physical changes only inside addRearGroundDetail: seven bent blades per instanced tuft, blade lengths sized for a roughly2.5-3in sward canopy; two curved blade sections plus a descending tip provide matte relief instead of upright spikes. Local patch density and shared mower lay produce clumps. Blade shading normal upward bias reduced from1.35 to.8 so the actual folded faces retain directional light/dark response.

Fallen maple/oak-style leaf outlines now span about3.5-7.8in and rest about2in above the base, partly occluded by the grass canopy. Previously average leaves were about3.3in wide and lay directly on the ground beneath the new taller sward.

R4 albedo/normal calibration, tile scale, loader/disposal guards, snow/wet material lifecycle, deck/plant exclusions, shoreline slope, and all front/global systems are unchanged.

Final selfshot renders/ground-r5-bent/photo12.png inspected at native resolution and in the same60,300,540,450 focused crop as the reference. Zero page exceptions,293/293 models loaded; front geometry remains482260 triangles xor166137678 sum3351587226.

Limits: native view still reveals repeated blade geometry and stylized angular leaf outlines. The focused crop has more appropriate leaf scale and directional grass relief, but no photograph pass is claimed. Geometry cost increased from3.9M to9.1M instanced blade triangles; no additional asset download payload.
