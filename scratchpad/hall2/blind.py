"""Make a blind A/B pair for a critic: our render and the reference photo,
copied to neutral names in a shuffled order, at the same pixel size.

    python blind.py p_runner r1_ crit/kneewall

Writes <outdir>/A.png and <outdir>/B.png plus <outdir>/.key (which is which).
The critic is handed A and B only; the caller reads .key afterwards.
Order is derived from a hash of the outdir name, so it is stable per run but
not guessable from the pose, and NOT the same for every piece.
"""
import hashlib, os, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "v2 Hallway-jpg"))
sys.path.insert(0, HERE)
from v3 import PHOTO, OUT   # noqa: E402


def make(pose, tag, outdir):
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    ours = os.path.join(OUT, f"{tag}{pose}.png")
    photo = os.path.join(PHOTOS, PHOTO[pose])
    if not os.path.exists(ours):
        raise SystemExit(f"missing render {ours} -- shoot it first")

    ri, pi = Image.open(ours).convert("RGB"), Image.open(photo).convert("RGB")
    # match on height, keep each one's own aspect: a squashed image is a tell.
    h = 1100
    ri = ri.resize((round(ri.width * h / ri.height), h), Image.LANCZOS)
    pi = pi.resize((round(pi.width * h / pi.height), h), Image.LANCZOS)

    flip = hashlib.sha1(os.path.basename(outdir).encode()).digest()[0] & 1
    first, second = (pi, ri) if flip else (ri, pi)
    first.save(os.path.join(outdir, "A.png"))
    second.save(os.path.join(outdir, "B.png"))
    with open(os.path.join(outdir, ".key"), "w") as fh:
        fh.write(f"A={'photo' if flip else 'render'}\nB={'render' if flip else 'photo'}\n"
                 f"pose={pose}\ntag={tag}\nrender={ours}\nphoto={photo}\n")
    print(os.path.join(outdir, "A.png"), os.path.join(outdir, "B.png"), "(key hidden)")


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
