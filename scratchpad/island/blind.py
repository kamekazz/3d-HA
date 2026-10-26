"""Prepare one blind A/B pair: the reference crop and our crop, same width, random sides.

    python blind.py <tag> <ref1|ref2> <ours.png> [<ours.png> ...]

Writes blind/<tag>/A.jpg, B.jpg (and C/D... if several of ours are given, each
paired with the ref as its own pair: <tag>-1, <tag>-2) and a key.json the
critic never sees. Our shot is auto-cropped to the island (everything that is
not the void) with the reference's own margin.
"""
import sys, os, json, random
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = {
    # the island panel of each reference, UI chrome cropped away
    'ref1': ('ref/ref1_stone_island.jpg', (236, 228, 1514, 946)),
    'ref2': ('ref/ref2_avondale.jpg', (60, 160, 1180, 890)),
}
W = 1280

def crop_ours(path):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int32)
    # the void is dark and blue-dominant; anything brighter or not blue-ish is island
    lum = a.mean(axis=2)
    # r5: void = clearly blue-dominant and darkish. The old "lum < 22 is void"
    # also ate the slab's dark underside at night and cropped it off
    blueish = (a[:, :, 2] > a[:, :, 1] + 6) & (a[:, :, 2] > a[:, :, 0] + 12)
    # (and near-black blue-ish is void too: the shadow under the plate, r6)
    # r8: the day void is a dark grey-navy that failed the blue test and was
    # counted as island (25% dead margin). Void = dark and blue >= red and
    # green: soil (red-heavy) and night trees (green-heavy) stay island.
    dark_blue = (lum < 45) & (a[:, :, 2] >= a[:, :, 0]) & (a[:, :, 2] >= a[:, :, 1])
    mask = ~((blueish & (lum < 90)) | dark_blue)
    ys, xs = np.nonzero(mask)
    x0, x1 = np.percentile(xs, [0.3, 99.7]); y0, y1 = np.percentile(ys, [0.3, 99.7])
    w, h = x1 - x0, y1 - y0
    # the references leave ~8% margin round the island
    mx, my = w * 0.05, h * 0.07   # r7: the reference panel is cropped about this tight
    x0, x1, y0, y1 = x0 - mx, x1 + mx, y0 - my, y1 + my
    # match the reference panel aspect (~16:9)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    tw, th = x1 - x0, y1 - y0
    aspect = 1278 / 718
    if tw / th < aspect: tw = th * aspect
    else: th = tw / aspect
    # keep the box inside the frame (shrink, keep aspect) -- never pad
    tw = min(tw, im.width, im.height * aspect); th = tw / aspect
    cx = min(max(cx, tw / 2), im.width - tw / 2); cy = min(max(cy, th / 2), im.height - th / 2)
    box = (int(cx - tw / 2), int(cy - th / 2), int(cx + tw / 2), int(cy + th / 2))
    return im.crop(box)

def fit(im):
    r = W / im.width
    return im.resize((W, int(im.height * r)), Image.LANCZOS)

tag, ref = sys.argv[1], sys.argv[2]
ours = sys.argv[3:]
rp, rbox = REFS[ref]
refim = fit(Image.open(os.path.join(HERE, rp)).convert('RGB').crop(rbox))
keys = {}
for i, o in enumerate(ours):
    t = tag if len(ours) == 1 else f'{tag}-{i + 1}'
    d = os.path.join(HERE, 'blind', t); os.makedirs(d, exist_ok=True)
    oim = fit(crop_ours(o))
    pair = [('ours', oim), ('bar', refim)]
    random.shuffle(pair)
    for lab, (who, im) in zip('AB', pair):
        im.save(os.path.join(d, f'{lab}.jpg'), quality=90)
    json.dump({'A': pair[0][0], 'B': pair[1][0], 'ours': o, 'ref': ref}, open(os.path.join(d, 'key.json'), 'w'))
    keys[t] = d
print(json.dumps(keys))
