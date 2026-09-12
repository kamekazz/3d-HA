"""Camera calibration from the four measured rear slider corners.

Reference points are manually measured on photo14; this fits camera pose only.
It does not change model geometry, lighting or reference image pixels.
"""
import json
from pathlib import Path
import numpy as np

# Image-left corresponds to the higher world-X jamb in this northeast view.
world=np.array([[16.20,11.28,-24.33],[9.48,11.28,-24.33],
                [9.48,2.20,-24.33],[16.20,2.20,-24.33]])
observed=np.array([[84.,25.],[238.5,71.],[241.5,200.],[127.5,228.5]])

def project(p):
    x,y,z,yaw,pitch,roll,fov=p
    forward=np.array([np.sin(yaw)*np.cos(pitch),np.sin(pitch),np.cos(yaw)*np.cos(pitch)])
    right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    r=right*np.cos(roll)+up*np.sin(roll)
    u=-right*np.sin(roll)+up*np.cos(roll)
    d=world-[x,y,z];depth=d@forward
    focal=225/np.tan(np.radians(fov)/2)
    return np.column_stack([300+focal*(d@r)/depth,225-focal*(d@u)/depth]),forward

def residual(p):
    uv,_=project(p)
    return (uv-observed).ravel()

p=np.array([25.,8.0,-33.,-.9,-.35,0.,85.])
lo=np.array([22,6,-46,-1.5,-.8,-.3,50])
hi=np.array([36,12,-28,-.2,.1,.3,110])
lam=.01
for _ in range(500):
    r=residual(p)
    j=np.column_stack([(residual(p+np.eye(7)[i]*1e-5)-r)/1e-5 for i in range(7)])
    step=np.linalg.solve(j.T@j+lam*np.eye(7),-j.T@r)
    candidate=np.clip(p+step,lo,hi)
    if np.sum(residual(candidate)**2)<np.sum(r*r):
        p=candidate;lam=max(1e-7,lam*.5)
    else:lam=min(1e7,lam*4)

uv,forward=project(p)
result={'fit_parameters':p.tolist(),'predicted_corners':uv.tolist(),
        'reference_corners':observed.tolist(),'pixel_rmse':float(np.sqrt(np.mean((uv-observed)**2))),
        'note':'Pose candidate from measured slider corners; actual app render still required.'}
here=Path(__file__).resolve().parent
(here/'photo14-fit-report.json').write_text(json.dumps(result,indent=2))
pose={'pos':p[:3].tolist(),'target':(p[:3]+forward*20).tolist(),'fov':float(p[6]),'roll':float(p[5]),'size':[1600,1200]}
(here/'photo14-fit-poses.json').write_text(json.dumps({'photo14_fit':pose},indent=2))
print(json.dumps(result,indent=2))
