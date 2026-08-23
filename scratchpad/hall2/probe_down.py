"""Raycast from the v2_down pose to identify what occludes the stairwell."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3 import POSES
from playwright.sync_api import sync_playwright

JS = """
async ({pose, level}) => {
  const T3 = await import('three');
  const house = await import('/js/house.js');
  const {camera, scene} = window.__scene3d;
  house.setLevel(level);
  await new Promise(r=>setTimeout(r,900));
  camera.position.set(pose.pos[0],pose.pos[1],pose.pos[2]);
  camera.lookAt(pose.target[0],pose.target[1],pose.target[2]);
  camera.fov = pose.fov||70; camera.near=0.05; camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  const T = T3;
  const rc = new T.Raycaster();
  const out = [];
  const grid = [[0,0],[0,0.4],[0,-0.4],[-0.3,0.2],[0.3,0.2],[0,0.7],[-0.5,0.5],[0.5,0.5]];
  for (const [gx,gy] of grid) {
    rc.setFromCamera(new T.Vector2(gx,gy), camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h=>h.object.visible);
    const rows = [];
    for (const h of hits.slice(0,4)) {
      let o=h.object, chain=[];
      while(o){ chain.push((o.name||o.type)+(o.userData&&o.userData.part?':'+o.userData.part:'')+(o.userData&&o.userData.kind?'#'+o.userData.kind:'')+(o.userData&&o.userData.roomName?'<'+o.userData.roomName+'>':'')); o=o.parent; }
      rows.push({d:+h.distance.toFixed(2), p:[+h.point.x.toFixed(2),+h.point.y.toFixed(2),+h.point.z.toFixed(2)], chain:chain.slice(0,5).join(' / ')});
    }
    out.push({ndc:[gx,gy], rows});
  }
  return out;
}
"""

pose = POSES["p_doors2"]
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width":900,"height":1200})
    pg.goto("http://127.0.0.1:5000", wait_until="networkidle")
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    res = pg.evaluate(JS, {"pose": pose, "level": 2})
    print(json.dumps(res, indent=1))
    b.close()
