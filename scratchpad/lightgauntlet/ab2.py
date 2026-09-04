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
S='ab_temp2.json'
def down():
    for oid,b in [
      (13,{'light_cfg':{'offset_y':-0.4}}),
      (203,{'entity_id':'light.rosemary_bedside_light','light_cfg':{'offset_y':1.4}}),
      (356,{'entity_id':'','light_cfg':None}),
      (14,{'entity_id':'','light_cfg':None}),
      (155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':1.5,'offset_y':6.2,'range':18}}),
      (370,{'light_cfg':dome(1.15,15)}),(371,{'light_cfg':dome(1.15,15)}),
      (390,{'x':3.6,'light_cfg':dome(1.15,14)}),
    ]: print('P',oid,*req('PATCH','/api/house/object/%d'%oid,b))
    t={}
    s,r=req('POST','/api/house/room/17/object',{'model_id':324,'name':'Hall2F Dome Mid','x':5.40,'y':7.54,'z':8.40,'rot_y':0,'scale':1.0,'entity_id':'light.2nd_floor_2nd_floor_hallway','light_cfg':dome(1.15,15)}); print(s,r); t['h']=r.get('id')
    s,r=req('POST','/api/house/room/27/object',{'model_id':324,'name':'Closet Dome East','x':10.0,'y':7.54,'z':2.20,'rot_y':0,'scale':1.0,'entity_id':'light.rosemarys_closet','light_cfg':dome(1.15,14)}); print(s,r); t['c']=r.get('id')
    json.dump(t,open(S,'w'))
def up():
    for k,oid in json.load(open(S)).items():
        if oid: print('D',oid,*req('DELETE','/api/house/object/%d'%oid))
    NS={'color':'#ffb877','glow_part':'lamp_shade','intensity':2.2,'offset_y':2.9,'range':5.5}
    for oid,b in [
      (13,{'light_cfg':{'color':'#ffb466','glow_part':'fan_glass|fan_drum','intensity':1.8,'offset_y':-0.4,'range':13}}),
      (203,{'entity_id':'','light_cfg':None}),
      (356,{'entity_id':'light.rosemary_bedside_light','light_cfg':NS}),
      (14,{'entity_id':'light.edwin_bedside_light','light_cfg':NS}),
      (155,{'light_cfg':{'color':'#ffd7ad','glow_part':'shade','intensity':2.6,'offset_y':6.2,'range':12}}),
      (370,{'light_cfg':dome(2.8,10)}),(371,{'light_cfg':dome(2.8,10)}),
      (390,{'x':6.8,'light_cfg':dome(2.2,11)}),
    ]: print('P',oid,*req('PATCH','/api/house/object/%d'%oid,b))
globals()[sys.argv[1]]()
