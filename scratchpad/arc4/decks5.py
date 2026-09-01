"""Round-5 control decks and coin doors -- ONE normalised table from four.

WHAT THIS EXISTS FOR.  Three independent critics rejected round 4 with the same
sentence: every cabinet in the room wore the same two-joystick deck (one red
top, one blue top) over the same row of flat square buttons, and the same
centred grey coin-door rectangle.  That was literal -- `ar2.upright()` built

    for k in range(2):
        jx = (-0.28 + 0.56 * k) * (bw / 2.20)      # two chrome shafts
        bx(... BUTTONS[k] ...)                     # one cube top each
        for b in range(3):
            rect_up(... BUTTONS[(k + b) % 4] ...)  # three flat squares
    bx(sub, CPANEL, -0.34, 0.34, plinth + 0.30, plinth + 0.92, ...)

on all sixteen machines regardless of slug.  The four round-5 art agents each
specified their own machines' real hardware -- and each invented a different
schema for it:

    art_g0   DECKS + DOORS          u -0.5..0.5,  button "r",    door in FEET
    art_g1   DECKS + COIN           u -0.5..0.5,  button "r",    door u/v 0..1
    art_g2   DECKS + FRONT_RECT     u -1..1,      button "r_ft", door in FEET
    art_g3   DECKS + COINDOOR       u 0..1,       button "d",    door u/v 0..1

They disagree on the coordinate frame, on the name of every field, on radius vs
diameter, and on what "no door" is spelled as (`None`, `[]`, `proud: 0.0`).
This module reads all four and returns one shape.  Nothing here invents a
control or a colour: every number traces to the module that read it off the
owner's photographs, and `why(slug)` returns that module's own evidence string.

THE TWO FRAMES, both identical to the frames the ARTWORK is authored in, so a
printed socket and the button standing in it cannot drift apart.

  DECK   `t` 0..1 across the deck art quad (width bw - 0.12), 0 at the x0 edge
         `v` 0..1 along it, 0 at the BACK edge (z = ft + 0.04, under the
              screen) and 1 at the player's edge (z = fd - 0.06)
         controls sit on the art plane, y = dy + 0.014
  FRONT  `fu` 0..1 across the printed front quad (width bw - 0.16)
         `fv` 0..1 DOWN it, 0 at the top (y = dy - 0.62), 1 at the bottom
              (y = plinth + 0.16)

Everything else is FEET.

ROUND 7 -- WHAT MOVED, AND WHAT IS STILL NOT READ.

The three art modules re-read their machines this round and their tables grew
new keys.  Round 6 read NONE of them, which is half of why it was rejected: a
spec that is quietly ignored is exactly how round 5 lost a round.  Consumed
here now, module by module, so a critic can check the wiring rather than take
it on trust:

  art_g0   `cap_r` and `dome_rise` on every button -- the MEASURED cap radius
           at the shoulder and the crown's rise above it, solved on v4 7 at
           14x with the T-molding as the ruler.  Round 6 threw both away and
           drew a fan of h*(1-0.45).  Also `pad_r`, which is PRINTED and is
           correctly still not built.
  art_g1   `emissive` (False on all 58 caps -- see `_btn`), and `profile`.
           `base_r` stays unbuilt, as its schema says.  `finish` and
           CONTROL_FINISH are prose for the engine and are answered in
           ar2.BTN, not here.
  art_g2   already normalised in round 5 and unchanged in shape; its `r_ft` /
           `h_ft` / `dust_*` and its `round_flat` profile all still arrive.
           `inferred` now flows through per machine rather than from the
           hard-coded tuple below, because round 7 moved it.
  art_g3   `emissive` per button, which is now the ONLY route to an emissive
           cap in this room and carries exactly the two Ridge Racer whites
           art_g3 flagged as lit.

NOTHING IS DROPPED SILENTLY.  Two specs are built but are NOT photograph
readings, and both say so themselves:

  street-fighter-2-champion-edition   `art_g2 inferred: True` -- "the controls
      do not resolve in any frame and this layout is declared as class
      inference".  ROUND 7 MOVED THIS: round 5's inferred machine was
      legends-ultimate, and art_g2 promoted it to READ this round off
      `Arcade Room v4 3.jpg` at 7-10x (red ball tops, gold button rings, a
      dark trackball, no spinner).  `INFERRED` below is now derived from the
      modules, not hard-coded, so it cannot go stale again.
  marvel-super-heroes   art_g1's own self-assessment: the Capcom 2x3 is a
      "DECLARED CHOICE, not a reading -- v4 6 resolves that deck's artwork
      completely and its caps not at all".  Its 14 caps are built because a
      bare deck reads as unbuilt, which is worse.

See `SKIPPED` for the two items that genuinely are not built, and why.
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import art_g0                                                # noqa: E402
import art_g1                                                # noqa: E402
import art_g2                                                # noqa: E402
import art_g3                                                # noqa: E402

button_cap = art_g1.button_cap        # 9 verts / 8 tris, 310 B in a saved GLB
ball_top = art_g1.ball_top

# The two things in the four specs that are NOT built, declared rather than
# silently dropped:
SKIPPED = {
    "time-crisis.extras.foot_pedal":
        "art_g2 asks for a red floor pedal ~1.0 x 0.8 x 0.35 ft, 0.9 ft in "
        "front of the deck lip.  It is real (v3 4, v4 5) but it stands on the "
        "FLOOR, not on the cabinet, and `upright()` builds a cabinet -- it "
        "would have to go into build_south_cabs' room frame.  Left for the "
        "next round; it is furniture, not the defect this round is fixing.",
    "star-wars-atari.fallback":
        "art_g3 offers four plain red buttons as a fallback if the flight "
        "yoke is too much to build.  The yoke IS built (57 verts), so the "
        "fallback is unused.",
}

def _inferred():
    """Which machines' decks are class inference rather than a reading.

    Derived from the modules every run.  Round 5 hard-coded this as
    ("legends-ultimate",) and round 7 moved it -- art_g2 promoted Legends
    Ultimate to READ and declared Champion Edition inferred instead.
    """
    out = [s for s, d in art_g2.DECKS.items() if d.get("inferred")]
    # art_g1 does not carry the flag; its own report declares this one.
    out.append("marvel-super-heroes")
    return tuple(sorted(out))


INFERRED = _inferred()


# --------------------------------------------------------------- utilities
def _lum(c):
    c = c.lstrip("#")
    return (0.299 * int(c[0:2], 16) + 0.587 * int(c[2:4], 16)
            + 0.114 * int(c[4:6], 16))


def _btn(t, v, r, h, col, profile="convex", emis=None,
         cap_r=None, rise=None):
    """One normalised button.

    ROUND 7 CHANGED TWO THINGS HERE, and both are the reason round 6 was
    rejected 0-4 for "flat 2-3 px coloured lozenges with no dome, no rim
    shadow and no specular".

    1. `emis` NOW DEFAULTS TO FALSE.  Round 5 wrote the rule above -- emissive
       on anything under luma 190 -- and it put 42 of art_g1's 58 caps, and
       most of art_g0's and art_g2's, through `ar2.cmat(col, .34, 0, col, .75)`.
       An emissive surface takes no highlight and no shading: whatever geometry
       stands under it renders as a flat disc of one hue.  art_g1's
       CONTROL_FINISH asks for exactly this change in writing
       ("buttons must be emissive:False ... ar2 today sends every coloured cap
       through cmat(col, 0.34, 0.0, col, 0.75) -- emissive at 0.75, which is
       why a cap renders as a flat disc of pure hue no matter what geometry is
       under it"), art_g0's BUTTON_MAT_REQUEST bans emissive on its three
       near-white colours, and art_g2's HW_HINTS asks for a roughness change
       that only means anything on a non-emissive surface.  Three of the four
       modules asked; the fourth (art_g3) sets `emissive` explicitly per button
       and its two lit Ridge Racer caps still come through True.
    2. `cap_r` and `rise` are carried.  art_g0 measured them
       (`cap_r` = the cap radius at the shoulder, `dome_rise` = the cap's rise
       above it); the other three did not, so they are derived below at the
       same ratios art_g0 measured -- cap_r/r 0.74 and rise/h 0.41 -- rather
       than invented per module.
    """
    if emis is None:
        emis = False
    if cap_r is None:
        cap_r = r * 0.74
    if rise is None:
        rise = h * 0.41
    return {"t": t, "v": v, "r": r, "h": h, "col": col,
            "profile": profile, "emis": emis,
            "cap_r": min(cap_r, r * 0.96), "rise": min(rise, h * 0.75)}


def _stick(t, v, shaft_r, shaft_h, shaft_col, top, top_r, top_h, top_col,
           washer_r=0.0, washer_col=None):
    return {"t": t, "v": v, "shaft_r": shaft_r, "shaft_h": shaft_h,
            "shaft_col": shaft_col, "top": top, "top_r": top_r,
            "top_h": top_h, "top_col": top_col,
            "washer_r": washer_r, "washer_col": washer_col}


def _empty():
    return {"sticks": [], "buttons": [], "trackball": None, "spinner": None,
            "guns": [], "yoke": None, "wheel": None, "lip": None,
            "why": "", "inferred": False}


# ------------------------------------------------------------ the four reads
def _from_g0(slug, d):
    """art_g0: u -0.5..0.5, button `r`/`profile`, stick `top_d` is a DIAMETER."""
    out = _empty()
    out["why"] = d.get("why", "")
    for s in d.get("sticks", []):
        out["sticks"].append(_stick(
            s["u"] + 0.5, s["v"], s["shaft_r"], s["shaft_h"], s["shaft_color"],
            s.get("top", "ball"), s["top_d"] / 2.0, s["top_d"] * 0.95,
            s["top_color"]))
    for b in d.get("buttons", []):
        out["buttons"].append(_btn(b["u"] + 0.5, b["v"], b["r"], b["h"],
                                   b["color"], b.get("profile", "convex"),
                                   cap_r=b.get("cap_r"),
                                   rise=b.get("dome_rise")))
    tb = d.get("trackball")
    if tb:
        out["trackball"] = {"t": tb["u"] + 0.5, "v": tb["v"], "r": tb["r"],
                            "col": tb["color"], "bezel": tb["bezel_color"]}
    return out


def _from_g1(slug, d):
    """art_g1: u -0.5..0.5, `col`, `base_r` is PAINTED (do not build it)."""
    out = _empty()
    out["why"] = "art_g1 deck spec"
    for s in d.get("sticks", []):
        out["sticks"].append(_stick(
            s["u"] + 0.5, s["v"], s["shaft_r"], s["shaft_h"], s["shaft_col"],
            s.get("top", "ball"), s["top_r"], s.get("top_h", 0.11),
            s["top_col"]))
    for b in d.get("buttons", []):
        # art_g1 sets `emissive` on every cap and every one of them is False;
        # round 6 never read the key.  `profile` is new this round too.
        out["buttons"].append(_btn(b["u"] + 0.5, b["v"], b["r"], b["h"],
                                   b["col"], b.get("profile", "convex"),
                                   emis=bool(b.get("emissive", False))))
    return out


def _from_g2(slug, d, bw):
    """art_g2: u -1..1 against HALF the width, `*_ft` names, `dust_*` washer."""
    aw = bw - 0.12                                    # the deck art quad width
    def _t(u):
        return 0.5 + u * (bw / 2.0 - 0.10) / aw
    out = _empty()
    out["why"] = d.get("note", "")
    out["inferred"] = bool(d.get("inferred"))
    for s in d.get("sticks", []):
        out["sticks"].append(_stick(
            _t(s["u"]), s["v"], 0.027, s["shaft_h_ft"], s["shaft_color"],
            s.get("top", "ball"), s["top_r_ft"], 0.115, s["top_color"],
            s.get("dust_r_ft", 0.0), s.get("dust_color")))
    for b in d.get("buttons", []):
        sh = b.get("shape", "round_convex")
        out["buttons"].append(_btn(
            _t(b["u"]), b["v"], b["r_ft"], b["h_ft"], b["color"],
            "flat" if sh == "round_flat" else "convex"))
    tb = d.get("trackball")
    if tb:
        out["trackball"] = {"t": _t(tb["u"]), "v": tb["v"], "r": tb["r_ft"],
                            "col": tb["color"], "bezel": tb["bezel_color"]}
    sp = d.get("spinner")
    if sp:
        out["spinner"] = {"t": _t(sp["u"]), "v": sp["v"], "r": sp["r_ft"],
                          "col": sp["color"]}
    for g in d.get("guns", []):
        out["guns"].append({"t": _t(g["u"]), "v": g["v"], "yaw": g["yaw_deg"],
                            "body": g["body"], "grip": g["grip"],
                            "len": g["len_ft"], "cradle": g.get("cradle"),
                            "cradle_col": g.get("cradle_color")})
    lp = d.get("lip")
    if lp:
        out["lip"] = {"col": lp["color"], "emissive": lp["emissive"],
                      "strength": lp["emissive_strength"], "h": lp["h_ft"]}
    return out


def _from_g3(slug, d):
    """art_g3: u 0..1 already, button `d` is a DIAMETER, `specials` list."""
    out = _empty()
    out["why"] = d.get("note", "")
    for s in d.get("sticks", []):
        out["sticks"].append(_stick(
            s["u"], s["v"], s["shaft_r"], s["shaft_h"], s["shaft_col"],
            s.get("type", "bat"), s["top_w"], s["top_h"], s["top_col"],
            s.get("washer_r", 0.0), s.get("washer_col")))
    for b in d.get("buttons", []):
        out["buttons"].append(_btn(b["u"], b["v"], b["d"] / 2.0, b["h"],
                                   b["col"], emis=b.get("emissive")))
    for sp in d.get("specials", []):
        if sp["kind"] == "yoke":
            out["yoke"] = dict(sp, t=sp["u"])
        elif sp["kind"] == "wheel":
            out["wheel"] = dict(sp, t=sp["u"])
    return out


# The one slot with no identity.  EAST_RUN[6] is the position the roster found
# EMPTY in all four frames that see the whole run, so no art module claims it
# and none specified a deck.  It is not left bare (an empty deck reads as
# unbuilt) and it is NOT given round 4's red-and-blue pair either: two black
# bat-tops and six unlit charcoal buttons, the plainest hardware in the room,
# which is what an unbranded black upright with no licensed graphic should
# look like.  Declared here rather than hidden in `upright()`.
_EAST7 = {
    "why": "no machine in this slot in any frame; plain unbranded hardware",
    "sticks": [{"u": u, "v": 0.58, "shaft_r": 0.028, "shaft_h": 0.17,
                "shaft_col": "#8f939a", "type": "bat", "top_w": 0.046,
                "top_h": 0.11, "top_col": "#14151a", "washer_r": 0.072,
                "washer_col": "#5c6068"} for u in (0.30, 0.70)],
    "buttons": [{"u": 0.30 + 0.40 * (k // 3) + 0.078 * (k % 3) - 0.078,
                 "v": 0.38 + 0.16 * ((k % 3) == 1), "d": 0.096, "h": 0.026,
                 "col": "#2e3037", "emissive": False} for k in range(6)],
    "specials": [],
}


def deck_for(slug, bw):
    """The normalised control deck for one machine, or None."""
    if slug == "east-7-no-machine":
        return _from_g3(slug, _EAST7)
    if slug in art_g0.DECKS:
        return _from_g0(slug, art_g0.DECKS[slug])
    if slug in art_g1.DECKS:
        return _from_g1(slug, art_g1.DECKS[slug])
    if slug in art_g2.DECKS:
        return _from_g2(slug, art_g2.DECKS[slug], bw)
    if slug in art_g3.DECKS:
        return _from_g3(slug, art_g3.DECKS[slug])
    return None


# ------------------------------------------------------------- coin doors
def _door(x0, x1, y0, y1, proud, plate, trim=None, slots=0, cup=None,
          boss=None, why=""):
    return {"x0": x0, "x1": x1, "y0": y0, "y1": y1, "proud": proud,
            "plate": plate, "trim": trim, "slots": slots, "cup": cup,
            "boss": boss, "why": why}


def coin_for(slug, bw, dy, plinth):
    """Coin doors for one machine, as a LIST of rects in cabinet-local FEET.

    `x` is 0 at the machine's centreline, `y` is height above the floor with
    the plinth already in, `proud` is how far the plate stands off the front
    face.  Two of the four schemas gave feet and two gave normalised u/v
    against the DEFAULT printed front quad (width bw - 0.16, top y = dy - 0.62,
    bottom y = plinth + 0.16); both are resolved to feet here so the caller
    never has to know which module wrote a machine.

    An EMPTY LIST means this machine has no proud coin door -- either the
    photographs show none (TMNT: art_g0 returns `None`, and says so), or the
    door is a flush recess the printed artwork already carries (Ridge Racer,
    Champion Edition, and the multicade apart from its one white plunger).
    Round 4 gave all sixteen machines the same 0.68 x 0.62 ft grey plate dead
    centre, which on NBA Jam landed through the middle of the printed badge.
    """
    fw = bw - 0.16                                   # front art quad width
    ytop, ybot = dy - 0.62, plinth + 0.16
    fh = ytop - ybot

    def _x(u):                                       # u 0..1 -> local feet
        return (u - 0.5) * fw

    def _y(v):                                       # v 0..1 top-down -> feet
        return ytop - v * fh

    if slug in art_g0.DOORS:                          # x/y in FEET, or None
        d = art_g0.DOORS[slug]
        if not d:
            return []
        out = [_door(d["x"][0], d["x"][1], d["y"][0], d["y"][1],
                     d["proud"], d["plate"], d.get("bezel"),
                     d.get("coin_slots", 0), why=d.get("why", ""))]
        rc = d.get("return_cup")
        if rc:
            out[0]["cup"] = {"x0": rc["x"][0], "x1": rc["x"][1],
                             "y": rc["y"], "col": rc["color"]}
        return out

    if slug in art_g1.COIN:                           # a LIST, u/v normalised
        return [_door(_x(c["u0"] + 0.5), _x(c["u1"] + 0.5),
                      _y(c["v1"]), _y(c["v0"]),
                      c["depth"], c["colour"], c.get("trim"), 2,
                      why=c.get("note", ""))
                for c in art_g1.COIN[slug]]

    if slug in art_g2.DECKS:                          # coin_geometry, in FEET
        g = art_g2.DECKS[slug].get("coin_geometry")
        if not g:
            return []
        xc = g["u"] * (bw / 2.0 - 0.10)
        w = g["w_ft"]
        out = _door(xc - w / 2.0, xc + w / 2.0,
                    plinth + g["y0_ft"], plinth + g["y1_ft"], g["depth_ft"],
                    g["plate"], g.get("recess"), 2, why=g.get("note", ""))
        if g.get("cup"):
            out["cup"] = {"x0": xc - w * 0.30, "x1": xc + w * 0.30,
                          "y": plinth + g["y0_ft"] + 0.09,
                          "col": g.get("cup_color") or "#0a0a0e"}
        return [out]

    if slug in art_g3.COINDOOR:                       # u/v 0..1, proud 0 = none
        d = art_g3.COINDOOR[slug]
        out = []
        if d.get("proud", 0.0) > 0.001 and d.get("plate"):
            o = _door(_x(d["u0"]), _x(d["u1"]), _y(d["v1"]), _y(d["v0"]),
                      d["proud"], d["plate"], None, 2, why=d.get("note", ""))
            out.append(o)
            c = d.get("cup")
            if c:
                out.append(_door(_x(c["u0"]), _x(c["u1"]),
                                 _y(c["v1"]), _y(c["v0"]),
                                 c["proud"], c["plate"], None, 0))
        b = d.get("boss")
        if b:
            out.append(_door(_x(b["u"] - b["r"]), _x(b["u"] + b["r"]),
                             _y(b["v"] + b["r"]), _y(b["v"] - b["r"]),
                             b["proud"], b["col"], None, 0,
                             boss=b, why=d.get("note", "")))
        return out

    return []


# --------------------------------------------------- the printed front rect
# art_g2's four machines print their front artwork all the way to the floor;
# `upright()`'s default rect stops at plinth + 0.16 and insets 0.08.
FRONT_RECT = dict(getattr(art_g2, "FRONT_RECT", {}))


def front_rect(slug, bw, dy, plinth):
    """(x0, x1, y0, y1) of the printed front quad, in cabinet-local feet."""
    r = FRONT_RECT.get(slug)
    if r:
        ins = r.get("inset_ft", 0.08)
        return (-bw / 2.0 + ins, bw / 2.0 - ins,
                plinth + r["y0_ft"], plinth + r["y1_ft"])
    # ROUND 8 -- FULL BLEED INTO THE T-MOLDING.  Round 7's default held the
    # printed front 0.08 ft inside each vertical edge and 0.16 ft off the floor,
    # and both art agents deleted their own painted edge trim this round on the
    # understanding that a real bead would take that strip.  `ar2.tmold()`
    # occupies x0-0.006 .. x0+0.056 of the front face, so a 0.045 inset puts the
    # last 0.011 ft of vinyl UNDER the bead -- which is what full bleed into a
    # T-molding means -- instead of leaving a bare sliver of carcase beside it.
    # Vertically the panel now runs from 0.05 (a kick reveal, not a margin) to
    # 0.02 ft short of where the flat front face itself ends and the sloped
    # apron begins, closing the widest unprinted strip on every machine.  The
    # panel ASPECTS follow automatically -- `ar2._aspects()` computes them from
    # this rect and hands them to atlas4 -- so every module's art re-renders to
    # the new shape rather than stretching into it.
    return (-bw / 2.0 + 0.045, bw / 2.0 - 0.045, plinth + 0.05, dy - 0.57)


# ONE machine's printed front does not sit on the cabinet's own front plane.
#
# `ar2.build_south_cabs` stands a separate blue box in front of Champion
# Edition -- "the blue CAPCOM lower cabinet the Champion Edition stands on",
# from round 3, and the photographs do show one.  It is a shell around the
# machine's lower body: x 3.62..6.28 against the machine's 3.74..6.16, and its
# FRONT face lands 0.255 ft in front of `zf`.  So every pixel of that machine's
# printed lower front is behind it, which is why the round-4 render showed a
# plain blue block and why `art_g2.FRONT_RECT` carries a "requires" note.
#
# art_g2 asked for the BOX to move back.  That does not work: the box runs to
# y 2.55 and the cabinet's sloped apron starts at 1.91, so pushing it behind
# the front plane makes it erupt through the control deck.  Pushing the printed
# QUAD forward onto the box's own face does work, costs nothing, and puts the
# artwork exactly where the real machine's artwork is -- on the blue base, with
# a 0.12 ft blue border left showing either side.
FRONT_Z = {"street-fighter-2-champion-edition": 0.265}


def front_z(slug):
    return FRONT_Z.get(slug, 0.0)


# --------------------------------------------------------------- self-check
if __name__ == "__main__":
    import atlas4
    RUNS = {}
    for mod, names in (("east", atlas4.EAST_SLUGS),
                       ("south", atlas4.SOUTH_SLUGS),
                       ("north", atlas4.NORTH_SLUGS)):
        for s in names:
            RUNS[s] = mod
    tot_b = tot_s = 0
    for s in RUNS:
        d = deck_for(s, 2.30)
        c = coin_for(s, 2.30, 2.50, 0.0)
        if d is None:
            print("%-36s NO DECK SPEC" % s)
            continue
        nb, ns = len(d["buttons"]), len(d["sticks"])
        tot_b += nb
        tot_s += ns
        extra = [k for k in ("trackball", "spinner", "yoke", "wheel", "lip")
                 if d[k]]
        if d["guns"]:
            extra.append("%d guns" % len(d["guns"]))
        print("%-36s %2d btn  %d stick  %d door  %s%s"
              % (s, nb, ns, len(c), ",".join(extra),
                 "   INFERRED" if d["inferred"] else ""))
    print("total %d buttons, %d sticks" % (tot_b, tot_s))
