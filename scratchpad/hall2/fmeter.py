"""Meter the photographed floor: hue, value, sd, mean|d1| along/across plank."""
import sys
import numpy as np
from PIL import Image

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"


def stats(a, label):
    g = a.astype(float).mean(axis=2)
    d1h = np.abs(np.diff(g, axis=1)).mean()
    d1v = np.abs(np.diff(g, axis=0)).mean()
    r, gg, b = [a[:, :, i].astype(float).mean() for i in range(3)]
    print(
        f"{label:28s} n={g.size:6d} mean={g.mean():6.1f} sd={g.std():5.2f} "
        f"|d1|x={d1h:5.2f} |d1|y={d1v:5.2f}  rgb=({r:.0f},{gg:.0f},{b:.0f}) "
        f"hex=#{int(r):02x}{int(gg):02x}{int(bb) if False else int(b):02x}"
    )
    return g.mean()


def sample(f, box, label):
    im = np.array(Image.open(f"{P}\\{f}").convert("RGB"))
    a = im[box[1]:box[3], box[0]:box[2]]
    return stats(a, label)


print("=== clean floor fields ===")
sample("two_closed_white_doors_1.jpg", (120, 400, 300, 520), "d1 alcove mid")
sample("two_closed_white_doors_1.jpg", (60, 480, 200, 590), "d1 alcove near")
sample("two_closed_white_doors_2.jpg", (330, 380, 430, 470), "d2 alcove mid")
sample("hallway_with_white_runner_rug.jpg", (10, 430, 130, 590), "runner-photo near L")
sample("hallway_with_white_runner_rug.jpg", (330, 400, 420, 500), "runner-photo near R")
sample("hallway_with_white_runner_rug.jpg", (150, 320, 200, 350), "runner-photo mid L")
sample("hallway_with_white_runner_rug.jpg", (285, 310, 330, 345), "runner-photo mid R")
sample("hallway_looking_towards_stairs.jpg", (30, 470, 160, 590), "stairs-photo near L")
sample("hallway_looking_towards_stairs.jpg", (150, 400, 250, 470), "stairs-photo mid")
sample("hallway_looking_towards_stairs.jpg", (185, 320, 240, 350), "stairs-photo far")

print()
print("=== longitudinal profile: runner photo, floor left of runner ===")
im = np.array(Image.open(f"{P}\\hallway_with_white_runner_rug.jpg").convert("RGB")).astype(float)
for y in range(300, 600, 20):
    # left-of-runner band narrows as y decreases; crude wedge
    t = (y - 300) / 300.0
    x0 = int(140 - 130 * t)
    x1 = int(175 - 165 * t)
    if x1 - x0 < 6:
        continue
    row = im[y:y + 8, x0:x1]
    print(f"  y={y:3d} x[{x0:3d}:{x1:3d}] mean={row.mean():6.1f} "
          f"rgb=({row[:,:,0].mean():.0f},{row[:,:,1].mean():.0f},{row[:,:,2].mean():.0f})")

print()
print("=== longitudinal profile: stairs photo, floor down the hall ===")
im2 = np.array(Image.open(f"{P}\\hallway_looking_towards_stairs.jpg").convert("RGB")).astype(float)
for y in range(320, 600, 20):
    t = (y - 320) / 280.0
    x0 = int(175 - 150 * t)
    x1 = int(200 - 130 * t)
    row = im2[y:y + 8, x0:x1]
    print(f"  y={y:3d} x[{x0:3d}:{x1:3d}] mean={row.mean():6.1f} "
          f"rgb=({row[:,:,0].mean():.0f},{row[:,:,1].mean():.0f},{row[:,:,2].mean():.0f})")
