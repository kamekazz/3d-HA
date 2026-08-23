import math, sys
BASE=18.0; ANCH=(6.70,6.55)
POSES={
 "p_stairs": ((12.10,BASE+5.30,21.90),(12.95,BASE+4.05,7.20),74,(900,1200)),
 "p_runner": ((12.60,BASE+5.30,8.40),(12.55,BASE+3.95,23.10),74,(900,1200)),
}
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    L=math.sqrt(sum(v*v for v in a)); return tuple(v/L for v in a)
def unproj(pose, px, py, yplane):
    C,T,fov,(W,H)=POSES[pose]
    f=norm(sub(T,C)); r=norm(cross(f,(0,1,0))); u=cross(r,f)
    tv=math.tan(math.radians(fov)/2); th=tv*W/H
    nx=(px/W)*2-1; ny=1-(py/H)*2
    d=tuple(f[i]+nx*th*r[i]+ny*tv*u[i] for i in range(3))
    t=(yplane-C[1])/d[1]
    return (C[0]+t*d[0], C[2]+t*d[2])
YC=BASE+8.0
print("pose      photo_px      world(x,z)      local(x,z)")
for pose, pts in (("p_stairs",[(225.5,130.2),(345.4,132.6),(227.7,167.3),(302.2,169.4)]),
                  ("p_runner",[(125.0,50.8),(240.1,50.6)])):
    for (px,py) in pts:
        w=unproj(pose, px*2, py*2, YC)
        print("%-9s (%6.1f,%6.1f)  (%6.2f,%6.2f)  (%6.2f,%6.2f)" % (pose,px,py,w[0],w[1],w[0]-ANCH[0],w[1]-ANCH[1]))

print()
print("== junction points ==")
for pose,pts in (("p_stairs",[(347,161),(400,131),(440,108),(300,190),(250,215)]),
                 ("p_runner",[(150,78),(120,86),(200,72),(255,66),(90,95)])):
    for (px,py) in pts:
        w=unproj(pose,px*2,py*2,YC)
        print("%-9s (%5.1f,%5.1f) -> local (%6.2f,%6.2f)" % (pose,px,py,w[0]-ANCH[0],w[1]-ANCH[1]))
