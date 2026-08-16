"""Round 2: wipe every 'Living *' object from room 5 so the room can be
re-metered empty and rebuilt against the re-traced footprint."""
import json, sys, urllib.request
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.place import _req

house = json.load(urllib.request.urlopen("http://127.0.0.1:5000/api/house"))
room = next(r for f in house["floors"] for r in f["rooms"] if r["id"] == 5)
for o in room.get("objects", []):
    if (o.get("name") or "").startswith("Living"):
        _req("DELETE", f"/api/house/object/{o['id']}")
        print("deleted", o["id"], o["name"])
for op in room.get("openings", []):
    _req("DELETE", f"/api/house/opening/{op['id']}")
    print("deleted opening", op["id"])
