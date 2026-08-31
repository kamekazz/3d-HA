import sys
from PIL import Image, ImageEnhance
src, out, box, scale = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
x0,y0,x1,y1 = [int(v) for v in box.split(',')]
im = Image.open(src).convert('RGB').crop((x0,y0,x1,y1))
w,h = im.size
im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
if len(sys.argv) > 5:
    im = ImageEnhance.Brightness(im).enhance(float(sys.argv[5]))
if len(sys.argv) > 6:
    im = ImageEnhance.Contrast(im).enhance(float(sys.argv[6]))
im.save(out)
print(out, im.size)
