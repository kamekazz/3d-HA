import json
import sys
import urllib.request

BASE = "http://127.0.0.1:5000"


def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as f:
        t = f.read().decode()
    return json.loads(t) if t.strip() else {}


BINDINGS = [
    (357, "light.rosemarys_closet", {"emit": True, "offset_y": 0.2}),
    (358, "light.rosemarys_closet", {"emit": True, "offset_y": 0.3}),
    (359, "light.rosemarys_closet", {"emit": True, "offset_y": 0.5}),
    (360, "light.rosemarys_closet", {"emit": True, "offset_y": 0.15}),
]

if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1] == "unbind":
        for oid, _, _ in BINDINGS:
            print(oid, req("DELETE", f"/api/house/object/{oid}"))
    else:
        for oid, ent, cfg in BINDINGS:
            print(oid, req("PATCH", f"/api/house/object/{oid}",
                           {"entity_id": ent, "light_cfg": cfg}))
