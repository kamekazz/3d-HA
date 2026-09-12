from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'python-deps'))
from PIL import Image, ImageOps, ImageDraw
from pillow_heif import register_heif_opener
register_heif_opener()
out = ROOT / 'references'
out.mkdir(parents=True, exist_ok=True)
manifest = []
sources = sorted(Path(r'C:\Users\Manuel\Downloads\Backyard reference').glob('*.heic'))
sheet = Image.new('RGB', (1400, 350 * ((len(sources)+3)//4)), '#202124')
draw = ImageDraw.Draw(sheet)
for n, src in enumerate(sources, 1):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    dest = out / f'{n:02d}.png'
    im.save(dest)
    manifest.append(dict(id=f'{n:02d}', filename=src.name, png=dest.name, width=im.width, height=im.height))
    thumb = im.copy()
    thumb.thumbnail((340, 310))
    x, y = ((n-1)%4)*350, ((n-1)//4)*350
    sheet.paste(thumb, (x+(350-thumb.width)//2, y))
    draw.text((x+10, y+315), f'{n:02d} | {im.width} x {im.height}', fill='white')
(out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
sheet.save(out/'contact-sheet.png')
print(json.dumps(manifest, indent=2))
