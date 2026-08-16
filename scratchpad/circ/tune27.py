import sys, r27
from ckit import save_and_place
from roomkit.glb import Material
mode = sys.argv[1]
if mode == "p2":
    r27.SKINS = {k: "#ffffff" for k in "nswe"}
    r27.CARP = [Material("m27c%d" % i, c, roughness=0.99) for i, c in
                enumerate(("#5a5a57", "#605f5c", "#545451", "#5d5d59"))]
    r27.BLK  = Material("m27blk",  "#3a3b3f", roughness=0.94)
    r27.BLK2 = Material("m27blk2", "#454650", roughness=0.92)
    r27.BLK3 = Material("m27blk3", "#2e2f33", roughness=0.95)
else:
    vals = dict(a.split("=") for a in sys.argv[2:])
    if "skins" in vals:
        r27.SKINS = dict(zip("nswe", vals["skins"].split(",")))
    if "carp" in vals:
        r27.CARP = [Material("m27c%d" % i, c, roughness=0.99) for i, c in
                    enumerate(vals["carp"].split(","))]
    if "blk" in vals:
        a, b, c = vals["blk"].split(",")
        r27.BLK  = Material("m27blk",  a, roughness=0.94)
        r27.BLK2 = Material("m27blk2", b, roughness=0.92)
        r27.BLK3 = Material("m27blk3", c, roughness=0.95)
save_and_place("Master Closet Wall Wash Skins", r27.piece_skins(r27.SKINS), 27)
save_and_place("Master Closet Floor Carpet", r27.piece_carpet(), 27)
save_and_place("Master Closet Wall Wash Dark", r27.piece_black_wall(), 27)
