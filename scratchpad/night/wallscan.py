"""Horizontal raycast (-z) grid against the shell's front wall: prints hit depth
and material colour per cell so windows/shutters/doors can be located."""
import json, os, sys
from playwright.sync_api import sync_playwright
BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
JS = """
async ({ x0, x1, y0, y1, step, zfrom }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1200));
  const shell = house.getShellRoot();
  shell.updateWorldMatrix(true, true);
  const rc = new THREE.Raycaster(); const dir = new THREE.Vector3(0, 0, -1);
  const rows = [];
  for (let y = y1; y >= y0; y -= step) {
    const row = [];
    for (let x = x0; x <= x1; x += step) {
      rc.set(new THREE.Vector3(x, y, zfrom), dir);
      const h = rc.intersectObject(shell, true)[0];
      row.push(h ? [+h.point.z.toFixed(2), h.object.material?.color?.getHexString?.() || '?', h.object.name] : null);
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
json.dump(rows, open(sys.argv[2], "w"))
cols = {}
def sym(v):
    if v is None: return ' '
    z, c, n = v
    key = c
    if key not in cols: cols[key] = chr(ord('a') + len(cols)) if len(cols) < 26 else chr(ord('A') + len(cols) - 26)
    return cols[key]
for y, row in rows: print("%6.2f %s" % (y, "".join(sym(v) for v in row)))
print(cols)
# depth summary per row
for y, row in rows[::4]:
    print("%6.2f" % y, " ".join(("%5.1f" % v[0]) if v else "  -  " for v in row[::4]))
