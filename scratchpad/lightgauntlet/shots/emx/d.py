import sys, os
import numpy as np
from PIL import Image
for tag in sys.argv[1:]:
    a=np.asarray(Image.open('before_%s.png'%tag).convert('RGB')).astype(int)
    b=np.asarray(Image.open('after_%s.png'%tag).convert('RGB')).astype(int)
    d=np.abs(a-b)
    n=int((d.max(axis=2)>0).sum())
    if n==0:
        print('%-14s IDENTICAL (0 px differ)'%tag); continue
    m=d.max(axis=2)>0
    lum=lambda im:(0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2])
    la,lb=lum(a)[m],lum(b)[m]
    print('%-14s %d px differ (%.2f%%) maxdelta=%d | changed-px L %.1f -> %.1f'%(
        tag,n,100.0*n/m.size,int(d.max()),la.mean(),lb.mean()))
