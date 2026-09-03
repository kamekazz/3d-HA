import math, sys
from PIL import Image
# night_front pose
P=(27,4,90); T=(14,14,30); FOV=92; W,H=1050,1400
def basis():
    f=[T[i]-P[i] for i in range(3)]; n=math.sqrt(sum(c*c for c in f)); f=[c/n for c in f]
    up=(0,1,0)
    r=[f[1]*up[2]-f[2]*up[1], f[2]*up[0]-f[0]*up[2], f[0]*up[1]-f[1]*up[0]]
    n=math.sqrt(sum(c*c for c in r)); r=[c/n for c in r]
    u=[r[1]*f[2]-r[2]*f[1], r[2]*f[0]-r[0]*f[2], r[0]*f[1]-r[1]*f[0]]
    return f,r,u
F,R,U=basis()
t=math.tan(math.radians(FOV/2)); asp=W/H
def px_to_ground(px,py,gy=0.16):
    ndx=(px/W*2-1)*t*asp; ndy=(1-py/H*2)*t
    d=[F[i]+R[i]*ndx+U[i]*ndy for i in range(3)]
    if d[1]>=0: return None
    s=(gy-P[1])/d[1]
    return (round(P[0]+d[0]*s,1), round(P[2]+d[2]*s,1))
def world_to_px(x,y,z):
    v=[x-P[0],y-P[1],z-P[2]]
    dz=sum(v[i]*F[i] for i in range(3)); dx=sum(v[i]*R[i] for i in range(3)); dy=sum(v[i]*U[i] for i in range(3))
    if dz<=0: return None
    return (round((dx/dz/(t*asp)+1)/2*W), round((1-dy/dz/t)/2*H))
if __name__=='__main__':
    for py in (1000,1100,1200,1300,1399):
        print('row',py,[px_to_ground(px,py) for px in (0,262,525,787,1049)])
    for name,pt in {'stepW':(12,2.13,44.5),'stepE':(19.5,2.13,44.5),'driveL@houseF':(20,0.16,29.5),'driveL@50':(20,0.16,50),'driveL@60':(20,0.16,60),'driveL@70':(20,0.16,70),'driveR@30':(47,0.16,30),'driveR@60':(47,0.16,60),'garageCorner':(20.3,0.16,29.8),'porchW':(-7,2.13,40.6)}.items():
        print(name, world_to_px(*pt))
    for name,px in {'walk_junction':(270,970),'flag1':(340,880),'flag2':(300,905),'mumpot':(525,830),'rightbed':(900,860),'rightbed2':(960,870),'leftbed_shrubs':(180,850),'leftedge_bottom':(0,1080)}.items():
        print(name, px_to_ground(*px, gy=0.16))
