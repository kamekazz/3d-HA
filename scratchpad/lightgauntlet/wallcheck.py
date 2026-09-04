"""Invariant checks for the night wall fill: hover, suspend, off-state, day.

No Home Assistant calls: state is forced client-side, exactly as lightshot does.
"""
import argparse, json, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright                      # noqa: E402
from roomkit.lightshot import BASE, READY_JS, COLLECT_JS             # noqa: E402
from roomkit.lightshot import SETUP_JS as FOCUS_SETUP                # noqa: E402

INSTALL = """
async ({ roomId }) => {
  const objects = await import('/js/objects.js');
  const res = await fetch('/api/house').then(r => r.json());
  const ids = [];
  for (const f of res.floors) for (const r of f.rooms) {
    if (r.id !== roomId) continue;
    for (const o of r.objects || []) if (/\\bwall wash\\b/i.test(o.name || '')) ids.push(o.id);
  }
  window.__skinIds = ids;
  window.__skinPeak = () => {
    let peak = 0, n = 0;
    for (const id of window.__skinIds) {
      const root = objects.objects3d.get(id);
      if (!root) continue;
      root.traverse((c) => {
        if (!c.isMesh || !c.material) return;
        const mats = Array.isArray(c.material) ? c.material : [c.material];
        for (const m of mats) {
          if (!m.emissive) continue;
          n += 1;
          peak = Math.max(peak, m.emissive.r * (m.emissiveIntensity ?? 1));
        }
      });
    }
    return { mats: n, peak: +peak.toFixed(4) };
  };
  return ids;
}
"""

CHECK = """
async ({ roomId }) => {
  const house = await import('/js/house.js');
  const rl = await import('/js/roomlights.js');
  const mesh = house.roomMeshes.get(roomId);
  const read = (tag) => {
    const w = house.wallParts(mesh)[0];
    return { tag,
      shellEmR: +w.material.emissive.r.toFixed(4),
      shellEi: w.material.emissiveIntensity,
      shellOpacity: +w.material.opacity.toFixed(3),
      fillEmissive: +(mesh.userData.fillEmissive || 0).toFixed(4),
      accentEmissive: +(mesh.userData.accentEmissive || 0).toFixed(4),
      skins: window.__skinPeak() };
  };
  const out = [];
  rl.settleRoomLights();
  out.push(read('settled'));
  house.paintRoomEmissive(mesh, 0.15);              // hover boost
  out.push(read('hovered'));
  house.paintRoomEmissive(mesh, mesh.userData.baseEmissive ?? 0);
  out.push(read('unhovered'));
  const restore = rl.suspendRoomLights();           // room-card capture
  out.push(read('suspended'));
  restore();
  out.push(read('restored'));
  return out;
}
"""

p = argparse.ArgumentParser()
p.add_argument('--room', type=int, required=True)
p.add_argument('--level', type=int, required=True)
p.add_argument('--day', action='store_true')
a = p.parse_args()
light = ({"elevation": 42, "azimuth": 155, "condition": "sunny"} if a.day
         else {"elevation": -18, "azimuth": 0, "condition": "clear-night"})

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=[
        '--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 900, 'height': 700}, device_scale_factor=1)
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
    print('skin ids', page.evaluate(INSTALL, {'roomId': a.room}))
    ids = page.evaluate(COLLECT_JS, a.room)['ids']
    for on in (True, False):
        arg = {'roomId': a.room, 'level': a.level, 'light': light,
               'entityIds': ids, 'on': on}
        page.evaluate(FOCUS_SETUP, arg); page.wait_for_timeout(1500)
        page.evaluate(FOCUS_SETUP, arg); page.wait_for_timeout(400)
        print(('ON ' if on else 'OFF') + ' day=' + str(a.day))
        for row in page.evaluate(CHECK, {'roomId': a.room}):
            print('   ', json.dumps(row))
    if errs:
        print('ERRORS', errs[:3])
    b.close()
