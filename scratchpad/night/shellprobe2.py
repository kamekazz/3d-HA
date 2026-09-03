"""Pixel -> world probe against the shell only, using shot.py's exact pose setup."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from roomkit.shot import SETUP_JS, load_poses
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:5000"
RAY = """
async ({ px, size }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  const { camera } = window.__scene3d;
  const shell = house.getShellRoot();
  const rc = new THREE.Raycaster();
  const out = [];
  for (const [sx, sy] of px) {
    rc.setFromCamera(new THREE.Vector2(sx / size[0] * 2 - 1, -(sy / size[1] * 2 - 1)), camera);
    const h = rc.intersectObject(shell, true)[0];
    out.push([sx, sy, h ? [h.object.name, +h.point.x.toFixed(2), +h.point.y.toFixed(2), +h.point.z.toFixed(2)] : null]);
  }
  return out;
}
"""
pose = load_poses()[sys.argv[1]]
px = [[float(v) for v in t.split(",")] for t in sys.argv[2].split()]
w, h = pose.get("size", [900, 1200])
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(2500)
    args = {"pose": pose, "level": "all", "light": {"elevation": -18, "azimuth": 0, "condition": "clear-night"}, "markers": False, "cutaway": True}
    pg.evaluate(SETUP_JS, args); pg.wait_for_timeout(2500); pg.evaluate(SETUP_JS, args); pg.wait_for_timeout(300)
    res = pg.evaluate(RAY, {"px": px, "size": [w, h]})
    b.close()
for r in res: print(r)
