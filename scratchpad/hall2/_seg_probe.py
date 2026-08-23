"""Per-skirting-segment: how far into room 17 the first HOUSE WALL surface sits.

house.js gives its own materials no name, so an unnamed hit is a room wall /
slab / opening panel; every named hit is another builder's GLB.
"""
import json, sys, math
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2")
from roomkit import shot
from playwright.sync_api import sync_playwright
import base as B

AX, AZ, AY = 6.70, 6.55, 18.0
samples = []
for (i, u0, u1) in B._segments():
    (ax, az), (ux, uz), L = B._edge(i)
    nx, nz = B._normal(i)
    for f in (0.04, 0.2, 0.5, 0.8, 0.96):
        u = u0 + (u1 - u0) * f
        px, pz = ax + ux * u, az + uz * u
        samples.append({"e": i, "u": round(u, 3),
                        "o": [AX + px + nx * 1.4, AY + 0.25, AZ + pz + nz * 1.4],
                        "d": [-nx, 0, -nz]})
light = {"elevation": 42, "azimuth": 155, "condition": "sunny"}
args = {"pose": {"pos": [12.10, 23.30, 21.90], "target": [12.95, 22.05, 7.20],
                 "fov": 74, "size": [900, 1200]},
        "level": 2, "light": light, "markers": False, "cutaway": False}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 1200})
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(2500)
    pg.evaluate(shot.SETUP_JS, args)
    for _ in range(40):
        st = pg.evaluate(shot.READY_JS)
        if st["total"] == 0 or st["loaded"] >= st["total"]:
            break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(1000)
    res = pg.evaluate("""async (samples) => {
      const THREE = await import('three');
      const scene = window.__scene3d.scene;
      return samples.map(s => {
        const o = new THREE.Vector3(...s.o), d = new THREE.Vector3(...s.d).normalize();
        const rc = new THREE.Raycaster(o, d, 0.01, 3.0);
        const hits = rc.intersectObject(scene, true).filter(h => h.object.visible);
        return [s.e, s.u, hits.slice(0,6).map(h => [+(1.4 - h.distance).toFixed(3),
                 (h.object.material && h.object.material.name) || ''])];
      }); }""", samples)
    json.dump(res, open(r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\_seg.json", "w"))
    b.close()
print("ok")
