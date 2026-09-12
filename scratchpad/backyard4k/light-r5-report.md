# Rear light R5 diagnostic

The causal follow-up in `light-r5-causal-report.md` supersedes this initial report's unresolved blocker/solar conclusions. It identifies near-tree shadows and finds geometry-supported195/30 illumination that separates the two lawn regions. Production remains unchanged.

No production source changed. `addRearLightDetail` and its root-owned contact transforms are preserved. The canonical sun stays sunny335°/42°. Read roomkit SKILL, RESUME, ROOM-BRIEF, STYLE-BAR, frontend CLAUDE, actual lighting and rear-contact source, references09/12 and prior R2 solar evidence.

Ran `light-r5-diagnostic.cjs` in the parent's serialized GPU slot. One ephemeral headless Chrome page; exact canonical camera positions, targets and FOVs, reduced1200×900 diagnostic capture. All293/293 object roots loaded. Browser closed in finally and process exited0 before releasing slot. No page exceptions or shader-error messages. Four resource HTTP502/503 console errors occurred; the first run did not record their URLs. These are diagnostics, not native-resolution final critic evidence.

## Main finding: indoor environment IBL overwhelms the shaded lawn

Global `scene.js getEnvIntensity()` is1.15, hemisphere0.994, sun1.482 at canonical335/42. The current sun already contributes effectively zero to the photo09 foreground ROI. Changing its direction cannot remove the dominant indirect contribution.

All means below are sRGB bytes after the normal renderer tone mapping. Component values are not linearly additive in this display space. The1200×900 canvas was downsampled by Canvas2D to600×450; foreground ROI is[60,365,540,450], siding[280,143,360,171], middle lawn[170,340,440,375]. Reference09 is the actual600×450 image sampled at the same coordinates. The facade cameras are only approximately registered, so exact siding means are secondary to the component ablation.

| photo09 illumination | Foreground RGB | Upper siding RGB |
|---|---|---|
| Reference09 |37.66 /48.45 /33.49 |147.91 /159.51 /175.19 |
| Canonical335/42 |121.50 /138.24 /94.82 |158.72 /162.70 /165.95 |
| Sun disabled |121.50 /138.24 /94.82 |103.40 /112.67 /124.33 |
| IBL and hemi disabled |0.00 /0.00 /0.00 |115.87 /115.32 /109.86 |
| IBL disabled |36.39 /50.49 /28.25 |142.11 /145.94 /149.17 |
| Hemi disabled |105.92 /120.66 /78.50 |139.04 /140.23 /137.63 |
| South180/25, all terms |120.91 /137.93 /94.74 |96.35 /107.21 /118.89 |
| South155/20, all terms |123.48 /139.92 /96.49 |94.25 /105.58 /117.26 |

The IBL-disabled diagnostic visibly recovers dark shaded grass while retaining a luminous sky. Southern low suns make the facade too dark and barely affect the grass. This confirms the earlier R2 ray evidence: the issue is not shadow-map coverage or disabled cast/receive flags. Existing roomkit comments explain why IBL was raised: its omnidirectional fill reduces indoor wall-to-wall differences. That is a global contract, not a rear-builder authorization to lower it.

At photo12, whole-lighting foreground is136.42/149.11/107.90 at335/42,134.56/147.85/106.70 at180/25,141.10/153.02/110.96 at155/20; reference same ROI is124.27/136.19/103.89. The ordinary source is much closer to this reference than photo09. No rear-wide indirect reduction is justified by one matching photo09 crop. In particular, the removed canopy AO must not be restored: it suppresses hemisphere and environment together, although the hemisphere alone already provides approximately the reference09 lawn level.

Artifacts: `renders/light-r5-diagnostic/*.png` and `probe.json`; the probe restores sun, hemisphere and material environment-map intensity immediately after every diagnostic render. No browser state was persisted and no geometry, light/weather/exposure configuration, sky dome or material production file was written.

## Photo12 regression gate completed

Parent granted a second serialized slot after porch and planting. `light-r5-diagnostic.cjs --photo12-components` ran one canonical1200×900 photo12 camera and five synchronous component renders. The browser closed in finally and process exited0; slot released before reporting.293/293 objects loaded, no page/shader errors. This run records the HTTP URLs: `/api/ha/structure`503, `/api/ha/states`502, `/api/ha/calendar?days=180`502; they are HA backend responses, not rendering assets. Whole photo12 means are exactly equal to the first run.

| photo12 canonical335/42 component | Foreground RGB | Middle lawn RGB |
|---|---|---|
| Reference12 |124.27 /136.19 /103.89 |131.50 /146.72 /109.27 |
| Whole |136.42 /149.11 /107.90 |137.14 /151.05 /109.92 |
| Sun disabled |136.41 /149.11 /107.89 |137.14 /151.05 /109.92 |
| IBL and hemi disabled |0.01 /0.01 /0.00 |0.00 /0.00 /0.00 |
| IBL disabled |34.18 /45.49 /25.75 |33.32 /45.36 /25.77 |
| Hemi disabled |125.16 /136.97 /95.25 |126.16 /139.26 /97.50 |

Inspected the IBL-disabled photo12: the lawn becomes uniformly dark, clearly unlike its bright reference. A uniform rear-ground environment-map multiplier would fix photo09 by breaking photo12. A multiplier on all indirect illumination would be worse, since it would also remove the useful existing hemisphere term. Applying it only to the grass rather than workstation metals avoids unrelated material changes, but does not resolve the two-photo contradiction.

**Decision: retain current source unchanged. No rear-only light adjustment or alternative sun preset is promoted.** Both currently visible lawn ROIs are effectively entirely indirect-lit under335/42, whereas their references call for very different light levels. A physically supported solution needs to establish the correct sun/canopy visibility at the bright photo12 lawn, or independently establish camera exposure differences; a camera-dependent field, fixed painted shadow, position-based albedo compensation, or reinstated canopy AO would conceal the mismatch. This experiment does not yet identify which actual caster removes the direct term at each photo12 lawn point. Root may investigate that geometry/capture relationship next; production global lighting remains outside this builder's scope.

Final additional evidence lives in `renders/light-r5-photo12-components/*.png` and `probe.json`. No new final critic round is warranted for lighting because this diagnostic intentionally made no production change.
