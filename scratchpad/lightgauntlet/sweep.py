"""Sweep FIXTURE_BASE / FILL_BASE in ONE page session and shoot each combo.

Safety unchanged: entity state is forced client-side only (roomkit.lightshot's
SETUP_JS); Home Assistant is never called.

  python sweep.py --room 13 --level 2 --combos 28:0.6,28:2,28:4,28:8 --out shots/sw13
"""
import argparse, json, os, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright                      # noqa: E402
from roomkit.lightshot import BASE, READY_JS, SETUP_JS, COLLECT_JS, meter  # noqa: E402

TUNE_JS = """
async ({ fixture, fill, slab }) => {
  const rl = await import('/js/roomlights.js');
  const { camera, renderer, scene } = window.__scene3d;
  const got = window.__roomlights.tune({ fixture, fill, slab });
  rl.settleRoomLights();
  renderer.render(scene, camera);
  return { got, slots: (window.__roomlights.slots() || []).filter(s => s.owner),
           fills: window.__roomlights.fills() };
}
"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--room', type=int, required=True)
    p.add_argument('--level', type=int, required=True)
    p.add_argument('--combos', required=True, help='fixture:fill,fixture:fill,...')
    p.add_argument('--out', required=True)
    p.add_argument('--size', default='1000x750')
    p.add_argument('--settle', type=int, default=1400)
    a = p.parse_args()
    w, h = (int(v) for v in a.size.lower().split('x'))
    combos = []
    for c in a.combos.split(','):
        v = [float(x) for x in c.split(':')]
        while len(v) < 3:
            v.append(0.0)
        combos.append(tuple(v))
    light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    res = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='chrome', args=[
            '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
        page = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
        page.goto(BASE, wait_until='load', timeout=60000)
        page.wait_for_function('() => !!window.__scene3d', timeout=30000)
        page.wait_for_timeout(2500)
        for _ in range(40):
            st = page.evaluate(READY_JS)
            if st['total'] == 0 or st['loaded'] >= st['total']:
                break
            page.wait_for_timeout(250)
        ids = page.evaluate(COLLECT_JS, a.room)['ids']
        arg = {'roomId': a.room, 'level': a.level, 'light': light,
               'entityIds': ids, 'on': True}
        page.evaluate(SETUP_JS, arg)
        page.wait_for_timeout(a.settle)
        page.evaluate(SETUP_JS, arg)
        page.wait_for_timeout(400)
        for fx, fl, sb in combos:
            arg2 = {'fixture': fx, 'fill': fl, 'slab': sb}
            info = page.evaluate(TUNE_JS, arg2)
            page.wait_for_timeout(400)
            page.evaluate(TUNE_JS, arg2)
            out = '%s_f%g_l%g_s%g.png' % (a.out, fx, fl, sb)
            page.screenshot(path=out)
            res.append({'fixture': fx, 'fill': fl, 'slab': sb, 'file': out,
                        'meter': meter(out), 'slots': info['slots']})
        b.close()
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    main()
