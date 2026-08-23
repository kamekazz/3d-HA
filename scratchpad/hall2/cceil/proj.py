import math, sys
BASE = 18.0; AX, AZ = 6.70, 6.55
def norm(v):
    n = math.sqrt(sum(c*c for c in v)); return tuple(c/n for c in v)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def project(pose, wx, wy, wz):
    pos, tgt, fov = pose['pos'], pose['target'], pose['fov']
    W, H = pose['size']
    f = norm(tuple(tgt[i]-pos[i] for i in range(3)))
    r = norm(cross(f,(0,1,0))); u = cross(r,f)
    v = (wx-pos[0], wy-pos[1], wz-pos[2])
    zc = sum(v[i]*f[i] for i in range(3))
    if zc <= 0.01: return None
    xc = sum(v[i]*r[i] for i in range(3)); yc = sum(v[i]*u[i] for i in range(3))
    t2 = math.tan(math.radians(fov)/2.0); asp = W/float(H)
    px = (xc/(zc*t2*asp)+1)/2*W
    py = (1-yc/(zc*t2))/2*H
    return px, py, zc
P = lambda x,y,z,tx,ty,tz,fov=74,size=(450,600): {"pos":[x,BASE+y,z],"target":[tx,BASE+ty,tz],"fov":fov,"size":list(size)}
POSES = {
 "p_stairs": P(12.10,5.30,21.90, 12.95,4.05,7.20),
 "p_runner": P(12.60,5.30,8.40, 12.55,3.95,23.10),
 "p_doors2": P(13.10,5.25,18.30, 7.40,3.60,21.60),
 "p_down":   P(16.40,6.30,13.90, 16.30,0.20,21.80),
}
CANS = [tuple(float(v) for v in a.split(',')) for a in sys.argv[1:]]
for k in ("p_stairs","p_runner","p_doors2","p_down"):
    print('==',k)
    for (lx,lz) in CANS:
        r = project(POSES[k], AX+lx, BASE+8.0, AZ+lz)
        print('   (%.2f,%.2f) -> %s' % (lx, lz, ('px %6.1f,%6.1f d=%.1f'%r) if r else 'behind'))
