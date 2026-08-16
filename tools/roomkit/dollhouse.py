"""Shoot the WHOLE HOUSE as one dollhouse — every floor stacked, walls cut away.

The app has two views and neither is this: House mode ('all') hides the rooms and
shows the exterior shell, and single-floor mode shows one storey. This forces the
third: all floors visible at once with the shell hidden, which is what a real
dollhouse looks like.

    python -m roomkit.dollhouse --out house.png
    python -m roomkit.dollhouse --az 35 --el 38 --out house_ne.png

Nothing here mutates the app — it only toggles visibility in the page for the
duration of the screenshot.
"""

import argparse
import json
import math
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

SETUP = """
async ({ pose, light, markers }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  const sceneMod = await import('/js/scene.js');
  const { camera, controls, renderer, scene } = window.__scene3d;

  // 'all' is House mode: it hides every room and shows the shell. Take that
  // view, then invert it — shell off, all floors on — for the dollhouse.
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 900));
  const shell = house.getShellRoot();
  if (shell) shell.visible = false;
  for (const [, group] of house.floorGroups) {
    group.visible = true;
    for (const child of group.children) {
      if (child.userData.kind === 'device' || child.isSprite) {
        child.visible = !!markers;
      } else {
        child.visible = true;      // rooms + furniture, hidden by House mode
      }
    }
  }
  for (const g of house.stairGroups || []) g.visible = true;

  if (light) window.__daylight?.simulate(light);

  camera.fov = pose.fov || 40;
  camera.near = 0.05;
  camera.updateProjectionMatrix();
  const unclamp = () => {
    controls.minDistance = 0.05; controls.maxDistance = 1e6;
    controls.enableDamping = false; controls.enablePan = false;
    controls.enableRotate = false;
  };
  unclamp();
  const pos = { x: pose.pos[0], y: pose.pos[1], z: pose.pos[2] };
  const tgt = { x: pose.target[0], y: pose.target[1], z: pose.target[2] };
  sceneMod.flyTo(pos, tgt);
  for (let i = 0; i < 240; i++) {
    await new Promise(r => requestAnimationFrame(r));
    const d = Math.hypot(camera.position.x - pos.x, camera.position.y - pos.y,
                         camera.position.z - pos.z);
    const dt = Math.hypot(controls.target.x - tgt.x, controls.target.y - tgt.y,
                          controls.target.z - tgt.z);
    if (d < 0.02 && dt < 0.02) break;
  }
  unclamp();
  for (const el of document.querySelectorAll('body > *:not(#scene-container)')) {
    el.style.display = 'none';
  }
  renderer.render(scene, camera);
  return { rooms: house.roomMeshes.size, shellHidden: !!shell };
}
"""


def house_bounds():
    import urllib.request
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        h = json.loads(r.read().decode())
    xs, zs, top = [], [], 0.0
    y = 0.0
    for f in sorted(h["floors"], key=lambda f: f["level"]):
        rooms = [r for r in f.get("rooms", []) if r["height"] > 2.0]
        for r in rooms:
            fp = r["footprint"]
            xs += [fp["x"], fp["x"] + fp["width"]]
            zs += [fp["z"], fp["z"] + fp["depth"]]
            top = max(top, y + r["height"])
        y += f.get("floor_height") or 10.0
    return min(xs), max(xs), min(zs), max(zs), top


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--az", type=float, default=-35.0,
                   help="degrees off south; negative looks from the west side")
    p.add_argument("--el", type=float, default=34.0, help="elevation degrees")
    p.add_argument("--fov", type=float, default=40.0)
    p.add_argument("--size", default="1600,1100")
    p.add_argument("--night", action="store_true")
    p.add_argument("--markers", action="store_true")
    a = p.parse_args()

    x0, x1, z0, z1, top = house_bounds()
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    span = max(x1 - x0, z1 - z0)
    el, az = math.radians(a.el), math.radians(a.az)
    dist = span * 1.5 + top
    w, hgt = (int(v) for v in a.size.split(","))
    pose = {
        "pos": [cx + dist * math.cos(el) * math.sin(az),
                top * 0.5 + dist * math.sin(el),
                cz + dist * math.cos(el) * math.cos(az)],
        "target": [cx, top * 0.34, cz],
        "fov": a.fov, "size": [w, hgt],
    }
    light = None if a.night else {"elevation": 46, "azimuth": 150, "condition": "sunny"}

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": w, "height": hgt},
                                device_scale_factor=1)
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(3000)
        # let every GLB resolve before the shot, or half the furniture is missing
        for _ in range(60):
            st = page.evaluate("""async () => {
                const o = await import('/js/objects.js');
                const r = [...o.objects3d.values()];
                return { t: r.length, l: r.filter(x => x.children.length > 0).length };
            }""")
            if st["t"] and st["l"] >= st["t"]:
                break
            page.wait_for_timeout(400)
        info = page.evaluate(SETUP, {"pose": pose, "light": light,
                                     "markers": a.markers})
        page.wait_for_timeout(900)
        page.evaluate(SETUP, {"pose": pose, "light": light, "markers": a.markers})
        page.wait_for_timeout(400)
        page.screenshot(path=a.out)
        browser.close()
    if errs:
        print("page errors:", errs[:3], file=sys.stderr)
    print(json.dumps({"out": a.out, **info, "pose": pose}))


if __name__ == "__main__":
    main()
