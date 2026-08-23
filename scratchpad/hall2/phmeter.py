"""Meter the PHOTOGRAPHS on clean fields, and draw the sample boxes so the
boxes themselves can be checked by eye (ROOM-BRIEF: sample a clean field)."""
import os
import numpy as np
from PIL import Image, ImageDraw
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
O = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
BOXES = {
 "hallway_with_white_runner_rug.jpg": {
   "greywall_near": (335,310,400,420),
   "greywall_far":  (55,255,105,325),
   "kw_hallface":   (181,266,199,299),
   "kw_captop":     (170,233,184,243),
   "kw_endface":    (152,302,162,330),
   "kw_baseboard":  (167,337,181,343),
   "door_white":    (215,140,258,215),
 },
 "hallway_looking_towards_stairs.jpg": {
   "greywall_right":(385,175,440,275),
   "kw_captop":     (332,392,400,418),
   "kw_hallface":   (312,428,344,486),
   "door_white":    (25,190,100,320),
 },
 "staircase_looking_down.jpg": {
   "greywall_shaft":(60,160,160,300),
   "kw_captop":     (352,176,414,191),
   "kw_wellface":   (300,235,378,298),
 },
}
for f, boxes in BOXES.items():
    im = Image.open(os.path.join(P, f)).convert("RGB")
    a = np.asarray(im).astype(float)
    L = a @ [0.2126,0.7152,0.0722]
    print("==", f)
    ref = None
    for nm,(x0,y0,x1,y1) in boxes.items():
        v = L[y0:y1, x0:x1]
        d = np.abs(np.diff(v, axis=1)).mean()
        if "greywall" in nm and ref is None: ref = v.mean()
        print(f"   {nm:16s} L={v.mean():6.1f} sd={v.std():5.2f} d1={d:4.2f} "
              f"ratio={v.mean()/ref:5.3f}" if ref else f"   {nm:16s} L={v.mean():6.1f}")
    d = ImageDraw.Draw(im)
    for nm,(x0,y0,x1,y1) in boxes.items():
        d.rectangle([x0,y0,x1,y1], outline=(255,0,0))
    im = im.resize((im.width*2, im.height*2), Image.LANCZOS)
    im.save(os.path.join(O, "box_"+f.replace(".jpg",".png")))
