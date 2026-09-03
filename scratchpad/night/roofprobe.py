"""Downward raycast heightmap against the SHELL only, dumped as JSON so the roof
edges (eaves / rakes) can be located numerically. Also lists the shell's mesh
names + bboxes so a roof mesh can be found by name if there is one."""
import argparse, json, os
from playwright.sync_api import sync_playwright
BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
JS = """
async ({ box, step }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1200));
  const shell = house.getShellRoot();
  if (!shell) return { err: 'no shell' };
  shell.updateWorldMatrix(true, true);
  const meshes = [];
  shell.traverse((o) => {
    if (!o.isMesh) return;
    const bb = new THREE.Box3().setFromObject(o);
    meshes.push({ name: o.name, tris: (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3,
      box: [bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z].map(v => +v.toFixed(2)),
      color: o.material?.color ? '#' + o.material.color.getHexString() : null });
  });
  const rc = new THREE.Raycaster(); const dir = new THREE.Vector3(0, -1, 0);
  const xs = [], zs = [], rows = [];
  for (let x = box[0]; x <= box[2] + 1e-6; x += step) xs.push(+x.toFixed(2));
  for (let z = box[1]; z <= box[3] + 1e-6; z += step) zs.push(+z.toFixed(2));
  for (const z of zs) {
    const row = [];
    for (const x of xs) {
      rc.set(new THREE.Vector3(x, 60, z), dir);
      const h = rc.intersectObject(shell, true);
      row.push(h.length ? [+h[0].point.y.toFixed(2), h[0].object.name] : null);
    }
    rows.push(row);
  }
  return { xs, zs, rows, meshes };
}
"""
p = argparse.ArgumentParser(); p.add_argument("--box", required=True)
p.add_argument("--step", type=float, default=0.5); p.add_argument("--out", required=True)
a = p.parse_args(); box = [float(v) for v in a.box.split(",")]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 600})
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(4000)
    res = pg.evaluate(JS, {"box": box, "step": a.step}); b.close()
json.dump(res, open(a.out, "w"))
print("meshes:")
for m in res["meshes"]: print("  %-30s %7d %s %s" % (m["name"][:30], m["tris"], m["box"], m["color"]))
