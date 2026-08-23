"""Raycast using the EXACT camera shot.py ends up with (flyTo), and report
what the black pixels actually are, by sampling the framebuffer too."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
sys.path.insert(0, TOOLS)
from v3 import POSES
from roomkit.shot import SETUP_JS
from playwright.sync_api import sync_playwright

PROBE = """
async ({grid}) => {
  const T = await import('three');
  const {camera, scene, renderer} = window.__scene3d;
  camera.updateMatrixWorld(true);
  const rc = new T.Raycaster();
  const gl = renderer.getContext();
  const W = renderer.domElement.width, H = renderer.domElement.height;
  const out = [];
  for (const [gx,gy,tag] of grid) {
    // framebuffer pixel at this ndc
    const px = Math.round((gx*0.5+0.5)*W), py = Math.round((gy*0.5+0.5)*H);
    const buf = new Uint8Array(4);
    gl.readPixels(px, py, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, buf);
    rc.setFromCamera(new T.Vector2(gx,gy), camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h=>h.object.visible);
    const rows = [];
    for (const h of hits.slice(0,3)) {
      let o=h.object, chain=[];
      while(o){ chain.push((o.name||o.type)+(o.userData&&o.userData.part?':'+o.userData.part:'')+(o.userData&&o.userData.roomName?'<'+o.userData.roomName+'>':'')); o=o.parent; }
      const m=h.object.material;
      rows.push({d:+h.distance.toFixed(2),
                 p:[+h.point.x.toFixed(2),+h.point.y.toFixed(2),+h.point.z.toFixed(2)],
                 col: m&&m.color? '#'+m.color.getHexString():'-',
                 side: m? m.side : '-',
                 chain:chain.slice(0,8).join(' / ')});
    }
    out.push({tag, ndc:[gx,gy], pixel:[buf[0],buf[1],buf[2]], rows});
  }
  return out;
}
"""

pose = POSES[sys.argv[1]]
grid = json.loads(sys.argv[2])
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": pose["size"][0], "height": pose["size"][1]})
    pg.goto("http://127.0.0.1:5000", wait_until="networkidle")
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.evaluate(SETUP_JS, {"pose": pose, "level": 2, "light": "day",
                           "markers": False, "cutaway": False})
    pg.wait_for_timeout(1200)
    for e in pg.evaluate(PROBE, {"grid": grid}):
        print(f"{e['tag']:<26} ndc{e['ndc']}  pixel={e['pixel']}")
        for r in e['rows']:
            print(f"     d={r['d']:<7} {r['p']} {r['col']} side={r['side']}  {r['chain']}")
    b.close()
