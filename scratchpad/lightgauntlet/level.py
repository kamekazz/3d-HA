"""Per-room levelling rig: sweep the DIRECT fixture budget in one page session
and meter lens-vs-wall plus the frame's clipping tail for every value.

Why sweeping the GLOBAL FIXTURE_BASE is a faithful stand-in for the per-fixture
light_cfg.intensity here: the shot is taken in ROOM FOCUS, so the only direct
lights in frame belong to the focused room, and slotGoal is
FIXTURE_BASE * intensity * glow * spill -- exactly linear in both. Multiplying
FIXTURE_BASE by k in this session therefore renders the same frame that
multiplying every one of this room's intensities by k would render after a
reload. The fill / slab / wall terms are gated on the eased glow, NOT on
intensity, so they do not move -- which is also true of the real edit.

Safety unchanged from roomkit.lightshot: entity state is forced CLIENT-SIDE via
state.applyState(). Home Assistant is never called.

    python level.py --room 16 --level 2 --ks 1,0.7,0.55,0.45 --out shots/lv16
    python level.py --room 16 --level 2 --pos 25,7,20 --target 25.4,6.4,11 --ks 1
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from playwright.sync_api import sync_playwright                      # noqa: E402
from roomkit.lightshot import BASE, READY_JS, SETUP_JS, COLLECT_JS   # noqa: E402

# Screen rect of every LIT part of every fixture in the room, plus a raycast
# naming of what sits either side of it. A "lit part" is a mesh whose material
# is currently emissive and bright -- which is exactly what paintFixture's
# partFilter leaves behind (everything it rejects is restored to __orig).
PROBE_JS = """
async ({ roomId }) => {
  const THREE = await import('three');
  const { camera, scene } = window.__scene3d;
  const objects = await import('/js/objects.js');
  const W = window.innerWidth, H = window.innerHeight;
  const toPx = (v) => {
    const p = v.clone().project(camera);
    return [(p.x * 0.5 + 0.5) * W, (-p.y * 0.5 + 0.5) * H, p.z];
  };
  const out = [];
  const fx = (window.__roomlights?.fixtures() || [])
    .filter(f => f.roomId === roomId && f.emits);
  for (const f of fx) {
    const root = objects.objects3d.get(f.objectId);
    if (!root) continue;
    root.updateWorldMatrix(true, true);
    const box = new THREE.Box3(); box.makeEmpty();
    let parts = [];
    root.traverse((c) => {
      if (!c.isMesh) return;
      const mats = Array.isArray(c.material) ? c.material : [c.material];
      const hot = mats.some(m => m && m.emissive && m.emissiveIntensity > 0.3
                                 && m.emissive.getHex() !== 0);
      if (!hot) return;
      parts.push(c.name || (Array.isArray(c.material) ? c.material[0]?.name : c.material?.name));
      const b = new THREE.Box3().setFromObject(c);
      box.union(b);
    });
    if (box.isEmpty()) { out.push({ id: f.objectId, glow: f.glow, shown: f.shown, empty: true }); continue; }
    const mn = box.min, mx = box.max;
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, behind = false;
    for (const cx of [mn.x, mx.x]) for (const cy of [mn.y, mx.y]) for (const cz of [mn.z, mx.z]) {
      const [px, py, pz] = toPx(new THREE.Vector3(cx, cy, cz));
      if (pz > 1) behind = true;
      x0 = Math.min(x0, px); x1 = Math.max(x1, px);
      y0 = Math.min(y0, py); y1 = Math.max(y1, py);
    }
    // is the lens actually visible from here, or behind a wall / off frame?
    const c3 = box.getCenter(new THREE.Vector3());
    const rc = new THREE.Raycaster();
    const dir = c3.clone().sub(camera.position);
    const want = dir.length();
    rc.set(camera.position, dir.normalize());
    const hits = rc.intersectObjects(scene.children, true).filter((hit) => {
      for (let n = hit.object; n; n = n.parent) if (!n.visible) return false;
      return true;
    });
    const firstAt = hits.length ? hits[0].distance : Infinity;
    out.push({
      id: f.objectId, glow: +f.glow.toFixed(2), shown: f.shown, on: f.on,
      parts: [...new Set(parts)].slice(0, 6),
      rect: [Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)],
      behind, dist: +want.toFixed(2), firstHit: +firstAt.toFixed(2),
      occluded: firstAt < want - 0.35,
      onScreen: x1 > 0 && x0 < W && y1 > 0 && y0 < H && !behind,
    });
  }
  return { out, W, H, at: [+camera.position.x.toFixed(2), +camera.position.y.toFixed(2),
                           +camera.position.z.toFixed(2)] };
}
"""

# The lens mask, shot rather than guessed. A fixture's own emissive is painted
# on its materials and owes NOTHING to the pool -- so a frame rendered with
# every pool light at zero contains the lens and almost nothing else (the slab
# and wall fills survive at 0.05 / 0.032, which meter in the teens). Threshold
# that frame and you have the exact silhouette of every lit lens in view,
# including a lens that is two tubes inside one mesh, which a projected bbox
# unions into a strip of blown wall and calls "the lens".
DARK_JS = """
async ({ dark }) => {
  const rl = await import('/js/roomlights.js');
  const { camera, renderer, scene } = window.__scene3d;
  // Pinned with a getter, not assigned: roomlights' onFrame tick lerps every
  // slot back toward its goal, so a plain `intensity = 0` is undone before the
  // screenshot's next composite and the "dark" frame comes back fully lit.
  const pts = scene.children.filter(o => o.isPointLight);
  if (dark) {
    window.__lvSaved = pts.map(o => [o, o.intensity]);
    for (const [o] of window.__lvSaved) {
      Object.defineProperty(o, 'intensity',
        { get: () => 0, set() {}, configurable: true });
    }
  } else {
    for (const [o, v] of (window.__lvSaved || [])) {
      delete o.intensity;
      o.intensity = v;
    }
    window.__lvSaved = null;
    rl.settleRoomLights();
  }
  renderer.render(scene, camera);
  return true;
}
"""

TUNE_JS = """
async ({ fixture }) => {
  const rl = await import('/js/roomlights.js');
  const { camera, renderer, scene } = window.__scene3d;
  const got = window.__roomlights.tune({ fixture });
  rl.settleRoomLights();
  renderer.render(scene, camera);
  return { got, slots: (window.__roomlights.slots() || []).filter(s => s.owner) };
}
"""

NAME_AT = """
async ({ px, py }) => {
  const THREE = await import('three');
  const { camera, scene } = window.__scene3d;
  const W = window.innerWidth, H = window.innerHeight;
  const rc = new THREE.Raycaster();
  rc.setFromCamera(new THREE.Vector2((px / W) * 2 - 1, -(py / H) * 2 + 1), camera);
  const hits = rc.intersectObjects(scene.children, true).filter((hit) => {
    for (let n = hit.object; n; n = n.parent) if (!n.visible) return false;
    return true;
  });
  if (!hits.length) return null;
  const o = hits[0].object;
  let name = o.name;
  for (let n = o; n; n = n.parent) if (n.userData && n.userData.name) { name = n.userData.name; break; }
  return { name, mesh: o.name, part: o.userData?.part || null,
           dist: +hits[0].distance.toFixed(2) };
}
"""


def lum(path):
    return np.asarray(Image.open(path).convert("L"), dtype=float)


def clampbox(r, W, H):
    x0, y0, x1, y1 = r
    return [max(0, min(W - 1, x0)), max(0, min(H - 1, y0)),
            max(1, min(W, x1)), max(1, min(H, y1))]


def dilate(mask, r):
    from PIL import ImageFilter
    im = Image.fromarray((mask * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MaxFilter(2 * r + 1))
    return np.asarray(im, dtype=np.uint8) > 127


def masks_from_dark(dark_png, thresh=90):
    """lens mask, the 'beside it' ring, and the far field, from the pool-dark frame."""
    d = lum(dark_png)
    lens = d > thresh
    near = dilate(lens, 3)            # a blown lens bleeds a pixel or two
    ring = dilate(lens, 26) & ~dilate(lens, 8)   # the surface right beside it
    return lens, near, ring


def split_by_rect(lens, rects):
    """One lens mask per fixture: the shot silhouette, cut by each fixture's own
    projected bbox. A room with three lamps must be judged lamp by lamp -- the
    critic's complaint about room 14 is its NIGHTSTANDS, and unioning them with
    a ceiling dome that passes hides exactly that."""
    H, W = lens.shape
    out = []
    for r in rects:
        x0, y0, x1, y1 = clampbox([r[0] - 4, r[1] - 4, r[2] + 4, r[3] + 4], W, H)
        m = np.zeros_like(lens)
        m[int(y0):int(y1), int(x0):int(x1)] = True
        out.append(lens & m)
    return out


def measure(path, lens, near, ring):
    a = lum(path)
    nl = a[~near]
    res = {
        "mean": round(float(a.mean()), 1),
        "frame_max": round(float(a.max()), 1),
        "nonlens_p99": round(float(np.percentile(nl, 99)), 1),
        "nonlens_p999": round(float(np.percentile(nl, 99.9)), 1),
        "nonlens_max": round(float(nl.max()), 1),
        "nonlens_frac_over210": round(float((nl > 210).mean() * 100), 3),
        "lens_px": int(lens.sum()),
    }
    if lens.sum():
        b = a[lens]
        res["lens_median"] = round(float(np.median(b)), 1)
        res["lens_p90"] = round(float(np.percentile(b, 90)), 1)
        res["lens_max"] = round(float(b.max()), 1)
    if ring.sum():
        b = a[ring]
        res["wall_median"] = round(float(np.median(b)), 1)
        res["wall_p90"] = round(float(np.percentile(b, 90)), 1)
        res["wall_max"] = round(float(b.max()), 1)
    if lens.sum() and ring.sum():
        res["ratio"] = round(res["lens_median"] / max(res["wall_median"], 0.5), 2)
    return res


def measure_one(a, lm):
    """lens median / wall-beside median / ratio for ONE fixture's silhouette."""
    if not lm.sum():
        return None
    rg = dilate(lm, 26) & ~dilate(lm, 8)
    out = {"px": int(lm.sum()), "lens": round(float(np.median(a[lm])), 1)}
    if rg.sum():
        out["wall"] = round(float(np.median(a[rg])), 1)
        out["wall_max"] = round(float(a[rg].max()), 1)
        out["ratio"] = round(out["lens"] / max(out["wall"], 0.5), 2)
    return out


