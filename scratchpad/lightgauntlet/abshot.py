"""A/B of windowlight.js from ONE pose: the lightshot room framing, lights OFF,
shot twice with __windowlight.setEnabled(false) then (true).

--nocut disables the wall cutaway for the shot. It is the only way to judge a
window that is bound to a NEAR wall: cutaway.js fades that wall and takes its
windows with it, so "Dining Windows" (five units on four walls of one GLB) is
not in a focused dining-room frame at all.

    python abshot.py <roomId> <level> <outprefix> [--day] [--nocut]
"""
import json, sys, os
sys.path.insert(0, os.path.abspath('../../tools'))
from roomkit.lightshot import SETUP_JS, COLLECT_JS, meter
from playwright.sync_api import sync_playwright

POSE = """
async ({ pos, target }) => {
  const { camera, controls, renderer, scene } = window.__scene3d;
  camera.position.set(pos[0], pos[1], pos[2]);
  controls.target.set(target[0], target[1], target[2]);
  controls.update();
  camera.updateMatrixWorld(true);
  window.__cutaway?.settle();
  renderer.render(scene, camera);
  return { at: camera.position.toArray().map(v => +v.toFixed(1)) };
}
"""

NOCUT = """
async () => {
  window.__cutaway?.setEnabled(false);
  window.__cutaway?.settle();
  const { camera, renderer, scene } = window.__scene3d;
  renderer.render(scene, camera);
}
"""
room, level, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
night = "--day" not in sys.argv
nocut = "--nocut" in sys.argv
light = ({"elevation": -18, "azimuth": 0, "condition": "clear-night"} if night
         else {"elevation": 42, "azimuth": 155, "condition": "sunny"})
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(9000)
    ids = p.evaluate(COLLECT_JS, room)["ids"]
    arg = {"roomId": room, "level": level, "light": light, "entityIds": ids, "on": False}
    p.evaluate(SETUP_JS, arg); p.wait_for_timeout(1500)
    info = p.evaluate(SETUP_JS, arg); p.wait_for_timeout(600)
    if nocut:
        p.evaluate(NOCUT); p.wait_for_timeout(600)
    pose = os.environ.get("ABSHOT_POSE")
    if pose:
        px, py, pz, tx, ty, tz = (float(v) for v in pose.split(","))
        info = p.evaluate(POSE, {"pos": [px, py, pz], "target": [tx, ty, tz]})
        p.wait_for_timeout(500)
    res = {"room": room, "night": night, "nocut": nocut, "at": info["at"]}
    for tag, on in (("before", False), ("after", True)):
        p.evaluate("(v) => window.__windowlight.setEnabled(v)", on)
        p.wait_for_timeout(700)
        f = "%s_%s.png" % (out, tag)
        p.screenshot(path=f)
        res[tag] = {"file": f, "meter": meter(f)}
    if errs:
        res["page_errors"] = errs[:3]
    print(json.dumps(res, indent=1))
    b.close()
