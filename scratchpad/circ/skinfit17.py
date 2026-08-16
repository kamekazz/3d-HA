import sys, json
import r17
from ckit import save_and_place
c = sys.argv[1]
r17.SKINS = {k: c for k in "nswe"}
save_and_place("Hall2F Wall Wash Skins", r17.piece_skins(r17.SKINS), 17)
