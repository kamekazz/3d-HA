"""Neutralize the CC0 scan without losing its directional weathering."""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'scratchpad/backyard4k/deck-material-source/albedo.jpg'
target = ROOT / 'frontend/textures/backyard/deck-grain-albedo.webp'
a = np.asarray(Image.open(source).convert('RGB'), dtype=float)
luma = a @ np.array([.2126, .7152, .0722])
# The photograph is cool neutral composite. Keep the actual scanned fine
# texture, faint board scratches, weather stains and fasteners; remove only
# the source timber's warm cast and calibrate the average to the live shader.
t = np.clip(90 + (luma - luma.mean()) * 1.12, 15, 200)
out = np.stack([t-1, t, t+1.5], axis=2)
Image.fromarray(out.astype('uint8')).save(target, quality=86, method=6)
print(target, target.stat().st_size)
