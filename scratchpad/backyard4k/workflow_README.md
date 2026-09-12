# Rear exterior capture workflow

Local app: http://127.0.0.1:5001/

Live progress: http://127.0.0.1:8765/progress.html

The existing Python 3.12 venv launcher is stale. `workflow_server.py` uses the
bundled Python runtime and appends the venv's retained pure-Python dependencies.
Servers were launched hidden. Their owned process IDs are in `workflow_servers.json`.
No existing server was killed. No app source or database was edited by this workflow.

## Capture

From repository root:

```
node scratchpad/backyard4k/workflow_capture.cjs baseline rear_overview rear_elevation
node scratchpad/backyard4k/workflow_capture.cjs round1 photo14 photo11 --pose-file scratchpad/backyard4k/workflow_matched_poses.json
```

Run the capture with network access (exec command `require_escalated`). The unmodified
app imports Three.js r160 and Socket.IO from jsDelivr; sandbox Chrome reports
`ERR_NETWORK_ACCESS_DENIED` and cannot initialize the scene. Scoped escalation was
approved and successfully rendered the real app.

`workflow_poses.json` is native 3840x2160. `workflow_matched_poses.json` uses native
3840x2880 for 4:3 references, and 2880x3840 for portrait 08. These initial photo poses
are estimates and require visual calibration, especially porch 02/14. Rear overview
and old deck poses reproduce the prior room3 camera documentation exactly.

The harness extracts the current `SETUP_JS` and `READY_JS` from roomkit/shot.py, flies
through the app camera controls twice, clears stage view offset, sets House level,
disables markers and cutaway, simulates sunny daylight at azimuth335/elevation42.
No exterior lights are forced. It waits for all 293 room object roots to load.

For every image, an adjacent JSON records requested and actual camera, render size,
projection, page errors, console errors, failed requests, renderer draw counts,
actual shadow map state, measured building box, front yard item descriptors, and
an order-independent front geometry checksum. The checksum considers only environment
triangles whose three world vertices have z>=0, hashes positions/normals/colors/UVs
and world matrix, and reports triangle count, xor and sum. Check this exact signature
before/after for front preservation; it does not audit materials or effects of rear
objects casting shadows onto the front.

Live progress polls progress.json every two seconds. The capture updates renders,
round and timestamp while preserving other fields. Parent may update status, details,
notes and references (map pose name to references/NN.png). Avoid concurrent captures
sharing the same round/pose and concurrent progress writes.

## Blind comparison

Use the parent's `blind_pair.py` to downsample render to the reference's native
dimensions without cropping. Give fresh critic only the neutral pair. Keep key.json
private until verdict. Never imply these 600x450 photographs have native 4K detail.

The process is the real-app render; references never enter render pixels. Optional
small previews are for image-tool size limits and are not native measurement inputs.
