"""Raycast from a shot pose through a screen point and report what is hit.

Used to identify a mystery surface in a render (e.g. the pure-black slab the
round-2 critic found).  Same setup as roomkit.shot, then a raycast per NDC point.

    python probe.py '<pose json>' 1 0.4,0.55 0.2,0.5
"""
import json
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.shot import SETUP_JS, READY_JS, BASE  # noqa
from playwright.sync_api import sync_playwright

PROBE_JS = """
async ({pts}) => {
  const THREE = await import('three');
  const { camera, scene } = window.__scene3d;
  const out = [];
  for (const p of pts) {
    const rc = new THREE.Raycaster();
    rc.setFromCamera(new THREE.Vector2(p[0]*2-1, -(p[1]*2-1)), camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h => h.object.visible);
    const rows = [];
    for (const h of hits.slice(0, 4)) {
      let o = h.object, chain = [];
      let n = o;
      while (n) { chain.push(n.name || n.type); n = n.parent; }
      const m = o.material;
      rows.push({
        d: +h.distance.toFixed(2),
        pt: [h.point.x, h.point.y, h.point.z].map(v => +v.toFixed(2)),
        name: o.name, type: o.type,
        chain: chain.slice(0, 6).join(' < '),
        ud: JSON.stringify(o.userData).slice(0, 160),
        mat: m ? {name: m.name, color: m.color && '#'+m.color.getHexString(),
                  emissive: m.emissive && '#'+m.emissive.getHexString(),
                  side: m.side, opacity: m.opacity, transparent: m.transparent} : null,
        faceNormal: h.face ? [h.face.normal.x, h.face.normal.y, h.face.normal.z]
                              .map(v=>+v.toFixed(2)) : null,
      });
    }
    out.push({ndc: p, hits: rows});
  }
  return out;
}
"""

pose = json.loads(sys.argv[1])
level = int(sys.argv[2])
pts = [[float(v) for v in a.split(",")] for a in sys.argv[3:]]
w, h = pose.get("size", [900, 1200])

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome",
                          args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(2500)
    light = {"elevation": 42, "azimuth": 155, "condition": "sunny"}
    pg.evaluate(SETUP_JS, {"pose": pose, "level": level, "light": light,
                           "markers": False})
    for _ in range(40):
        st = pg.evaluate(READY_JS)
        if st["total"] == 0 or st["loaded"] >= st["total"]:
            break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(1200)
    pg.evaluate(SETUP_JS, {"pose": pose, "level": level, "light": light,
                           "markers": False})
    print(json.dumps(pg.evaluate(PROBE_JS, {"pts": pts}), indent=1))
    b.close()
