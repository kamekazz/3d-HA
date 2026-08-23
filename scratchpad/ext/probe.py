"""Pixel -> world probe against the running app.

  python probe.py --pose-json '{...}' --px "480,700 620,795"
Raycasts through each screen pixel and reports the first hit: object name, its
root ancestor (shell / environment / floor group), world point and the mesh's
world bbox. This is how you find out what a stray white line actually is.
"""
import argparse, json, os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

SETUP = """
async ({ pose, level }) => {
  const house = await import('/js/house.js');
  const sceneMod = await import('/js/scene.js');
  const { camera, controls } = window.__scene3d;
  house.setLevel(level);
  await new Promise(r => setTimeout(r, 900));
  window.__daylight?.simulate({elevation: 42, azimuth: 155, condition: 'sunny'});
  camera.fov = pose.fov || 70; camera.near = 0.05; camera.updateProjectionMatrix();
  controls.minDistance = 0.05; controls.maxDistance = 1e6;
  controls.enableDamping = false;
  sceneMod.flyTo({x:pose.pos[0],y:pose.pos[1],z:pose.pos[2]},
                 {x:pose.target[0],y:pose.target[1],z:pose.target[2]});
  for (let i=0;i<200;i++){ await new Promise(r=>requestAnimationFrame(r));
    const d=Math.hypot(camera.position.x-pose.pos[0],camera.position.y-pose.pos[1],camera.position.z-pose.pos[2]);
    if(d<0.02) break; }
  return true;
}
"""

RAY = """
async ({ px, size }) => {
  const THREE = await import('three');
  const { camera, scene } = window.__scene3d;
  const rc = new THREE.Raycaster();
  const out = [];
  for (const [sx, sy] of px) {
    const ndc = new THREE.Vector2(sx / size[0] * 2 - 1, -(sy / size[1] * 2 - 1));
    rc.setFromCamera(ndc, camera);
    const hits = rc.intersectObjects(scene.children, true).filter(h => h.object.visible);
    const rows = [];
    for (const h of hits.slice(0, 4)) {
      let o = h.object, chain = [];
      while (o) { if (o.name) chain.push(o.name); o = o.parent; }
      const bb = new THREE.Box3().setFromObject(h.object);
      rows.push({ name: h.object.name || '(unnamed)', chain: chain.slice(0, 4),
        pt: [+h.point.x.toFixed(2), +h.point.y.toFixed(2), +h.point.z.toFixed(2)],
        tris: h.object.geometry?.index ? h.object.geometry.index.count/3
              : (h.object.geometry?.attributes?.position?.count||0)/3,
        box: [+bb.min.x.toFixed(2), +bb.min.y.toFixed(2), +bb.min.z.toFixed(2),
              +bb.max.x.toFixed(2), +bb.max.y.toFixed(2), +bb.max.z.toFixed(2)] });
    }
    out.push({ px: [sx, sy], hits: rows });
  }
  return out;
}
"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pose-json", required=True)
    p.add_argument("--px", required=True, help='"x,y x,y ..."')
    p.add_argument("--level", default="all")
    a = p.parse_args()
    pose = json.loads(a.pose_json)
    px = [[float(v) for v in t.split(",")] for t in a.px.split()]
    w, h = pose.get("size", [900, 1200])
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome",
                               args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        pg = b.new_page(viewport={"width": int(w), "height": int(h)}, device_scale_factor=1)
        pg.goto(BASE, wait_until="load", timeout=60000)
        pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
        pg.wait_for_timeout(3500)
        lvl = a.level if a.level == "all" else int(a.level)
        pg.evaluate(SETUP, {"pose": pose, "level": lvl})
        pg.wait_for_timeout(1500)
        res = pg.evaluate(RAY, {"px": px, "size": [w, h]})
        b.close()
    for r in res:
        print("px", r["px"])
        for hrow in r["hits"]:
            print("   %-24s %-38s pt %s tris %d box %s" %
                  (hrow["name"][:24], "/".join(hrow["chain"])[:38], hrow["pt"],
                   hrow["tris"], hrow["box"]))

if __name__ == "__main__":
    main()
