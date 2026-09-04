import sys, json
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright
from roomkit.lightshot import BASE, READY_JS

JS = """
async () => {
  const house = await import('/js/house.js');
  const THREE = await import('/vendor/three/three.module.js').catch(()=>null);
  house.setLevel(2);
  await new Promise(r => setTimeout(r, 1200));
  const out = {rooms:{}, objs:{}};
  for (const rid of [13,15,16,27,17]) {
    const m = house.roomMeshes.get(rid);
    if (!m) continue;
    m.updateWorldMatrix(true,true);
    out.rooms[rid] = {pos:[m.position.x,m.position.y,m.position.z]};
  }
  const found = {};
  for (const g of house.floorGroups.values()) {
    g.traverse(c => {
      if (c.userData && c.userData.kind === 'object') {
        const p = new c.position.constructor();
        c.getWorldPosition(p);
        found[c.userData.objectId] = [ +p.x.toFixed(2), +p.y.toFixed(2), +p.z.toFixed(2) ];
      }
    });
  }
  out.objs = found;
  return out;
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width":900,"height":700})
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(2500)
    for _ in range(40):
        st = pg.evaluate(READY_JS)
        if st["total"]==0 or st["loaded"]>=st["total"]: break
        pg.wait_for_timeout(250)
    print(json.dumps(pg.evaluate(JS), indent=1))
    b.close()
