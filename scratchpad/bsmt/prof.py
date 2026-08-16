import sys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im).astype(np.float32) @ np.array([0.2126,0.7152,0.0722],dtype=np.float32)
x0,x1 = int(sys.argv[2]), int(sys.argv[3])
step = int(sys.argv[4]) if len(sys.argv)>4 else 25
for y in range(0, a.shape[0]-step, step):
    p = a[y:y+step, x0:x1]
    print("y=%4d n=%-6d mean=%6.1f sd=%5.1f" % (y, p.size, p.mean(), p.std()))
