from PIL import Image
import numpy as np, sys
def st(path, box, label, scale=2.0):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    x0,y0,x1,y1 = [int(v*scale) for v in box]
    s = a[y0:y1, x0:x1]; g = s.mean(axis=2)
    d1 = (np.abs(np.diff(g,axis=1)).mean()+np.abs(np.diff(g,axis=0)).mean())/2
    print('%-30s %-24s L=%.1f sd=%.2f |d1|=%.2f' % (path.split('/')[-1], label, g.mean(), g.std(), d1))
p='shots/ceil0_p_stairs.png'
st(p,(250,100,300,125),'ceiling clean')
st(p,(150,215,200,265),'left wall')
st(p,(380,230,440,300),'right wall')
p='shots/ceil0_p_runner.png'
st(p,(150,10,215,40),'ceiling near')
st(p,(260,15,330,45),'ceiling right')
st(p,(20,120,90,220),'west wall upper')
st(p,(350,150,430,260),'east wall')
