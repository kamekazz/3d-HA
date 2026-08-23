import argparse, os
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:5000"
JS = """
async ({ box, nx, nz }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1200));
  const shell = house.getShellRoot();
  shell.updateWorldMatrix(true, true);
  const rc = new THREE.Raycaster(); const dir = new THREE.Vector3(0,-1,0);
  const rows = [];
  for (let j = 0; j < nz; j++) {
    const z = box[1] + (box[3]-box[1]) * j / (nz-1);
    const row = [];
    for (let i = 0; i < nx; i++) {
      const x = box[0] + (box[2]-box[0]) * i / (nx-1);
      rc.set(new THREE.Vector3(x, 45, z), dir);
      const h = rc.intersectObject(shell, true);
      row.push(h.length ? +h[0].point.y.toFixed(2) : null);
    }
    rows.push([+z.toFixed(1), row]);
  }
  return rows;
}
"""
p = argparse.ArgumentParser(); p.add_argument("--box", required=True)
p.add_argument("--nx", type=int, default=40); p.add_argument("--nz", type=int, default=24)
a = p.parse_args(); box=[float(v) for v in a.box.split(",")]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width":900,"height":600})
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(3500)
    rows = pg.evaluate(JS, {"box":box,"nx":a.nx,"nz":a.nz}); b.close()
def sym(v):
    if v is None: return '.'
    if v < 0.4: return '_'
    if v < 1.1: return 'a'
    if v < 1.9: return 'b'
    if v < 2.4: return 'H'
    return '#'
print("x from %.1f to %.1f  (%d cols)" % (box[0], box[2], a.nx))
for z,row in rows: print("z%7.1f  %s" % (z, "".join(sym(v) for v in row)))
