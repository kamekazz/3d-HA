import sys
from PIL import Image, ImageDraw
src, out, box, scale = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
step = int(sys.argv[5]) if len(sys.argv)>5 else 20
x0,y0,x1,y1 = [int(v) for v in box.split(',')]
im = Image.open(src).convert('RGB').crop((x0,y0,x1,y1))
w,h = im.size
im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
d = ImageDraw.Draw(im)
for gx in range(x0 - x0%step + step, x1, step):
    X = (gx-x0)*scale
    d.line([(X,0),(X,im.size[1])], fill=(255,0,0), width=1)
    d.text((X+2,2), str(gx), fill=(255,0,0))
for gy in range(y0 - y0%step + step, y1, step):
    Y = (gy-y0)*scale
    d.line([(0,Y),(im.size[0],Y)], fill=(0,255,0), width=1)
    d.text((2,Y+2), str(gy), fill=(0,255,0))
im.save(out); print(out, im.size)
