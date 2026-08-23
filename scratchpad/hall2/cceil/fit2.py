import math
exec(open('cceil/proj.py').read().split('CANS =')[0])
obs = [("p_stairs",(225.5,130.2),(345.5,132.5)), ("p_runner",(240.2,50.7),(124.7,50.7))]
def err(w,e,which=None):
    tot=0.0; parts=[]
    for pose, ow, oe in obs:
        for can,o in ((w,ow),(e,oe)):
            r=project(POSES[pose], AX+can[0], BASE+8.0, AZ+can[1])
            if r is None: return 1e9,[]
            d=(r[0]-o[0])**2+(r[1]-o[1])**2; tot+=d
            parts.append((pose,round(r[0],1),round(r[1],1),o,round(math.sqrt(d),1)))
    return tot,parts
def fit(free_z):
    best=None
    rng=lambda a,b,s=20:[v/s for v in range(int(a*s),int(b*s)+1)]
    for wx in rng(4.5,8.0):
      for wz in rng(4.0,14.0):
        for ex in rng(6.0,11.0):
          for ez in (rng(4.0,14.0) if free_z else [wz]):
            t,_=err((wx,wz),(ex,ez))
            if best is None or t<best[0]: best=(t,(wx,wz),(ex,ez))
    return best
b=fit(True)
print('free-z rms=%.1f'%math.sqrt(b[0]/4), b[1], b[2])
for p in err(b[1],b[2])[1]: print('  ',p)
