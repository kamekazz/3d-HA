"""lightshot with a HAND-AIMED camera, for judging a fixture model close up.

Same safety rule as roomkit.lightshot: entity state is forced CLIENT-SIDE via
state.applyState(). Home Assistant is never called.

    python fixshot.py --room 27 --level 2 --entities light.rosemarys_closet \
        --pos 26,19.2,23.8 --target 24,25.2,15.5 --out shots/fx
"""

import argparse
import json
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from playwright.sync_api import sync_playwright  # noqa: E402
from roomkit.lightshot import BASE, READY_JS, meter  # noqa: E402

SETUP_JS = """
async ({ roomId, level, light, entityIds, on, pose }) => {
  const house = await import('/js/house.js');
  const sceneMod = await import('/js/scene.js');
  const focus = await import('/js/focus.js');
  const state = await import('/js/state.js');
  const { camera, controls, renderer, scene } = window.__scene3d;

  house.setLevel(level);
  await new Promise(r => setTimeout(r, 900));
  if (light) window.__daylight?.simulate(light);

  for (const id of entityIds) {
    const prev = state.getState(id) || {};
    state.applyState(id, { entity_id: id, state: on ? 'on' : 'off',
      attributes: { ...(prev.attributes || {}), brightness: on ? 255 : null } });
  }

  focus.enterFocus(roomId, { frame: false });
  await new Promise(r => setTimeout(r, 500));
  {
    const me = house.roomMeshes.get(roomId);
    const lvl = me?.userData.level;
    for (const [rid, m] of house.roomMeshes) {
      if (rid === roomId || m.userData.level !== lvl) continue;
      m.visible = false;
      m.userData.pickable = false;
    }
  }

  const unclamp = () => {
    for (const [k, v] of [['minDistance', 0.05], ['maxDistance', 1e6],
                          ['minPolarAngle', 0], ['maxPolarAngle', Math.PI]]) {
      try { Object.defineProperty(controls, k, { get: () => v, set() {}, configurable: true }); }
      catch (e) {}
    }
    controls.enableDamping = false;
    controls.enablePan = false;
    controls.enableRotate = false;
  };
  unclamp();
  camera.clearViewOffset();
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.fov = pose.fov;
  camera.near = 0.05;
  camera.updateProjectionMatrix();

  const P = { x: pose.pos[0], y: pose.pos[1], z: pose.pos[2] };
  const T = { x: pose.target[0], y: pose.target[1], z: pose.target[2] };
  sceneMod.flyTo(P, T);
  for (let i = 0; i < 240; i++) {
    await new Promise(r => requestAnimationFrame(r));
    const d = Math.hypot(camera.position.x - P.x, camera.position.y - P.y,
                         camera.position.z - P.z);
    const t = Math.hypot(controls.target.x - T.x, controls.target.y - T.y,
                         controls.target.z - T.z);
    if (d < 0.02 && t < 0.02) break;
  }
  unclamp();
  camera.position.set(P.x, P.y, P.z);
  controls.target.set(T.x, T.y, T.z);
  camera.lookAt(T.x, T.y, T.z);

  for (const group of house.floorGroups.values()) {
    for (const child of group.children) {
      if (child.userData.kind === 'device' || child.isSprite) child.visible = false;
    }
  }
  for (const el of document.querySelectorAll('body > *:not(#scene-container)')) {
    el.style.display = 'none';
  }
  window.__cutaway?.setEnabled(true);
  window.__cutaway?.settle();

  for (const id of entityIds) {
    const prev = state.getState(id) || {};
    state.applyState(id, { entity_id: id, state: on ? 'on' : 'off',
      attributes: { ...(prev.attributes || {}), brightness: on ? 255 : null } });
  }

  camera.clearViewOffset();
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.fov = pose.fov;
  camera.updateProjectionMatrix();
  camera.position.set(P.x, P.y, P.z);
  camera.lookAt(T.x, T.y, T.z);
  renderer.render(scene, camera);
  return { at: [+camera.position.x.toFixed(2), +camera.position.y.toFixed(2),
                +camera.position.z.toFixed(2)],
           fixtures: (window.__roomlights?.fixtures() || [])
             .filter(f => f.roomId === roomId)
             .map(f => ({ id: f.objectId, on: f.on, glow: +f.glow.toFixed(2),
                          emits: f.emits, shown: f.shown })) };
}
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--room", type=int, required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--entities", required=True)
    p.add_argument("--pos", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--fov", type=float, default=74)
    p.add_argument("--day", action="store_true")
    p.add_argument("--settle", type=int, default=1400)
    p.add_argument("--size", default="1200x900")
    a = p.parse_args()

    w, h = (int(v) for v in a.size.lower().split("x"))
    light = ({"elevation": 42, "azimuth": 155, "condition": "sunny"} if a.day
             else {"elevation": -18, "azimuth": 0, "condition": "clear-night"})
    pose = {"pos": [float(v) for v in a.pos.split(",")],
            "target": [float(v) for v in a.target.split(",")], "fov": a.fov}
    ids = [s.strip() for s in a.entities.split(",") if s.strip()]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)

    res = {"pose": pose, "entities": ids}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(2500)
        for _ in range(40):
            st = page.evaluate(READY_JS)
            if st["total"] == 0 or st["loaded"] >= st["total"]:
                break
            page.wait_for_timeout(250)
        for on, tag in ((True, "on"), (False, "off")):
            arg = {"roomId": a.room, "level": a.level, "light": light,
                   "entityIds": ids, "on": on, "pose": pose}
            page.evaluate(SETUP_JS, arg)
            page.wait_for_timeout(a.settle)
            info = page.evaluate(SETUP_JS, arg)
            page.wait_for_timeout(400)
            out = "%s_%s.png" % (a.out, tag)
            page.screenshot(path=out)
            res[tag] = {"file": out, "meter": meter(out), **info}
        browser.close()
    if errs:
        res["page_errors"] = errs[:3]
    res["delta"] = round(res["on"]["meter"]["centre"] - res["off"]["meter"]["centre"], 1)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
