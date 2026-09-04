"""Whole-house smoke check: no page errors, pool sane, fill records exist."""
import json, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright
from roomkit.lightshot import BASE, READY_JS

JS = """
async () => {
  const state = await import('/js/state.js');
  const house = await import('/js/house.js');
  const rl = await import('/js/roomlights.js');
  // force EVERY house light + every bound fixture entity on, client-side only
  const ids = new Set([...rl.getAllHouseLightIds(), ...rl.boundEntities]);
  for (const id of ids) {
    const prev = state.getState(id) || {};
    state.applyState(id, { entity_id: id, state: 'on',
      attributes: { ...(prev.attributes || {}), brightness: 255 } });
  }
  window.__daylight?.simulate({ elevation: -18, azimuth: 0, condition: 'clear-night' });
  house.setLevel('all');
  await new Promise(r => setTimeout(r, 1500));
  rl.settleRoomLights();
  const on = {
    slots: window.__roomlights.slots().filter(s => s.owner),
    fills: window.__roomlights.fills(),
    decays: [...new Set(window.__roomlights.slots().map(s => s.decay))],
  };
  // now everything OFF
  for (const id of ids) {
    const prev = state.getState(id) || {};
    state.applyState(id, { entity_id: id, state: 'off',
      attributes: { ...(prev.attributes || {}), brightness: null } });
  }
  await new Promise(r => setTimeout(r, 1500));
  rl.settleRoomLights();
  const off = {
    slots: window.__roomlights.slots().filter(s => s.owner),
    fills: window.__roomlights.fills(),
    maxIntensity: Math.max(0, ...window.__roomlights.slots().map(s => s.intensity)),
  };
  return { forced: ids.size, on, off };
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=[
        '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 1000, 'height': 750})
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' else None)
    page.goto(BASE, wait_until='load', timeout=60000)
    page.wait_for_function('() => !!window.__scene3d', timeout=30000)
    page.wait_for_timeout(2500)
    for _ in range(40):
        st = page.evaluate(READY_JS)
        if st['total'] == 0 or st['loaded'] >= st['total']:
            break
        page.wait_for_timeout(250)
    out = page.evaluate(JS)
    page.screenshot(path='shots/smoke_house.png')
    b.close()
out['page_errors'] = errs[:6]
print(json.dumps(out, indent=2))
