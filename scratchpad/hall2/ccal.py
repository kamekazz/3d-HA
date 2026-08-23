"""CALIBRATION ONLY -- 8 tones across the VISIBLE ceiling width, 3 emissive z-bands."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "circ"))
from ckit import *                                   # noqa
from roomkit.glb import Part                          # noqa
ROOM = 17; YC = 8.0 - 0.010
AL_X, AL_Z0, AL_Z1 = 3.86, 10.77, 16.15
EX, DZ, M = 11.92, 16.89, 0.14
EMIS = ["#5a5a5a", "#6f6f6f", "#828282"]
TONES = [1.0, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30]
MATS = [Material("cal%d" % i, "#ffffff", roughness=0.95, emissive=e,
                 double_sided=False) for i, e in enumerate(EMIS)]
def strip(m, mat, x0, x1, z0, z1, tone, y):
    m.add(Part([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)], [(0,1,2),(0,2,3)],
               smooth=True, colors=[(tone,tone,tone)]*4), mat)
m = Model()
zb = [-M, 4.0, 9.0, DZ + M]
x0, x1 = AL_X - M, 8.02
for zi in range(3):
    for ei, t in enumerate(TONES):
        a = x0 + (x1-x0)*ei/8.0; b = x0 + (x1-x0)*(ei+1)/8.0
        strip(m, MATS[zi], a, b, zb[zi], zb[zi+1], t, YC)
    strip(m, MATS[zi], 8.02, EX+M, zb[zi], zb[zi+1], 1.0, YC)
strip(m, MATS[1], -M, AL_X-M, AL_Z0-M, AL_Z1+M, 0.8, YC-0.005)
path = os.path.join(HERE, "glb", "hall2f_ceiling_cal.glb"); m.save(path)
lo, hi = m.bounds()
from roomkit.place import place
place("Hall2F Ceiling", path, ROOM, pos=((lo[0]+hi[0])/2, lo[1], (lo[2]+hi[2])/2), rot_y_deg=0.0)
print("bands far/mid/near emissive", EMIS, "tones W->E", TONES)
