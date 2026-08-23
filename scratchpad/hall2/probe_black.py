import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v3 import POSES
from playwright.sync_api import sync_playwright

JS = """
async ({pose, level, grid}) => {
  const T = await import('three');
  const house = await import('/js/house.js');
  const {camera, scene} = window.__scene3d;
  house.setLevel(level);
  await new Promise(r=>setTimeout(r,900));
  camera.position.set(pose.pos[0],pose.pos[1],pose.pos[2]);
  camera.up.set(0,1,0);
  camera.lookAt(pose.target[0],pose.target[1],pose.target[2]);
  camera.fov = pose.fov||70; camera.near=0.05; camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  const rc = new T.Raycaster();
  const out = [];
  for (const [gx,gy,tag] of grid) {
    rc.setFromCamera(new T.Vector2(gx,gy), camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h=>h.object.visible);
    const rows = [];
    for (const h of hits.slice(0,3)) {
      let o=h.object, chain=[];
      while(o){ chain.push((o.name||o.type)+(o.userData&&o.userData.part?':'+o.userData.part:'')+(o.userData&&o.userData.kind?'#'+o.userData.kind:'')+(o.userData&&o.userData.roomName?'<'+o.userData.roomName+'>':'')); o=o.parent; }
      const m=h.object.material;
      rows.push({d:+h.distance.toFixed(2),
                 p:[+h.point.x.toFixed(2),+h.point.y.toFixed(2),+h.point.z.toFixed(2)],
                 col: m&&m.color? '#'+m.color.getHexString():'-',
                 chain:chain.slice(0,4).join(' / ')});
    }
    out.push({tag, ndc:[gx,gy], n:hits.length, rows});
  }
  return out;
}
"""
pose = POSES[sys.argv[1]]
grid = json.loads(sys.argv[2])
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width":900,"height":1200})
    pg.goto("http://127.0.0.1:5000", wait_until="networkidle")
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    for e in pg.evaluate(JS, {"pose": pose, "level": 2, "grid": grid}):
        print(e['tag'], e['ndc'], 'hits', e['n'])
        for r in e['rows']: print('   ', r['d'], r['p'], r['col'], r['chain'])
    b.close()
