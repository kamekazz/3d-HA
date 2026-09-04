cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
P="C:/Users/Manuel/Desktop/Pro/3d HA/backend/.venv/Scripts/python.exe"
"$P" fixshot.py --room 7 --level 1 --entities light.garage --pos 29.1,12.01,25.5 --target 29.1,10.01,15.2 --out shots/r7_round4 2>&1 | tail -2
"$P" fixshot.py --room 9 --level 1 --entities switch.laundry_room --pos 29.05,10.91,12.75 --target 32.35,11.71,8.2 --fov 92 --out shots/r9_round4 2>&1 | tail -2
"$P" fixshot.py --room 10 --level 1 --entities switch.pantry --pos 20.15,12.01,12.65 --target 20.35,12.81,7.7 --fov 84 --out shots/r10_round4 2>&1 | tail -2
"$P" fixshot.py --room 22 --level 1 --entities switch.office_closet --pos 39.1,10.41,12.7 --target 33.7,12.41,7.5 --fov 90 --out shots/r22_round4 2>&1 | tail -2
echo ALLDONE4
