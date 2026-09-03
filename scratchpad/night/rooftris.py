"""Dump the world-space triangles of the shell's roof meshes (few triangles,
so the eave/rake edges can be read off directly)."""
import json, os, sys
from playwright.sync_api import sync_playwright
BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
JS = """
async ({ names }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1200));
  const shell = house.getShellRoot();
  shell.updateWorldMatrix(true, true);
  const out = {};
  shell.traverse((o) => {
    if (!o.isMesh || !names.includes(o.name)) return;
    const g = o.geometry; const pos = g.attributes.position; const idx = g.index;
    const n = idx ? idx.count : pos.count;
    const tris = [];
    const v = new THREE.Vector3();
    for (let i = 0; i < n; i += 3) {
      const t = [];
      for (let k = 0; k < 3; k++) {
        const j = idx ? idx.getX(i + k) : i + k;
        v.fromBufferAttribute(pos, j).applyMatrix4(o.matrixWorld);
        t.push([+v.x.toFixed(3), +v.y.toFixed(3), +v.z.toFixed(3)]);
      }
      tris.push(t);
    }
    out[o.name] = tris;
  });
  return out;
}
"""
names = sys.argv[1].split(",")
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 600})
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(4000)
    res = pg.evaluate(JS, {"names": names}); b.close()
json.dump(res, open(sys.argv[2], "w"), indent=0)
for name, tris in res.items():
    print(name, len(tris), "tris")
    for t in tris: print("  ", t)
