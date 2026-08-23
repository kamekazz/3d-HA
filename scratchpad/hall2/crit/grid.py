import sys, os
from PIL import Image, ImageDraw
p = sys.argv[1]
step = int(sys.argv[2]) if len(sys.argv) > 2 else 100
im = Image.open(p).convert("RGB")
W, H = im.size
d = ImageDraw.Draw(im)
for x in range(0, W, step):
    d.line([(x, 0), (x, H)], fill=(255, 0, 0), width=1)
    d.text((x + 2, 2), str(x), fill=(255, 0, 0))
for y in range(0, H, step):
    d.line([(0, y), (W, y)], fill=(0, 200, 255), width=1)
    d.text((2, y + 2), str(y), fill=(0, 200, 255))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "g.png")
im.save(out)
print(out, im.size)
