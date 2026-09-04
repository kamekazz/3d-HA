"""Inspect the room-wall emissive after a lightshot setup: is it written, and
is the wall mesh actually the surface the camera sees?"""
import argparse, json, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from playwright.sync_api import sync_playwright                      # noqa: E402
from roomkit.lightshot import BASE, READY_JS, COLLECT_JS             # noqa: E402
from roomkit.lightshot import SETUP_JS as FOCUS_SETUP                # noqa: E402
from critshot import SETUP_JS as AIMED_SETUP                         # noqa: E402

PROBE = """
async ({ roomId, wall }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  const rl = await import('/js/roomlights.js');
  window.__roomlights.tune({ wall });
  rl.settleRoomLights();
  const mesh = house.roomMeshes.get(roomId);
  const ud = mesh.userData;
  const walls = house.wallParts(mesh).map(w => ({
    edge: w.userData.edgeIndex, vis: w.visible,
    op: +w.material.opacity.toFixed(2),
    em: [w.material.emissive.r, w.material.emissive.g, w.material.emissive.b]
          .map(v => +v.toFixed(4)),
    ei: w.material.emissiveIntensity,
  }));
  // what does the camera actually hit? cast a fan of rays from the eye
  const { camera, scene } = window.__scene3d;
  const rc = new THREE.Raycaster();
  const hits = {};
  for (let i = 0; i < 11; i++) for (let j = 0; j < 9; j++) {
    rc.setFromCamera(new THREE.Vector2(-0.9 + i * 0.18, -0.6 + j * 0.16), camera);
    const hit = rc.intersectObjects(scene.children, true)
      .find(h => h.object.visible && h.object.material
                 && (h.object.material.opacity ?? 1) > 0.5);
    if (!hit) continue;
    let owner = hit.object, kind = hit.object.userData.part || '';
    for (let n = hit.object; n; n = n.parent) {
      if (n.userData.kind === 'object') { owner = n; kind = 'object:' + (n.userData.name || n.name); break; }
      if (n.userData.part === 'wall') { kind = 'room-wall'; break; }
      if (n.userData.kind === 'room') { break; }
    }
    hits[kind] = (hits[kind] || 0) + 1;
  }
  return { fillEmissive: ud.fillEmissive, accentEmissive: ud.accentEmissive,
           walls, hits, surfaces: window.__roomlights.surfaces().filter(s => s.roomId === roomId) };
}
"""

p = argparse.ArgumentParser()
p.add_argument('--room', type=int, required=True)
p.add_argument('--level', type=int, required=True)
p.add_argument('--wall', type=float, default=0.15)
p.add_argument('--pos'); p.add_argument('--target'); p.add_argument('--fov', type=float, default=74)
a = p.parse_args()
aimed = bool(a.pos and a.target)
setup = AIMED_SETUP if aimed else FOCUS_SETUP
light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome', args=['--use-gl=angle', '--enable-unsafe-swiftshader', '--hide-scrollbars'])
    page = b.new_page(viewport={'width': 1000, 'height': 750}, device_scale_factor=1)
    errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    page.goto(BASE, wait_until='load', timeout=60000)
    page.wait_for_function('() => !!window.__scene3d', timeout=30000)
    page.wait_for_timeout(2500)
    for _ in range(40):
        st = page.evaluate(READY_JS)
        if st['total'] == 0 or st['loaded'] >= st['total']: break
        page.wait_for_timeout(250)
    ids = page.evaluate(COLLECT_JS, a.room)['ids']
    arg = {'roomId': a.room, 'level': a.level, 'light': light, 'entityIds': ids, 'on': True}
    if aimed:
        arg['pose'] = {'pos': [float(v) for v in a.pos.split(',')],
                       'target': [float(v) for v in a.target.split(',')], 'fov': a.fov}
    page.evaluate(setup, arg); page.wait_for_timeout(1600)
    page.evaluate(setup, arg); page.wait_for_timeout(400)
    print(json.dumps(page.evaluate(PROBE, {'roomId': a.room, 'wall': a.wall}), indent=1))
    if errs: print('ERRORS', errs[:3])
    b.close()
