"""Compare render floor patches with the photographs on the same footing.

The renders are 900x1200, the photos 450x600, so every render patch is ALSO
metered at half scale -- |d1| is resolution-dependent and comparing 900-wide
render grain against a 450-wide photo flatters the render by ~2x.
"""
import sys
import numpy as np
from PIL import Image

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"


def st(a):
    g = a.astype(float).mean(axis=2)
    return (g.mean(), g.std(), np.abs(np.diff(g, axis=1)).mean(),
            np.abs(np.diff(g, axis=0)).mean(),
            a[:, :, 0].mean(), a[:, :, 1].mean(), a[:, :, 2].mean())


def row(path, box, label, half=False):
    im = Image.open(path).convert("RGB").crop(box)
    if half:
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    a = np.array(im)
    mu, sd, dx, dy, r, g, b = st(a)
    print(f"{label:30s} mean={mu:6.1f} sd={sd:5.2f} |d1|x={dx:5.2f} |d1|y={dy:5.2f} "
          f"|d1|/sd={dx/max(sd,1e-6):5.3f}  rgb=({r:.0f},{g:.0f},{b:.0f})")
    return mu


# clean, object-free floor patches -- see ROOM-BRIEF "how to meter honestly"
PHOTO = [
    ("hallway_with_white_runner_rug.jpg", (20, 440, 120, 570), "PH runner  floor nearL"),
    ("hallway_with_white_runner_rug.jpg", (300, 400, 380, 470), "PH runner  floor nearR"),
    ("hallway_looking_towards_stairs.jpg", (40, 480, 150, 590), "PH stairs  floor nearL"),
    ("hallway_looking_towards_stairs.jpg", (160, 410, 240, 465), "PH stairs  floor mid"),
    ("two_closed_white_doors_1.jpg", (150, 400, 300, 500), "PH doors1  alcove floor"),
    ("two_closed_white_doors_1.jpg", (60, 490, 180, 585), "PH doors1  alcove near"),
]
PHOTO_WALL = [
    ("hallway_with_white_runner_rug.jpg", (355, 300, 430, 400), "PH runner  E wall"),
    ("hallway_looking_towards_stairs.jpg", (350, 200, 430, 320), "PH stairs  E wall"),
    ("two_closed_white_doors_1.jpg", (370, 180, 440, 330), "PH doors1  wall right"),
]

REND = [
    ("p_runner", (632, 950, 700, 1080), "RN runner  floor R"),
    ("p_runner", (300, 1040, 342, 1180), "RN runner  floor L"),
    ("p_stairs", (215, 985, 330, 1180), "RN stairs  floor nearL"),
    ("p_stairs", (575, 930, 675, 1090), "RN stairs  floor nearR"),
    ("p_stairs", (405, 815, 560, 868), "RN stairs  floor mid"),
    ("p_doors1", (300, 1010, 700, 1160), "RN doors1  alcove floor"),
]
REND_WALL = [
    ("p_runner", (700, 380, 830, 540), "RN runner  E wall"),
    ("p_stairs", (700, 300, 830, 500), "RN stairs  E wall"),
    ("p_doors1", (620, 300, 800, 700), "RN doors1  wall right"),
]

if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "floor_"
    print("========= PHOTOGRAPHS (450x600 native) =========")
    pw = [row(f"{P}\\{f}", b, l) for (f, b, l) in PHOTO_WALL]
    pf = [row(f"{P}\\{f}", b, l) for (f, b, l) in PHOTO]
    print(f"  photo floor/wall: runner {pf[0]/pw[0]:.3f} {pf[1]/pw[0]:.3f}  "
          f"stairs {pf[2]/pw[1]:.3f} {pf[3]/pw[1]:.3f}  doors1 {pf[4]/pw[2]:.3f} {pf[5]/pw[2]:.3f}")
    print()
    print(f"========= RENDER  {tag}  (downsampled to 450x600) =========")
    rw = [row(f"{S}\\{tag}{p}.png", b, l, half=True) for (p, b, l) in REND_WALL]
    rf = [row(f"{S}\\{tag}{p}.png", b, l, half=True) for (p, b, l) in REND]
    print(f"  render floor/wall: runner {rf[0]/rw[0]:.3f} {rf[1]/rw[0]:.3f}  "
          f"stairs {rf[2]/rw[1]:.3f} {rf[3]/rw[1]:.3f} {rf[4]/rw[1]:.3f}  "
          f"doors1 {rf[5]/rw[2]:.3f}")
