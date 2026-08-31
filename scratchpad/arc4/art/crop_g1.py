import sys
from PIL import Image
src, out, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
z = float(sys.argv[7]) if len(sys.argv) > 7 else 4.0
im = Image.open(src).crop((x0, y0, x1, y1))
im = im.resize((int(im.width*z), int(im.height*z)), Image.LANCZOS)
im.save(out); print(im.size)
