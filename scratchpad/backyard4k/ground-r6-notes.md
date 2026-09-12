Rear ground R6: paired morphology and illumination diagnosis

Photo12 filename is This is the grass before the lake; no exact eye height is specified. Same-photo-resolution crop60,300,540,450 gave R5 green-pixel mean86/103/74 vsphoto130/144/108. Luma90th percentile113 vs176. Mean adjacent-pixel variation9.5/9.6 vs22.7/20.3. Full numbers: ground-r6-morphology.json.

A controlled browser test changed only rearSkyCount from actual tozero: crop mean92/107/79 became129/145/113. This identified the added spherical canopy sky-occlusion term as the main40RGB deficit. Parent independently measured its replacement and removed that unvalidated additional term; actual direct-light foliage shadows and porch/shrub contact shading remain. No ground tint compensation was made.

Projection math for the calibrated lake_r2 camera gives3in vertical blades5.35/7.52/9.65pixels high at photoY325/375/425; a6in leaf spans10.9/15.5/20pixels. A separate lower camera test exists in ground_r6_lower_pose.json, but enlarges the already-large near trunks, so final capture retains lake_r2_poses.json.

Geometry R6 reduces160000 clumps from260000, using broader folded blades and stronger patchwise density/height/lay variation. Blade triangles reduced9.1M to5.6M. Fallen leaves now vary length/width/asymmetry, curl over a two-ring surface, and partly bury at different grass-canopy levels instead of sharing one flat plane.

All material texture calibration, loading/disposal guards, wet/snow lifecycle, deck/plant exclusions, shore ramp, front yard, and global light/weather settings unchanged by this agent. Source changes only addRearGroundDetail.

Final image renders/ground-r6-final/photo12.png captured3840x2880, inspected full and native plus same diagnostic crop. Zero page exceptions,293/293loaded, front unchanged482260 triangles xor166137678 sum3351587226. Final metrics in ground-r6-final-metrics.json. No photo-pass claim; native render still exposes repeated modeled grass and stylized leaf outlines.
