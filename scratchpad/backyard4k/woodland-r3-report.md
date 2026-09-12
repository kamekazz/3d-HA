# Woodland round 3

Scope: `addRearLakeDetail`, plus the explicitly approved rearBark-only `bucketMesh` split. No ordinary/front bucket material changes. Existing planar water reflection, cleanup and shoreline levels remain. Bark assets supplied by root are local CC0 Poly Haven Jolcham Oak Bark 01 albedo and OpenGL normal, with attribution in the texture directory.

Changes:
- Continuous swept, curved trunks and branch scaffolds with variable taper, asymmetric forks, relief and low buttress roots. Correct outward winding on swept surfaces.
- Physically scaled bark UVs: tile is 3.28084 ft wide × 6.56168 ft high. Bark stays in recorded geometry buckets so trees retain per-item edits. A yard-owned material disposes both textures when disposed.
- Ovate folded leaves have six outline vertices and a raised lighter center; coherent spray-level colour and arbitrary 3D rotations replace highly independent triangular confetti.
- Branch/crown joins and hanging levels vary. Broad lateral crowns reach over the bank, western undergrowth is lower, and distant woodland is denser. Geometry `userData.rearFoliage` remains intact for rear indirect-light occlusion.

Capture chronology:
- `woodland-r3`: diagnostic, excessive open sky; captured before outward sweep winding correction. Zero JS errors and original front fingerprint.
- `woodland-r3-final`: second diagnostic; bark corrected and distant bank improved, but crown still too open. Zero JS errors and original front fingerprint.
- `woodland-r3-covered`: final candidate, denser variable-height lower crowns. Native 3840×2880 capture; final checks to be appended.

No independent critic has judged round 3. Bark now has real surface detail, but leaf underside shading and broad simplified shore/water shapes still expose the procedural scene; this is not a photoreal claim.

Final material refinement:
- The explicitly approved rearFoliage material hook adds 22% opposite-face directional diffuse and 28% opposite-face hemisphere diffuse. Both depend on real scene irradiance (the directional term uses the shadow-attenuated light colour). No extra light, emissive fill or global normal/light changes. Exact Three.js 0.160.0 diffuse marker was verified against the app's CDN shader source.
- Curved leaf surfaces now supply smooth analytic normals. Leaf colour was calibrated from excessively dark HSL .185–.240 to .265–.320 after native crop inspection.
- `woodland-r3-thinleaf` is the pre-albedo-calibration diagnostic; zero shader/JS errors, 293/293 models, front checksum unchanged. Render info: 15 calls / 8,380,779 triangles with reflection.
- **Use `woodland-r3-review` for the fresh blind critic**; all prior R3 folders are diagnostic.

Final verification: personally inspected `woodland-r3-review/photo11-preview.jpg` and the native crop `photo11-native.jpg`, from native 3840×2880 PNG. 293/293 models loaded, zero JavaScript/shader errors, zero failed network requests. Existing unrelated API/camera responses still log 502/503. Shadows enabled/type 2. Exact front fingerprint remains **482260 triangles, xor 166137678, sum 3351587226**. Syntax check passes. Final render info is 15 calls / 8,380,779 triangles including reflection.

Largest remaining gap: the near crowns still expose too much center sky and too broad an uninterrupted water window compared with reference 11's dense, deeply layered woodland. Native leaf silhouettes/materials also remain visibly geometric. The bark and forks are a meaningful improvement over smooth poles, but this is not a photographic match. Builder is now done editing and ready for independent critique.
