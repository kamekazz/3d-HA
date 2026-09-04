import json, urllib.request, sys
BASE='http://127.0.0.1:5000'
def req(m,p,b=None):
    r=urllib.request.Request(BASE+p,data=(json.dumps(b).encode() if b is not None else None),
                             method=m,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as f: return f.status, json.loads(f.read().decode() or '{}')
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:150]
D='shade|lens|glass'
dome=lambda i,r:{'color':'#ffc48f','glow_part':D,'intensity':i,'offset_y':0.15,'range':r}
NS={'color':'#ffb877','glow_part':'lamp_shade','intensity':2.2,'offset_y':2.9,'range':5.5}
S='pair_tmp.json'
DOWN={
 13:[(369,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':1.25,'offset_y':0.15,'range':14}}),
     (235,{'light_cfg':{'color':'#ffc48f','glow_part':'gshade|gbulb','intensity':0.9,'offset_y':2.95,'range':11}})],
 14:[(13,{'light_cfg':{'offset_y':-0.4}}),
     (203,{'entity_id':'light.rosemary_bedside_light','light_cfg':{'offset_y':1.4}}),
     (356,{'entity_id':'','light_cfg':None}),(14,{'entity_id':'','light_cfg':None})],
 16:[(155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':1.5,'offset_y':6.2,'range':18}})],
 17:[(370,{'light_cfg':dome(1.15,15)}),(371,{'light_cfg':dome(1.15,15)})],
 27:[(390,{'x':3.6,'light_cfg':dome(1.15,14)})],
}
UP={
 13:[(369,{'light_cfg':{'color':'#ffc48f','glow_part':D,'intensity':3.2,'offset_y':0.15,'range':9.5}}),
     (235,{'light_cfg':{'color':'#ffb877','glow_part':'gshade|gbulb','intensity':3.2,'offset_y':2.95,'range':4.5}})],
 14:[(13,{'light_cfg':{'color':'#ffb466','glow_part':'fan_glass|fan_drum','intensity':1.8,'offset_y':-0.4,'range':13}}),
     (203,{'entity_id':'','light_cfg':None}),
     (356,{'entity_id':'light.rosemary_bedside_light','light_cfg':NS}),
     (14,{'entity_id':'light.edwin_bedside_light','light_cfg':NS})],
 16:[(155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':2.6,'offset_y':6.2,'range':12}})],
 17:[(370,{'light_cfg':dome(2.8,10)}),(371,{'light_cfg':dome(2.8,10)})],
 27:[(390,{'x':6.8,'light_cfg':dome(2.2,11)})],
}
EXTRA={17:(17,{'model_id':324,'name':'Hall2F Dome Mid','x':5.40,'y':7.54,'z':8.40,'rot_y':0,'scale':1.0,
               'entity_id':'light.2nd_floor_2nd_floor_hallway','light_cfg':dome(1.15,15)}),
       27:(27,{'model_id':324,'name':'Closet Dome East','x':10.0,'y':7.54,'z':2.20,'rot_y':0,'scale':1.0,
               'entity_id':'light.rosemarys_closet','light_cfg':dome(1.15,14)})}
mode, room = sys.argv[1], int(sys.argv[2])
if mode == 'down':
    for oid,b in DOWN[room]: print('P',oid,*req('PATCH','/api/house/object/%d'%oid,b))
    tmp = json.load(open(S)) if __import__('os').path.exists(S) else {}
    if room in EXTRA:
        rid, body = EXTRA[room]
        s,r = req('POST','/api/house/room/%d/object'%rid, body); print('POST',s,r)
        tmp[str(room)] = r.get('id'); json.dump(tmp, open(S,'w'))
else:
    import os
    tmp = json.load(open(S)) if os.path.exists(S) else {}
    if tmp.get(str(room)): print('D',*req('DELETE','/api/house/object/%d'%tmp[str(room)]))
    for oid,b in UP[room]: print('P',oid,*req('PATCH','/api/house/object/%d'%oid,b))
