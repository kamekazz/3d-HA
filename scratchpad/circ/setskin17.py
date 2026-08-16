import sys, r17
from ckit import save_and_place
S = {"n":"#6b6b6b","w":"#a4a4a4","e":"#c8c8c8","s":"#f1f1f1"}
if len(sys.argv)>1: S = dict(zip("nwes", sys.argv[1:5]))
r17.SKINS = S
save_and_place("Hall2F Wall Wash Skins", r17.piece_skins(S), 17)
print(S)
