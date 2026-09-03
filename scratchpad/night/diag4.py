import json
from playwright.sync_api import sync_playwright
JS = """
async () => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all'); await new Promise(r => setTimeout(r, 1500));
  const shell = house.getShellRoot(); const rows = [];
  shell.traverse((o) => { if (!o.isMesh) return; for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {
    rows.push({ mesh: o.name, mat: m.name, type: m.type, color: m.color?.getHexString(), emissive: m.emissive?.getHexString(), ei: m.emissiveIntensity, transparent: m.transparent, opacity: m.opacity, metal: m.metalness, rough: m.roughness, map: !!m.map, transmission: m.transmission, envI: m.envMapIntensity, tris: (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3 }); } });
  // which mesh/material is at the shell window glass (front, z ~26.5 and 29.4)?
  const rc = new THREE.Raycaster(); const hits = [];
  for (const [x, y] of [[16, 19.5], [16, 22.5], [13, 20], [3, 20], [-3, 20], [4, 6], [-3, 6]]) { rc.set(new THREE.Vector3(x, y, 36), new THREE.Vector3(0, 0, -1)); const h = rc.intersectObject(shell, true)[0]; hits.push([x, y, h ? [h.object.name, h.object.material?.name, +h.point.z.toFixed(2)] : null]); }
  const drive = []; scene = window.__scene3d.scene;
  rc.set(new THREE.Vector3(30, 5, 60), new THREE.Vector3(0, -1, 0));
  for (const h of rc.intersectObjects(scene.children, true).filter(h => { let o = h.object; while (o) { if (!o.visible) return false; o = o.parent; } return true; }).slice(0, 4)) { const m = h.object.material; drive.push({ name: h.object.name, y: +h.point.y.toFixed(2), rough: m.roughness, metal: m.metalness, type: m.type, col: m.color?.getHexString(), transparent: m.transparent, opacity: m.opacity, blending: m.blending }); }
  return { rows, hits, drive };
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 600})
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(4000)
    r = pg.evaluate(JS); b.close()
for row in r["rows"]: print(row)
print("window hits:", r["hits"]); print("drive stack:", r["drive"])
