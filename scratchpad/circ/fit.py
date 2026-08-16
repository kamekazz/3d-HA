import math, sys
def fit(a1,v1,a2,v2,target):
    b = math.log(v2/v1)/math.log(a2/a1)
    k = v1/(a1**b)
    a = (target/k)**(1.0/b)
    return b, max(4.0, min(255.0, a))
for name,a1,v1,a2,v2,t in [
    ("17 n",180,185.1,255,241.0,160),
    ("17 w",180,177.2,255,217.9,160),
    ("17 e",180, 85.1,255,191.9,160),
    ("17 s",180, 63.9,255,168.7,160),
]:
    b,a = fit(a1,v1,a2,v2,t)
    print("%s  b=%.3f  A=%.1f  #%02x%02x%02x" % (name,b,a,round(a),round(a),round(a)))
