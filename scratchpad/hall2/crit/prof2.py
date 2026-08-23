import os
from PIL import Image
import numpy as np
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
def lum(f):
    a=np.asarray(Image.open(os.path.join(P,f)).convert("RGB"),dtype=float)
    return 0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
L2=lum("two_closed_white_doors_2.jpg"); L1=lum("two_closed_white_doors_1.jpg")
def S(L,y0,y1,x0,x1,lbl):
    b=L[y0:y1,x0:x1]
    print("%-26s mean %6.1f sd %5.2f |d1|h %5.2f |d1|v %5.2f"%(lbl,b.mean(),b.std(),
        np.abs(np.diff(b,axis=1)).mean(), np.abs(np.diff(b,axis=0)).mean()))
print("--- doors_2 ---")
S(L2,150,230,270,340,"right leaf field")
S(L2,120,300,95,200,"left leaf field")
S(L2,60,300,352,362,"right casing (side)")
S(L2,30,45,270,340,"right head casing")
S(L2,100,300,375,430,"wall right of casing")
S(L2,150,300,20,55,"wall left")
S(L2,340,380,300,360,"baseboard right")
print("--- doors_1 ---")
S(L1,20,300,200,340,"right leaf field")
S(L1,30,290,355,368,"right casing side")
S(L1,60,300,390,440,"wall far right")
S(L1,100,300,10,120,"left leaf field")
# row across the reveal on doors_2 right door, strike side  (x 250..275)
print("reveal row y=170:", " ".join("%d"%v for v in L2[170,244:270]))
print("reveal row y=250:", " ".join("%d"%v for v in L2[250,244:270]))
print("casing/wall row y=200:", " ".join("%d"%v for v in L2[200,340:400]))
print("head row x=300:", " ".join("%d"%v for v in L2[20:70,300]))
