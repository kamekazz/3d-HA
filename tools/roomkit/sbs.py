"""Stack the reference photo and a render side by side at matched height.

The comparison is the whole point of this build, so make it one image rather than
two the eye has to switch between.

    python -m roomkit.sbs shots/render.png shots/compare.png
"""

import os
import sys

from PIL import Image

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                   "docs", "Master bedroom.heic")  # a JPEG despite the name


def compare(render_path, out, height=900, gap=12):
    ref = Image.open(REF).convert("RGB")
    ren = Image.open(render_path).convert("RGB")
    imgs = [im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
            for im in (ref, ren)]
    w = sum(i.width for i in imgs) + gap
    canvas = Image.new("RGB", (w, height), (255, 255, 255))
    x = 0
    for im in imgs:
        canvas.paste(im, (x, 0))
        x += im.width + gap
    canvas.save(out, quality=92)
    print(out, canvas.size, "(left = photo, right = render)")


if __name__ == "__main__":
    compare(sys.argv[1], sys.argv[2])
