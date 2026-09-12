"""Rear-only worn composite: broken chalk wear, scanned scuffs and fine pits.

Source: Poly Haven Wood Planks Grey, CC0; no house photograph is used as albedo.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'frontend/textures/backyard'
source = np.asarray(Image.open(ROOT / 'scratchpad/backyard4k/deck-material-source/albedo.jpg').convert('RGB'), dtype=float)
luma = source @ np.array([.2126, .7152, .0722])
h, w = luma.shape
rng = np.random.default_rng(61514)
fx, fy = np.fft.fftfreq(w)*w, np.fft.fftfreq(h)*h

def lowpass(a, nx, ny):
    kernel = np.exp(-.5*((fx[None,:]/nx)**2+(fy[:,None]/ny)**2))
    return np.fft.ifft2(np.fft.fft2(a)*kernel).real

def field(nx, ny):
    a = lowpass(rng.normal(size=(h,w)), nx, ny)
    return (a-a.mean()) / a.std()

# Thresholded multiscale fields make broken abrasion patches with granular
# edges, rather than the smooth low-frequency cloud field of round five.
chalk_shape = field(24,38)*.72 + field(90,110)*.30 + field(180,220)*.10
chalk = np.clip((chalk_shape-.17)*2.0, 0, 1)
dark_shape = field(33,43)*.8 + field(110,150)*.20
pits = np.clip((dark_shape-.84)*2.1, 0, 1)
patch = np.clip((field(14,23)+.10)*.50, .04, .85)
detail = luma-lowpass(luma, 30, 40)
grain = (luma-lowpass(luma, 7, 11))*(.09+.28*patch)
t = 86.0 + 1.3*field(8,12) + 1.3*field(50,85)
t += 12.5*chalk - 10*pits + grain + .49*detail

# Grit is a clustered population of individually resolved chips and pits.
# All fields wrap along a board; no horizontal atlas join is introduced.
flecks = np.zeros((h,w), dtype=np.float32)
for _ in range(10500):
    x,y = rng.integers(0,w),rng.integers(0,h)
    length = int(rng.choice([1,1,2,3,4,7,12]))
    width = int(rng.choice([1,1,1,2,3]))
    value = rng.uniform(5,23)*rng.choice([-1,1],p=[.43,.57])
    for j in range(length):
        for i in range(width):
            flecks[(y+j)%h,(x+i)%w] += value*(1-.30*j/length)
t += flecks + rng.normal(0,1.5,(h,w))
t = np.clip(t,34,148)
rgb = np.stack([t-.8,t,t+1.1],axis=2).astype('uint8')
Image.fromarray(rgb).save(OUT/'deck-grain-albedo.webp',quality=88,method=6)

# A subtle matching micro-relief avoids laying the original scan's long
# fibres over the new wear. This is surface relief, never baked lighting.
height = lowpass(t,140,180)
gx = (np.roll(height,-1,1)-np.roll(height,1,1))*.025
gy = (np.roll(height,-1,0)-np.roll(height,1,0))*.025
normal = np.stack([-gx,gy,np.ones_like(gx)],axis=2)
normal /= np.linalg.norm(normal,axis=2,keepdims=True)
normal = ((normal*.5+.5)*255).clip(0,255).astype('uint8')
Image.fromarray(normal).resize((512,512),Image.Resampling.LANCZOS).save(OUT/'deck-wood-normal.webp',quality=80,method=6)
rough = (231 + 13*chalk - 6*patch + 3*pits).clip(205,250).astype('uint8')
Image.fromarray(rough).resize((512,512),Image.Resampling.LANCZOS).save(OUT/'deck-roughness.webp',quality=85,method=6)
total = 0
for name in ['deck-grain-albedo.webp','deck-wood-normal.webp','deck-roughness.webp']:
    size=(OUT/name).stat().st_size
    print(name,size)
    total += size
print('total bytes', total)
assert total <= 300_000, total
