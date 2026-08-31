import os, sys, tempfile, json, struct, collections
_R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..",".."))
for p in (os.path.join(_R,"tools"), os.path.join(_R,"scratchpad","bsmt"),
          os.path.join(_R,"scratchpad","arc4"), os.path.join(_R,"scratchpad","arc4","art")):
    if p not in sys.path: sys.path.insert(0,p)
import bkit
TMP=tempfile.mkdtemp(); bkit.OUT=TMP; bkit.place=lambda *a,**k:{"action":"dry"}
import ar2
ar2.save_and_place=bkit.save_and_place; ar2.place=bkit.place
for k in ("east","south","ncab"):
    ar2.BUILDERS[k]()
for fn in sorted(os.listdir(TMP)):
    p=os.path.join(TMP,fn); raw=open(p,'rb').read()
    jl=struct.unpack("<I",raw[12:16])[0]
    g=json.loads(raw[20:20+jl])
    bv=g["bufferViews"]; acc=g["accessors"]
    rows=[]
    for pr in g["meshes"][0]["primitives"]:
        b=0
        for a in list(pr["attributes"].values())+[pr["indices"]]:
            b+=bv[acc[a]["bufferView"]]["byteLength"]
        nm=g["materials"][pr["material"]].get("name","?")
        rows.append((b/1024., nm, acc[pr["attributes"]["POSITION"]]["count"]))
    rows.sort(reverse=True)
    print("== %s  %d prims  json %.1f KB  bin %.1f KB"%(fn,len(rows),jl/1024.,(len(raw)-20-jl)/1024.))
    for b,nm,n in rows: print("   %7.2f KB  %5d v  %s"%(b,n,nm))
