"""List what windowlight.js has latched onto, both detectors."""
import json, sys, os
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(14000)
    ws = p.evaluate("() => window.__windowlight.windows()")
    ws.sort(key=lambda w: (w["via"], w["name"] or ""))
    for w in ws:
        print("%-8s %-30s peak=%-8s obj=%s" % (w["via"], w["name"], w["peak"], w.get("objectId")))
    print(len(ws), "tracked")
    if errs: print("PAGE ERRORS:", errs[:3])
    b.close()
