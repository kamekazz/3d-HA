cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
P="C:/Users/Manuel/Desktop/Pro/3d HA/backend/.venv/Scripts/python.exe"
V=${V:-0,0.03,0.04}
"$P" wallsweep.py --room 1 --level 0 --values $V --out shots/wf_r1 > json/wf_r1.json 2>&1
"$P" wallsweep.py --room 2 --level 0 --values $V --out shots/wf_r2 > json/wf_r2.json 2>&1
"$P" wallsweep.py --room 5 --level 1 --values $V --out shots/wf_r5 > json/wf_r5.json 2>&1
"$P" wallsweep.py --room 7 --level 1 --values $V --pos 29.1,12.01,25.5 --target 29.1,11.31,15.4 --out shots/wf_r7 > json/wf_r7.json 2>&1
"$P" wallsweep.py --room 8 --level 1 --values $V --pos 35.8,13.6,6.1 --target 32.8,11.9,-1.0 --out shots/wf_r8 > json/wf_r8.json 2>&1
echo WFDONE
