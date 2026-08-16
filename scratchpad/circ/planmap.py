"""Register a HA floor-plan screenshot to world feet and print an ASCII wall map.

Fit (Main Floor Plan App.png), from long wall lines matched to known room rects:
    world_x = 39.35 - (px - 52.0)  * 0.044565      # image LEFT  = world +X (east)
    world_z = 34.80 - (py - 546.5) * 0.044617      # image TOP   = world +Z (front)
Checks: px 517.5 -> 18.61 (garage/pantry/bath west edge 18.7-18.9, hall east 18.3)
        px 977.5 -> -1.89 (living/master west wall -1.92)
        px 1029  -> -4.19 (kitchen/dining west wall -4.19)
        py 840.5 -> 21.68 (dining north 21.70 / kitchen south 21.48)
        py 1036.5-> 12.94 (garage & laundry z=13.0)
        py 1167.5->  7.09 (laundry 7.3 / office 7.1)
"""
import sys
import numpy as np
from PIL import Image

PLANS = {
    "main": (r"C:/Users/Manuel/Desktop/Pro/3d HA/docs/floor plan/Main Floor Plan App.png",
             39.35, 52.0, 0.044565, 34.80, 546.5, 0.044617),
    # Second floor, fitted the same way:
    #   px  53.0 -> 33.40 (master bath east)      px 1027.5 -> -1.90 (Rios west)
    #   py 428.5 -> 34.40 (front facade)          py 1720.5 -> -12.38 (master bed rear)
    # checks: px 468 -> 18.37 (hall/master-bath party wall 18.6)
    #         px 683 -> 10.58 (hall/guest party wall 10.5)
    #         py 1201 -> 6.43 (master bed 6.30 / hall 6.60)
    #         py 1030 -> 12.60 (master closet & bath 12.4)
    #         py 804  -> 20.79 (master closet 20.8)
    #         py 901  -> 17.29 (guest room 17.30)
    "2f": (r"C:/Users/Manuel/Desktop/Pro/3d HA/docs/floor plan/Second Floor Plan App.png",
           33.40, 53.0, 0.036223, 34.40, 428.5, 0.036208),
}


def load(key="main"):
    path, X0, PX0, SX, Z0, PY0, SZ = PLANS[key]
    a = np.asarray(Image.open(path).convert("L")).astype(int)
    mask = ((a >= 216) & (a <= 233))
    def w2p(wx, wz):
        return (PX0 + (X0 - wx) / SX, PY0 + (Z0 - wz) / SZ)
    return mask, w2p


def ascii_map(key, x0, x1, z0, z1, step=0.25):
    mask, w2p = load(key)
    H, W = mask.shape
    zs = np.arange(z1, z0 - 1e-9, -step)      # top row = largest z
    xs = np.arange(x1, x0 - 1e-9, -step)      # left col = largest x
    print("      " + "".join("|" if abs(x - round(x)) < 1e-6 and int(round(x)) % 2 == 0 else " " for x in xs))
    for z in zs:
        row = []
        for x in xs:
            px, py = w2p(x, z)
            ix, iy = int(round(px)), int(round(py))
            r = 2
            blk = mask[max(0, iy - r):iy + r + 1, max(0, ix - r):ix + r + 1]
            row.append("#" if blk.mean() > 0.34 else ("+" if blk.any() else "."))
        print(f"{z:6.2f}" + "".join(row))


if __name__ == "__main__":
    key = sys.argv[1]
    x0, x1, z0, z1 = (float(v) for v in sys.argv[2:6])
    step = float(sys.argv[6]) if len(sys.argv) > 6 else 0.25
    ascii_map(key, x0, x1, z0, z1, step)
