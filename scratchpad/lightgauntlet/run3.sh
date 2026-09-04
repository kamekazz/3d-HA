cd "C:/Users/Manuel/Desktop/Pro/3d HA/tools"
"C:/Users/Manuel/Desktop/Pro/3d HA/backend/.venv/Scripts/python.exe" -m roomkit.lightshot --room 5 --level 1 --out ../scratchpad/lightgauntlet/shots/r5_round2 2>&1 | tail -2
cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
P="C:/Users/Manuel/Desktop/Pro/3d HA/backend/.venv/Scripts/python.exe"
"$P" fixshot.py --room 6 --level 1 --entities switch.kitchen --pos 8.11,13.81,17.54 --target 1.31,10.81,10.74 --out shots/r6_round4 2>&1 | tail -2
"$P" fixshot.py --room 7 --level 1 --entities light.garage --pos 29.1,12.11,32.5 --target 29.1,11.11,17.0 --out shots/r7_round3 2>&1 | tail -2
"$P" fixshot.py --room 8 --level 1 --entities light.work_office_desk --pos 35.8,13.6,6.1 --target 32.8,11.9,-1.0 --out shots/r8_round4 2>&1 | tail -2
"$P" fixshot.py --room 9 --level 1 --entities switch.laundry_room --pos 29.1,11.01,12.65 --target 32.4,11.81,8.2 --fov 84 --out shots/r9_round3 2>&1 | tail -2
"$P" fixshot.py --room 10 --level 1 --entities switch.pantry --pos 20.35,12.21,12.3 --target 20.35,13.01,7.9 --fov 80 --out shots/r10_round3 2>&1 | tail -2
"$P" fixshot.py --room 22 --level 1 --entities switch.office_closet --pos 38.8,11.41,12.4 --target 34.0,12.01,7.7 --fov 82 --out shots/r22_round3 2>&1 | tail -2
echo ALLDONE3
