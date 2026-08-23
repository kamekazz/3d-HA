import numpy as np
from PIL import Image

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"


def m(path, box, label):
    a = np.array(Image.open(path).convert("RGB")).astype(float)[box[1]:box[3], box[0]:box[2]]
    g = a.mean(axis=2)
    print(f"{label:34s} mean={g.mean():6.1f} sd={g.std():5.2f} "
          f"|d1|x={np.abs(np.diff(g,axis=1)).mean():5.2f} "
          f"rgb=({a[:,:,0].mean():.0f},{a[:,:,1].mean():.0f},{a[:,:,2].mean():.0f})")
    return g.mean()


print("--- PHOTO: hallway_with_white_runner_rug ---")
wr = m(f"{P}\\hallway_with_white_runner_rug.jpg", (355, 300, 430, 400), "  E wall (right, mid)")
wl = m(f"{P}\\hallway_with_white_runner_rug.jpg", (30, 180, 90, 300), "  W wall (left, mid)")
f1 = m(f"{P}\\hallway_with_white_runner_rug.jpg", (20, 440, 120, 570), "  floor near left")
f2 = m(f"{P}\\hallway_with_white_runner_rug.jpg", (300, 400, 380, 470), "  floor near right")
print(f"  floor/wall = {f1/wr:.3f} (nearL/Ewall)  {f2/wr:.3f}")

print("--- PHOTO: hallway_looking_towards_stairs ---")
w2 = m(f"{P}\\hallway_looking_towards_stairs.jpg", (350, 200, 430, 320), "  E wall (right)")
f3 = m(f"{P}\\hallway_looking_towards_stairs.jpg", (40, 480, 150, 590), "  floor near left")
f4 = m(f"{P}\\hallway_looking_towards_stairs.jpg", (255, 470, 340, 560), "  floor near right")
print(f"  floor/wall = {f3/w2:.3f}  {f4/w2:.3f}")

print("--- PHOTO: two_closed_white_doors_1 ---")
w3 = m(f"{P}\\two_closed_white_doors_1.jpg", (370, 180, 440, 330), "  wall right")
f5 = m(f"{P}\\two_closed_white_doors_1.jpg", (150, 400, 300, 500), "  alcove floor")
print(f"  floor/wall = {f5/w3:.3f}")

print("--- RENDER (baseline) ---")
rw = m(f"{S}\\floorbase_p_runner.png", (700, 380, 830, 540), "  E wall")
rf = m(f"{S}\\floorbase_p_runner.png", (620, 810, 780, 890), "  floor near right (GLB)")
rw2 = m(f"{S}\\floorbase_p_doors1.png", (600, 300, 780, 700), "  doors1 wall right")
rf2 = m(f"{S}\\floorbase_p_doors1.png", (300, 1020, 700, 1180), "  doors1 alcove floor (slab)")
print(f"  floor/wall = {rf/rw:.3f}   alcove {rf2/rw2:.3f}")
