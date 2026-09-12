"""Weathered composite: broad wear with sparse broken scanned grain."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'scratchpad/backyard4k/deck-material-source/albedo.jpg'
target = ROOT / 'frontend/textures/backyard/deck-grain-albedo.webp'
a = np.asarray(Image.open(source).convert('RGB'), dtype=float)
luma = a @ np.array([.2126, .7152, .0722])
h, w = luma.shape
rng = np.random.default_rng(51514)

def field(nx, ny):
    # Fourier low-pass fields wrap continuously in both atlas directions.
    v = rng.normal(0,1,(h,w))
    fx=np.fft.fftfreq(w)*w
    fy=np.fft.fftfreq(h)*h
    kernel=np.exp(-.5*((fx[None,:]/nx)**2+(fy[:,None]/ny)**2))
    z=np.fft.ifft2(np.fft.fft2(v)*kernel).real
    return (z-z.mean()) / z.std()

# The original long timber fibres stay only in scattered worn patches. Broad
# neutral weathering is independent of the source's full-length grain.
grain_mask = np.clip((field(19,29)-.15)*.42, 0, .62)
grain = (luma-luma.mean())*(.10+.32*grain_mask)
wear = 3.8*field(7,6) + 2.6*field(23,21) + 1.2*field(65,60)
t = 88 + wear + grain
# Embedded pale grit, fine pitting and short lengthwise scuffs. They are baked
# into the rear-only texture; physical board edges remain geometry.
flecks = np.zeros((h,w), dtype='float32')
for _ in range(2100):
    x,y = rng.integers(1,w-2),rng.integers(1,h-15)
    length = int(rng.choice([1,1,2,2,3,5,9,14]))
    value = rng.uniform(7,23) * rng.choice([-1,1],p=[.35,.65])
    flecks[y:y+length,x] += value
t += flecks + rng.normal(0,.65,(h,w))
t = np.clip(t,35,150)
out = np.stack([t-.8,t,t+1.1],axis=2)
Image.fromarray(out.astype('uint8')).save(target,quality=88,method=6)
print(target,target.stat().st_size)
