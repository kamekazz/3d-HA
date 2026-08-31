import sys
from PIL import Image
src, out, box, scale = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
x0,y0,x1,y1 = [int(v) for v in box.split(",")]
im = Image.open(src).convert("RGB").crop((x0,y0,x1,y1))
im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
im.save(out); print(out, im.size)
