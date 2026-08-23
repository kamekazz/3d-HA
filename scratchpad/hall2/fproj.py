"""Sample the RENDER's floor at exact room-local points by projecting them
through the same pose the shot was taken with.

Every hand-drawn sample box on a hallway floor this narrow swallows a baseboard
or the runner edge -- three of mine did, and they reported the skirting as
floor at 195.  This projects known floor points instead, so a sample is clean by
construction.  Usage:  python fproj.py <tag> <pose>
"""
import math, os, sys
import numpy as np
from PIL import Image
from v3 import POSES

HERE = os.path.dirname(os.path.abspath(__file__))
ANCH = (6.70, 18.0, 6.55)
RUG = (4.30, 7.10, 2.70, 14.60)     # runner footprint + margin, room-local


def project(pose, p):
    px, py, pz = p
    cx, cy, cz = pose["pos"]
    tx, ty, tz = pose["target"]
    fx, fy, fz = tx - cx, ty - cy, tz - cz
    n = math.sqrt(fx * fx + fy * fy + fz * fz)
    fx, fy, fz = fx / n, fy / n, fz / n
    rx, ry, rz = fy * 0 - fz * 1, fz * 0 - fx * 0, fx * 1 - fy * 0   # cross(f,up)
    n = math.hypot(rx, rz) or 1.0
    rx, ry, rz = rx / n, 0.0, rz / n
    ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx
    dx, dy, dz = px - cx, py - cy, pz - cz
    z = dx * fx + dy * fy + dz * fz
    if z <= 0.05:
        return None
    x = dx * rx + dy * ry + dz * rz
    y = dx * ux + dy * uy + dz * uz
    W, H = pose["size"]
    t = math.tan(math.radians(pose["fov"]) / 2.0)
    ndx = (x / z) / (t * (W / H))
    ndy = (y / z) / t
    return ((ndx * 0.5 + 0.5) * W, (0.5 - ndy * 0.5) * H)


def sample(img, uv, r=5):
    if uv is None:
        return None
    u, v = uv
    W, H = img.size
    if u < r or v < r or u > W - r or v > H - r:
        return None
    a = np.asarray(img.crop((int(u) - r, int(v) - r, int(u) + r, int(v) + r)), float)
    return 0.2126 * a[..., 0].mean() + 0.7152 * a[..., 1].mean() + 0.0722 * a[..., 2].mean()


if __name__ == "__main__":
    tag, pose_name = sys.argv[1], sys.argv[2]
    pose = POSES[pose_name]
    img = Image.open(os.path.join(HERE, "shots", f"{tag}{pose_name}.png")).convert("RGB")
    print(f"{tag}{pose_name}: floor value at room-local (x, z), 10x10 px patches")
    print("      z:", "  ".join(f"{z:5.1f}" for z in [0.9, 2.5, 4.5, 6.5, 8.5, 10.5,
                                                      12.5, 14.5, 16.3]))
    for x in (1.9, 3.0, 4.3, 5.7, 7.0, 8.5, 10.5):
        row = []
        for z in (0.9, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5, 14.5, 16.3):
            inside = ((3.86 <= x <= 11.92 and 0 <= z <= 6.81)
                      or (3.86 <= x <= 7.61 and 0 <= z <= 16.89)
                      or (0 <= x <= 3.86 and 10.77 <= z <= 16.15))
            if not inside or (RUG[0] <= x <= RUG[1] and RUG[2] <= z <= RUG[3]):
                row.append("    .")
                continue
            v = sample(img, project(pose, (ANCH[0] + x, ANCH[1] + 0.018, ANCH[2] + z)))
            row.append("    -" if v is None else f"{v:5.0f}")
        print(f"  x{x:5.1f} " + "  ".join(row))
