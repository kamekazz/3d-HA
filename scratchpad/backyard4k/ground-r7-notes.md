Rear grass R7: fine-shadow hypothesis and blade cavity response

Read exact Three.js r160 ShaderChunk shadowmap_vertex and lights_fragment_begin code from the version used by the app. directionalLightShadows[i].shadowNormalBias offsets shadowWorldPosition in world feet. The global1ft normal offset is much larger than the3in turf, and global depth bias-.0005 across399ft is also about2.4in. Neither global was edited.

Controlled runtime-only shader trials: baseline, rear grass normal bias .012ft, .05ft, and .012ft plus directional depth bias limited to-.00002. Final probe hard-resets and records camera position/target/FOV before every render, preserving instancing/world transforms. All variants use[-2,5.7,-77] toward[26,3.1,-111], fov68. Earlier camera-drifted trial images were discarded; one invalid preview is explicitly named as such. Final probe metadata and metrics live in renders/ground-r7-shadow-probe.

Actual result: normal/depth clamps provide no useful fine relief at2048px over280ft. Grain9.912/9.350 baseline vs9.914/9.348 normal clamp and9.912/9.343 combined. MeanRGB stays within0.1. No shader errors. Do not ship this unsupported shadow change; none was added to source.

Alternative implemented only in addRearGroundDetail: existing blade vertex colours now darken buried roots and the enclosed lower folds while keeping upper folds/tips bright. No added mesh faces and no extra projected shadow/decal layer. Intermediate grain increased to14.33/13.22, but meanRGB fell by12; blade-base reflectance is multiplied1.5 to balance that range. Texture calibration, weather/loading/disposal, geometry count, ground placement, and global lighting are unchanged. Parent owns and independently updated bed exclusions during this round.

Final balanced capture renders/ground-r7-balanced/photo12.png captured native3840x2880. Zero page exceptions,293/293models loaded, front unchanged482260 triangles xor166137678 sum3351587226. Metrics in ground-r7-balanced-metrics.json. No photo-pass claimed; repeated polygonal grass remains visible in native inspection.
