import sys, json
from PIL import Image, ImageDraw
spec = json.load(open(sys.argv[1]))
out = sys.argv[2]
for i,(img, boxes) in enumerate(spec.items()):
    im = Image.open(img).convert("RGB")
    d = ImageDraw.Draw(im)
    for name,b in boxes.items():
        d.rectangle(b, outline=(255,0,0), width=4)
        d.text((b[0]+5,b[1]+5), name, fill=(255,60,0))
    im.save(out.replace("#", str(i)))
    print(out.replace("#", str(i)))
