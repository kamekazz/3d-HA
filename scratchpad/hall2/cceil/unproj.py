import math
BASE = 18.0
AX, AZ = 6.70, 6.55          # room 17 anchor
CEIL_Y = BASE + 8.0

def norm(v):
    n = math.sqrt(sum(c*c for c in v)); return tuple(c/n for c in v)
def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def unproject(pose, px, py, plane_y=CEIL_Y):
    pos = pose['pos']; tgt = pose['target']; fov = pose['fov']
    W, H = pose['size']
    f = norm(tuple(tgt[i]-pos[i] for i in range(3)))
    r = norm(cross(f, (0, 1, 0)))
    u = cross(r, f)
    t2 = math.tan(math.radians(fov)/2.0)
    asp = W/float(H)
    xn = (2.0*px/W - 1.0) * t2 * asp
    yn = (1.0 - 2.0*py/H) * t2
    d = norm(tuple(f[i] + r[i]*xn + u[i]*yn for i in range(3)))
    if abs(d[1]) < 1e-9: return None
    t = (plane_y - pos[1]) / d[1]
    if t < 0: return None
    p = tuple(pos[i] + d[i]*t for i in range(3))
    return (p[0]-AX, p[2]-AZ, t)

P = lambda x, y, z, tx, ty, tz, fov=74, size=(450, 600): {
    "pos": [x, BASE+y, z], "target": [tx, BASE+ty, tz], "fov": fov, "size": list(size)}

POSES = {
 "p_stairs": P(12.10, 5.30, 21.90, 12.95, 4.05, 7.20),
 "p_runner": P(12.60, 5.30, 8.40, 12.55, 3.95, 23.10),
 "p_up":     P(16.20, -8.20, 26.00, 16.20, -3.40, 18.40),
}
DATA = {
 "p_stairs": [(225.5,130.2),(345.5,132.5),(227.7,167.1),(302.3,169.2)],
 "p_runner": [(124.7,50.7),(240.2,50.7)],
 "p_up":     [(239.7,18.8)],
}
for k, pts in DATA.items():
    print('==', k)
    for (px, py) in pts:
        r = unproject(POSES[k], px, py)
        if r: print('   px(%.0f,%.0f) -> local x=%.2f z=%.2f  dist=%.1f' % (px, py, r[0], r[1], r[2]))
        else: print('   px(%.0f,%.0f) -> no hit' % (px, py))
