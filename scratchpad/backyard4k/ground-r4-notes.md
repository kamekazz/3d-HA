Rear turf material round 4

Source scope: addRearGroundDetail in frontend/js/environment.js only. Uses the parent-provided CC0 cgbookcase Grass01 assets (albedo 157342 bytes plus normal 100014 bytes, total 257356 bytes), attribution retained in frontend/textures/backyard/ATTRIBUTION.md. Albedo repeats at 1.8ft; normal is DirectX and uses normalScale(.38,-.38). A measured species tint reduces the source moss yellow cast while preserving the actual texture detail.

The 260000 modeled bent tufts, clover, fallen leaves, deck and planting exclusions, and shared shoreline ramp are retained. No reference photo projection, fixed tree-shadow painting, global lighting, global weather, or front-yard edits. The source canopy-light helper composes the material snow and grass normal hooks.

Lifecycle integration uses the default Three TextureLoader during yard assembly so the existing boot loader gate waits. Each map is disposed with its material. Async callbacks reject a disposed material or replaced yard. Failed images keep the procedural fallback. Snow blends the combined albedo/vertex colour toward neutral snow after texture sampling, preventing green snow; wetness darkens reflectance and slightly reduces roughness.

Browser integration probe passed: boot done with 667/667 manager items loaded, actual albedo768 and normal512 dimensions, normal Y negative, two map disposal events on rebuild, new maps loaded after rebuild, and clean CanvasTexture fallback after forced texture request failures. No page exceptions. Snow screenshot crop RGB233/234/235, wet darker than dry. Probe JSON and images: renders/ground-material-probe.

Turf tint calibrated under canonical sunny elevation42 azimuth335, with physically motivated canopy sky occlusion supplied by the light builder. Ground material itself has no camera or light direction-specific colour field.

Last source tint is a4abd9; final ground-r4-final/photo12 captured at native 3840x2880 with zero page exceptions and all293 models loaded. Front remains482260 triangles xor166137678 sum3351587226. Final matched grass crop mean RGB [125.69778706 138.80300731 103.53642953]. Independent photo critic required. The rendered grass still has obvious procedural tuft repetition at native resolution; no photo-pass claim.
