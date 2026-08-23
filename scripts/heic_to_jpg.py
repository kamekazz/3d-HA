"""Convert reference photos to docs/photos-jpg/*.jpg, once.

The reference photos ship as HEIC, which nothing in the toolchain (PIL without a
plugin, the browser, an agent's image reader) can open. Every critic needs to
look at the actual image rather than a description of it, so they get converted
up front and the JPEGs are what photos.json points at.

Idempotent: files already converted are skipped. Long edge is capped at 1600 px —
big enough to read a room off, small enough to hand to an agent.

    python scripts/heic_to_jpg.py                     # the original drop
    python scripts/heic_to_jpg.py --src "docs/v3/Frontyard" --name Frontyard

With --name the outputs are numbered ("Frontyard 1.jpg", "Frontyard 2.jpg", …)
in sorted source order, because the later drops arrived with camera-roll names
like `80887617814__32603D15-….heic` that say nothing about the room. Without it
the source basename is kept, which is what the first drop relies on.

Non-HEIC stills (the back-yard camera PNGs) are converted too — same cap, same
numbering — so one map covers every reference regardless of what it shipped as.
"""

import argparse
import glob
import os

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "docs", "photos-jpg")
MAX_EDGE = 1600
EXTS = (".heic", ".png", ".jpg", ".jpeg")


def sources(src):
    """Every still in `src`, deduped by realpath, in sorted order.

    Windows globbing is case-insensitive, so *.heic already covers *.HEIC;
    dedupe by realpath so a case-variant pair is not converted twice.
    """
    seen, files = set(), []
    for f in sorted(glob.glob(os.path.join(src, "*"))):
        if not f.lower().endswith(EXTS):
            continue
        key = os.path.normcase(os.path.realpath(f))
        if key not in seen:
            seen.add(key)
            files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join("docs", "Photos-1-001"),
                    help="source directory, relative to the repo root")
    ap.add_argument("--name", default=None,
                    help="rename outputs to '<name> 1.jpg', '<name> 2.jpg', …")
    args = ap.parse_args()

    src = args.src if os.path.isabs(args.src) else os.path.join(ROOT, args.src)
    os.makedirs(DST, exist_ok=True)
    files = sources(src)

    made = skipped = 0
    for i, f in enumerate(files, 1):
        if args.name:
            base = f"{args.name} {i}"
        else:
            # trailing dots in the source names ("Movie room..heic") would
            # produce "Movie room..jpg" and confuse the photos.json map
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
