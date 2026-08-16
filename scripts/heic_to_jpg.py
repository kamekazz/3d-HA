"""Convert docs/Photos-1-001/*.heic to docs/photos-jpg/*.jpg, once.

The reference photos ship as HEIC, which nothing in the toolchain (PIL without a
plugin, the browser, an agent's image reader) can open. Every critic needs to
look at the actual image rather than a description of it, so they get converted
up front and the JPEGs are what photos.json points at.

Idempotent: files already converted are skipped. Long edge is capped at 1600 px —
big enough to read a room off, small enough to hand to an agent.

    python scripts/heic_to_jpg.py
"""

import glob
import os

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "Photos-1-001")
DST = os.path.join(ROOT, "docs", "photos-jpg")
MAX_EDGE = 1600


def main():
    os.makedirs(DST, exist_ok=True)
    # Windows globbing is case-insensitive, so *.heic already covers *.HEIC;
    # dedupe by realpath so a case-variant pair is not converted twice.
    seen = set()
    files = []
    for f in sorted(glob.glob(os.path.join(SRC, "*.heic"))):
        key = os.path.normcase(os.path.realpath(f))
        if key not in seen:
            seen.add(key)
            files.append(f)

    made = skipped = 0
    for f in files:
        # trailing dots in the source names ("Movie room..heic") would produce
        # "Movie room..jpg" and confuse the photos.json map
        base = os.path.splitext(os.path.basename(f))[0].strip().rstrip(".")
        out = os.path.join(DST, base + ".jpg")
        if os.path.exists(out):
            skipped += 1
            continue
        try:
            im = Image.open(f).convert("RGB")
            im.thumbnail((MAX_EDGE, MAX_EDGE))
            im.save(out, "JPEG", quality=88)
            made += 1
        except Exception as e:  # a single unreadable photo must not stop the run
            print(f"FAIL {os.path.basename(f)}: {e}")
    print(f"{made} converted, {skipped} already present -> {DST}")


if __name__ == "__main__":
    main()
