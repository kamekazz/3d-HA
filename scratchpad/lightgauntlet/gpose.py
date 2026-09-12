import json
from playwright.sync_api import sync_playwright
JS = """
async () => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  const objects = await import('/js/objects.js');
  house.setLevel(1);
  await new Promise(r => setTimeout(r, 900));
  const root = [...objects.objects3d.values()].find(o => o.userData.objectId === 192);
  root.updateWorldMatrix(true, true);
  const b = new THREE.Box3().setFromObject(root);
  const mesh = house.roomMeshes.get(7);
  mesh.updateWorldMatrix(true, true);
  const rb = new THREE.Box3().setFromObject(mesh);
  return { door: [b.min.toArray(), b.max.toArray()], room: [rb.min.toArray(), rb.max.toArray()] };
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader","--hide-scrollbars"])
    p = b.new_page(viewport={"width":1000,"height":750})
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(12000)
    print(json.dumps(p.evaluate(JS), indent=1))
    b.close()
