import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.join(HERE, "..", "shots")
B = 18.0
def P(x,y,z,tx,ty,tz,fov=70,size=(900,900)):
    return {"pos":[x,B+y,z],"target":[tx,B+ty,tz],"fov":fov,"size":list(size)}
POSES = {
  # high oblique over the head of the stairwell, looking SE
  "k_head": P(11.0, 9.0, 6.0, 16.5, -2.0, 16.0, fov=70),
  # low eye just north of the wall's near end, looking straight at the head
  "k_low":  P(12.6, 5.3, 9.5, 15.6, 1.0, 15.0, fov=70),
  # side elevation of the run from the walking strip
  "k_elev": P(11.6, 3.0, 18.5, 14.3, 2.6, 13.6, fov=60),
}
def shoot(n, level=2, tag=""):
    out = os.path.join(OUT, f"{tag}{n}.png")
    cmd=[PY,"-m","roomkit.shot","--pose-json",json.dumps(POSES[n]),"--level",str(level),
         "--day","--out",out,"--no-cutaway"]
    r=subprocess.run(cmd,cwd=TOOLS,capture_output=True,text=True)
    print(n, "ok" if r.returncode==0 else "FAIL", out)
    if r.returncode: print(r.stdout[-800:], r.stderr[-800:])
if __name__=="__main__":
    tag=os.environ.get("TAG","")
    for n in (sys.argv[1:] or list(POSES)): shoot(n, tag=tag)
