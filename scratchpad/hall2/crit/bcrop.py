import sys, os
from PIL import Image
src = sys.argv[1]; box = tuple(int(v) for v in sys.argv[2].split(",")); sc=float(sys.argv[3]) if len(sys.argv)>3 else 4
out = sys.argv[4] if len(sys.argv)>4 else "crit/_c.png"
im = Image.open(src).convert("RGB")
print("size", im.size)
c = im.crop(box)
c = c.resize((int(c.width*sc), int(c.height*sc)), Image.LANCZOS)
c.save(out); print(out, c.size)
