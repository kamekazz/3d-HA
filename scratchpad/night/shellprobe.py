"""Pixel -> world probe restricted to the house shell (+ its bbox per hit)."""
import json, os, sys
from playwright.sync_api import sync_playwright
BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
SETUP = open(os.path.join(os.path.dirname(__file__), "..", "ext", "probe.py")).read().split('SETUP = """')[1].split('"""')[0]
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
    const hits = rc.intersectObject(shell, true);
    const h = hits[0];
    out.push({ px: [sx, sy], hit: h ? { name: h.object.name, pt: [+h.point.x.toFixed(2), +h.point.y.toFixed(2), +h.point.z.toFixed(2)],
      n: h.face ? [+h.face.normal.x.toFixed(2), +h.face.normal.y.toFixed(2), +h.face.normal.z.toFixed(2)] : null } : null });
  }
  return out;
}
"""
pose = json.loads(sys.argv[1]); px = [[float(v) for v in t.split(",")] for t in sys.argv[2].split()]
w, h = pose.get("size", [900, 1200])
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    pg = b.new_page(viewport={"width": int(w), "height": int(h)}, device_scale_factor=1)
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(3500)
    pg.evaluate(SETUP, {"pose": pose, "level": "all"})
    pg.wait_for_timeout(1500)
    res = pg.evaluate(RAY, {"px": px, "size": [w, h]})
    b.close()
for r in res: print(r["px"], r["hit"])
