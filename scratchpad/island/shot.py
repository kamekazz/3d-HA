"""Island gauntlet capture rig: boot the app, wait for the yard, pose and shoot.

    python shot.py <out.png> [--light day|dusk|night] [--pose px,py,pz,tx,ty,tz]
                   [--size WxH] [--port 5001] [--query yard=lite] [--js "<expr>"] [--mobile]

Default pose = whatever the app frames on the House level (pass --pose to override).
Prints JSON: pose, boot timeline, vertex/program counts, console errors.
"""
import json, sys, os, argparse, time
from playwright.sync_api import sync_playwright

LIGHTS = {
    'day':   {"elevation": 42, "azimuth": 155, "condition": "sunny"},
    'dusk':  {"elevation": -7, "azimuth": 250, "condition": "clear-night"},
    'night': {"elevation": -18, "azimuth": 0, "condition": "clear-night"},
}

SETUP_JS = """
async ({ light, pose, free }) => {
  const house = await import('/js/house.js');
  const { camera, controls } = window.__scene3d;
  house.setLevel('all');
  window.__daylight?.simulate(light);
  await new Promise(r => setTimeout(r, 1600));
  if (pose) {
    if (free) { controls.maxDistance = 1e5; controls.minDistance = 0; controls.maxPolarAngle = Math.PI; camera.far = Math.max(camera.far, 5000); camera.updateProjectionMatrix(); }
    camera.position.set(pose[0], pose[1], pose[2]);
    controls.target.set(pose[3], pose[4], pose[5]);
    controls.update();
    const sc = await import('/js/scene.js');
    if (free) sc.setMaxZoom(1e5);
    sc.focusOn(pose[3], pose[4], pose[5]);
    camera.updateMatrixWorld(true);
  }
  await new Promise(r => setTimeout(r, 400));
  return { pos: camera.position.toArray().map(v => +v.toFixed(1)),
           target: controls.target.toArray().map(v => +v.toFixed(1)) };
}
"""

STATS_JS = """
() => {
  const { renderer, scene } = window.__scene3d;
  let verts = 0;
  scene.traverseVisible(o => { if (o.isMesh && o.geometry?.attributes?.position) verts += o.geometry.attributes.position.count * (o.count || 1); });
  const tl = window.__boot?.timeline?.();
  return { verts, programs: renderer.info.programs?.length, calls: renderer.info.render.calls,
           tris: renderer.info.render.triangles, boot: tl };
}
"""

HIDE_CHROME_JS = """
() => { for (const el of document.querySelectorAll('body > *:not(canvas):not(#scene):not(#app)')) {
          if (!el.querySelector('canvas')) el.style.visibility = 'hidden'; } }
"""

a = argparse.ArgumentParser()
a.add_argument('out')
a.add_argument('--light', default='day')
a.add_argument('--pose')
a.add_argument('--size', default='1400x900')
a.add_argument('--port', default='5001')
a.add_argument('--query', default='yard=full')
a.add_argument('--wait', type=int, default=120000)
a.add_argument('--js')
a.add_argument('--keep-chrome', action='store_true')
a.add_argument('--mobile', action='store_true')
a.add_argument('--free', action='store_true')
args = a.parse_args()
w, h = (int(v) for v in args.size.lower().split('x'))
pose = [float(v) for v in args.pose.split(',')] if args.pose else None

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--hide-scrollbars"])
    ctx_kw = dict(viewport={"width": w, "height": h}, device_scale_factor=1)
    if args.mobile:
        ctx_kw.update(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True,
                      user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36")
    p = b.new_context(**ctx_kw).new_page()
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: errs.append('console.error: ' + m.text) if m.type == 'error' else None)
    t0 = time.time()
    p.goto("http://127.0.0.1:%s/?%s" % (args.port, args.query), wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_function("() => !document.getElementById('boot-screen') || getComputedStyle(document.getElementById('boot-screen')).display === 'none' || getComputedStyle(document.getElementById('boot-screen')).opacity === '0'", timeout=args.wait)
    reveal = time.time() - t0
    p.wait_for_function("() => window.__environment && window.__environment.state().standing && window.__environment.state().shown", timeout=args.wait)
    p.wait_for_timeout(2500)
    info = p.evaluate(SETUP_JS, {"light": LIGHTS[args.light], "pose": pose, "free": args.free})
    p.wait_for_timeout(1200)
    info = p.evaluate(SETUP_JS, {"light": LIGHTS[args.light], "pose": pose or (info["pos"] + info["target"]), "free": args.free})
    if args.js:
        info["js"] = p.evaluate(args.js)
        p.wait_for_timeout(800)
    if not args.keep_chrome:
        p.evaluate(HIDE_CHROME_JS)
    p.wait_for_timeout(600)
    p.screenshot(path=args.out)
    stats = p.evaluate(STATS_JS)
    res = {"file": args.out, "reveal_s": round(reveal, 1), "pose": info,
           "verts": stats["verts"], "programs": stats["programs"], "calls": stats["calls"]}
    tl = stats.get("boot")
    if tl: res["boot_tail"] = tl[-3:] if isinstance(tl, list) else tl
    if errs: res["errors"] = errs[:6]
    print(json.dumps(res, indent=1, default=str))
    b.close()
