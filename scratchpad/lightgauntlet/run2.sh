P="../../backend/.venv/Scripts/python.exe"
cd "C:/Users/Manuel/Desktop/Pro/3d HA/tools" && $P -m roomkit.lightshot --room 5 --level 1 --out ../scratchpad/lightgauntlet/shots/r5_round2 2>&1 | tail -2
cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
$P fixshot.py --room 6 --level 1 --entities switch.kitchen --pos 8.11,13.81,17.54 --target 1.31,10.81,10.74 --out shots/r6_round3 2>&1 | tail -2
$P fixshot.py --room 7 --level 1 --entities light.garage --pos 29.1,11.21,32.5 --target 29.1,12.81,16.5 --out shots/r7_round2 2>&1 | tail -2
$P fixshot.py --room 8 --level 1 --entities light.work_office_desk --pos 35.8,13.6,6.1 --target 32.8,11.9,-1.0 --out shots/r8_round3 2>&1 | tail -2
$P fixshot.py --room 9 --level 1 --entities switch.laundry_room --pos 29.1,11.31,12.6 --target 32.3,12.41,8.3 --fov 82 --out shots/r9_round2 2>&1 | tail -2
$P fixshot.py --room 10 --level 1 --entities switch.pantry --pos 19.4,11.31,12.5 --target 21.3,12.41,8.1 --fov 84 --out shots/r10_round2 2>&1 | tail -2
$P fixshot.py --room 22 --level 1 --entities switch.office_closet --pos 33.8,11.21,12.4 --target 38.8,11.81,7.6 --fov 84 --out shots/r22_round2 2>&1 | tail -2
echo ALLDONE
