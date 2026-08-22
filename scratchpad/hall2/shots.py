"""Room 17 shot driver -- poses matched to the docs/v2 Hallway photos."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)

gen = json.loads(subprocess.run([PY, "-m", "roomkit.rooms", "17", "--poses-only"],
                                cwd=TOOLS, capture_output=True, text=True).stdout)

# world feet. room 17 rect x 10.50..18.60, z 6.60..23.30; walking strip x 10.50..14.45
# floor 3 (level 2) has its slab at world Y = 18.0 -- every eye height is BASE + h.
BASE = 18.0
def P(x, y, z, tx, ty, tz, fov=74, size=(900, 1200)):
    return {"pos": [x, BASE + y, z], "target": [tx, BASE + ty, tz],
            "fov": fov, "size": list(size)}

POSES = dict(gen)
POSES.update({
    # 'hallway_looking_towards_stairs' -- south end of the strip, looking north
    "v2_north": P(12.45, 5.35, 21.60, 13.30, 4.30, 6.90),
    # 'hallway_with_white_runner_rug' -- north end, looking south down the hall
    "v2_south": P(12.45, 5.35, 8.10, 12.60, 4.10, 23.00),
    # 'staircase_looking_down' -- head of the flight, looking down it
    "v2_down": P(16.30, 6.40, 13.20, 16.30, 0.60, 21.50),
    # 'two_closed_white_doors_*' -- the south dead end, looking at the doors
    "v2_doors": P(13.40, 5.10, 20.10, 11.10, 3.30, 22.80),
})

def shoot(name, level=2, tag=""):
    """v2_* poses stand inside the room like the photographer did, so they keep
    the ceiling and all four walls; doll/plan poses keep the cutaway."""
    out = os.path.join(OUT, f"{tag}{name}.png")
    cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[name]),
           "--level", str(level), "--day", "--out", out]
    if name.startswith("v2_"):
        cmd.append("--no-cutaway")
    r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
    print(f"{name:<12} {'ok' if r.returncode == 0 else 'FAIL'}  {out}")
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-1500:])

if __name__ == "__main__":
    tag = os.environ.get("TAG", "")
    names = sys.argv[1:] or ["plan", "v2_north", "v2_south", "v2_down", "doll_se"]
    for n in names:
        shoot(n, tag=tag)
