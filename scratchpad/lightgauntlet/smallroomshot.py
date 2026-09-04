"""lightshot with a hand-placed eye, for rooms the shared rig cannot frame.

roomkit.lightshot derives the eye at `max(sx,sz) * 0.46` back from the room
centre. That works in a bedroom and fails in a 7-9 ft bathroom: in room 23 it
lands inside the east wall body, and clamping it merely moves it inside the
shower stall. Both bathrooms are ringed by full-height fixtures with one clear
corner, so the eye is given here in ROOM-LOCAL FEET (the same frame the objects
table uses) instead of derived.

Everything else -- the client-side state forcing, the focus scoping, the
cutaway settle, the metering -- is the shared rig's, imported unchanged, so
these shots stay comparable to the ones it takes.

    python smallroomshot.py --room 23 --level 1 --eye 8.5,0.7 --aim 2.0,1.4 \
        --out .../r23_round3
"""
import sys

from roomkit import lightshot

OLD = """  const target = [c.x, box.min.y + h * 0.34, c.z];
  const pos = [c.x + (alongZ ? 0 : back), box.min.y + h * 0.62, c.z + (alongZ ? back : 0)];"""
NEW = """  const target = eye
    ? [box.min.x + aim[0], box.min.y + h * 0.34, box.min.z + aim[1]]
    : [c.x, box.min.y + h * 0.34, c.z];
  const pos = eye
    ? [box.min.x + eye[0], box.min.y + h * 0.62, box.min.z + eye[1]]
    : [c.x + (alongZ ? 0 : back), box.min.y + h * 0.62, c.z + (alongZ ? back : 0)];"""
assert OLD in lightshot.SETUP_JS, "lightshot pose block moved -- re-derive the patch"
lightshot.SETUP_JS = (lightshot.SETUP_JS
                      .replace("async ({ roomId, level, light, entityIds, on }) => {",
                               "async ({ roomId, level, light, entityIds, on, eye, aim }) => {")
                      .replace(OLD, NEW))

_pair = lambda s: [float(v) for v in s.split(",")]
_eye = _aim = None
argv = []
it = iter(sys.argv[1:])
for a in it:
    if a == "--eye":
        _eye = _pair(next(it))
    elif a == "--aim":
        _aim = _pair(next(it))
    else:
        argv.append(a)
sys.argv = [sys.argv[0]] + argv

_shoot = lightshot.shoot


def shoot(page, room, out, on, level, light, settle, entity_ids):
    arg = {"roomId": room, "level": level, "light": light,
           "entityIds": entity_ids, "on": on, "eye": _eye, "aim": _aim}
    page.evaluate(lightshot.SETUP_JS, arg)
    page.wait_for_timeout(settle)
    info = page.evaluate(lightshot.SETUP_JS, arg)
    page.wait_for_timeout(400)
    page.screenshot(path=out)
    return info


lightshot.shoot = shoot

if __name__ == "__main__":
    lightshot.main()
