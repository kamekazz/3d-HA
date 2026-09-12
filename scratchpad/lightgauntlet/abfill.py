"""A/B of windowlight.js's FILL ramp alone, from one pose in one page session.

abshot.py toggles the whole module, which also puts the window ramp back, and a
before/after across two lightshot runs cannot answer a fine question at all --
the rig reproduces a frame only to about 1 sRGB level, and other agents land
changes to roomlights.js between runs. So this shoots the live frame first and
then UNDOES the fill ramp in the page, by handing the affected materials their
`__orig` back.

Which materials those are is derived, not re-implemented: at this moment the
only writer of an unbound object's emissive is windowlight, its window mode
touches only VIEW_MATS (or a whole object named "window"), so "differs from
__orig, is not a view material, is not in a window-named or entity-bound
object" is exactly the set the fill ramp wrote.

    python abfill.py <roomId> <level> <outprefix> [--on] [--day]
"""
import json, sys, os
sys.path.insert(0, os.path.abspath('../../tools'))
from roomkit.lightshot import SETUP_JS, COLLECT_JS, READY_JS, meter
from playwright.sync_api import sync_playwright

UNFILL = """
async () => {
  const objects = await import('/js/objects.js');
  const VIEW = new Set(['pane','m2pane','skyhi','skymid','wtrees','leafout','wlawn','wrail','win_glass']);
  const WINDOW_RE = /\bwindows?\b/i;
  let n = 0;
  for (const root of objects.objects3d.values()) {
    const ud = root.userData;
    if (ud.entityId || WINDOW_RE.test(ud.name || '')) continue;
    root.traverse((ch) => {
      if (!ch.isMesh) return;
      const origs = ch.userData.__orig ||
        (ch.parent?.isMesh ? ch.parent.userData.__orig : null);
      if (!origs) return;
      const mats = Array.isArray(ch.material) ? ch.material : [ch.material];
      mats.forEach((m, i) => {
        const o = origs[i];
        if (!m.emissive || !o || o.emissive === null) return;
        if (VIEW.has((m.name || '').toLowerCase().replace(/\.\d+$/, ''))) return;
        if (m.emissive.getHex() === o.emissive &&
            m.emissiveIntensity === o.emissiveIntensity) return;
        m.emissive.setHex(o.emissive);
        m.emissiveIntensity = o.emissiveIntensity;
        n += 1;
      });
    });
  }
  const { camera, renderer, scene } = window.__scene3d;
  renderer.render(scene, camera);
  return n;
}
"""

room, level, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
night = "--day" not in sys.argv
lights_on = "--on" in sys.argv
light = ({"elevation": -18, "azimuth": 0, "condition": "clear-night"} if night
         else {"elevation": 42, "azimuth": 155, "condition": "sunny"})
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    # Wait for every object GLB, not a flat timeout: SETUP_JS solves the camera
    # pose by casting rays for clear air, so a shot taken while half the
    # furniture is still loading picks a direction that is about to be a
    # cabinet -- room 6 put the eye inside its own upper cabinets and metered a
    # flat grey 99. lightshot's own main() gates on this for the same reason.
    p.wait_for_timeout(4000)
    for _ in range(60):
        st = p.evaluate(READY_JS)
        if st["total"] and st["loaded"] >= st["total"]:
            break
        p.wait_for_timeout(1000)
    ids = p.evaluate(COLLECT_JS, room)["ids"]
    arg = {"roomId": room, "level": level, "light": light, "entityIds": ids, "on": lights_on}
    info = p.evaluate(SETUP_JS, arg); p.wait_for_timeout(1500)
    arg["pose"] = info.get("pose")
    info = p.evaluate(SETUP_JS, arg); p.wait_for_timeout(900)
    res = {"room": room, "night": night, "lights_on": lights_on, "at": info["at"]}
    f = out + "_after.png"; p.screenshot(path=f)
    res["after"] = {"file": f, "meter": meter(f)}
    res["restored"] = p.evaluate(UNFILL)
    p.wait_for_timeout(300)
    f = out + "_before.png"; p.screenshot(path=f)
    res["before"] = {"file": f, "meter": meter(f)}
    if errs: res["page_errors"] = errs[:3]
    print(json.dumps(res, indent=1))
    b.close()
