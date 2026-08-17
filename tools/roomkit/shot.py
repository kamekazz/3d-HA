"""Screenshot the running app from a fixed camera pose.

This is the critic's eyes: every comparison against the reference photo has to be
taken from the same viewpoint, so poses live in poses.json and are addressed by
name rather than retyped per run.

    python -m roomkit.shot --pose ref --out shots/round3.png

The app must already be running (http://127.0.0.1:5000). Uses the installed
Chrome, so nothing is downloaded.
"""

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
POSES = os.path.join(os.path.dirname(__file__), "poses.json")

# Level 2 is the second floor; its slab sits at Y=18 (8 ft basement + 10 ft
# first floor). Every pose Y below is absolute world height, so eye level in
# this room is 18 + ~5.5.
DEFAULT_LEVEL = 2


def load_poses():
    with open(POSES) as fh:
        return json.load(fh)


# Setting camera.position directly does not stick: floorview.js issues its own
# fly-to on levelChanged, and scene.js's render loop owns the camera while a
# pose tween is live (and afterwards lerps distance back toward zoomTarget).
# So we go through the same flyTo() the app uses, wait for it to converge --
# which hands the camera back and adopts our distance as the zoom target --
# and only then unclamp OrbitControls so an interior pose is not pushed back
# out to the dollhouse framing.
SETUP_JS = """
async ({ pose, level, light, markers }) => {
  const house = await import('/js/house.js');
  const sceneMod = await import('/js/scene.js');
  const { camera, controls, renderer, scene } = window.__scene3d;

  house.setLevel(level);
  await new Promise(r => setTimeout(r, 900));   // let floorview issue its fly-to

  if (light) window.__daylight?.simulate(light);

  camera.fov = pose.fov || 70;
  camera.near = 0.05;
  camera.updateProjectionMatrix();

  // Unclamp before the flight, not just after: MIN_ZOOM (10 ft) would shove a
  // close interior pose back out along the view ray the moment the tween ends,
  // and relaxing the limit afterwards does not undo that push.
  const unclamp = () => {
    controls.minDistance = 0.05;
    controls.maxDistance = 1e6;
    controls.enableDamping = false;
    controls.enablePan = false;
    controls.enableRotate = false;
  };
  unclamp();

  const pos = { x: pose.pos[0], y: pose.pos[1], z: pose.pos[2] };
  const tgt = { x: pose.target[0], y: pose.target[1], z: pose.target[2] };
  sceneMod.flyTo(pos, tgt);

  // Wait on the TARGET as well as the position. On a re-assert the camera is
  // already sitting at pose.pos, so a position-only test passes on frame 1 while
  // controls.target is still lerping away from floorview's recenterFloor goal --
  // the shot then comes out yawed off the pose by however little the tween got
  // done in the trailing wait, i.e. by however slow the scene is to draw.
  for (let i = 0; i < 200; i++) {
    await new Promise(r => requestAnimationFrame(r));
    const d = Math.hypot(camera.position.x - pos.x, camera.position.y - pos.y,
                         camera.position.z - pos.z);
    const t = Math.hypot(controls.target.x - tgt.x, controls.target.y - tgt.y,
                         controls.target.z - tgt.z);
    if (d < 0.02 && t < 0.02) break;
  }

  unclamp();

  // HA device markers are an app feature, not part of the room -- hide them so
  // a comparison against the photo is about the room and nothing else.
  if (!markers) {
    for (const group of house.floorGroups.values()) {
      for (const child of group.children) {
        if (child.userData.kind === 'device' || child.isSprite) child.visible = false;
      }
    }
  }

  for (const el of document.querySelectorAll('body > *:not(#scene-container)')) {
    el.style.display = 'none';
  }

  // walls no longer backface-cull; cutaway.js fades the near ones out over
  // ~0.2s, so a screenshot taken right after the flight catches them mid-fade
  window.__cutaway?.settle();
  renderer.render(scene, camera);
  const p = camera.position;
  return { rooms: house.roomMeshes.size, level,
           at: [+p.x.toFixed(2), +p.y.toFixed(2), +p.z.toFixed(2)] };
}
"""

# Furniture loads through GLTFLoader promises, so "network idle" is necessary
# but not sufficient -- poll the object roots until each has its model child.
READY_JS = """
async () => {
  const objects = await import('/js/objects.js');
  const roots = [...objects.objects3d.values()];
  return { total: roots.length, loaded: roots.filter(r => r.children.length > 0).length };
}
"""


def take(pose, out, level=DEFAULT_LEVEL, light=None, settle=1200, markers=False):
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    w, h = pose.get("size", [900, 1200])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # not networkidle: the SocketIO connection stays open, so idle never fires
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(2500)  # first house fetch + buildHouse

        info = page.evaluate(SETUP_JS, {"pose": pose, "level": level, "light": light,
                                        "markers": markers})

        for _ in range(40):
            st = page.evaluate(READY_JS)
            if st["total"] == 0 or st["loaded"] >= st["total"]:
                break
            page.wait_for_timeout(250)
        page.wait_for_timeout(settle)

        # re-assert the pose: async model loads can trigger a rebuild that
        # re-runs setLevel and its camera work
        page.evaluate(SETUP_JS, {"pose": pose, "level": level, "light": light,
                                        "markers": markers})
        page.wait_for_timeout(300)

        page.screenshot(path=out)
        browser.close()
    if errors:
        print("page errors:", errors[:3], file=sys.stderr)
    return {"out": out, **info}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pose", default="ref", help="name in poses.json")
    p.add_argument("--pose-json", help='inline pose, e.g. \'{"pos":[18,23,-5],'
                   '"target":[4,22,-16],"fov":70,"size":[900,1200]}\' -- use this '
                   "for one-off close-ups instead of editing poses.json, which "
                   "parallel agents would race on")
    p.add_argument("--out", required=True)
    # a string so "all" works: that is the app's House mode, which hides the
    # generated rooms and shows the whole-house shell GLB — the only way to
    # shoot the exterior
    p.add_argument("--level", default=str(DEFAULT_LEVEL),
                   help="floor level, or 'all' for the exterior shell view")
    p.add_argument("--day", action="store_true", help="force bright daylight")
    p.add_argument("--markers", action="store_true", help="keep HA device markers visible")
    p.add_argument("--settle", type=int, default=1200)
    a = p.parse_args()

    if a.pose_json:
        pose = json.loads(a.pose_json)
    else:
        poses = load_poses()
        if a.pose not in poses:
            raise SystemExit(f"unknown pose {a.pose!r}; have {sorted(poses)}")
        pose = poses[a.pose]
    level = a.level if a.level == "all" else int(a.level)
    light = {"elevation": 42, "azimuth": 155, "condition": "sunny"} if a.day else None
    print(json.dumps(take(pose, a.out, level, light, a.settle, a.markers)))


if __name__ == "__main__":
    sys.exit(main())
