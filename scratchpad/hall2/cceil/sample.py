from PIL import Image
import numpy as np, os
d = r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
def st(f, box, label):
    a = np.asarray(Image.open(os.path.join(d, f)).convert('RGB')).astype(float)
    x0,y0,x1,y1 = box
    s = a[y0:y1, x0:x1]
    g = s.mean(axis=2)
    d1 = (np.abs(np.diff(g,axis=1)).mean() + np.abs(np.diff(g,axis=0)).mean())/2
    print('%-34s %-22s mean RGB=(%.0f,%.0f,%.0f) L=%.1f sd=%.2f |d1|=%.2f ratio=%.3f' % (
        f[:20], label, s[:,:,0].mean(), s[:,:,1].mean(), s[:,:,2].mean(), g.mean(), g.std(), d1, d1/max(g.std(),1e-6)))
F1='hallway_with_white_runner_rug.jpg'; F2='hallway_looking_towards_stairs.jpg'
st(F1,(150,10,215,40),'ceiling clean (near)')
st(F1,(260,15,330,45),'ceiling clean (right)')
st(F1,(150,62,210,72),'ceiling far strip')
st(F1,(20,120,90,220),'west wall upper')
st(F1,(20,300,90,400),'west wall lower')
st(F1,(350,150,430,260),'east wall')
st(F2,(250,100,300,125),'ceiling clean')
st(F2,(360,145,420,165),'ceiling right of can')
st(F2,(150,215,200,265),'left wall')
st(F2,(380,230,440,300),'right wall')
# can core colours
a = np.asarray(Image.open(os.path.join(d,F2)).convert('RGB')).astype(float)
for (cx,cy,l) in [(225,130,'canA'),(345,132,'canB'),(228,167,'canC')]:
    print(l, a[cy-1:cy+2, cx-2:cx+3].reshape(-1,3).mean(axis=0).round(1))
a2 = np.asarray(Image.open(os.path.join(d,F1)).convert('RGB')).astype(float)
for (cx,cy,l) in [(125,51,'canE'),(240,51,'canF')]:
    print(l, a2[cy-2:cy+3, cx-3:cx+4].reshape(-1,3).mean(axis=0).round(1))
# halo profile around canB in F2
g = a.mean(axis=2)
print('halo across canB (y=132, x 300..420):', [int(v) for v in g[132,300:420:6]])
print('halo across canE (y=51, x 60..200):', [int(v) for v in a2.mean(axis=2)[51,60:200:7]])
