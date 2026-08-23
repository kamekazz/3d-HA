from wprof import *
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
import numpy as np
def line(a, x0, x1, y0, y1, label):
    g = a @ LUM
    print(f"  {label}")
    for y in range(y0, y1):
        print(f"      y={y:3d}  {g[y, x0:x1].mean():6.1f}")
a = load(P + r"\hallway_with_white_runner_rug.jpg")
line(a, 420, 448, 60, 100, "runner: right-wall ceiling junction x420-448")
line(a, 415, 448, 470, 500, "runner: right-wall FLOOR/baseboard junction")
b = load(P + r"\two_closed_white_doors_2.jpg")
line(b, 400, 448, 8, 40, "doors2: right-wall ceiling junction")
d = load(P + r"\staircase_looking_down.jpg")
line(d, 30, 110, 10, 45, "down: left shaft wall ceiling junction")
