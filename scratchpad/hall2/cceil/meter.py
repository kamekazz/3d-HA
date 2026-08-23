from PIL import Image
import numpy as np, os, sys
PH = r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
def load(p, half=False):
    im = Image.open(p).convert('RGB')
    if half: im = im.resize((im.width//2, im.height//2), Image.LANCZOS)
    return np.asarray(im).astype(float)
def st(a, box, label):
    x0,y0,x1,y1 = box; s = a[y0:y1, x0:x1]; g = s.mean(axis=2)
    d1 = (np.abs(np.diff(g,axis=1)).mean()+np.abs(np.diff(g,axis=0)).mean())/2
    print('  %-26s L=%6.1f  sd=%5.2f  |d1|=%5.2f  ratio=%.3f' % (label, g.mean(), g.std(), d1, d1/max(g.std(),1e-9)))
    return g.mean()
tag = sys.argv[1] if len(sys.argv)>1 else 'ceiling_'
print('--- p_stairs  (render downsampled to 450x600 to match the photo) ---')
r = load('shots/%sp_stairs.png'%tag, True); p = load(os.path.join(PH,'hallway_looking_towards_stairs.jpg'))
for box,l in [((250,100,300,125),'ceiling clean'),((195,110,215,125),'ceiling L of canA'),((355,140,395,160),'ceiling R of canB')]:
    print(' RENDER'); st(r,box,l); print(' PHOTO '); st(p,box,l)
print('--- p_runner ---')
r = load('shots/%sp_runner.png'%tag, True); p = load(os.path.join(PH,'hallway_with_white_runner_rug.jpg'))
for box,l in [((150,10,215,40),'ceiling near'),((260,15,330,45),'ceiling right'),((150,62,210,72),'ceiling far strip')]:
    print(' RENDER'); st(r,box,l); print(' PHOTO '); st(p,box,l)
