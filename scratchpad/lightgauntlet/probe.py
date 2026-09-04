import json
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = "http://127.0.0.1:5000"

JS = """
async (ids) => {
  const THREE = await import('three');
  const objects = await import('/js/objects.js');
  const out = [];
  for (const id of ids) {
    const root = objects.objects3d.get(id);
    if (!root) { out.push({ id, missing: true }); continue; }
    root.updateWorldMatrix(true, true);
    const b = new THREE.Box3().setFromObject(root);
    const meshes = [];
    root.traverse(c => { if (c.isMesh) meshes.push(c.material?.name || '?'); });
    out.push({ id, visible: root.visible, kids: root.children.length,
      min: b.min.toArray().map(v => +v.toFixed(2)),
      max: b.max.toArray().map(v => +v.toFixed(2)),
      size: b.getSize(new THREE.Vector3()).toArray().map(v => +v.toFixed(3)),
      mats: meshes });
  }
  return out;
}
"""

with sync_playwright() as pw:
    br = pw.chromium.launch(channel="chrome", args=[
        "--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = br.new_page(viewport={"width": 900, "height": 700})
    msgs = []
    pg.on("console", lambda m: msgs.append(m.type + ": " + m.text))
    pg.on("pageerror", lambda e: msgs.append("ERR " + str(e)))
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.evaluate("async (lv) => { const h = await import('/js/house.js'); h.setLevel(lv); }", 2)
    pg.wait_for_timeout(6000)
    print(json.dumps(pg.evaluate(JS, [357, 358, 359, 360]), indent=1))
    print("\n".join(m for m in msgs if "err" in m.lower() or "warn" in m.lower())[:2000])
    br.close()
