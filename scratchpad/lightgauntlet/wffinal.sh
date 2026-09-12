cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
P="C:/Users/Manuel/Desktop/Pro/3d HA/backend/.venv/Scripts/python.exe"
V=0,0.032
"$P" wallsweep.py --room 1 --level 0 --values $V --out shots/wfz_r1 > json/wfz_r1.json 2>&1
"$P" wallsweep.py --room 2 --level 0 --values $V --out shots/wfz_r2 > json/wfz_r2.json 2>&1
"$P" wallsweep.py --room 5 --level 1 --values $V --out shots/wfz_r5 > json/wfz_r5.json 2>&1
"$P" wallsweep.py --room 7 --level 1 --values $V --pos 29.1,12.01,25.5 --target 29.1,11.31,15.4 --out shots/wfz_r7 > json/wfz_r7.json 2>&1
"$P" wallsweep.py --room 8 --level 1 --values $V --pos 35.8,13.6,6.1 --target 32.8,11.9,-1.0 --out shots/wfz_r8 > json/wfz_r8.json 2>&1
"$P" wallsweep.py --room 5 --level 1 --values $V --day --out shots/wfd_r5 > json/wfd_r5.json 2>&1
"$P" wallsweep.py --room 7 --level 1 --values $V --day --pos 29.1,12.01,25.5 --target 29.1,11.31,15.4 --out shots/wfd_r7 > json/wfd_r7.json 2>&1
echo WFZDONE
