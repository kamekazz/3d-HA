"""Camera-only fit to measured rear gable and slider anchor points."""
from pathlib import Path
import json
import numpy as np

world=np.array([[20.60,26.41,-24.44],[-7.28,26.41,-24.44],
 [6.66,40.59,-24.44],[16.11,11.108,-24.33],[9.58,11.108,-24.33],
 [16.11,2.74,-24.33],[9.58,2.74,-24.33]])
observed=np.array([[275,153],[410,157],[349,91],
 [294,230],[331,230],[295,274],[331,274]],float)

def project(p):
 x,y,z,yaw,pitch,roll,fov=p
 f=np.array([np.sin(yaw)*np.cos(pitch),np.sin(pitch),np.cos(yaw)*np.cos(pitch)])
 r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r);u=np.cross(r,f)
 rr=r*np.cos(roll)+u*np.sin(roll);uu=-r*np.sin(roll)+u*np.cos(roll)
 d=world-[x,y,z];depth=d@f;focal=225/np.tan(np.radians(fov)/2)
 return np.column_stack([300+focal*(d@rr)/depth,225-focal*(d@uu)/depth]),f

def residual(p):return(project(p)[0]-observed).ravel()
lo=np.array([0,3,-110,-.8,-.1,-.10,50])
hi=np.array([30,12,-50,.5,.7,.10,105])
best=None
for startZ in [-65,-80,-95]:
 p=np.array([18,5.7,startZ,-.07,.2,0,75.]);lam=.01
 for _ in range(450):
  r=residual(p)
  j=np.column_stack([(residual(p+np.eye(7)[i]*1e-5)-r)/1e-5 for i in range(7)])
  step=np.linalg.solve(j.T@j+lam*np.eye(7),-j.T@r)
  candidate=np.clip(p+step,lo,hi)
  if np.sum(residual(candidate)**2)<np.sum(r*r):p=candidate;lam=max(1e-7,lam*.5)
  else:lam=min(1e7,lam*4)
 score=float(np.mean(residual(p)**2))
 if best is None or score<best[0]:best=(score,p)
score,p=best;uv,f=project(p)
here=Path(__file__).resolve().parent
report={'parameters':p.tolist(),'rmse':score**.5,'projected':uv.tolist(),'observed':observed.tolist()}
(here/'photo09-fit-report.json').write_text(json.dumps(report,indent=2))
pose={'pos':p[:3].tolist(),'target':(p[:3]+f*50).tolist(),'roll':float(p[5]),'fov':float(p[6]),'size':[1600,1200]}
(here/'photo09-fit-poses.json').write_text(json.dumps({'photo09_fit':pose},indent=2))
print(json.dumps(report,indent=2))
