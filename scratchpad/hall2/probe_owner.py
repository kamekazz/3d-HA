"""Name the object that owns whatever the ray hits."""
import json, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE,"..","..","tools")))
from v3 import POSES
from roomkit.shot import SETUP_JS
from playwright.sync_api import sync_playwright

PROBE = """
async ({grid}) => {
  const T = await import('three');
  const {camera, scene} = window.__scene3d;
  camera.updateMatrixWorld(true);
  const rc = new T.Raycaster();
  const out = [];
  for (const [gx,gy,tag] of grid) {
    rc.setFromCamera(new T.Vector2(gx,gy), camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h=>h.object.visible);
    const rows = [];
    for (const h of hits.slice(0,3)) {
      let o=h.object, owner='?', kind='?';
      while(o){ if(o.userData && o.userData.kind){kind=o.userData.kind; owner=o.userData.name||o.userData.roomName||o.userData.modelName||'?';} o=o.parent; }
      let q=h.object, names=[];
      for(let i=0;i<7&&q;i++){ names.push(JSON.stringify(q.userData||{}).slice(0,90)); q=q.parent; }
      const m=h.object.material;
      rows.push({d:+h.distance.toFixed(2), col:m&&m.color?'#'+m.color.getHexString():'-',
                 matname: m? m.name : '-', kind, owner, ud:names});
    }
    out.push({tag, rows});
  }
  return out;
}
"""
pose=POSES[sys.argv[1]]; grid=json.loads(sys.argv[2])
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome")
    pg=b.new_page(viewport={"width":pose["size"][0],"height":pose["size"][1]})
    pg.goto("http://127.0.0.1:5000", wait_until="networkidle")
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.evaluate(SETUP_JS,{"pose":pose,"level":2,"light":"day","markers":False,"cutaway":False})
    pg.wait_for_timeout(1200)
    for e in pg.evaluate(PROBE,{"grid":grid}):
        print('##',e['tag'])
        for r in e['rows']:
            print(f"   d={r['d']} {r['col']} mat={r['matname']} kind={r['kind']} owner={r['owner']}")
            for u in r['ud']: print('        ',u)
    b.close()
