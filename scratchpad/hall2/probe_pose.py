"""Round-3 door poses.  `d2` is framed to match docs/v2 Hallway-jpg/
two_closed_white_doors_2.jpg: standing in the walking strip a little east of
centre, ~7 ft back from the SW corner, eye 5.3 ft, tilted down onto the floor.
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.join(HERE, "shots"); os.makedirs(OUT, exist_ok=True)
BASE = 18.0
def P(x,y,z,tx,ty,tz,fov=74,size=(450,600)):
    return {"pos":[x,BASE+y,z],"target":[tx,BASE+ty,tz],"fov":fov,"size":list(size)}
CAND = {
  # the two_closed_white_doors_2 framing: bath door left, corner, Rios right
  "d2":   P(13.55,5.30,16.90, 11.15,3.15,22.45),
  # the two_closed_white_doors_1 framing: closer, more face-on to the bath
  "d1":   P(13.05,5.35,18.30, 11.90,3.05,23.10),
  # look due west at the three west doors
  "dw":   P(13.90,5.20,19.60, 10.40,3.60,19.10),
  # close on a long skirting run (west wall, north half) to read the
  # contact shadow and the cap highlight
  "sk":   P(13.20,2.60,9.30, 12.90,0.10,6.75, 60, (600,600)),
  "c_s":  P(12.60,5.20,17.60, 12.20,3.60,23.20),
}
names = sys.argv[1:] or list(CAND)
for n in names:
    out=os.path.join(OUT,"r3_%s.png"%n)
    r=subprocess.run([PY,"-m","roomkit.shot","--pose-json",json.dumps(CAND[n]),"--level","2","--day","--no-cutaway","--out",out],cwd=TOOLS,capture_output=True,text=True)
    print(n, "ok" if r.returncode==0 else "FAIL", out)
    if r.returncode: print(r.stdout[-800:], r.stderr[-800:])
