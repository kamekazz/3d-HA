"""Floor -> House round trip at night: does the moon dome come back?"""
import json
from playwright.sync_api import sync_playwright
JS = """
async () => {
  const h = await import('/js/house.js');
  window.__daylight.simulate({elevation:-18, azimuth:0, condition:'clear-night'});
  await new Promise(r=>setTimeout(r,2000));
  const sc = window.__scene3d.scene, out = {};
  const probe = (tag) => { const d = sc.getObjectByName('yard-sky-dome'), n = sc.getObjectByName('nightSky');
    out[tag] = { dome: d ? d.visible && !!d.parent : null, nightSky: n?.visible, bg: sc.background?.isColor ? sc.background.getHexString() : 'texture',
      sun: +window.__scene3d.sunLight.intensity.toFixed(2), hemi: +window.__scene3d.hemiLight.intensity.toFixed(2), graded: window.__environment.state().graded }; };
  probe('house0');
  h.setLevel(1); await new Promise(r=>setTimeout(r,3000)); probe('floor1');
  h.setLevel('all'); await new Promise(r=>setTimeout(r,3000)); probe('house1');
  return out;
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("http://127.0.0.1:5001/", wait_until="load", timeout=60000)
    p.wait_for_function("() => window.__environment && window.__environment.state().standing && window.__environment.state().shown", timeout=120000)
    p.wait_for_timeout(2000)
    res = p.evaluate(JS)
    p.screenshot(path='shots/roundtrip_house.png')
    print(json.dumps({"probe": res, "errors": errs[:3]}, indent=1))
    b.close()
