import os
from PIL import Image
import numpy as np
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
def lum(f):
    a=np.asarray(Image.open(os.path.join(P,f)).convert("RGB"),dtype=float)
    return 0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
L2=lum("two_closed_white_doors_2.jpg")
L1=lum("two_closed_white_doors_1.jpg")
def row(L,y,x0,x1,lbl):
    print(lbl, " ".join("%d"%v for v in L[y,x0:x1]))
def col(L,x,y0,y1,lbl):
    print(lbl, " ".join("%d"%v for v in L[y0:y1,x]))
print("== d2 right door: horizontal through the two lower panels, y=200 ==")
row(L2,200,255,355,"y200")
print("== d2 right door: vertical through left lower panel x=285 ==")
col(L2,285,150,300,"x285")
print("== d2 left door: horizontal through the two mid panels, y=180 ==")
row(L2,180,80,240,"y180")
print("== d2 left door vertical through panel x=140 ==")
col(L2,140,100,230,"x140")
print("== d1: horizontal through right door panels y=100 ==")
row(L1,100,190,350,"y100")
