import json, urllib.request
BASE = 'http://127.0.0.1:5000'

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r) as f:
            return f.status, f.read().decode()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]

DOME = 'shade|lens|glass'
patches = [
    # --- room 13 Guest: ceiling dome tightened, bedside lamp made a tight amber bubble
    (369, {'light_cfg': {'color': '#ffc48f', 'glow_part': DOME,
                         'intensity': 1.7, 'offset_y': 0.15, 'range': 10.5}}),
    (235, {'light_cfg': {'color': '#ffb877', 'glow_part': 'gshade|gbulb',
                         'intensity': 1.5, 'offset_y': 2.95, 'range': 7}}),
    # --- room 14 Master: fan tightened + glow limited to its light kit
    (13,  {'light_cfg': {'color': '#ffb466', 'glow_part': 'fan_glass|fan_drum',
                         'intensity': 1.5, 'offset_y': -0.4, 'range': 13}}),
    # dresser lamp unbound; the binding moves to the real nightstand lamp
    (203, {'entity_id': '', 'light_cfg': None}),
    (356, {'entity_id': 'light.rosemary_bedside_light',
           'light_cfg': {'color': '#ffb877', 'glow_part': 'lamp_shade',
                         'intensity': 1.4, 'offset_y': 2.9, 'range': 7}}),
    (14,  {'entity_id': 'light.edwin_bedside_light',
           'light_cfg': {'color': '#ffb877', 'glow_part': 'lamp_shade',
                         'intensity': 1.4, 'offset_y': 2.9, 'range': 7}}),
    # --- room 16 Master Bath vanity bar
    (155, {'light_cfg': {'color': '#ffd7ad', 'glow_part': 'shade',
                         'intensity': 2.0, 'offset_y': 6.2, 'range': 10}}),
    # --- room 17 Hallway: two domes, not three
    (370, {'light_cfg': {'color': '#ffc48f', 'glow_part': DOME,
                         'intensity': 2.0, 'offset_y': 0.15, 'range': 10}}),
    (371, {'light_cfg': {'color': '#ffc48f', 'glow_part': DOME,
                         'intensity': 2.0, 'offset_y': 0.15, 'range': 10}}),
    # --- room 27 Master Closet: one dome
    (390, {'light_cfg': {'color': '#ffc48f', 'glow_part': DOME,
                         'intensity': 2.2, 'offset_y': 0.15, 'range': 10.5}}),
]
for oid, body in patches:
    print('PATCH', oid, *req('PATCH', f'/api/house/object/{oid}', body))
for oid in (392, 391):
    print('DELETE', oid, *req('DELETE', f'/api/house/object/{oid}'))
