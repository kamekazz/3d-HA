import sys
import numpy as np
from PIL import Image
for a_,b_ in zip(sys.argv[1::2], sys.argv[2::2]):
    a=np.asarray(Image.open(a_+'.png').convert('RGB')).astype(int)
    b=np.asarray(Image.open(b_+'.png').convert('RGB')).astype(int)
    d=np.abs(a-b); m=d.max(axis=2)>0; n=int(m.sum())
    lum=lambda im:(0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2])
    print('%-22s vs %-22s %7d px (%.2f%%) maxdelta=%3d meanL %.2f -> %.2f'%(
        a_,b_,n,100.0*n/m.size,int(d.max()),lum(a).mean(),lum(b).mean()))
