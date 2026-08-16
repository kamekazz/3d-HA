"""Stack a reference photo and a render side by side at matched height.

The comparison is the whole point of this build, so make it one image rather than
two the eye has to switch between.

    python -m roomkit.sbs render.png out.png                 # room 14's photo
    python -m roomkit.sbs render.png out.png --room 6        # that room's primary photo
    python -m roomkit.sbs render.png out.png --ref "docs/photos-jpg/Kitchen A.jpg"

`--blind` drops the left/right labels and shuffles the order by a hash of the
output name, so a critic cannot tell which side is ours from position alone. It
prints the key to stderr, never into the image.
"""

import argparse
import hashlib
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PHOTO_DIR = os.path.join(ROOT, "docs", "photos-jpg")
PHOTOS = os.path.join(HERE, "photos.json")


def primary_photo(room_id):
    with open(PHOTOS) as fh:
        data = json.load(fh)
    entry = data["rooms"].get(str(room_id))
    if not entry or not entry["photos"]:
        raise SystemExit(f"room {room_id} has no reference photo in photos.json")
    return os.path.join(PHOTO_DIR, entry["photos"][0])


def compare(render_path, out, ref_path, height=900, gap=12, blind=False):
    ref = Image.open(ref_path).convert("RGB")
    ren = Image.open(render_path).convert("RGB")
    imgs = [im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
            for im in (ref, ren)]
    names = ["photo", "render"]
    if blind:
        # deterministic per output name, so a re-run of the same comparison is
        # stable but the critic cannot learn "ours is always on the right"
        if int(hashlib.sha256(os.path.basename(out).encode()).hexdigest(), 16) % 2:
            imgs.reverse()
            names.reverse()
    w = sum(i.width for i in imgs) + gap
    canvas = Image.new("RGB", (w, height), (255, 255, 255))
    x = 0
    for im in imgs:
        canvas.paste(im, (x, 0))
        x += im.width + gap
    canvas.save(out, quality=92)
    if blind:
        print(f"KEY (do not show the critic): left={names[0]} right={names[1]}",
              file=sys.stderr)
        print(f"{out} {canvas.size}")
    else:
        print(f"{out} {canvas.size} (left = photo, right = render)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("render")
    p.add_argument("out")
    p.add_argument("--room", type=int, default=14)
    p.add_argument("--ref", help="explicit reference image path")
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--blind", action="store_true",
                   help="no labels, order shuffled by output name")
    a = p.parse_args()
    ref = a.ref if a.ref else primary_photo(a.room)
    if not os.path.isabs(ref):
        cand = os.path.join(ROOT, ref)
        ref = cand if os.path.exists(cand) else ref
    compare(a.render, a.out, ref, a.height, blind=a.blind)


if __name__ == "__main__":
    main()
