"""Payload of agent g3's thirteen round-5 panels, against round 4's thirteen.

Packs each set with atlas4's own shelf packer, sizes, supersample and
re-quantisation (all read out of atlas4.py rather than copied, see
preview_g3.py) and writes the PNG through roomkit's own writer -- so the bytes
printed are the bytes the wall-run atlas will actually gain or lose.

Round 4's versions of these three machines lived in TWO modules (Star Wars and
the multicade in art_g0, Ridge Racer in art_g3), so the baseline is assembled
from art_g0.py and art_g3_r4.bak.py.  Either baseline is skipped, with a note,
if that module no longer paints the key -- round 5 re-dealt the machines
between the agents and art_g0 is being edited in parallel.

    $PY scratchpad/arc4/art/size_g3.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_ROOT, "tools"))

from roomkit.glb import png_rgb                                 # noqa: E402
import preview_g3 as P                                          # noqa: E402

KEYS = ["star-wars-atari.marquee", "star-wars-atari.side",
        "star-wars-atari.front", "star-wars-atari.deck",
        "ridge-racer.marquee", "ridge-racer.side",
        "ridge-racer.front", "ridge-racer.deck", "ridge-racer.bezel",
        "north-1-graffiti-multicade.marquee",
        "north-1-graffiti-multicade.side",
        "north-1-graffiti-multicade.front",
        "north-1-graffiti-multicade.deck"]

# which wall run each machine stands on, so the cost lands where it is paid
RUN = {"star-wars-atari": "east", "ridge-racer": "south",
       "north-1-graffiti-multicade": "north"}


def pack(panels, keys):
    """atlas4.Atlas's shelf pack, cut down to bytes-only."""
    items = sorted([k for k in keys if k in panels],
                   key=lambda k: (-P.size_of(k), k))
    if not items:
        return 0, 0, []
    area = sum(P.size_of(k) ** 2 for k in items)
    width = 128
    while width * width < area * 1.30:
        width *= 2
    placed, x, y, shelf = {}, 0, 0, 0
    for k in items:
        n = P.size_of(k)
        if x + n > width:
            x, y, shelf = 0, y + shelf, 0
        placed[k] = (x, y, n)
        x += n
        shelf = max(shelf, n)
    height = max(1, y + shelf)
    px = [[(0, 0, 0)] * width for _ in range(height)]
    for k, (ox, oy, n) in placed.items():
        big = n * P.SS
        buf = [[(0, 0, 0)] * big for _ in range(big)]
        panels[k](buf, 0, 0, big)
        inv = 1.0 / (P.SS * P.SS)
        for yy in range(n):
            rows = buf[yy * P.SS:(yy + 1) * P.SS]
            out = []
            for xx in range(n):
                r = g = bb = 0
                for sr in rows:
                    for c in sr[xx * P.SS:(xx + 1) * P.SS]:
                        r += c[0]
                        g += c[1]
                        bb += c[2]
                out.append((P._q(r * inv), P._q(g * inv), P._q(bb * inv)))
            px[oy + yy][ox:ox + n] = out
    return len(png_rgb(px)), width * height, items


def main():
    import art_g3
    new = art_g3.PANELS
    old = {}
    try:
        import art_g0
        old.update({k: v for k, v in art_g0.PANELS.items() if k in KEYS})
    except Exception as e:                                      # noqa: BLE001
        print("!! art_g0 unavailable for the baseline:", e)
    try:
        import art_g3_r4_bak as _b
        old.update({k: v for k, v in _b.PANELS.items() if k in KEYS})
    except Exception as e:                                      # noqa: BLE001
        print("!! round-4 g3 backup unavailable:", e)

    print("%-8s %10s %10s %9s" % ("run", "round4 KB", "round5 KB", "delta"))
    tot4 = tot5 = 0
    for run in ("east", "south", "north"):
        ks = [k for k in KEYS if RUN[k.split(".")[0]] == run]
        b4, _, got4 = pack(old, ks)
        b5, _, got5 = pack(new, ks)
        tot4 += b4
        tot5 += b5
        print("%-8s %10.1f %10.1f %+9.1f   (%d/%d panels had a round-4 twin)"
              % (run, b4 / 1024.0, b5 / 1024.0, (b5 - b4) / 1024.0,
                 len(got4), len(got5)))
    print("%-8s %10.1f %10.1f %+9.1f" % ("TOTAL", tot4 / 1024.0,
                                         tot5 / 1024.0, (tot5 - tot4) / 1024.0))
    print("\nper-panel bytes, round 5 (packed alone, so each includes its own"
          " PNG overhead -- the run totals above are the real numbers):")
    for k in KEYS:
        b, _, _ = pack(new, [k])
        print("  %-44s %4d px  %6.1f KB" % (k, P.size_of(k), b / 1024.0))


if __name__ == "__main__":
    main()
