import json, sys, os
sys.path.insert(0, os.path.abspath('../../tools'))
from roomkit.lightshot import SETUP_JS, COLLECT_JS
from playwright.sync_api import sync_playwright

PICK = """
async (pts) => {
  const THREE = await import('three');
  const { camera, scene } = window.__scene3d;
  const rc = new THREE.Raycaster();
  const out = [];
  const W = window.innerWidth, H = window.innerHeight;
  for (const [px, py] of pts) {
    rc.setFromCamera(new THREE.Vector2((px / W) * 2 - 1, -(py / H) * 2 + 1), camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h => {
      for (let n = h.object; n; n = n.parent) if (!n.visible) return false;
      return true;
    }).slice(0, 3);
    out.push({ px, py, hits: hits.map(h => {
      const m = Array.isArray(h.object.material) ? h.object.material[0] : h.object.material;
      const chain = [];
      for (let n = h.object; n; n = n.parent) chain.push(n.userData.name || n.name || n.userData.kind || n.type);
      const e = m && m.emissive ? (0.2126*m.emissive.r+0.7152*m.emissive.g+0.0722*m.emissive.b)*m.emissiveIntensity : null;
      return { d: +h.distance.toFixed(2), mat: m && m.name, emis: e === null ? null : +e.toFixed(4),
               color: m && m.color ? m.color.getHexString() : null, chain: chain.slice(0, 5) };
    })});
  }
  return out;
}
"""
room, level = int(sys.argv[1]), int(sys.argv[2])
pts = [[int(a) for a in p.split(',')] for p in sys.argv[3:]]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader","--hide-scrollbars"])
    p = b.new_page(viewport={"width":1000,"height":750}, device_scale_factor=1)
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(9000)
    ids = p.evaluate(COLLECT_JS, room)["ids"]
    arg = {"roomId": room, "level": level,
           "light": {"elevation": -18, "azimuth": 0, "condition": "clear-night"},
           "entityIds": ids, "on": False}
    p.evaluate(SETUP_JS, arg); p.wait_for_timeout(1400)
    p.evaluate(SETUP_JS, arg); p.wait_for_timeout(400)
    p.screenshot(path="shots/probe_pick_r%d.png" % room)
    print("ENTITIES", ids)
    print(json.dumps(p.evaluate(PICK, pts)))
    b.close()
