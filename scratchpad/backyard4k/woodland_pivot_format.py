from pathlib import Path
import json,re
p=Path('frontend/js/environment.js');s=p.read_text(); pivots=json.loads(Path('scratchpad/backyard4k/rear-tree-pivots-r3.json').read_text());
txt='  // These measured R3 pivots are the saved Outside-editor identities. Crown\n  // growth must not move their keys or the centers of existing transforms.\n  const rearTreePivots=[\n'+''.join('    '+json.dumps(i['pivot'])+',\n' for i in pivots)+'  ];'
s=re.sub(r'  const rearTreePivots=\[.*?\];',lambda m:txt,s,count=1)
p.write_text(s)
