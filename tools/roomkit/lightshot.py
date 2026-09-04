"""Shoot one room with its lights forced ON and forced OFF, and meter the pair.

This is the light gauntlet's eyes. Two rules make it safe and repeatable:

  * It NEVER calls Home Assistant. Turning a room's lights "on" here means
    calling state.js applyState() in the page, so the browser believes the
    entity is on. The real house is untouched -- this is a rendering test, and
    nobody's actual bedside lamp should flick on because a critic took a shot.
  * The pose is DERIVED from the room's own world-space Box3, not hand-authored
    per room, so a new room needs no poses.json entry. The framing is Sims-like:
    an angled overhead looking down into the room, which is the view that shows
    both the pool of light on the floor and the wash up the walls.

    python -m roomkit.lightshot --room 6 --out shots/kitchen
      -> shots/kitchen_on.png, shots/kitchen_off.png, and a JSON metering line

The app must already be running (http://127.0.0.1:5000).
"""

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

# Entities a room "owns" for the purposes of this test: the light.* ids
# roomlights already attributes to the room, plus whatever its furniture is
# bound to (which may be a switch.* -- a switch-controlled lamp is common here).
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

# The room is framed by the app's OWN room focus, not a pose derived from the
# room's bounds. A derived pose has to guess a standoff, and any standoff wide
# enough to see a whole room puts the camera outside the shell -- the first
# version of this shot every room from above the roof. enterFocus() already
# solves that (it frames the room's world Box3 and scopes the scene to it), and
# roomlights.js deliberately keeps FULL light spill in focus, which is exactly
# the view a lamp is meant to be judged in.
SETUP_JS = """
async ({ roomId, level, light, entityIds, on, pose: given }) => {
  const house = await import('/js/house.js');
  const sceneMod = await import('/js/scene.js');
  const focus = await import('/js/focus.js');
  const state = await import('/js/state.js');
  const { camera, controls, renderer, scene } = window.__scene3d;

  // This whole function is run TWICE per shot (once, then re-asserted after the
  // settle, so a late model load cannot leave a stale pose or state). That
  // makes the focus scope order load-bearing: setLevel re-shows every room on
  // the level, undoing the sibling-hiding enterFocus did on the first pass --
  // and enterFocus then early-returns, because it is already focused on this
  // room. The result was sibling rooms holding pool slots at CENTRE_BASE (90
  // cd) during the re-assert, and a point light is occluded by nothing, so
  // they lit the subject straight through its walls. Every "unlit" shot came
  // out with a false ambient floor. Drop focus first so the re-entry is real.
  if (focus.getFocusedRoomId() === roomId) focus.exitFocus({ flyBack: false });
  house.setLevel(level);
  await new Promise(r => setTimeout(r, 900));
  if (light) window.__daylight?.simulate(light);

  // --- the whole point: believe these entities are on/off, locally ---
  // A dimmable bulb reports brightness; pin it to full so "on" means the same
  // thing in every room regardless of what the real bulb was last set to.
  for (const id of entityIds) {
    const prev = state.getState(id) || {};
    state.applyState(id, {
      entity_id: id,
      state: on ? 'on' : 'off',
      attributes: { ...(prev.attributes || {}), brightness: on ? 255 : null },
    });
  }

  // Focus is used for its SCOPING only -- it hides the sibling rooms, their
  // furniture and the stairs, which is what makes one room judgeable on its
  // own. Its framing is not used: enterFocus and floorview both issue a fly-to
  // on the same level change, and whichever lands second wins, which parked
  // early runs of this at the whole-house framing 125 ft up. So the camera is
  // taken outright afterwards, the way shot.py does it.
  focus.enterFocus(roomId, { frame: false });
  await new Promise(r => setTimeout(r, 500));

  const THREE = await import('three');
  const mesh = house.roomMeshes.get(roomId);
  if (!mesh) return { error: 'no mesh for room ' + roomId };
  mesh.updateWorldMatrix(true, true);
  const box = new THREE.Box3().setFromObject(mesh);
  const c = box.getCenter(new THREE.Vector3());
  const s = box.getSize(new THREE.Vector3());

  // The eye goes INSIDE the room's air volume. Any standoff wide enough to see
  // a whole room from outside is also outside the shell, and then the roof is
  // what gets photographed. Inside, nothing occludes: the near walls are faded
  // by the cutaway and the ceiling with them.
  // The tilt is a compromise the room has to satisfy on both counts: aimed low
  // it shows the pool of light on the floor but crops the ceiling, and most of
  // this house's fixtures are ceiling-mounted -- a shot that cannot see the
  // fixture cannot show whether the fixture glows. Eye a little above
  // mid-height looking slightly down keeps the floor pool and the ceiling
  // fitting in one 74-degree frame.
  const h = Math.max(6, s.y);
  const want = Math.max(s.x, s.z) * 0.46;
  const target = [c.x, box.min.y + h * 0.34, c.z];

  // Where to stand. Backing off along the room's long axis is right on an empty
  // rectangle and wrong in a real room: six of the seven first-floor rooms put
  // the eye inside a cabinet, a shelf box or a slab, and the shot came back as
  // a frame of solid brown with a delta near zero. So probe first -- cast a ray
  // out from the room centre at eye height along eight compass directions, take
  // whichever has the most clear air, and stop short of whatever it does hit.
  // Walls count as hits on purpose: they are what keeps the camera in the room.
  // ...and probed ONCE per pair, never per pass. The probe reads the live scene,
  // and the scene is not the same on the second pass: the first has already
  // enabled the cutaway and hidden the device markers, so the rays fly further
  // and a different direction can win. In a near-square room several directions
  // sit within a foot of each other, so the winner flips -- room 15 shot its ON
  // frame from the east wall and its OFF frame from a diagonal, and the delta
  // between two different photographs means nothing. The caller solves the pose
  // on the first pass and hands the same one back for every pass after it.
  const eyeY = box.min.y + h * 0.62;
  const from = new THREE.Vector3(c.x, eyeY, c.z);
  const rc = new THREE.Raycaster();
  rc.far = want + 3;
  const D = 0.7071;
  const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0],
                [D, D], [-D, D], [D, -D], [-D, -D]];
  let best = null;
  for (const [dx, dz] of dirs) {
    const dir = new THREE.Vector3(dx, 0, dz).normalize();
    rc.set(from, dir);
    // Raycaster skips objects flagged invisible, but not ones whose PARENT is
    // hidden -- and focus hides whole rooms by their group. Walk the chain.
    const hits = rc.intersectObjects(scene.children, true).filter((hit) => {
      for (let n = hit.object; n; n = n.parent) if (!n.visible) return false;
      return true;
    });
    const clear = hits.length ? hits[0].distance : rc.far;
    if (!best || clear > best.clear) best = { dir, clear };
  }
  // 0.7 ft of standoff from whatever was hit, and never closer than 1.6 ft or
  // the near plane starts clipping through the furniture in front of the eye.
  const dist = Math.min(want, Math.max(1.6, best.clear - 0.7));
  const solved = { pos: [c.x + best.dir.x * dist, eyeY, c.z + best.dir.z * dist],
                   target, fov: 74,
                   probe: { clear: +best.clear.toFixed(2), dist: +dist.toFixed(2) } };
  const pose = given || solved;

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

  // Re-assert the state last: a rebuild triggered by the level change or a late
  // model load refetches HA state and would put the lamp back to its real value.
  for (const id of entityIds) {
    const prev = state.getState(id) || {};
    state.applyState(id, {
      entity_id: id,
      state: on ? 'on' : 'off',
      attributes: { ...(prev.attributes || {}), brightness: on ? 255 : null },
    });
  }

  camera.clearViewOffset();
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.fov = pose.fov;
  camera.updateProjectionMatrix();
  renderer.render(scene, camera);

  const slots = (window.__roomlights?.slots() || []).filter(s => s.owner);
  const probe = pose.probe;
  const mine = (window.__roomlights?.fixtures() || []).filter(f => f.roomId === roomId);
  return { slots, fixtures: mine, probe, pose,
           night: +(window.__daylight?.state()?.current?.nightFactor ?? -1).toFixed(3),
           at: [+camera.position.x.toFixed(2), +camera.position.y.toFixed(2),
                +camera.position.z.toFixed(2)] };
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
    """Mean luminance of the frame and of its centre box, 0-255."""
    from PIL import Image
    im = Image.open(path).convert("L")
    w, h = im.size
    full = list(im.getdata())
    box = im.crop((int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8)))
    bd = list(box.getdata())
    return {
        "mean": round(sum(full) / len(full), 1),
        "centre": round(sum(bd) / len(bd), 1),
        "p95": round(sorted(full)[int(len(full) * 0.95)], 1),
    }


def shoot(page, room, out, on, level, light, settle, entity_ids, pose=None):
    """One frame. `pose` pins the camera; the first call solves it and returns it
    so the rest of the pair reuses it -- see the probe comment in SETUP_JS."""
    arg = {"roomId": room, "level": level, "light": light,
           "entityIds": entity_ids, "on": on, "pose": pose}
    first = page.evaluate(SETUP_JS, arg)
    arg["pose"] = pose or first.get("pose")
    page.wait_for_timeout(settle)
    info = page.evaluate(SETUP_JS, arg)   # re-assert after any late rebuild
    page.wait_for_timeout(400)
    page.screenshot(path=out)
    return info


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--room", type=int, required=True)
    p.add_argument("--level", type=int, required=True,
                   help="floor LEVEL (not floor id): 0 basement, 1 first, 2 second")
    p.add_argument("--out", required=True, help="prefix; _on.png/_off.png appended")
    p.add_argument("--entities", help="comma-separated override of what to force")
    p.add_argument("--night", action="store_true", default=True)
    p.add_argument("--day", dest="night", action="store_false")
    p.add_argument("--settle", type=int, default=1400)
    p.add_argument("--size", default="1000x750")
    a = p.parse_args()

    w, h = (int(v) for v in a.size.lower().split("x"))
    # daylight.simulate() takes a SUN override, not a clock: {elevation, azimuth,
    # condition}. Handing it {hour: 22} makes the sun direction NaN, which
    # propagates through nightFactor into every pool light's intensity as NaN --
    # a black frame with no error anywhere. Keep these two dicts in the shape
    # shot.py uses.
    light = ({"elevation": -18, "azimuth": 0, "condition": "clear-night"}
             if a.night else
             {"elevation": 42, "azimuth": 155, "condition": "sunny"})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=1)
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

        res = {"room": a.room, "level": a.level, "entities": ids,
               "fixtures": collected["fixtures"]}
        pose = None
        for on, tag in ((True, "on"), (False, "off")):
            out = "%s_%s.png" % (a.out, tag)
            info = shoot(page, a.room, out, on, a.level, light, a.settle, ids, pose)
            pose = pose or info.get("pose")
            res[tag] = {"file": out, "meter": meter(out), "slots": info["slots"],
                        "fixtures": info["fixtures"], "night": info["night"],
                        "at": info["at"]}
        browser.close()

    res["delta"] = round(res["on"]["meter"]["centre"] - res["off"]["meter"]["centre"], 1)
    if errors:
        res["page_errors"] = errors[:3]
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
