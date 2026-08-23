"""Raycast the running scene through screen pixels of a v3 pose and report what
each hit belongs to.  Read-only: touches nothing in the DB."""
import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools")))
from roomkit import shot as S
from playwright.sync_api import sync_playwright
import v3

RAY_JS = """
async ({pts}) => {
  const T = await import('three');
  const { camera, scene } = window.__scene3d;
  const rc = new T.Raycaster();
  const out = [];
  for (const p of pts) {
    const ndc = new T.Vector2(p[0]*2-1, -(p[1]*2-1));
    rc.setFromCamera(ndc, camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h=>h.object.visible);
    const rows = [];
    for (const h of hits.slice(0,4)) {
      let o = h.object, name = null, kind = null, chain=[];
      while (o) { if(o.name) chain.push(o.name); if (o.userData){ if(o.userData.name){name=o.userData.name; break;} if(o.userData.kind) kind=o.userData.kind; } o = o.parent; }
      if(!name) name = chain.slice(0,3).join('<');
      rows.push({d:+h.distance.toFixed(2), p:[+h.point.x.toFixed(2),+h.point.y.toFixed(2),+h.point.z.toFixed(2)], name, kind, mesh:h.object.name||''});
    }
    out.push({px:p, hits:rows});
  }
  return out;
}
"""

def main():
    pose_name = sys.argv[1]
    pts = [tuple(float(v) for v in a.split(",")) for a in sys.argv[2:]]
    pose = v3.POSES[pose_name]
    w, h = pose["size"]
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader","--hide-scrollbars"])
        pg = b.new_page(viewport={"width":w,"height":h}, device_scale_factor=1)
        pg.goto(S.BASE, wait_until="load", timeout=60000)
        pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
        pg.wait_for_timeout(2500)
        args = {"pose":pose, "level":2, "light":{"elevation":42,"azimuth":155,"condition":"sunny"}, "markers":False, "cutaway":False}
        pg.evaluate(S.SETUP_JS, args)
        for _ in range(40):
            st = pg.evaluate(S.READY_JS)
            if st["total"]==0 or st["loaded"]>=st["total"]: break
            pg.wait_for_timeout(250)
        pg.wait_for_timeout(1200)
        pg.evaluate(S.SETUP_JS, args)
        pg.wait_for_timeout(300)
        res = pg.evaluate(RAY_JS, {"pts":[[x/w, y/h] for x,y in pts]})
        b.close()
    for r, (x,y) in zip(res, pts):
        print(f"px {x:.0f},{y:.0f}")
        for hh in r["hits"]:
            print(f"    d={hh['d']:6.2f}  {str(hh['name']):34s} kind={hh['kind']}  world={hh['p']}")

main()
