import json,urllib.request,sys
BASE='http://127.0.0.1:5000'
def req(m,p,b=None):
    r=urllib.request.Request(BASE+p,data=(json.dumps(b).encode() if b is not None else None),
                             method=m,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as f: return f.status,f.read().decode()[:120]
    except urllib.error.HTTPError as e: return e.code,e.read().decode()[:120]
D='shade|lens|glass'
for oid,body in [
 (369,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':2.2,'offset_y':0.15,'range':10}}),
 (235,{'light_cfg':{'color':'#ffb877','glow_part':'gshade|gbulb','intensity':3.2,'offset_y':2.95,'range':4.5}}),
 (370,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':2.8,'offset_y':0.15,'range':10}}),
 (371,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':2.8,'offset_y':0.15,'range':10}}),
]:
    print('PATCH',oid,*req('PATCH','/api/house/object/%d'%oid,body))
