"""Downward raycast grid against the SHELL only, reporting cells whose surface
sits between --ymin and --ymax. Finds baked shell props that stand proud of
the terrain (leftover fence rails, kerbs) and prints their world bbox."""
import argparse, json, os
from playwright.sync_api import sync_playwright
BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
JS = """
async ({ box, step, ymin, ymax }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1200));
  const shell = house.getShellRoot();
  if (!shell) return { err: 'no shell' };
  shell.updateWorldMatrix(true, true);
  const rc = new THREE.Raycaster();
  const dir = new THREE.Vector3(0, -1, 0);
  const hits = [];
  for (let x = box[0]; x <= box[2]; x += step) {
    for (let z = box[1]; z <= box[3]; z += step) {
      rc.set(new THREE.Vector3(x, 40, z), dir);
      const h = rc.intersectObject(shell, true);
      if (!h.length) continue;
      const y = h[0].point.y;
      if (y >= ymin && y <= ymax) hits.push([+x.toFixed(2), +y.toFixed(3), +z.toFixed(2)]);
    }
  }
  const bb = hits.length ? hits.reduce((a, p) => [
    Math.min(a[0], p[0]), Math.min(a[1], p[1]), Math.min(a[2], p[2]),
    Math.max(a[3], p[0]), Math.max(a[4], p[1]), Math.max(a[5], p[2])],
    [1e9, 1e9, 1e9, -1e9, -1e9, -1e9]) : null;
  return { n: hits.length, bbox: bb, sample: hits.slice(0, 12) };
}
"""
p = argparse.ArgumentParser()
p.add_argument("--box", required=True, help="x0,z0,x1,z1")
p.add_argument("--step", type=float, default=0.25)
p.add_argument("--ymin", type=float, default=0.4)
p.add_argument("--ymax", type=float, default=3.0)
a = p.parse_args()
box = [float(v) for v in a.box.split(",")]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 600})
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(3500)
    print(json.dumps(pg.evaluate(JS, {"box": box, "step": a.step,
                                      "ymin": a.ymin, "ymax": a.ymax}), indent=1))
    b.close()
