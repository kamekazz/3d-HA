from wprof import *
import numpy as np
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
def hline(a, x0, x1, y0, y1, label, step=3):
    g = a @ LUM
    print(f"  {label}  (rows {y0}-{y1})")
    vals=[(x, g[y0:y1, x:x+step].mean()) for x in range(x0, x1, step)]
    print("      " + " ".join(f"{x}:{v:.0f}" for x,v in vals))
def vline(a, x0, x1, y0, y1, label, step=4):
    g = a @ LUM
    print(f"  {label}  (cols {x0}-{x1})")
    vals=[(y, g[y:y+step, x0:x1].mean()) for y in range(y0, y1, step)]
    print("      " + " ".join(f"{y}:{v:.0f}" for y,v in vals))

c = load(P + r"\two_closed_white_doors_2.jpg")
hline(c, 300, 448, 60, 140, "doors2 corner sweep, upper")
hline(c, 300, 448, 200, 300, "doors2 corner sweep, lower")
vline(c, 400, 445, 4, 340, "doors2 R wall vertical")
vline(c, 306, 330, 20, 330, "doors2 return wall vertical (between corner and door)")
r = load(P + r"\hallway_with_white_runner_rug.jpg")
vline(r, 415, 448, 60, 500, "runner R wall vertical near")
vline(r, 300, 330, 100, 340, "runner R wall vertical far")
hline(r, 250, 448, 150, 250, "runner R wall horizontal (far->near)", 6)
s = load(P + r"\hallway_looking_towards_stairs.jpg")
vline(s, 405, 448, 40, 440, "stairs R wall vertical near")
vline(s, 128, 170, 120, 330, "stairs L wall vertical")
