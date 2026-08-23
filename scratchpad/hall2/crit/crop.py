import sys, os
from PIL import Image
src, x0,y0,x1,y1, sc, out = sys.argv[1], *[int(v) for v in sys.argv[2:6]], float(sys.argv[6]), sys.argv[7]
im = Image.open(src).convert("RGB").crop((x0,y0,x1,y1))
im = im.resize((int(im.width*sc), int(im.height*sc)), Image.LANCZOS)
im.save(out); print(out, im.size)