def centre_mean(path):
    a = lum(path)
    H, W = a.shape
    return round(float(a[int(H * .2):int(H * .8), int(W * .2):int(W * .8)].mean()), 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--room", type=int, required=True)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--ks", default="1", help="multipliers on the current direct budget")
    p.add_argument("--out", required=True)
    p.add_argument("--pos"); p.add_argument("--target"); p.add_argument("--fov", type=float, default=74)
    p.add_argument("--entities")
    p.add_argument("--size", default="1000x750")
    p.add_argument("--settle", type=int, default=1600)
    p.add_argument("--base", type=float, default=24.0)
    a = p.parse_args()

    w, h = (int(v) for v in a.size.lower().split("x"))
    ks = [float(v) for v in a.ks.split(",")]
    light = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    given = None
    if a.pos and a.target:
        given = {"pos": [float(v) for v in a.pos.split(",")],
                 "target": [float(v) for v in a.target.split(",")], "fov": a.fov}

    res = {"room": a.room, "level": a.level, "ks": ks}
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(2500)
        for _ in range(40):
            st = page.evaluate(READY_JS)
            if st["total"] == 0 or st["loaded"] >= st["total"]:
                break
            page.wait_for_timeout(250)

        # COLLECT_JS reads roomlights' live records, which are empty until the
        # house AND the HA structure have both landed. Under parallel runs that
        # is well after the model gate: an empty id list forces nothing, so the
        # "on" and "off" frames are both just whatever the real house is doing
        # and every ratio comes back 1.00. Wait for it.
        ids = []
        for _ in range(60):
            ids = ([s.strip() for s in a.entities.split(",")] if a.entities
                   else page.evaluate(COLLECT_JS, a.room)["ids"])
            if ids:
                break
            page.wait_for_timeout(500)
        if not ids:
            raise SystemExit("room %d: no entities after 30 s" % a.room)
        res["entities"] = ids
        arg = {"roomId": a.room, "level": a.level, "light": light,
               "entityIds": ids, "on": True, "pose": given}
        first = page.evaluate(SETUP_JS, arg)
        arg["pose"] = given or first.get("pose")
        page.wait_for_timeout(a.settle)
        info = page.evaluate(SETUP_JS, arg)
        page.wait_for_timeout(500)
        res["pose"] = arg["pose"]
        res["at_on"] = info["at"]

        res["probe"] = page.evaluate(PROBE_JS, {"roomId": a.room})

        # the lens silhouette, shot with the pool dark
        page.evaluate(DARK_JS, {"dark": True})
        page.wait_for_timeout(250)
        dark = "%s_dark.png" % a.out
        page.screenshot(path=dark)
        page.evaluate(DARK_JS, {"dark": False})
        page.wait_for_timeout(250)
        lens, near, ring = masks_from_dark(dark)
        res["lens_px"] = int(lens.sum())
        res["ring_px"] = int(ring.sum())
        onscreen = [f for f in res["probe"]["out"]
                    if f.get("onScreen") and not f.get("occluded")]
        per = split_by_rect(lens, [f["rect"] for f in onscreen])
        res["fixture_ids"] = [f["id"] for f in onscreen]

        res["sweep"] = []
        for k in ks:
            fx = a.base * k
            tinfo = page.evaluate(TUNE_JS, {"fixture": fx})
            page.wait_for_timeout(350)
            page.evaluate(TUNE_JS, {"fixture": fx})
            page.wait_for_timeout(250)
            out = "%s_k%g_on.png" % (a.out, k)
            page.screenshot(path=out)
            m = measure(out, lens, near, ring)
            aa = lum(out)
            m["per_fixture"] = {str(fid): measure_one(aa, lm)
                                for fid, lm in zip(res["fixture_ids"], per)}
            m["k"] = k
            m["fixture_base"] = fx
            m["file"] = out
            m["centre"] = centre_mean(out)
            m["slots"] = tinfo["slots"]
            res["sweep"].append(m)

        # the OFF frame -- independent of the direct budget, so one is enough
        page.evaluate(TUNE_JS, {"fixture": a.base})
        arg2 = dict(arg); arg2["on"] = False
        page.evaluate(SETUP_JS, arg2)
        page.wait_for_timeout(a.settle)
        oinfo = page.evaluate(SETUP_JS, arg2)
        page.wait_for_timeout(500)
        off = "%s_off.png" % a.out
        page.screenshot(path=off)
        res["off"] = {"file": off, "centre": centre_mean(off),
                      "at": oinfo["at"],
                      "slots": [s for s in oinfo["slots"] if s["intensity"] > 0.01],
                      "all_slots": oinfo["slots"]}
        b.close()
    for s in res["sweep"]:
        s["lit_unlit"] = round(s["centre"] / max(res["off"]["centre"], 0.01), 2)
    if errs:
        res["page_errors"] = errs[:3]
    print(json.dumps(res, indent=2))
    with open(a.out + "_report.json", "w") as fh:
        json.dump(res, fh, indent=2)


if __name__ == "__main__":
    main()
