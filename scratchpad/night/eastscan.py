import json, os, sys
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:5000"
JS = """
async ({ z0, z1, y0, y1, step, xfrom }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all'); await new Promise(r => setTimeout(r, 1200));
  const shell = house.getShellRoot(); shell.updateWorldMatrix(true, true);
  const rc = new THREE.Raycaster(); const dir = new THREE.Vector3(-1, 0, 0);
  const rows = [];
  for (let y = y1; y >= y0; y -= step) {
    const row = [];
    for (let z = z1; z >= z0; z -= step) {
      rc.set(new THREE.Vector3(xfrom, y, z), dir);
      const h = rc.intersectObject(shell, true)[0];
      row.push(h ? +h.point.x.toFixed(2) : null);
    }
    rows.push([+y.toFixed(2), row]);
  }
  return rows;
}
"""
a = json.loads(sys.argv[1])
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 600})
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(4000)
    rows = pg.evaluate(JS, a); b.close()
zs = [a["z1"] - a["step"] * i for i in range(len(rows[0][1]))]
print("       " + "".join("%6.1f" % z for z in zs))
for y, row in rows: print("%6.2f " % y + "".join(("%6.1f" % v) if v is not None else "   -  " for v in row))
