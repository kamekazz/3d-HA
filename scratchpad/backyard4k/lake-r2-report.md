# Lake / shoreline round 2

Implementation scope is `addRearLakeDetail` only in `frontend/js/environment.js`, plus scratchpad artifacts. The existing `rearSite.yardN = L.yardN - 20` remains in the parent's integration, so shoreline and every lake tree preserve the expanded lawn.

## Camera registration

`lake_r2_poses.json` is independent of the shared master poses. Reference 11 is photographed standing on grass immediately beside the gravel and pitched down: position `[16,5.7,-82]`, target `[16,-2,-108]`, vertical field of view 65, native 3840×2880. Reference 12 is `[-2,5.7,-77]` towards `[26,3.1,-111]`, FOV 68. These remain visual registrations, not a solved photogrammetric camera.

## Changes

- Thirteen uneven mature tree positions, diameters, lean and bank offsets, with continuous tapered curved main stems and branches attached at differing heights. Low western boughs and north-reaching hanging boughs close the woodland opening with actual arbitrarily rotated folded leaves. The material uses the existing rear foliage bucket and casts/receives shadows.
- Own local gravel material at an approximately one-inch aggregate scale, mixed smaller rounded cobbles, raised gravel .72 ft above `L.lo`, and a sloped apron. Ground builder coordinated its slope to this height; water stays at `L.lo+.018`.
- A 1024×768 planar reflection render target shows actual scene geometry through a mirrored camera with oblique clipping. Existing MeshStandardMaterial lighting remains. Updates happen inside the water mesh's `onBeforeRender` (maximum once/160ms while moving, once/2s stationary), without a global frame callback. Render target, XR, shadow auto-update and viewport are restored. The target is disposed with the material; gravel texture is disposed with its material.
- Two black path-light housings and a hanging feeder from reference 11; geometry only, no emitted light or HA state change. Fallen gravel leaves.

## Capture chronology and invalidation

- `lake-r2-camera/photo11` is a valid camera check before the new geometry, with baseline front fingerprint.
- `lake-r2/photo11` and `photo12` were valid geometry checks, but the canopy was too low and the leaves too coarse.
- `lake-r2-final/photo11` and `photo12` were valid checks after reducing leaf size; the skyline reopened too much.
- **`lake-r2-verified` is INVALID.** A continuous-stem refinement passed syntax but fed numeric arrays to CatmullRomCurve3. Diagnostic capture caught the runtime exception / partial scene. It was corrected by constructing Vector3 points, and captures restarted as `lake-r2-complete`. Never present `lake-r2-verified` as evidence of success.

No independent critic has judged round 2. Matching the reference photography is not claimed.

## Final self-inspection and checks

`lake-r2-complete/photo11.png` and `photo12.png` are both valid native **3840×2880** captures. Personally inspected full-image viewing reductions and native-resolution crops from each. Both loaded **293/293** models, report **zero JavaScript errors**, retain shadow maps enabled/type 2, and preserve the exact baseline front geometry fingerprint: **482260 triangles, xor 166137678, sum 3351587226**. `node --check frontend/js/environment.js` passes. Remaining console messages are existing failed 502/503 API/camera resources, with no shader error.

The overhead canopy is now connected, actual tree reflections are visible, the curb is smaller/rounder, and the ground-to-gravel slope joins cleanly. Photo12 shows the 20-foot lawn expansion and receding shoreline across a second viewpoint.

Still visibly short of the photograph: the lower water opening remains too continuous and unobstructed on the left; branching and bark still look procedural; leaf silhouettes remain angular in native crops; gravel texture is overly even; water ripple distortion is visibly regular and the 1024-pixel reflection is softer than the native 4K image. A final photo11 capture reports 15 calls / 6,343,046 triangles when the reflection pass runs (the reflection renders actual scene geometry, so this includes the additional pass). This is not a photoreal pass and requires a fresh independent critic.

The builder is done editing. Use **lake-r2-complete** for the new blind comparison; previous rounds are diagnostics.
