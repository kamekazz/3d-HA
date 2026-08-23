"""CALIBRATION for Hall2F Ceiling -- uniform-plane sweep.

SAFETY: this places a plain WHITE/GREY uniform ceiling (never a test card), and
the caller (ceiling3.py --cal) always re-places the real piece in the same run.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "circ"))
from ckit import *                       # noqa
from roomkit.glb import Part             # noqa
from roomkit.place import place          # noqa

ROOM = 17
YC = 8.0 - 0.010
AL_X, AL_Z0, AL_Z1 = 3.86, 10.77, 16.15
EX, DZ, M = 11.92, 16.89, 0.14

BOXES = {"near": (330, 60, 430, 140), "mid": (480, 130, 620, 200),
         "well": (700, 100, 820, 180)}


def flat(mat, tone):
    m = Model()
    def strip(x0, x1, z0, z1, y):
        v = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
        m.add(Part(v, [(0, 1, 2), (0, 2, 3)], smooth=True,
                   colors=[(tone, tone, tone)] * 4), mat)
    strip(AL_X - M, EX + M, -M, DZ + M, YC)
    strip(-M, AL_X - M + 0.10, AL_Z0 - M, AL_Z1 + M, YC - 0.004)
    return m


def shoot_and_meter(tag):
    subprocess.run([sys.executable, "v3.py", "p_stairs"], cwd=HERE,
                   env={**os.environ, "TAG": tag}, capture_output=True, text=True)
    a = np.asarray(Image.open(os.path.join(HERE, "shots", tag + "p_stairs.png"))
                   .convert("RGB")).astype(float).mean(axis=2)
    return {k: float(a[b[1]:b[3], b[0]:b[2]].mean()) for k, b in BOXES.items()}


CASES = [
    ("e58_100",  dict(color="#ffffff", roughness=0.95, emissive="#585858"), 1.00),
    ("e58_060",  dict(color="#ffffff", roughness=0.95, emissive="#585858"), 0.60),
    ("e70_100",  dict(color="#ffffff", roughness=0.95, emissive="#707070"), 1.00),
    ("e70_060",  dict(color="#ffffff", roughness=0.95, emissive="#707070"), 0.60),
    ("e88_100",  dict(color="#ffffff", roughness=0.95, emissive="#888888"), 1.00),
    ("e88_060",  dict(color="#ffffff", roughness=0.95, emissive="#888888"), 0.60),
    ("ea8_100",  dict(color="#ffffff", roughness=0.95, emissive="#a8a8a8"), 1.00),
    ("ea8_060",  dict(color="#ffffff", roughness=0.95, emissive="#a8a8a8"), 0.60),
    ("ed0_100",  dict(color="#ffffff", roughness=0.95, emissive="#d0d0d0"), 1.00),
    ("ed0_060",  dict(color="#ffffff", roughness=0.95, emissive="#d0d0d0"), 0.60),
    ("effx15",   dict(color="#ffffff", roughness=0.95, emissive="#ffffff",
                      emissive_strength=1.5), 1.00),
    ("effx3",    dict(color="#ffffff", roughness=0.95, emissive="#ffffff",
                      emissive_strength=3.0), 1.00),
    ("noem_100", dict(color="#ffffff", roughness=0.95, emissive=None), 1.00),
    ("noem_050", dict(color="#ffffff", roughness=0.95, emissive=None), 0.50),
    ("e40_100",  dict(color="#ffffff", roughness=0.95, emissive="#404040"), 1.00),
    ("e80_100",  dict(color="#ffffff", roughness=0.95, emissive="#808080"), 1.00),
    ("e80_050",  dict(color="#ffffff", roughness=0.95, emissive="#808080"), 0.50),
    ("ec0_100",  dict(color="#ffffff", roughness=0.95, emissive="#c0c0c0"), 1.00),
    ("eff_100",  dict(color="#ffffff", roughness=0.95, emissive="#ffffff"), 1.00),
    ("eff_050",  dict(color="#ffffff", roughness=0.95, emissive="#ffffff"), 0.50),
    ("effx2",    dict(color="#ffffff", roughness=0.95, emissive="#ffffff",
                      emissive_strength=2.0), 1.00),
]


def run():
    out = {}
    for name, kw, tone in CASES:
        mat = Material("cal", double_sided=False, **kw)
        m = flat(mat, tone)
        p = os.path.join(HERE, "glb", "hall2f_ceiling_cal.glb")
        m.save(p)
        lo, hi = m.bounds()
        place("Hall2F Ceiling", p, ROOM,
              pos=((lo[0]+hi[0])/2, lo[1], (lo[2]+hi[2])/2), rot_y_deg=0.0)
        r = shoot_and_meter("cc3_")
        out[name] = r
        print("  %-10s %s" % (name, {k: round(v, 1) for k, v in r.items()}))
    with open(os.path.join(HERE, "ccal3.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


if __name__ == "__main__":
    run()
