import json, urllib.request
BASE='http://127.0.0.1:5000'
def req(m,p,b=None):
    r=urllib.request.Request(BASE+p,data=(json.dumps(b).encode() if b is not None else None),
                             method=m,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as f: return f.status,f.read().decode()[:120]
    except urllib.error.HTTPError as e: return e.code,e.read().decode()[:120]
D='shade|lens|glass'
for oid,body in [
 (369,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':1.9,'offset_y':0.15,'range':10}}),
 (235,{'light_cfg':{'color':'#ffb877','glow_part':'gshade|gbulb','intensity':2.6,'offset_y':2.95,'range':5.5}}),
 (155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':1.8,'offset_y':6.2,'range':12}}),
 (370,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':2.3,'offset_y':0.15,'range':11}}),
 (371,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':2.3,'offset_y':0.15,'range':11}}),
 (390,{'x':6.8,'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':2.2,'offset_y':0.15,'range':11}}),
]:
    print('PATCH',oid,*req('PATCH','/api/house/object/%d'%oid,body))
