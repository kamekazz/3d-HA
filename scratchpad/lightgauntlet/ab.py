import json, urllib.request, sys
BASE='http://127.0.0.1:5000'
def req(m,p,b=None):
    r=urllib.request.Request(BASE+p,data=(json.dumps(b).encode() if b is not None else None),
                             method=m,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as f: return f.status, json.loads(f.read().decode() or '{}')
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:150]
D='shade|lens|glass'
R1_DOME=lambda i,r:{'color':'#ffc48f','glow_part':D,'intensity':i,'offset_y':0.15,'range':r}
STATE='ab_temp.json'

def to_round1():
    for oid,body in [
      (369,{'light_cfg':R1_DOME(1.25,14)}),
      (235,{'light_cfg':{'color':'#ffc48f','glow_part':'gshade|gbulb','intensity':0.9,'offset_y':2.95,'range':11}}),
      (13,{'light_cfg':{'offset_y':-0.4}}),
      (203,{'entity_id':'light.rosemary_bedside_light','light_cfg':{'offset_y':1.4}}),
      (356,{'entity_id':'','light_cfg':None}),
      (14,{'entity_id':'','light_cfg':None}),
      (155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':1.5,'offset_y':6.2,'range':18}}),
      (370,{'light_cfg':R1_DOME(1.15,15)}),
      (371,{'light_cfg':R1_DOME(1.15,15)}),
      (390,{'x':3.6,'light_cfg':R1_DOME(1.15,14)}),
    ]: print('PATCH',oid,*req('PATCH','/api/house/object/%d'%oid,body))
    tmp={}
    s,r=req('POST','/api/house/room/17/object',{'model_id':324,'name':'Hall2F Dome Mid',
        'x':5.40,'y':7.54,'z':8.40,'rot_y':0,'scale':1.0,
        'entity_id':'light.2nd_floor_2nd_floor_hallway','light_cfg':R1_DOME(1.15,15)})
    print('POST hall mid',s,r); tmp['hall']=r.get('id')
    s,r=req('POST','/api/house/room/27/object',{'model_id':324,'name':'Closet Dome East',
        'x':10.0,'y':7.54,'z':2.20,'rot_y':0,'scale':1.0,
        'entity_id':'light.rosemarys_closet','light_cfg':R1_DOME(1.15,14)})
    print('POST closet east',s,r); tmp['closet']=r.get('id')
    json.dump(tmp,open(STATE,'w'))

def to_round2():
    tmp=json.load(open(STATE))
    for k,oid in tmp.items():
        if oid: print('DELETE',oid,*req('DELETE','/api/house/object/%d'%oid))
    for oid,body in [
      (369,{'light_cfg':R1_DOME(2.4,9.5)}),
      (235,{'light_cfg':{'color':'#ffb877','glow_part':'gshade|gbulb','intensity':3.2,'offset_y':2.95,'range':4.5}}),
      (13,{'light_cfg':{'color':'#ffb466','glow_part':'fan_glass|fan_drum','intensity':1.5,'offset_y':-0.4,'range':13}}),
      (203,{'entity_id':'','light_cfg':None}),
      (356,{'entity_id':'light.rosemary_bedside_light','light_cfg':{'color':'#ffb877','glow_part':'lamp_shade','intensity':1.4,'offset_y':2.9,'range':7}}),
      (14,{'entity_id':'light.edwin_bedside_light','light_cfg':{'color':'#ffb877','glow_part':'lamp_shade','intensity':1.4,'offset_y':2.9,'range':7}}),
      (155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':1.8,'offset_y':6.2,'range':12}}),
      (370,{'light_cfg':R1_DOME(2.8,10)}),
      (371,{'light_cfg':R1_DOME(2.8,10)}),
      (390,{'x':6.8,'light_cfg':R1_DOME(2.2,11)}),
    ]: print('PATCH',oid,*req('PATCH','/api/house/object/%d'%oid,body))

globals()[sys.argv[1]]()
