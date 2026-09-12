"""Sweep SLAB_FILL in ONE page session and shoot each value, ON and OFF.

Identical rig to wallsweep.py -- same poses, same setups, same safety rule
(entity state is forced CLIENT-SIDE only; Home Assistant is never called) --
but it drives `tune({slab})` instead of `tune({wall})`, which since the floor
skins landed moves the room's slab AND the `<Room> Floor*` GLB laid over it.

  python slabsweep.py --room 7 --level 1 --values 0,0.05,0.08,0.12 \
      --pos 29.1,12.01,25.5 --target 29.1,11.31,15.4 --out shots/ff_r7
"""
import argparse
import json
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright                          # noqa: E402
from roomkit.lightshot import BASE, READY_JS, COLLECT_JS, meter          # noqa: E402
from roomkit.lightshot import SETUP_JS as FOCUS_SETUP                    # noqa: E402
from critshot import SETUP_JS as AIMED_SETUP                             # noqa: E402

TUNE_JS = """
async ({ slab }) => {
  const rl = await import('/js/roomlights.js');
  const { camera, renderer, scene } = window.__scene3d;
  const got = window.__roomlights.tune({ slab });
  rl.settleRoomLights();
  renderer.render(scene, camera);
  return { got, slots: (window.__roomlights.slots() || []).filter(s => s.owner),
           surfaces: window.__roomlights.surfaces() };
}
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--room', type=int, required=True)
    p.add_argument('--level', type=int, required=True)
    p.add_argument('--values', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--pos')
    p.add_argument('--target')
    p.add_argument('--fov', type=float, default=74)
    p.add_argument('--day', action='store_true')
    p.add_argument('--size', default='1000x750')
    p.add_argument('--settle', type=int, default=1600)
    a = p.parse_args()

    w, h = (int(v) for v in a.size.lower().split('x'))
    vals = [float(v) for v in a.values.split(',')]
    light = ({"elevation": 42, "azimuth": 155, "condition": "sunny"} if a.day
             else {"elevation": -18, "azimuth": 0, "condition": "clear-night"})
    aimed = bool(a.pos and a.target)
    setup = AIMED_SETUP if aimed else FOCUS_SETUP
    pose = ({'pos': [float(v) for v in a.pos.split(',')],
             'target': [float(v) for v in a.target.split(',')], 'fov': a.fov}
            if aimed else None)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)

    res = {'room': a.room, 'aimed': aimed, 'day': a.day, 'frames': []}
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='chrome', args=[
            '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
        page = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
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
        ids = page.evaluate(COLLECT_JS, a.room)['ids']
        for on, tag in ((True, 'on'), (False, 'off')):
            arg = {'roomId': a.room, 'level': a.level, 'light': light,
                   'entityIds': ids, 'on': on}
            # Pin the pose for the WHOLE run, not just per pass. wallsweep.py
            # never did this on the focus path, and the clearance probe reads
            # the live scene -- so the ON and OFF frames of room 1 were shot
            # from [8.30,4.77,34.28] and [16.17,4.77,31.02], two different
            # photographs. lightshot.py's own main() solves once and feeds the
            # answer back in; do the same.
            if pose is not None:
                arg['pose'] = pose
            page.evaluate(setup, arg)
            page.wait_for_timeout(a.settle)
            info = page.evaluate(setup, arg)
            if pose is None:
                pose = info['pose']
                arg['pose'] = pose
                info = page.evaluate(setup, arg)
            page.wait_for_timeout(400)
            for v in vals:
                t = page.evaluate(TUNE_JS, {'slab': v})
                page.wait_for_timeout(300)
                t = page.evaluate(TUNE_JS, {'slab': v})
                out = '%s_s%g_%s.png' % (a.out, v, tag)
                page.screenshot(path=out)
                res['frames'].append({
                    'slab': v, 'state': tag, 'file': out, 'meter': meter(out),
                    'at': info['at'],
                    'surfaces': [s for s in t['surfaces'] if s['roomId'] == a.room],
                    'nonzero_surfaces': [s for s in t['surfaces']
                                         if s['slab'] or s['wall']],
                })
        b.close()
    if errs:
        res['page_errors'] = errs[:3]
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
