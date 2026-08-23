from PIL import Image
import numpy as np, os
d = r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
try:
    from scipy import ndimage
    HAVE = True
except Exception:
    HAVE = False
def blobs(mask):
    lab = np.zeros(mask.shape, int); cur = 0; out = []
    H, W = mask.shape
    for j in range(H):
        for i in range(W):
            if mask[j, i] and lab[j, i] == 0:
                cur += 1; st = [(j, i)]; lab[j, i] = cur; pts = []
                while st:
                    a, b = st.pop(); pts.append((a, b))
                    for da, db in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        na, nb = a+da, b+db
                        if 0 <= na < H and 0 <= nb < W and mask[na, nb] and lab[na, nb] == 0:
                            lab[na, nb] = cur; st.append((na, nb))
                out.append(pts)
    return out
for f, box in [('hallway_looking_towards_stairs.jpg', (0, 0, 450, 260)),
               ('hallway_with_white_runner_rug.jpg', (0, 0, 450, 200)),
               ('staircase_looking_up.jpg', (150, 0, 350, 60))]:
    a = np.asarray(Image.open(os.path.join(d, f)).convert('L')).astype(float)
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    thr = max(np.percentile(sub, 98.5), 232)
    print(f, 'thr', round(thr, 1), 'max', sub.max())
    for pts in blobs(sub >= thr):
        if len(pts) < 5: continue
        ys = np.array([p[0] for p in pts]); xs = np.array([p[1] for p in pts])
        print('   c=(%.1f,%.1f) n=%d w=%d h=%d peak=%d' % (
            xs.mean()+x0, ys.mean()+y0, len(pts), xs.max()-xs.min()+1, ys.max()-ys.min()+1,
            sub[ys, xs].max()))
