"""List what windowlight.js has latched onto, all three detectors, with mode.

Waits for every object GLB to land first (probe_wl.py's flat 14 s timeout was
short of it -- ~270 models -- and an object that has not arrived yet has not
called noteWindowObject).
"""
import sys
from playwright.sync_api import sync_playwright

READY = """
async () => {
  const objects = await import('/js/objects.js');
  const roots = [...objects.objects3d.values()];
  return { total: roots.length, loaded: roots.filter(r => r.children.length > 0).length };
}
"""
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(4000)
    for _ in range(60):
        st = p.evaluate(READY)
        if st["total"] and st["loaded"] >= st["total"]:
            break
        p.wait_for_timeout(1000)
    print("objects", st)
    ws = p.evaluate("() => window.__windowlight.windows()")
    ws.sort(key=lambda w: (w["mode"], w["via"], w["name"] or ""))
    for w in ws:
        print("%-7s %-9s %-32s peak=%-8s obj=%s" %
              (w["mode"], w["via"], w["name"], w["peak"], w.get("objectId")))
    print(len(ws), "tracked;",
          sum(1 for w in ws if w["mode"] == "fill"), "fill,",
          sum(1 for w in ws if w["mode"] == "window"), "window")
    if errs: print("PAGE ERRORS:", errs[:3])
    b.close()
