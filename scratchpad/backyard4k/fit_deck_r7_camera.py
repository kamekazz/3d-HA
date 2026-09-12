"""Offline experimental photo14 calibration, not a canonical-pose update.

Uses actual photographic slider corners, two visible perimeter anchors, and
world-X seam convergence. No imposed physical eye height or board spacing.
"""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
world = np.array([
    [16.20, 11.28, -24.33], [9.48, 11.28, -24.33],
    [9.48, 2.20, -24.33], [16.20, 2.20, -24.33],
    [20.60, 2.744, -24.43], [3.0, 2.744, -42.20],
])
observed = np.array([
    [84., 25.], [238.5, 71.], [241.5, 200.], [127.5, 228.5],
    [55., 259.], [513., 263.],
])
labels = ['slider image top-left', 'slider image top-right',
          'slider image bottom-right', 'slider image bottom-left',
          'upper deck at house separator', 'upper north-west rail foot']
# Broad perimeter tolerance acknowledges occlusion by rail/grill and lens warp.
sigma = np.array([4., 4., 4., 4., 12., 12.])[:, None]

seams350 = np.array([260, 290, 320, 350, 380, 409, 438, 467, 495.])
seams380 = np.array([229, 264, 298, 332, 366, 399, 432, 465, 497.])
slope, offset = np.linalg.lstsq(
    np.column_stack([seams350, np.ones(len(seams350))]), seams380, rcond=None)[0]
vanishing = np.array([offset/(1-slope), 350-30/(slope-1)])

def projection(p):
    x, y, z, yaw, pitch, roll, fov = p
    forward = np.array([np.sin(yaw)*np.cos(pitch), np.sin(pitch),
                        np.cos(yaw)*np.cos(pitch)])
    right = np.cross(forward, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    r = right*np.cos(roll)+up*np.sin(roll)
    u = -right*np.sin(roll)+up*np.cos(roll)
    d = world-[x, y, z]; depth = d@forward
    focal = 225/np.tan(np.radians(fov)/2)
    uv = np.column_stack([300+focal*(d@r)/depth, 225-focal*(d@u)/depth])
    vp = np.array([300+focal*r[0]/forward[0], 225-focal*u[0]/forward[0]])
    return uv, vp, forward, depth

def residual(p):
    uv, vp, _, depth = projection(p)
    return np.r_[((uv-observed)/sigma).ravel(), (vp-vanishing)/8,
                 np.minimum(depth-.1, 0)*100]

lo = np.array([10, 2.8, -65, -2.5, -1.1, -.5, 35])
hi = np.array([45, 25, -24.5, -.25, .05, .5, 130])
initial = np.array([22, 10.0804973898, -35.5195237357,
                    -1.2745914777, -.5064758516, .2465878691, 97.46023505])
best = None
for start in [initial, np.array([22, 8, -39, -.9, -.3, 0., 86]),
              np.array([18, 6, -36, -1.2, -.4, .1, 85])]:
    p = start.copy(); lam = .01
    for _ in range(400):
        res = residual(p)
        jac = np.column_stack([(residual(p+np.eye(7)[i]*1e-5)-res)/1e-5
                               for i in range(7)])
        step = np.linalg.solve(jac.T@jac+lam*np.eye(7), -jac.T@res)
        candidate = np.clip(p+step, lo, hi)
        if np.sum(residual(candidate)**2) < np.sum(res**2):
            p = candidate; lam = max(1e-7, lam*.5)
        else:
            lam = min(1e7, lam*4)
    score = float(np.sum(residual(p)**2))
    if best is None or score < best[0]: best = (score, p)

score, p = best
uv, vp, forward, depth = projection(p)
pose = {'pos': p[:3].tolist(), 'target': (p[:3]+forward*20).tolist(),
        'fov': float(p[6]), 'roll': float(p[5]), 'size': [3840, 2880]}
report = {
    'status': 'EXPERIMENTAL; actual native capture required; not canonical',
    'reference': 'references/14.png', 'fit_parameters': p.tolist(),
    'weighted_squared_residual': score,
    'anchor_labels': labels, 'world': world.tolist(),
    'observed': observed.tolist(), 'predicted': uv.tolist(),
    'anchor_error_pixels': np.linalg.norm(uv-observed, axis=1).tolist(),
    'seam_observed_vanishing': vanishing.tolist(),
    'seam_predicted_vanishing': vp.tolist(),
    'note': 'No geometry change or imposed camera height/board width; perimeter anchors have 12px tolerance.'
}
(HERE/'deck-r7-camera-candidate.json').write_text(json.dumps({'photo14_candidate_r7': pose}, indent=2))
(HERE/'deck-r7-camera-fit-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
