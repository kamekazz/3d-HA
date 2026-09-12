from pathlib import Path
from PIL import Image
import numpy as np
import json

root=Path(__file__).parent
out=root/'renders/ground-r10'
photo=out/'photo12.png'
im=Image.open(photo)
im.resize((1200,900),Image.Resampling.LANCZOS).save(out/'photo12-preview.jpg')
im.crop((1000,2000,2100,2800)).save(out/'photo12-native-grass.png')
result={}
for label,path in [('reference',root/'references/12.png'),('candidate',photo)]:
    image=Image.open(path).convert('RGB').resize((600,450),Image.Resampling.LANCZOS)
    roi=image.crop((60,300,540,450))
    roi.resize((960,300)).save(out/(label+'-focus.png'))
    a=np.asarray(roi,dtype=float)
    luma=a@np.array([.2126,.7152,.0722])
    green=(a[:,:,1]>a[:,:,0]+2)&(a[:,:,1]>a[:,:,2]+3)
    result[label]={'mean':a.mean((0,1)).tolist(),
        'gradient':[float(np.abs(np.diff(luma,axis=1)).mean()),float(np.abs(np.diff(luma,axis=0)).mean())],
        'p10_50_90':np.percentile(luma,[10,50,90]).tolist(),
        'green_mean':a[green].mean(0).tolist()}
(out/'metrics.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
