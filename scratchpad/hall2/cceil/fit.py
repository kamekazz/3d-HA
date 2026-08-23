import math, itertools
exec(open('cceil/proj.py').read().split('CANS =')[0])
obs = [   # (pose, expected px, py) for (west_can, east_can)
  ("p_stairs", (225.5,130.2), (345.5,132.5)),
  ("p_runner", (240.2, 50.7), (124.7, 50.7)),
]
def err(w, e):
    tot = 0.0; parts=[]
    for pose, ow, oe in obs:
        for can, o in ((w, ow), (e, oe)):
            r = project(POSES[pose], AX+can[0], BASE+8.0, AZ+can[1])
            if r is None: return 1e9, []
            d = (r[0]-o[0])**2 + (r[1]-o[1])**2
            tot += d; parts.append((pose, round(r[0],1), round(r[1],1), o, round(math.sqrt(d),1)))
    return tot, parts
best=None
for wx in [x/20 for x in range(90,150)]:
  for wz in [z/20 for z in range(100,280)]:
    for ex in [x/20 for x in range(130,200)]:
      e2 = err((wx,wz),(ex,wz))
      if best is None or e2[0]<best[0]: best=(e2[0],(wx,wz),(ex,wz))
print('same-z fit rms=%.1f px'%math.sqrt(best[0]/4), best[1], best[2])
t,parts = err(best[1],best[2])
for p in parts: print('  ',p)
