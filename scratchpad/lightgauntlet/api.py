import json, sys, urllib.request
BASE = "http://127.0.0.1:5000"

def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=60) as f:
        t = f.read().decode()
    return json.loads(t) if t.strip() else {}

def add(room, **kw):
    return req("POST", f"/api/house/room/{room}/object", kw)

def patch(oid, **kw):
    return req("PATCH", f"/api/house/object/{oid}", kw)

def delete(oid):
    return req("DELETE", f"/api/house/object/{oid}")

if __name__ == "__main__":
    print(json.dumps(req(sys.argv[1], sys.argv[2],
                         json.loads(sys.argv[3]) if len(sys.argv) > 3 else None), indent=1))
