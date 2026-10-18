"""Night exterior frame of the House level, moon gauntlet.

    python shot.py <out.png> [--day] [--pose px,py,pz,tx,ty,tz] [--size WxH] [--port 5001]

Waits for the boot curtain AND the yard (environment.js) to stand, forces the
clear-night sun override, parks the camera on the street view and screenshots.
Prints JSON with the pose used and a luminance meter.
"""
import json, sys, os, argparse
sys.path.insert(0, os.path.abspath('../../tools'))
from roomkit.lightshot import meter
from playwright.sync_api import sync_playwright

READY_JS = """
() => {
  const b = window.__boot?.timeline?.();
  const env = window.__environment;
  const standing = !!(env && env.standing && env.standing());
  return { curtain: !document.querySelector('#boot-curtain, .boot-curtain, #curtain') ||
           getComputedStyle(document.querySelector('#boot-curtain, .boot-curtain, #curtain')).display === 'none' ||
           getComputedStyle(document.querySelector('#boot-curtain, .boot-curtain, #curtain')).opacity === '0',
           standing };
}
"""

SETUP_JS = """
async ({ light, pose }) => {
  const house = await import('/js/house.js');
  const { camera, controls, renderer, scene } = window.__scene3d;
  house.setLevel('all');
  window.__daylight?.simulate(light);
  await new Promise(r => setTimeout(r, 1600));
  if (pose) {
    camera.position.set(pose[0], pose[1], pose[2]);
    controls.target.set(pose[3], pose[4], pose[5]);
    controls.update();
    camera.updateMatrixWorld(true);
  }
  await new Promise(r => setTimeout(r, 400));
  return { pos: camera.position.toArray().map(v => +v.toFixed(1)),
           target: controls.target.toArray().map(v => +v.toFixed(1)),
           night: window.__daylight?.getNightFactor?.() };
}
"""

HIDE_CHROME_JS = """
() => { for (const el of document.querySelectorAll('body > *:not(canvas):not(#scene):not(#app)')) {
          if (!el.querySelector('canvas')) el.style.visibility = 'hidden'; } }
"""

a = argparse.ArgumentParser()
a.add_argument('out')
a.add_argument('--day', action='store_true')
a.add_argument('--pose')
a.add_argument('--size', default='1280x800')
a.add_argument('--port', default='5001')
a.add_argument('--wait', type=int, default=60000)
a.add_argument('--keep-chrome', action='store_true')
args = a.parse_args()
w, h = (int(v) for v in args.size.lower().split('x'))
light = ({"elevation": 42, "azimuth": 155, "condition": "sunny"} if args.day
         else {"elevation": -18, "azimuth": 0, "condition": "clear-night"})
pose = [float(v) for v in args.pose.split(',')] if args.pose else None

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: errs.append('console.error: ' + m.text) if m.type == 'error' else None)
    p.goto("http://127.0.0.1:%s/?yard=full" % args.port, wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_function("() => !document.getElementById('boot-screen') || getComputedStyle(document.getElementById('boot-screen')).display === 'none' || getComputedStyle(document.getElementById('boot-screen')).opacity === '0'", timeout=args.wait)
    p.wait_for_function("() => window.__environment && window.__environment.state().standing && window.__environment.state().shown", timeout=args.wait)
    p.wait_for_timeout(2500)
    info = p.evaluate(SETUP_JS, {"light": light, "pose": pose})
    p.wait_for_timeout(1200)
    info = p.evaluate(SETUP_JS, {"light": light, "pose": pose or (info["pos"] + info["target"])})
    if not args.keep_chrome:
        p.evaluate(HIDE_CHROME_JS)
    p.wait_for_timeout(600)
    p.screenshot(path=args.out)
    res = {"file": args.out, "pose": info, "meter": meter(args.out)}
    if errs: res["errors"] = errs[:5]
    print(json.dumps(res, indent=1))
    b.close()
