"""Sweep EMISSIVE_MAX in one page session: does the lens out-glow its wall?

The critic's finding: a wall within ~2 ft of a lamp saturates at 240-252 while
the lens caps around 245, so the fixture cannot be the brightest thing in frame.
This measures both ends off the same frame -- the frame's brightest pixels (the
lens) against the 99th percentile of everything else (the near wall).
"""
import argparse, json, os, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright
from roomkit.lightshot import BASE, READY_JS, SETUP_JS, COLLECT_JS

TUNE = """
async (o) => {
  const rl = await import('/js/roomlights.js');
  const { camera, renderer, scene } = window.__scene3d;
  const got = window.__roomlights.tune(o);
  rl.settleRoomLights();
  renderer.render(scene, camera);
  return got;
}
"""

def stats(path):
    from PIL import Image
    im = Image.open(path).convert('L')
    px = sorted(im.getdata())
    n = len(px)
    return {'max': px[-1], 'p999': px[int(n*0.999)], 'p99': px[int(n*0.99)],
            'p95': px[int(n*0.95)], 'mean': round(sum(px)/n, 1),
            'clipped': sum(1 for v in px[int(n*0.99):] if v >= 254)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--room', type=int, required=True)
    p.add_argument('--level', type=int, required=True)
    p.add_argument('--emissive', required=True, help='comma list')
    p.add_argument('--fixture', type=float, default=None)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='chrome', args=[
            '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
        page = b.new_page(viewport={'width': 1000, 'height': 750}, device_scale_factor=1)
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
               'entityIds': ids, 'on': True, 'pose': None}
        first = page.evaluate(SETUP_JS, arg)
        arg['pose'] = first.get('pose')
        page.wait_for_timeout(1400)
        page.evaluate(SETUP_JS, arg)
        page.wait_for_timeout(400)
        out = []
        for e in [float(x) for x in a.emissive.split(',')]:
            o = {'emissive': e}
            if a.fixture is not None:
                o['fixture'] = a.fixture
            page.evaluate(TUNE, o)
            page.wait_for_timeout(350)
            page.evaluate(TUNE, o)
            f = '%s_e%g.png' % (a.out, e)
            page.screenshot(path=f)
            out.append({'emissive': e, 'file': f, **stats(f)})
        b.close()
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
