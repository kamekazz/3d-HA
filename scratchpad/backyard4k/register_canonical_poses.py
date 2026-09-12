"""Collect reviewed real-app poses; never promote camera-fit experiments."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
read=lambda name:json.loads((p/name).read_text(encoding='utf-8-sig'))
poses={}
for file,keys in [('elevation_poses.json',['photo09']),
                  ('deck_layout_poses.json',['photo14','photo02']),
                  ('lake_r2_poses.json',['photo11','photo12']),
                  ('site_poses.json',['rear_site','lawn_spacing'])]:
 d=read(file)
 for key in keys:poses[key]=d[key]
(p/'canonical_poses.json').write_text(json.dumps(poses,indent=2))
