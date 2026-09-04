"""Raycast through a screen pixel at the lightshot pose and name what is there."""
import json, sys, os
sys.path.insert(0, os.path.abspath('../../tools'))
from roomkit.lightshot import SETUP_JS, COLLECT_JS
from playwright.sync_api import sync_playwright

PICK = """
async ({ px, py }) => {
  const THREE = await import('three');
  const { camera, scene, renderer } = window.__scene3d;
  const w = window.innerWidth, h = window.innerHeight;
  const rc = new THREE.Raycaster();
  rc.setFromCamera(new THREE.Vector2((px / w) * 2 - 1, -(py / h) * 2 + 1), camera);
  const hits = rc.intersectObjects(scene.children, true).filter((hit) => {
    for (let n = hit.object; n; n = n.parent) if (!n.visible) return false;
    return true;
  });
  return hits.slice(0, 4).map((hit) => {
    const o = hit.object;
    let owner = o, name = null;
    for (let n = o; n; n = n.parent) {
      if (n.userData && n.userData.kind) { owner = n; name = n.userData.name; break; }
    }
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    return {
      dist: +hit.distance.toFixed(2),
      owner: name, kind: owner.userData?.kind, objectId: owner.userData?.objectId,
      meshName: o.name,
      mats: mats.map((m) => ({
        name: m.name, type: m.type,
        color: m.color ? '#' + m.color.getHexString() : null,
        emissive: m.emissive ? '#' + m.emissive.getHexString() : null,
        ei: m.emissiveIntensity,
      })),
      orig: o.userData.__orig || o.parent?.userData?.__orig || null,
    };
  });
}
"""
room, level = int(sys.argv[1]), int(sys.argv[2])
px, py = float(sys.argv[3]), float(sys.argv[4])
light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(11000)
    ids = p.evaluate(COLLECT_JS, room)["ids"]
    arg = {"roomId": room, "level": level, "light": light, "entityIds": ids, "on": False}
    p.evaluate(SETUP_JS, arg); p.wait_for_timeout(1500)
    info = p.evaluate(SETUP_JS, arg); p.wait_for_timeout(600)
    print("camera at", info["at"])
    print(json.dumps(p.evaluate(PICK, {"px": px, "py": py}), indent=1))
    b.close()
