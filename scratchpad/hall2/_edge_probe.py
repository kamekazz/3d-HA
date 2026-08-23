"""Measure, per polygon edge of room 17, how far the FIRST solid surface sits
from the footprint line -- neighbouring rooms' wall masses project 0.35 ft past
their own footprints, and several of room 17's neighbours are traced 0.06-0.35 ft
inside its line, so the surface you actually see is not the room's own wall."""
import json, sys, math
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit import shot
from playwright.sync_api import sync_playwright

POLY = [(11.92,6.81),(7.61,6.81),(7.61,16.89),(3.86,16.89),(3.86,16.15),
        (0.0,16.15),(0.0,10.77),(3.86,10.77),(3.86,0.0),(11.92,0.0)]
AX, AZ, AY = 6.70, 6.55, 18.0
samples = []
for i in range(len(POLY)):
    a = POLY[i]; b = POLY[(i+1) % len(POLY)]
    dx, dz = b[0]-a[0], b[1]-a[1]
    L = math.hypot(dx, dz); ux, uz = dx/L, dz/L
    nx, nz = -uz, ux
    for t in (0.15, 0.35, 0.5, 0.65, 0.85):
        px, pz = a[0]+ux*L*t, a[1]+uz*L*t
        for y in (0.10, 0.25, 0.40):
            samples.append({"e": i, "t": t, "y": y,
                            "o": [AX+px+nx*1.2, AY+y, AZ+pz+nz*1.2],
                            "d": [-nx, 0, -nz]})
light = {"elevation": 42, "azimuth": 155, "condition": "sunny"}
args = {"pose": {"pos":[12.10,23.30,21.90],"target":[12.95,22.05,7.20],"fov":74,"size":[900,1200]},
        "level":2, "light":light, "markers":False, "cutaway":False}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width":900,"height":1200})
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(2500)
    pg.evaluate(shot.SETUP_JS, args)
    for _ in range(40):
        st = pg.evaluate(shot.READY_JS)
        if st["total"]==0 or st["loaded"]>=st["total"]: break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(1000)
    res = pg.evaluate("""async (samples) => {
      const THREE = await import('three');
      const scene = window.__scene3d.scene;
      return samples.map(s => {
        const o = new THREE.Vector3(...s.o), d = new THREE.Vector3(...s.d).normalize();
        const rc = new THREE.Raycaster(o, d, 0.01, 3.0);
        const hits = rc.intersectObject(scene, true).filter(h => h.object.visible);
        if (!hits.length) return [s.e, s.t, s.y, null, ''];
        const h = hits[0];
        const nm = (h.object.material && h.object.material.name) || '';
        return [s.e, s.t, s.y, +(1.2 - h.distance).toFixed(3), nm];
      }); }""", samples)
    print(json.dumps(res))
    b.close()
