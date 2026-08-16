"""Analytic model of the `ref` camera for room 14, so photo pixels <-> room feet.

Pose (poses.json, read-only):  pos world (18.0, 23.6, -3.7)
                              target    (13.0, 21.8, -16.0)
                              fov 78 (vertical), size 900x1200
Room 14 local -> world:  wx = lx + 6.0 ,  wy = 18.0 + ly ,  wz = lz - 20.5
Photo is 1200x1600; render is 900x1200 -> photo px * 0.75 = render px.
"""
import math

POS = (18.0, 23.6, -3.7)
TGT = (13.0, 21.8, -16.0)
FOV = 78.0
RW, RH = 900, 1200
PW, PH = 1200, 1600
P2R = RW / PW          # 0.75


def _sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def _cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def _norm(a):
    L = math.sqrt(_dot(a, a)); return (a[0]/L, a[1]/L, a[2]/L)


FWD = _norm(_sub(TGT, POS))
RIGHT = _norm(_cross(FWD, (0.0, 1.0, 0.0)))
UP = _cross(RIGHT, FWD)
TANH = math.tan(math.radians(FOV)/2)          # half-height at z=1
ASPECT = RW/RH
TANW = TANH*ASPECT


def l2w(p):
    return (p[0]+6.0, 18.0+p[1], p[2]-20.5)


def w2l(p):
    return (p[0]-6.0, p[1]-18.0, p[2]+20.5)


def proj_world(p):
    """world ft -> render pixel (x,y) at 900x1200."""
    d = _sub(p, POS)
    z = _dot(d, FWD)
    x = _dot(d, RIGHT)
    y = _dot(d, UP)
    return ((x/z/TANW + 1)*0.5*RW, (1 - y/z/TANH)*0.5*RH, z)


def proj(p):
    """room-local ft -> render pixel."""
    return proj_world(l2w(p))


def projp(p):
    """room-local ft -> PHOTO pixel (1200x1600)."""
    x, y, z = proj(p)
    return (x/P2R, y/P2R, z)


def ray_photo(px, py):
    """photo pixel -> (origin, direction) world ray."""
    return ray(px*P2R, py*P2R)


def ray(rx, ry):
    ndx = (rx/RW)*2-1
    ndy = 1-(ry/RH)*2
    d = tuple(FWD[i] + RIGHT[i]*ndx*TANW + UP[i]*ndy*TANH for i in range(3))
    return POS, _norm(d)


def hit_plane_photo(px, py, axis, value_local):
    """Back-project a photo pixel onto the local plane axis(0=x,1=y,2=z)=value.

    Returns room-local (x, y, z)."""
    o, d = ray_photo(px, py)
    ow = w2l(o)
    dl = d  # directions are the same in local (pure translation)
    t = (value_local - ow[axis]) / dl[axis]
    return (ow[0]+dl[0]*t, ow[1]+dl[1]*t, ow[2]+dl[2]*t)


if __name__ == "__main__":
    # sanity: room corners
    for name, p in [("NW floor", (0, 0, 0)), ("NE floor", (15, 0, 0)),
                    ("SW floor", (0, 0, 16)), ("SE floor", (15, 0, 16)),
                    ("N wall top W", (0, 8, 0)), ("N wall top E", (15, 8, 0))]:
        x, y, z = projp(p)
        print(f"{name:14s} photo px ({x:7.1f},{y:7.1f})  depth {z:5.2f}")
