"""Randomize a native-resolution photo/render pair without disclosing its key.

The critic sees only pair.png. Do not read key.json until a verdict is written.
No compositing, image enhancement, AI generation or selective retouching occurs.
"""
import argparse, json, secrets
from pathlib import Path
from PIL import Image, ImageOps

p = argparse.ArgumentParser()
p.add_argument('--render', required=True)
p.add_argument('--reference', required=True)
p.add_argument('--out', required=True)
p.add_argument('--crop', nargs=4, type=int, metavar=('LEFT','TOP','RIGHT','BOTTOM'),
               help='Optional component diagnostic: same pixel rectangle on both native-photo-sized images; full-frame gate remains separate')
a = p.parse_args()
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
photo = ImageOps.exif_transpose(Image.open(a.reference)).convert('RGB')
render = Image.open(a.render).convert('RGB')
if abs(render.width/render.height - photo.width/photo.height) > 0.02:
    raise ValueError('Camera aspect must match the photo; no field-of-view crops permitted')
render = render.resize(photo.size, Image.Resampling.LANCZOS)
if a.crop:
    x0,y0,x1,y1=a.crop
    if not (0 <= x0 < x1 <= photo.width and 0 <= y0 < y1 <= photo.height):
        raise ValueError('Diagnostic crop must lie inside both images')
    photo=photo.crop(a.crop)
    render=render.crop(a.crop)
photo_left = bool(secrets.randbits(1))
pair = Image.new('RGB', (photo.width*2+16, photo.height), '#303030')
pair.paste(photo if photo_left else render, (0, 0))
pair.paste(render if photo_left else photo, (photo.width+16, 0))
pair.save(out/'pair.png')
(out/'key.json').write_text(json.dumps({'photograph':'left' if photo_left else 'right',
    'reference':str(Path(a.reference).resolve()), 'render':str(Path(a.render).resolve()),
    'comparison_size':list(photo.size), 'diagnostic_crop':a.crop,
    'test':'focused component diagnostic' if a.crop else 'full-frame blind gate'}, indent=2), encoding='utf-8')
print(str((out/'pair.png').resolve()))
