from PIL import Image
import numpy as np, sys
def blobs(mask):
    H,W=mask.shape; lab=np.zeros(mask.shape,int); cur=0; out=[]
    for j in range(H):
        for i in range(W):
            if mask[j,i] and lab[j,i]==0:
                cur+=1; st=[(j,i)]; lab[j,i]=cur; pts=[]
                while st:
                    a,b=st.pop(); pts.append((a,b))
                    for da,db in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        na,nb=a+da,b+db
                        if 0<=na<H and 0<=nb<W and mask[na,nb] and lab[na,nb]==0:
                            lab[na,nb]=cur; st.append((na,nb))
                out.append(pts)
    return out
for p in sys.argv[1:]:
    im=Image.open(p).convert('L'); im=im.resize((450,600),Image.LANCZOS)
    a=np.asarray(im).astype(float)[:280,:]
    print(p, 'max', a.max())
    for pts in blobs(a>=232):
        if len(pts)<5: continue
        ys=np.array([q[0] for q in pts]); xs=np.array([q[1] for q in pts])
        print('   c=(%.1f,%.1f) n=%d peak=%d'%(xs.mean(),ys.mean(),len(pts),a[ys,xs].max()))
