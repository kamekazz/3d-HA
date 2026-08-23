from PIL import Image
import numpy as np, os
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
def s(f, box, label):
    im = np.asarray(Image.open(os.path.join(P,f)).convert("RGB")).astype(float)
    x0,y0,x1,y1 = box
    p = im[y0:y1, x0:x1].reshape(-1,3)
    L = p @ [0.2126,0.7152,0.0722]
    print(f"{label:38s} n={len(p):5d} RGB=({p[:,0].mean():5.1f},{p[:,1].mean():5.1f},{p[:,2].mean():5.1f})  L={L.mean():6.1f} sd={L.std():5.2f}")
R="hallway_with_white_runner_rug.jpg"; S="hallway_looking_towards_stairs.jpg"; D="staircase_looking_down.jpg"
s(R,(160,230,195,244),"runner: cap TOP")
s(R,(178,258,200,300),"runner: kneewall HALL face upper")
s(R,(150,290,168,330),"runner: kneewall END face")
s(R,(60,250,110,330),"runner: grey wall LEFT (far)")
s(R,(330,300,400,420),"runner: grey wall RIGHT (near)")
s(R,(210,120,255,220),"runner: bath DOOR leaf (white)")
s(S,(300,330,420,420),"stairs: cap TOP near")
s(S,(275,300,340,340),"stairs: kneewall HALL face")
s(S,(360,120,440,260),"stairs: grey wall RIGHT")
s(S,(20,180,105,330),"stairs: master DOOR leaf (white)")
s(D,(330,150,430,215),"down: cap TOP")
s(D,(300,230,380,300),"down: surface BELOW cap (well side)")
s(D,(60,150,160,300),"down: grey shaft wall LEFT")
s(D,(345,10,430,110),"down: 2F door leaf white")
