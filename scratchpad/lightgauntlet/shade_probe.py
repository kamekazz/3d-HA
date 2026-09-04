"""Meter room 14's `lamp_shade` at night with every light off, in TWO states:
as it stands (roomlights owns it, since the nightstands are now bound), and with
its AUTHORED emissive handed back -- which is what the material looked like
before any binding, and the thing the brief asked about. Client-side only: no
DB write, no HA call."""
import sys, os
sys.path.insert(0, os.path.abspath('../../tools'))
from roomkit.lightshot import SETUP_JS, COLLECT_JS
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image

RESTORE = """
async (ids) => {
  const objects = await import('/js/objects.js');
  const state = await import('/js/state.js');
  const out = [];
  for (const id of ids) {
    const root = objects.objects3d.get(id);
    if (!root) { out.push({ id, err: 'no root' }); continue; }
    state.paintModelState(root, { emissiveHex: null, grey: false });
    root.traverse((c) => {
      if (!c.isMesh) return;
      const mats = Array.isArray(c.material) ? c.material : [c.material];
      mats.forEach((m) => {
        if ((m.name || '').toLowerCase() === 'lamp_shade')
          out.push({ id, emissive: '#' + m.emissive.getHexString(), ei: m.emissiveIntensity });
      });
    });
  }
  const { camera, renderer, scene } = window.__scene3d;
  renderer.render(scene, camera);
  return out;
}
"""
BOX = """
async (matName) => {
  const THREE = await import('three');
  const { camera, scene } = window.__scene3d;
  const w = window.innerWidth, h = window.innerHeight;
  const out = [];
  scene.traverse((o) => {
    if (!o.isMesh) return;
    for (let n = o; n; n = n.parent) if (!n.visible) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    if (!mats.some((m) => (m.name || '').toLowerCase() === matName)) return;
    o.updateWorldMatrix(true, false);
    const g = o.geometry; if (!g.boundingBox) g.computeBoundingBox();
    const bb = g.boundingBox;
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (let i = 0; i < 8; i++) {
      const v = new THREE.Vector3(i&1?bb.max.x:bb.min.x, i&2?bb.max.y:bb.min.y, i&4?bb.max.z:bb.min.z);
      o.localToWorld(v); v.project(camera);
      const sx=(v.x*0.5+0.5)*w, sy=(-v.y*0.5+0.5)*h;
      x0=Math.min(x0,sx); x1=Math.max(x1,sx); y0=Math.min(y0,sy); y1=Math.max(y1,sy);
    }
    let owner=null; for (let n=o;n;n=n.parent) if (n.userData?.kind) { owner=n.userData; break; }
    out.push({ objectId: owner?.objectId, box: [Math.round(x0),Math.round(y0),Math.round(x1),Math.round(y1)] });
  });
  return out;
}
"""
def meter(png, boxes, tag):
    a = np.asarray(Image.open(png).convert("RGB")).astype(float)
    lum = 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2]
    print("%-10s frame L mean %.1f p95 %.1f p99 %.1f max %.1f" % (tag, lum.mean(),
          np.percentile(lum,95), np.percentile(lum,99), lum.max()))
    for f in boxes:
        x0,y0,x1,y1 = f["box"]
        x0=max(0,x0); y0=max(0,y0); x1=min(a.shape[1],x1); y1=min(a.shape[0],y1)
        if x1<=x0 or y1<=y0: continue
        r=lum[y0:y1,x0:x1]; c=a[y0:y1,x0:x1]
        i=np.unravel_index(np.argmax(r), r.shape)
        print("   obj%-5s shade L mean %.1f p95 %.1f max %.1f  brightest sRGB %s"
              % (f["objectId"], r.mean(), np.percentile(r,95), r.max(),
                 tuple(int(v) for v in c[i])))

light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle","--enable-unsafe-swiftshader","--hide-scrollbars"])
    p = b.new_page(viewport={"width":1000,"height":750}, device_scale_factor=1)
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(11000)
    ids = p.evaluate(COLLECT_JS, 14)["ids"]
    arg = {"roomId":14,"level":2,"light":light,"entityIds":ids,"on":False}
    p.evaluate(SETUP_JS, arg); p.wait_for_timeout(1500)
    p.evaluate(SETUP_JS, arg); p.wait_for_timeout(600)
    boxes = p.evaluate(BOX, "lamp_shade")
    p.screenshot(path="shots/after/master_shade_bound.png")
    print("forced-off entities:", ids)
    meter("shots/after/master_shade_bound.png", boxes, "BOUND")
    print("restore ->", p.evaluate(RESTORE, [14, 356]))
    p.wait_for_timeout(400)
    p.screenshot(path="shots/after/master_shade_authored.png")
    meter("shots/after/master_shade_authored.png", boxes, "AUTHORED")
    b.close()
