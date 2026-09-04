"""lightshot with the room isolation RE-ASSERTED before the frame is grabbed.

roomkit.lightshot evaluates SETUP_JS twice (the second pass re-asserts entity
state after any late rebuild). Its first line is house.setLevel(level), and
house.js setLevel() sets `child.visible = true` for every room mesh in the
floor group -- undoing focus.js's sibling hiding. focus.enterFocus() then early
-returns (`focusedRoomId === roomId`), so the isolation is never restored, and
the screenshot is taken with every OTHER room on the level visible. Their
whole-room fallback lights (CENTRE_BASE 90 cd) are not occluded by anything, so
a neighbour's lit bedroom washes through the wall into the "unlit" shot.

Nothing else is changed -- same client-side state forcing, same derived pose,
same metering -- so the numbers stay comparable apart from the leak.
"""
import sys

from roomkit import lightshot

OLD = """  focus.enterFocus(roomId, { frame: false });
  await new Promise(r => setTimeout(r, 500));"""
NEW = """  focus.enterFocus(roomId, { frame: false });
  await new Promise(r => setTimeout(r, 500));
  // re-assert isolation: setLevel() above re-showed every sibling and
  // enterFocus() early-returns when it is already focused on this room.
  {
    const me = house.roomMeshes.get(roomId);
    const lvl = me?.userData.level;
    for (const [rid, m] of house.roomMeshes) {
      if (rid === roomId || m.userData.level !== lvl) continue;
      m.visible = false;
      m.userData.pickable = false;
    }
  }"""
assert OLD in lightshot.SETUP_JS, "lightshot focus block moved -- re-derive the patch"
lightshot.SETUP_JS = lightshot.SETUP_JS.replace(OLD, NEW)


# --- optional hand-placed eye ------------------------------------------------
# The derived pose ("back" from the room centre) lands INSIDE the dresser in
# room 13. --eye X,Z and --aim X,Z give the camera in ROOM-LOCAL FEET instead
# (same frame the objects table uses); --eyey/--aimy override the heights as a
# fraction of room height. smallroomshot.py does the same trick but its assert
# is written against an older copy of the pose block.
POSE_OLD = """  const target = [c.x, box.min.y + h * 0.34, c.z];
  const pos = [c.x + (alongZ ? 0 : back), box.min.y + h * 0.62, c.z + (alongZ ? back : 0)];"""
POSE_NEW = """  const target = eye
    ? [box.min.x + aim[0], box.min.y + h * aimy, box.min.z + aim[1]]
    : [c.x, box.min.y + h * 0.34, c.z];
  const pos = eye
    ? [box.min.x + eye[0], box.min.y + h * eyey, box.min.z + eye[1]]
    : [c.x + (alongZ ? 0 : back), box.min.y + h * 0.62, c.z + (alongZ ? back : 0)];"""
assert POSE_OLD in lightshot.SETUP_JS, "pose block moved"
lightshot.SETUP_JS = (lightshot.SETUP_JS
    .replace("async ({ roomId, level, light, entityIds, on }) => {",
             "async ({ roomId, level, light, entityIds, on, eye, aim, eyey, aimy }) => {")
    .replace(POSE_OLD, POSE_NEW))

_pair = lambda s: [float(v) for v in s.split(",")]
_eye = _aim = None
_eyey, _aimy = 0.62, 0.34
_argv = []
_it = iter(sys.argv[1:])
for _a in _it:
    if _a == "--eye":
        _eye = _pair(next(_it))
    elif _a == "--aim":
        _aim = _pair(next(_it))
    elif _a == "--eyey":
        _eyey = float(next(_it))
    elif _a == "--aimy":
        _aimy = float(next(_it))
    else:
        _argv.append(_a)
sys.argv = [sys.argv[0]] + _argv


def shoot(page, room, out, on, level, light, settle, entity_ids):
    arg = {"roomId": room, "level": level, "light": light, "entityIds": entity_ids,
           "on": on, "eye": _eye, "aim": _aim, "eyey": _eyey, "aimy": _aimy}
    page.evaluate(lightshot.SETUP_JS, arg)
    page.wait_for_timeout(settle)
    info = page.evaluate(lightshot.SETUP_JS, arg)
    page.wait_for_timeout(400)
    page.screenshot(path=out)
    return info


lightshot.shoot = shoot

if __name__ == "__main__":
    lightshot.main()
