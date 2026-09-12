Rear turf round 3

Scope: addRearGroundDetail only. Deterministic private grass seed; no front geometry, global lighting or weather code changed.

Geometry: 260,000 instanced five-blade folded tufts, shorter and wider than round 2; coherent but irregular mowing lay, tuft height patches, existing clover and fallen leaves retained. Plant exclusions follow the new rear deck and east bed footprint.

Material: procedural directional microtexture with restrained bump; denser vertex mesh supports non-tiling broad botanical pale/cool/dry variation shared with grass instances. A rear-only shader biases blade normals upward to approximate thin leaf scattering while responding to the actual scene lights. No fixed painted tree shadows.

Camera: retained matched photo12 pose [-2,5.7,-60] toward [26,4.2,-90], fov68. The 5.5ft eye height above low grade is plausible; there was not enough evidence for a different eye height.

Validation: native 3840x2880 round3b loaded 293/293 models, zero page exceptions, unchanged front 482260 triangles xor166137678 sum3351587226. Several existing backend 502/503 console responses were present. First r3b attempt timed out initializing the scene and succeeded on retry.

Visual result is NOT a photo pass. The base still looks procedural and the tree/lake scene remains a strong cue outside grass ownership. The r3c shader capture succeeded with zero page exceptions and removed the harsh black blade silhouettes. After coordinating with the lake builder, the shore ramp now rises .685ft over 2.6ft to match its raised bank. Final r3d capture succeeded at 3840x2880, zero page exceptions, all 293 models loaded, same front geometry hash. Native grass and shoreline crop inspected. Fresh root critic pending; no photograph pass claimed.
