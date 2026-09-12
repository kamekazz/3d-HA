"""Which rooms did FLOOR_SKIN_RE find a floor in, and is every dark room's pair
of emissive terms still exactly zero? Client-side state only; HA is never called.
"""
import json, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright
from roomkit.lightshot import BASE, READY_JS

JS = """
async (on) => {
  const rl = await import('/js/roomlights.js');
  const state = await import('/js/state.js');
  const ids = new Set(rl.getAllHouseLightIds());
  for (const f of (window.__roomlights.fixtures() || [])) ids.add(f.entityId);
  window.__daylight?.simulate({elevation:-18, azimuth:0, condition:'clear-night'});
  for (const id of ids) {
    const prev = state.getState(id) || {};
    state.applyState(id, { entity_id: id, state: on ? 'on' : 'off',
      attributes: { ...(prev.attributes||{}), brightness: on ? 255 : null } });
  }
  await new Promise(r => setTimeout(r, 400));
  rl.settleRoomLights();
  const house = await (await fetch('/api/house')).json();
  const RE = /\bfloor(\s+(planks?|boards?|tiles?|carpet|nap))?$/i;
  const named = {};
  for (const f of house.floors||[]) for (const r of f.rooms||[]) {
    const hit = (r.objects||[]).filter(o => !o.entity_id && RE.test(o.name||''))
                               .map(o => o.name);
    if (hit.length) named[r.id] = hit;
  }
  return { surfaces: window.__roomlights.surfaces(), named };
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=[
        '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 900, 'height': 700})
    page.goto(BASE, wait_until='load', timeout=90000)
    page.wait_for_function('() => !!window.__scene3d', timeout=30000)
    page.wait_for_timeout(3000)
    for _ in range(40):
        st = page.evaluate(READY_JS)
        if st['total'] == 0 or st['loaded'] >= st['total']:
            break
        page.wait_for_timeout(250)
    page.wait_for_timeout(1500)
    on = page.evaluate(JS, True)
    off = page.evaluate(JS, False)
    b.close()

print('rooms whose objects matched FLOOR_SKIN_RE:')
for rid, names in sorted(on['named'].items(), key=lambda kv: int(kv[0])):
    print('  room %-3s %s' % (rid, names))
print('\nlights ON (night):')
for s in on['surfaces']:
    print('  room %-3d mode %-6s slab %.4f wall %.4f skins floor=%d wall=%d'
          % (s['roomId'], s['mode'], s['slab'], s['wall'],
             s['skins']['floor'], s['skins']['wall']))
bad = [s for s in off['surfaces'] if s['slab'] or s['wall']]
print('\nlights OFF (night): rooms with a non-zero term:', bad if bad else 'NONE')
