from playwright.sync_api import sync_playwright
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 900, "height": 600})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
    pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_timeout(12000)
    print("scene3d:", pg.evaluate("() => !!window.__scene3d"), " boot:", pg.evaluate("() => window.__boot ? window.__boot.state() : null"))
    b.close()
for e in errs[:15]: print(e[:600])
