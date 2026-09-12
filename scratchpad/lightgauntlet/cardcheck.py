"""Read the room-card labels. Read-only: never calls api.control, so no real
light is ever switched."""
import sys, json
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright
from roomkit.lightshot import BASE

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=[
        '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 1400, 'height': 900})
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.goto(BASE, wait_until='load', timeout=60000)
    page.wait_for_function("() => document.body.classList.contains('booted')",
                           timeout=180000)
    page.wait_for_timeout(2000)
    out = page.evaluate("""async () => {
      const rl = await import('/js/roomlights.js');
      const ids = [1,2,4,5,6,7,8,9,10,13,14,15,16,17,22,27];
      return ids.map(id => ({
        room: id,
        control: [...rl.getRoomControlIds(id)],
        lightOnly: [...rl.getRoomLightIds(id)],
      }));
    }""")
    cards = page.evaluate("""() => [...document.querySelectorAll('.room-card')]
        .map(c => ({ name: c.querySelector('.t-name,.rc-name,b')?.textContent?.trim(),
                     sub: c.querySelector('.rc-sub,.t-sub,small,span')?.textContent?.trim() }))
        .filter(x => x.name)""")
    b.close()
print('page errors:', errs[:3] or 'none')
for r in out:
    extra = [i for i in r['control'] if i not in r['lightOnly']]
    if extra or not r['lightOnly']:
        print('room %-3d light-only=%-2d control=%-2d  newly controllable: %s'
              % (r['room'], len(r['lightOnly']), len(r['control']), extra or '-'))
print('--- cards ---')
for c in cards[:14]:
    print('  %-20s %s' % (c['name'], c['sub']))
