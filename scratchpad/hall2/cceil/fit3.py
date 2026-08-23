import math
exec(open('cceil/proj.py').read().split('CANS =')[0])
def solve(o_stairs, o_runner, label):
    best=None
    for xi in range(300,1200):
        x=xi/100.0
        for zi in range(200,1600):
            z=zi/100.0
            t=0.0; ok=True
            for pose,o in (("p_stairs",o_stairs),("p_runner",o_runner)):
                r=project(POSES[pose], AX+x, BASE+8.0, AZ+z)
                if r is None: ok=False; break
                t+=(r[0]-o[0])**2+(r[1]-o[1])**2
            if ok and (best is None or t<best[0]): best=(t,x,z)
    t,x,z=best
    print('%s  x=%.2f z=%.2f  rms=%.1f px'%(label,x,z,math.sqrt(t/2)))
    for pose,o in (("p_stairs",o_stairs),("p_runner",o_runner)):
        r=project(POSES[pose], AX+x, BASE+8.0, AZ+z)
        print('    %s pred %.1f,%.1f  obs %.1f,%.1f'%(pose,r[0],r[1],o[0],o[1]))
    return x,z
solve((225.5,130.2),(240.2,50.7),'WEST can')
solve((345.5,132.5),(124.7,50.7),'EAST can')
