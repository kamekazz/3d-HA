import json, os
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:5000"
JS = """
async () => {
  const env = await import('/js/environment.js');
  const house = await import('/js/house.js');
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1500));
  const root = env.getEnvironmentRoot();
  const out = [];
  root.traverse(o => {
    if (!o.isMesh) return;
    const g = o.geometry;
    const tris = g.index ? g.index.count/3 : (g.attributes.position?.count||0)/3;
    out.push({ tris, verts: g.attributes.position?.count || 0 });
  });
  return { meshes: out.length, tris: out.reduce((a,b)=>a+b.tris,0),
           each: out.map(o=>o.tris) };
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width":1000,"height":700})
    errs, cons = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: cons.append(m.type + ": " + m.text) if m.type in ("error","warning") else None)
    pg.goto(BASE, wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000)
    pg.wait_for_timeout(4000)
    print(json.dumps(pg.evaluate(JS), indent=1)[:1200])
    print("PAGE ERRORS:", errs[:6])
    print("CONSOLE:", cons[:10])
    b.close()
