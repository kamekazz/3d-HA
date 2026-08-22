"""Door-builder's own poses for room 17 (shots.py is shared and being edited)."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)
BASE = 18.0


def P(x, y, z, tx, ty, tz, fov=74, size=(900, 1200)):
    return {"pos": [x, BASE + y, z], "target": [tx, BASE + ty, tz],
            "fov": fov, "size": list(size)}


POSES = {
    # standing in the strip looking at the dead-end corner, like
    # two_closed_white_doors_2.jpg
    "dd_a": P(13.90, 5.20, 16.20, 10.90, 3.40, 22.60),
    "dd_b": P(13.60, 5.10, 18.60, 10.80, 3.50, 22.40),
    # square on to the bathroom door (south wall)
    "bath": P(12.45, 4.90, 18.60, 12.45, 3.80, 23.30, fov=68),
    # square on to the three west doors
    "west": P(14.10, 4.90, 20.10, 10.50, 3.80, 20.10, fov=78),
    # square on to the GUEST door alone (opening 125, world z 14.55..17.28)
    "guest_face": P(14.20, 4.95, 15.92, 10.50, 3.85, 15.92, fov=84),
    # the fix_guest_face2 framing: guest door near/right, closet + Rios receding left
    "guest_ang": P(13.60, 5.20, 13.40, 10.60, 3.60, 17.70, fov=74),
    # standing INSIDE room 26 looking north at the bath door (world x 11.40..14.20)
    "bath_inside": P(12.80, 5.00, 29.10, 12.80, 3.60, 23.40, fov=62),
    "westn": P(14.10, 4.90, 15.50, 10.50, 3.80, 16.20, fov=78),
    # the whole hall, north end looking south
    "hall_s": P(12.45, 5.35, 8.10, 12.60, 4.10, 23.00),
    # south end looking north at the master door
    "hall_n": P(12.45, 5.35, 21.60, 13.30, 4.30, 6.90),
    "doll": None,
}


def shoot(name, tag="", cut=False):
    out = os.path.join(OUT, f"{tag}{name}.png")
    cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[name]),
           "--level", "2", "--day", "--out", out]
    if not cut:
        cmd.append("--no-cutaway")
    r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
    print(f"{name:<10} {'ok' if r.returncode == 0 else 'FAIL'}  {out}")
    if r.returncode:
        print(r.stdout[-1200:], r.stderr[-1200:])


if __name__ == "__main__":
    tag = os.environ.get("TAG", "")
    for n in (sys.argv[1:] or ["dd_a", "west", "bath", "hall_s"]):
        shoot(n, tag=tag)
