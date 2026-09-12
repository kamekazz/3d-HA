"""Create lightweight previews; full-resolution capture remains the download."""
import sys
from pathlib import Path
from PIL import Image

for name in sys.argv[1:]:
    source = Path(name)
    with Image.open(source) as image:
        image = image.convert('RGB')
        image.thumbnail((1600, 1200), Image.Resampling.LANCZOS)
        image.save(source.with_name(source.stem + '-progress.jpg'), quality=88)
