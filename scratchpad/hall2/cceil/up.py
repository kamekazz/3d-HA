import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.abspath(os.path.join(HERE, "..", "shots"))
B = 18.0
# private check poses -- NOT in v3.py, used only to verify ceiling coverage
POSES = {
  # private check poses -- NOT in v3.py.  Modest up-tilt only: a steep look-up
  # makes roomkit.shot clip the level and show sky, which is a tool artefact.
  "c_alcove":  {"pos": [7.6, B+4.9, 22.2], "target": [10.2, B+6.9, 18.6], "fov": 78, "size": [800, 800]},
  "c_alcove2": {"pos": [10.3, B+5.0, 18.0], "target": [7.2, B+6.6, 21.4], "fov": 78, "size": [800, 800]},
  "c_well":    {"pos": [13.0, B+5.2, 21.5], "target": [17.6, B+6.9, 17.0], "fov": 82, "size": [900, 800]},
  "c_wide":    {"pos": [12.3, B+5.2, 22.6], "target": [12.9, B+6.9, 8.0],  "fov": 88, "size": [900, 1000]},
}
for n, p in POSES.items():
    out = os.path.join(OUT, "ceiling_%s.png" % n)
    r = subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(p),
                        "--level", "2", "--day", "--out", out, "--no-cutaway"],
                       cwd=TOOLS, capture_output=True, text=True)
    print(n, "ok" if r.returncode == 0 else r.stderr[-400:])
