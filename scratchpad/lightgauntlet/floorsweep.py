"""Single-floor dollhouse view, every room's lights forced ON, WALL_FILL swept.

The per-room shots are taken in room focus, which is the one view roomlights
keeps full spill in -- this is the other one, where a dozen lit rooms are on
screen at once and a washed-out floor plan would be the regression to catch.
Client-side state only; Home Assistant is never called.
"""
import argparse, json, os, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright                # noqa: E402
from roomkit.lightshot import BASE, READY_JS, meter            # noqa: E402

SETUP = """
async ({ level, light, on }) => {
  const house = await import('/js/house.js');
  const rl = await import('/js/roomlights.js');
  const state = await import('/js/state.js');
  const focus = await import('/js/focus.js');
  if (focus.getFocusedRoomId() !== null) focus.exitFocus({ flyBack: false });
  house.setLevel(level);
  window.__daylight?.simulate(light);
  const ids = new Set();
  for (const id of rl.getAllHouseLightIds()) ids.add(id);
  for (const f of (window.__roomlights?.fixtures() || [])) ids.add(f.entityId);
  for (const id of ids) {
    const prev = state.getState(id) || {};
    state.applyState(id, { entity_id: id, state: on ? 'on' : 'off',
      attributes: { ...(prev.attributes || {}), brightness: on ? 255 : null } });
  }
  for (const el of document.querySelectorAll('body > *:not(#scene-container)')) {
    el.style.display = 'none';
  }
  await new Promise(r => setTimeout(r, 1200));
  window.__cutaway?.settle();
  return { ids: ids.size };
}
"""

TUNE = """
async ({ wall }) => {
  const rl = await import('/js/roomlights.js');
  const { camera, renderer, scene } = window.__scene3d;
  window.__roomlights.tune({ wall });
  rl.settleRoomLights();
  renderer.render(scene, camera);
  return window.__roomlights.surfaces().filter(s => s.wall > 0).length;
}
"""

p = argparse.ArgumentParser()
p.add_argument('--level', type=int, required=True)
p.add_argument('--values', required=True)
p.add_argument('--out', required=True)
p.add_argument('--day', action='store_true')
a = p.parse_args()
light = ({"elevation": 42, "azimuth": 155, "condition": "sunny"} if a.day
         else {"elevation": -18, "azimuth": 0, "condition": "clear-night"})
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
res = []
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=[
        '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 1000, 'height': 750}, device_scale_factor=1)
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.goto(BASE, wait_until='load', timeout=60000)
    page.wait_for_function('() => !!window.__scene3d', timeout=30000)
    page.wait_for_timeout(2500)
    for _ in range(40):
        st = page.evaluate(READY_JS)
        if st['total'] == 0 or st['loaded'] >= st['total']:
            break
        page.wait_for_timeout(250)
    for on, tag in ((True, 'on'), (False, 'off')):
        page.evaluate(SETUP, {'level': a.level, 'light': light, 'on': on})
        page.wait_for_timeout(2500)
        page.evaluate(SETUP, {'level': a.level, 'light': light, 'on': on})
        page.wait_for_timeout(1200)
        for v in [float(x) for x in a.values.split(',')]:
            n = page.evaluate(TUNE, {'wall': v})
            page.wait_for_timeout(400)
            n = page.evaluate(TUNE, {'wall': v})
            out = '%s_w%g_%s.png' % (a.out, v, tag)
            page.screenshot(path=out)
            res.append({'wall': v, 'state': tag, 'file': out,
                        'rooms_with_fill': n, 'meter': meter(out)})
    b.close()
print(json.dumps({'frames': res, 'errors': errs[:3]}, indent=2))
