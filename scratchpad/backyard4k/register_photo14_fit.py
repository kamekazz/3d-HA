import json
from pathlib import Path
p=Path(__file__).resolve().parent
f=p/'deck_layout_poses.json'
poses=json.loads(f.read_text(encoding='utf-8-sig'))
(p/'deck_layout_poses_before_photo14_fit.json').write_text(json.dumps(poses,indent=2))
candidate=json.loads((p/'photo14-fit-poses.json').read_text())['photo14_fit']
candidate['size']=[3840,2880]
poses['photo14']=candidate
f.write_text(json.dumps(poses,indent=2))
