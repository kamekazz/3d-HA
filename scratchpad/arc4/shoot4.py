"""Round-4 arcade shoot.  usage: shoot4.py <prefix> [pose ...]

Poses are the ones rooms/2.json already records as photo matches, plus two new
close-ups on the cabinet runs -- round 4 is judged on printed ARTWORK, so the
judged frames must be close enough to read a marquee.

    $PY scratchpad/arc4/shoot4.py r4 a_look_s b_look_n cab_east cab_north
"""
import json, os, subprocess, sys

PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\arc4\shots"

# world feet.  Room 2 is world x -0.35..20.35 (local x 0..20.7 -> world x-0.35),
# Room 2 origin_world = (-2.1, 0, -11.9); local (x,z) -> world (x-2.1, z-11.9).
# East run local x 19.38 z 2.85..16.41; north run local z 1.32 x 6.55..13.55;
# south run local z 21.58 x 2.05..10.05.
POSES = {
    # the two matches round 3 was judged on
    "a_look_s":  {"pos": [14.4, 5.4, -9.5], "target": [6.6, 2.9, 11.4],
                  "fov": 80, "size": [900, 1200]},
    "b_look_n":  {"pos": [4.5, 5.4, 7.7], "target": [9.4, 2.2, -10.9],
                  "fov": 100, "size": [900, 1200]},
    # NEW round-4 close-ups: near enough that a marquee is legible, which is
    # what this round is actually judged on.
    "cab_east":  {"pos": [7.9, 5.2, 8.1], "target": [17.3, 4.1, -3.9],
                  "fov": 72, "size": [1200, 900]},
    "cab_north": {"pos": [13.9, 4.6, -3.4], "target": [7.4, 3.6, -10.6],
                  "fov": 60, "size": [1200, 900]},
    "cab_south": {"pos": [9.4, 5.4, -1.4], "target": [2.9, 4.2, 9.4],
                  "fov": 74, "size": [1200, 900]},
    # ROUND 4 addition.  The four frames above all aim DOWN -- every one of them
    # crops the machines at the screen bezel, so not one marquee is in shot, and
    # round 4 is judged on printed artwork of which the marquee is the loudest
    # piece.  These three stand at marquee height and look level along each run.
    "mq_east":   {"pos": [4.6, 5.80, -8.6], "target": [17.28, 5.55, -8.6],
                  "fov": 70, "size": [1400, 620]},
    "mq_north":  {"pos": [4.95, 5.80, -1.0], "target": [4.95, 5.55, -10.58],
                  "fov": 58, "size": [1400, 620]},
    "mq_south":  {"pos": [9.6, 5.85, 1.2], "target": [9.6, 5.60, 9.68],
                  "fov": 52, "size": [1400, 620]},
    "mq_south_w": {"pos": [6.95, 5.85, 0.6], "target": [6.95, 5.60, 9.68],
                   "fov": 64, "size": [1400, 620]},
    # ROUND 6 addition.  The mq_* frames stand AT marquee height and look level,
    # which crops every lower front, coin door and control deck out of shot --
    # the integrator flagged it and a critic then failed the room for "not one
    # coin door anywhere in the frame" while judging a frame that could not
    # contain one.  These stand at chest height and take the whole machine.
    "full_east":  {"pos": [4.6, 4.35, -8.6], "target": [17.28, 3.55, -8.6],
                   "fov": 76, "size": [1400, 900]},
    "full_north": {"pos": [4.95, 4.35, -1.2], "target": [4.95, 3.55, -10.58],
                   "fov": 64, "size": [1400, 900]},
    "full_south": {"pos": [9.6, 4.55, 1.2], "target": [9.6, 3.45, 9.68],
                   "fov": 62, "size": [1400, 800]},
    # Ridge Racer and the Star Wars cabinet appear in NO other judged frame.
    "corner_sw":  {"pos": [3.0, 4.20, 5.6], "target": [-0.78, 3.30, 9.65],
                   "fov": 60, "size": [1200, 900]},
    "doll_nw":   {"pos": [-7.156, 40.009, -22.252], "target": [8.25, 2.24, -0.25],
                  "fov": 42, "size": [1200, 900]},
    "plan":      {"pos": [8.25, 37.0, -0.25], "target": [8.25, 0.0, -0.25],
                  "fov": 45, "size": [900, 900]},
}
CUTAWAY_OK = ("doll_nw", "plan")

# The four frames round 4 is judged on.  cab_south is deliberately NOT here:
# the west desk run stands between every south-facing camera and the south
# cabinets, so that frame judges the desk.  The south run reads in a_look_s.
# corner_sw is NOT here: every camera aimed at Ridge Racer from inside the room
# lands in the west desk run or a desk plant. mq_south_w already carries it.
JUDGED = ["full_east", "full_north", "full_south",
          "mq_east", "mq_north", "mq_south_w"]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    prefix = sys.argv[1]
    names = sys.argv[2:] or JUDGED
    for n in names:
        out = os.path.join(OUT, f"{prefix}_{n}.png")
        cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[n]),
               "--level", "0", "--day", "--out", out]
        if n not in CUTAWAY_OK:
            cmd.append("--no-cutaway")
        r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
        print(n, r.returncode, (r.stdout or r.stderr).strip()[-140:])
