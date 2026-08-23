"""Room 17 shot poses matched to docs/v2 Hallway-jpg/, re-aimed for the
re-traced footprint (world x 6.70..18.62, z 6.55..23.44; slab Y = 18.0).

The walking strip is x 10.56..14.31. The stairwell is east of x=14.31
(open cut z 13.36..17.20, shaft room 28 z 17.20..23.44). The west arm
alcove is x 6.70..10.56, z 17.32..22.70 with doors on its S/W/N walls.
"""
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

# Every photo is a portrait phone shot held at ~5.3 ft, tilted slightly down.
POSES = {
    # hallway_looking_towards_stairs.jpg -- south end of the strip looking N,
    # knee wall running away on the RIGHT, master-bed door at the far end.
    "p_stairs":  P(12.10, 5.30, 21.90, 12.95, 4.05, 7.20),
    # hallway_with_white_runner_rug.jpg -- north end looking S down the hall,
    # knee wall on the LEFT, bath door dead ahead, sculpture near on the RIGHT.
    "p_runner":  P(12.60, 5.30, 8.40, 12.55, 3.95, 23.10),
    # staircase_looking_down.jpg -- head of the flight, looking down it.
    "p_down":    P(16.40, 6.30, 13.90, 16.30, 0.20, 21.80),
    # staircase_looking_up.jpg -- standing in the 1F hall at the foot.
    "p_up":      P(16.20, -8.20, 26.00, 16.20, -3.40, 18.40),
    # two_closed_white_doors_1.jpg -- close on the alcove corner, Rios door
    # (S wall) left, room-25 door (W wall) centre.
    "p_doors1":  P(12.40, 5.15, 19.20, 7.60, 3.40, 22.10, fov=70),
    # two_closed_white_doors_2.jpg -- one step back, all three alcove doors.
    "p_doors2":  P(13.10, 5.25, 18.30, 7.40, 3.60, 21.60, fov=74),
}

def shoot(name, level=2, tag=""):
    out = os.path.join(OUT, f"{tag}{name}.png")
    cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[name]),
           "--level", str(level), "--day", "--out", out, "--no-cutaway"]
    r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
    print(f"{name:<10} {'ok' if r.returncode == 0 else 'FAIL'}  {out}")
    if r.returncode:
        print(r.stdout[-1200:], r.stderr[-1200:])

PHOTO = {
    "p_stairs": "hallway_looking_towards_stairs.jpg",
    "p_runner": "hallway_with_white_runner_rug.jpg",
    "p_down":   "staircase_looking_down.jpg",
    "p_up":     "staircase_looking_up.jpg",
    "p_doors1": "two_closed_white_doors_1.jpg",
    "p_doors2": "two_closed_white_doors_2.jpg",
}

if __name__ == "__main__":
    tag = os.environ.get("TAG", "")
    for n in (sys.argv[1:] or list(POSES)):
        shoot(n, level=1 if n == "p_up" else 2, tag=tag)
