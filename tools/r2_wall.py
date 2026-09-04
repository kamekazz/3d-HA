"""Fixed-pose wall probe for the light gauntlet round 2.

lightshot.py derives its pose from an 8-direction raycast for clear air, and
that probe reads the CUTAWAY state left by the previous shot in the same browser
session -- so the on and off frames of rooms 1, 7 and 8 came out from different
camera positions, and no before/after pixel comparison is possible. This rig
takes the pose as an argument instead: stand at one end of the room, look at the
far wall, so a horizontal band across the frame runs under one fixture, through
the gap, and under the next.

  python r2_wall.py --room 1 --level 0 --pos 8.3,4.5,20 --target 8.3,4.5,34.9 \
      --out ../scratchpad/lightgauntlet/shots/w1_base

Never calls Home Assistant: state is forced client-side exactly as lightshot does.
"""
import argparse
import json
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

COLLECT_JS = """
async (roomId) => {
  const rl = await import('/js/roomlights.js');
  const ids = new Set([...rl.getRoomLightIds(roomId)]);
  const fixtures = (window.__roomlights?.fixtures() || [])
    .filter(f => f.roomId === roomId);
  for (const f of fixtures) ids.add(f.entityId);
  return { ids: [...ids], fixtures };
}
"""

SETUP_JS = """
async ({ roomId, level, light, entityIds, on, pos, target, fov }) => {
  const house = await import('/js/house.js');
  const sceneMod = await import('/js/scene.js');
  const focus = await import('/js/focus.js');
  const state = await import('/js/state.js');
  const { camera, controls, renderer, scene } = window.__scene3d;

  if (focus.getFocusedRoomId() === roomId) focus.exitFocus({ flyBack: false });
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
  camera.fov = fov;
  camera.near = 0.05;
  camera.updateProjectionMatrix();

  const P = { x: pos[0], y: pos[1], z: pos[2] };
  const T = { x: target[0], y: target[1], z: target[2] };
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
  camera.fov = fov;
  camera.updateProjectionMatrix();
  camera.position.set(P.x, P.y, P.z);
  controls.target.set(T.x, T.y, T.z);
  camera.lookAt(T.x, T.y, T.z);
  renderer.render(scene, camera);

  return {
    slots: (window.__roomlights?.slots() || []).filter(s => s.owner),
    fixtures: (window.__roomlights?.fixtures() || []).filter(f => f.roomId === roomId),
    at: [+camera.position.x.toFixed(2), +camera.position.y.toFixed(2),
         +camera.position.z.toFixed(2)],
    night: +(window.__daylight?.state()?.current?.nightFactor ?? -1).toFixed(3),
  };
}
"""

READY_JS = """
async () => {
  const objects = await import('/js/objects.js');
  const roots = [...objects.objects3d.values()];
  return { total: roots.length, loaded: roots.filter(r => r.children.length > 0).length };
}
"""


def meter(path):
    from PIL import Image
    im = Image.open(path).convert("L")
    w, h = im.size
    full = list(im.getdata())
    box = im.crop((int(w * .2), int(h * .2), int(w * .8), int(h * .8)))
    bd = list(box.getdata())
    return {"mean": round(sum(full) / len(full), 1),
            "centre": round(sum(bd) / len(bd), 1),
            "p95": round(sorted(full)[int(len(full) * .95)], 1)}


def band(path, y0, y1, n=7):
    from PIL import Image
    im = Image.open(path).convert("L")
    w, h = im.size
    out = []
    for i in range(n):
        c = im.crop((int(w * i / n), int(h * y0), int(w * (i + 1) / n), int(h * y1)))
        d = list(c.getdata())
        out.append(round(sum(d) / len(d)))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--room", type=int, required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--pos", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--fov", type=float, default=70)
    p.add_argument("--out", required=True)
    p.add_argument("--entities")
    p.add_argument("--band", default="0.30,0.45", help="y0,y1 fractions for the wall band")
    p.add_argument("--settle", type=int, default=1400)
    p.add_argument("--size", default="1000x750")
    a = p.parse_args()

    w, h = (int(v) for v in a.size.lower().split("x"))
    pos = [float(v) for v in a.pos.split(",")]
    target = [float(v) for v in a.target.split(",")]
    y0, y1 = (float(v) for v in a.band.split(","))
    light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(2500)
        for _ in range(40):
            st = page.evaluate(READY_JS)
            if st["total"] == 0 or st["loaded"] >= st["total"]:
                break
            page.wait_for_timeout(250)

        collected = page.evaluate(COLLECT_JS, a.room)
        ids = ([s.strip() for s in a.entities.split(",") if s.strip()]
               if a.entities else collected["ids"])
        res = {"room": a.room, "pos": pos, "target": target, "entities": ids}
        for on, tag in ((True, "on"), (False, "off")):
            out = "%s_%s.png" % (a.out, tag)
            arg = {"roomId": a.room, "level": a.level, "light": light,
                   "entityIds": ids, "on": on, "pos": pos, "target": target,
                   "fov": a.fov}
            page.evaluate(SETUP_JS, arg)
            page.wait_for_timeout(a.settle)
            info = page.evaluate(SETUP_JS, arg)
            page.wait_for_timeout(400)
            page.screenshot(path=out)
            res[tag] = {"file": out, "meter": meter(out), "band": band(out, y0, y1),
                        "at": info["at"], "night": info["night"],
                        "slots": [(s["owner"], s["intensity"]) for s in info["slots"]]}
        browser.close()
    res["delta"] = round(res["on"]["meter"]["centre"] - res["off"]["meter"]["centre"], 1)
    if errors:
        res["page_errors"] = errors[:3]
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
