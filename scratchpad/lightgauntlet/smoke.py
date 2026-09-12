"""Boot smoke test: load the app cold and report page errors + load counts."""
import sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright
from roomkit.lightshot import BASE, READY_JS

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=[
        '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 1200, 'height': 800})
    errs, console = [], []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('console', lambda m: console.append(m.text) if m.type == 'error' else None)
    page.goto(BASE, wait_until='load', timeout=60000)
    page.wait_for_function('() => !!window.__scene3d', timeout=30000)
    # Wait for the CURTAIN, not just the loader counts: boot.js lifts it only
    # after settleLoaders, the shell's refitStage, compileAsync and the
    # cutaway/daylight/light settles -- which is the thing being smoke-tested.
    page.wait_for_function(
        "() => document.body.classList.contains('booted')", timeout=180000)
    page.wait_for_timeout(2500)
    info = page.evaluate("""async () => {
      const rl = window.__roomlights, wl = window.__windowlight;
      return {
        objects: (await import('/js/objects.js')).objects3d.size,
        rooms: (await import('/js/house.js')).roomMeshes.size,
        pool: rl?.poolSize?.(), bound: rl?.bound?.().length,
        fixtures: rl?.fixtures?.().length,
        litSlots: (rl?.slots?.() || []).filter(s => s.owner).length,
        windows: wl?.windows?.().length,
        boot: window.__boot?.state?.(),
      };
    }""")
    page.screenshot(path='shots/smoke_final.png')
    b.close()
print('page errors:', errs[:5] or 'none')
print('console errors:', console[:5] or 'none')
print(info)
