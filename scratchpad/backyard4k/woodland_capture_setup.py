from pathlib import Path
p=Path('scratchpad/backyard4k/workflow_capture.cjs');s=p.read_text();s=s.replace('frontSum},frontItems};',"frontSum},frontItems,rearTrees:env.getYardItems().filter(i=>i.label==='Rear mature broadleaf').map(i=>({key:i.key,pivot:i.pivot}))};")
Path('scratchpad/backyard4k/workflow_capture_woodland.cjs').write_text(s)
