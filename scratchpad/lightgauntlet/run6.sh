cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
P="C:/Users/Manuel/Desktop/Pro/3d HA/backend/.venv/Scripts/python.exe"
"$P" fixshot.py --room 9 --level 1 --entities switch.laundry_room --pos 29.05,11.41,12.75 --target 32.35,13.21,8.3 --fov 92 --out shots/r9_round6 2>&1 | tail -2
"$P" fixshot.py --room 10 --level 1 --entities switch.pantry --pos 20.15,12.51,12.3 --target 20.35,13.11,7.8 --fov 80 --out shots/r10_round6 2>&1 | tail -2
echo ALLDONE6
