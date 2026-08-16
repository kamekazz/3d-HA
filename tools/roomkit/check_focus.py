"""Verify room focus really isolates one room, and measure what it saves.

Focus used to ghost sibling rooms at opacity 0.04, which still drew every wall
and left every other room's furniture at full cost — so "isolate a room" made
the scene slower, not faster. This asserts the new behaviour: entering focus
hides sibling rooms and their furniture, and exiting restores everything.

Reports renderer.info draw calls and triangles before/after so the saving is a
measurement rather than a claim.

    python -m roomkit.check_focus 5 --level 1
"""

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

JS = """
async ({ roomId, level }) => {
  const house = await import('/js/house.js');
  const focus = await import('/js/focus.js');
  const objects = await import('/js/objects.js');
  const { renderer, scene, camera } = window.__scene3d;

  const settle = async (n = 30) => {
    for (let i = 0; i < n; i++) await new Promise(r => requestAnimationFrame(r));
  };

  house.setLevel(level);
  await settle(40);

  const snap = () => {
    renderer.info.reset();
    renderer.render(scene, camera);
    const rooms = [...house.roomMeshes.entries()]
      .filter(([, m]) => m.userData.level === level);
    const objs = [...objects.objects3d.values()]
      .filter(o => o.userData.level === level);
    return {
      calls: renderer.info.render.calls,
      tris: renderer.info.render.triangles,
      roomsVisible: rooms.filter(([, m]) => m.visible).length,
      roomsOnLevel: rooms.length,
      objsVisible: objs.filter(o => o.visible).length,
      objsOnLevel: objs.length,
    };
  };

  const before = snap();
  focus.enterFocus(roomId);
  await settle(90);              // let the fly-to finish
  const during = snap();
  const focused = house.roomMeshes.get(roomId);
  const focusedVisible = !!focused && focused.visible;
  const otherRoomsShown = [...house.roomMeshes.entries()]
    .filter(([id, m]) => m.userData.level === level && id !== roomId && m.visible)
    .map(([id]) => id);
  const otherObjsShown = [...objects.objects3d.values()]
    .filter(o => o.userData.level === level && o.userData.roomId !== roomId && o.visible)
    .map(o => o.userData.name);

  focus.exitFocus({ flyBack: false });
  await settle(60);
  const after = snap();

  return { before, during, after, focusedVisible, otherRoomsShown, otherObjsShown };
}
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("room", type=int)
    p.add_argument("--level", type=int, required=True)
    a = p.parse_args()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(4000)
        res = page.evaluate(JS, {"roomId": a.room, "level": a.level})
        browser.close()

    print(json.dumps(res, indent=2))
    if errs:
        print("PAGE ERRORS:", errs[:3], file=sys.stderr)

    b, d, af = res["before"], res["during"], res["after"]
    fail = []
    if not res["focusedVisible"]:
        fail.append("the focused room itself is not visible")
    if res["otherRoomsShown"]:
        fail.append(f"other rooms still drawn: {res['otherRoomsShown']}")
    if res["otherObjsShown"]:
        fail.append(f"other rooms' furniture still drawn: {res['otherObjsShown'][:6]}")
    if af["roomsVisible"] != b["roomsVisible"]:
        fail.append(f"exit did not restore rooms ({af['roomsVisible']} vs {b['roomsVisible']})")
    if af["objsVisible"] != b["objsVisible"]:
        fail.append(f"exit did not restore furniture ({af['objsVisible']} vs {b['objsVisible']})")
    if d["calls"] >= b["calls"]:
        fail.append(f"focus did not reduce draw calls ({b['calls']} -> {d['calls']})")

    if fail:
        for f in fail:
            print("FAIL:", f)
        sys.exit(1)

    print(f"\nOK: focusing room {a.room} isolates it and cuts the scene down.")
    print(f"  rooms drawn     {b['roomsVisible']}/{b['roomsOnLevel']} -> {d['roomsVisible']}")
    print(f"  furniture drawn {b['objsVisible']}/{b['objsOnLevel']} -> {d['objsVisible']}")
    print(f"  draw calls      {b['calls']} -> {d['calls']}"
          f"  ({100 * (b['calls'] - d['calls']) / max(b['calls'], 1):.0f}% fewer)")
    print(f"  triangles       {b['tris']:,} -> {d['tris']:,}"
          f"  ({100 * (b['tris'] - d['tris']) / max(b['tris'], 1):.0f}% fewer)")
    print(f"  restored on exit: {af['calls']} calls, {af['roomsVisible']} rooms")


if __name__ == "__main__":
    main()
