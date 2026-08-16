import json, os, sys
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:5000"
JS = """
async (pts) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  house.setLevel('all');
  for (let i = 0; i < 120; i++) { if (house.getShellRoot()) break; await new Promise(r=>setTimeout(r,250)); }
  const shell = house.getShellRoot();
  if (!shell) return {error:'no shell'};
  const box = new THREE.Box3().setFromObject(shell);
  const rc = new THREE.Raycaster();
  const out = [];
  for (const p of pts) {
    rc.set(new THREE.Vector3(p[0], 200, p[1]), new THREE.Vector3(0,-1,0));
    const hits = rc.intersectObject(shell, true);
    out.push({x:p[0], z:p[1], y: hits.length ? +hits[0].point.y.toFixed(2) : null, n: hits.length});
  }
  return {bbox:{min:box.min.toArray().map(v=>+v.toFixed(2)), max:box.max.toArray().map(v=>+v.toFixed(2))}, out};
}
"""
pts = []
for x in (19.5, 22, 25, 28, 31.5):
    for z in (13.0, 15, 17, 19, 20.5):
        pts.append([x, z])
# also hallway/master bath reference
for x in (12, 16, 20, 26):
    pts.append([x, 8.0])
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width":900,"height":700})
    pg.goto(BASE); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(4000)
    r = pg.evaluate(JS, pts)
    print(json.dumps(r))
    b.close()
