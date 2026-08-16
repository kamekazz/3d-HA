"""Regression check: a room-wide surface object must not steal the room's clicks.

Builders place floors/ceilings/wall washes as objects. pick() raycasts objects
before rooms, so an un-guarded room-sized floor plane would swallow every click
in that room and the room editor could never be opened. objects.js marks those
`pickable:false` by name; this asserts the whole chain still holds in the app.

    python -m roomkit.check_pick 15

Exits non-zero if a click at the centre of the room does not resolve to the room.
"""

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

JS = """
async ({ roomId, level }) => {
  const THREE = await import('three');
  const house = await import('/js/house.js');
  const objects = await import('/js/objects.js');
  const { camera, scene } = window.__scene3d;

  house.setLevel(level);
  await new Promise(r => setTimeout(r, 700));

  const mesh = house.roomMeshes.get(roomId);
  if (!mesh) return { error: 'no such room in the scene' };

  const ownerOf = (o) => { let n = o; while (n && !n.userData?.kind) n = n.parent; return n; };
  // pick() filters every hit through isShown; without it these rays run
  // straight through the hidden floors below and report their furniture
  const isShown = (o) => { let n = o; while (n) { if (!n.visible) return false; n = n.parent; } return true; };

  // A single ray at the room centre proves nothing: real furniture legitimately
  // sits there (an island, a bed), and clicking it SHOULD select it. The real
  // regression is a room-sized surface leaving NO floor anywhere to click. So
  // sample a grid across the footprint and count where each click lands.
  const box = new THREE.Box3().setFromObject(mesh);
  const N = 7, pad = 0.12;
  const objRoots = [...objects.objects3d.values()];
  let toRoom = 0, toObject = 0, offRoom = 0;
  const blockers = {};
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < N; j++) {
      const fx = pad + (1 - 2 * pad) * i / (N - 1);
      const fz = pad + (1 - 2 * pad) * j / (N - 1);
      const x = box.min.x + fx * (box.max.x - box.min.x);
      const z = box.min.z + fz * (box.max.z - box.min.z);
      const ray = new THREE.Raycaster(new THREE.Vector3(x, box.max.y + 40, z),
                                      new THREE.Vector3(0, -1, 0));
      if (ray.intersectObject(mesh, true).length === 0) { offRoom++; continue; }
      let winner = null;
      for (const h of ray.intersectObjects(objRoots, true)) {
        const owner = ownerOf(h.object);
        if (!owner || !isShown(h.object)) continue;
        if (owner.userData.pickable !== false) { winner = owner; break; }
      }
      if (winner) {
        toObject++;
        const k = `${winner.userData.name} (room ${winner.userData.roomId})`;
        blockers[k] = (blockers[k] || 0) + 1;
      } else {
        toRoom++;
      }
    }
  }

  const surfaces = objRoots
    .filter(o => o.userData.roomId === roomId)
    .map(o => ({ name: o.userData.name, pickable: o.userData.pickable !== false }));

  return { sampled: N * N, toRoom, toObject, offRoom, blockers, surfaces };
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
        page = browser.new_page(viewport={"width": 900, "height": 700})
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(3500)
        res = page.evaluate(JS, {"roomId": a.room, "level": a.level})
        browser.close()

    print(json.dumps(res, indent=2))
    if res.get("error"):
        sys.exit(f"FAIL: {res['error']}")
    on_room = res["sampled"] - res["offRoom"]
    if on_room == 0:
        sys.exit(f"FAIL: no sample point landed on room {a.room} at all")
    if res["toRoom"] == 0:
        worst = max(res["blockers"], key=res["blockers"].get)
        sys.exit(f"FAIL: every one of the {on_room} points inside room {a.room} "
                 f"hits an object ({worst} worst) — the room can never be "
                 f"selected. Name room-sized surfaces so SURFACE_RE matches "
                 f"(floor/ceiling/wall wash/baseboards/crown), or shrink them.")
    pct = 100 * res["toRoom"] / on_room
    print(f"OK: room {a.room} is selectable — {res['toRoom']}/{on_room} floor "
          f"samples ({pct:.0f}%) resolve to the room, {res['toObject']} to "
          f"furniture ({len(res['surfaces'])} objects placed)")


if __name__ == "__main__":
    main()
