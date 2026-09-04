import json
from api import add, patch

DOME, PEND, VBAR, STRIP = 324, 325, 326, 327
G = "shade|lens|glass"

JOBS = [
    # room, model, name, x, y, z, rot, entity, cfg
    (5, DOME, "Living Dome NW",  5.5, 8.03,  4.5, 0, "light.living_room_livingroom",
        dict(color="#ffb877", intensity=1.9, offset_y=0.2, range=14, glow_part=G)),
    (5, DOME, "Living Dome NE", 15.0, 8.03,  4.5, 0, "light.living_room_livingroom",
        dict(color="#ffb877", intensity=1.9, offset_y=0.2, range=14, glow_part=G)),
    (5, DOME, "Living Dome SW",  5.5, 8.03, 12.5, 0, "light.living_room_livingroom",
        dict(color="#ffb877", intensity=1.9, offset_y=0.2, range=14, glow_part=G)),
    (5, DOME, "Living Dome SE", 15.0, 8.03, 12.5, 0, "light.living_room_livingroom",
        dict(color="#ffb877", intensity=1.9, offset_y=0.2, range=14, glow_part=G)),

    (6, PEND, "Kitchen Pendant North", 7.20, 6.32, 6.30, 0, "switch.kitchen",
        dict(color="#ffc48f", intensity=1.5, offset_y=0.35, range=12, glow_part=G)),
    (6, PEND, "Kitchen Pendant South", 7.20, 6.32, 9.70, 0, "switch.kitchen",
        dict(color="#ffc48f", intensity=1.5, offset_y=0.35, range=12, glow_part=G)),
    (6, DOME, "Kitchen Dome North", 11.00, 8.07, 3.50, 0, "switch.kitchen",
        dict(color="#ffc48f", intensity=1.3, offset_y=0.2, range=12, glow_part=G)),
    (6, DOME, "Kitchen Dome South",  4.20, 8.07, 13.50, 0, "switch.kitchen",
        dict(color="#ffc48f", intensity=1.3, offset_y=0.2, range=12, glow_part=G)),

    (7, STRIP, "Garage Strip NW",  6.0, 6.72,  6.0, 0, "light.garage",
        dict(color="#ffe6c8", intensity=1.6, offset_y=0.15, range=14, glow_part=G)),
    (7, STRIP, "Garage Strip NE", 14.5, 6.72,  6.0, 0, "light.garage",
        dict(color="#ffe6c8", intensity=1.6, offset_y=0.15, range=14, glow_part=G)),
    (7, STRIP, "Garage Strip SW",  6.0, 6.72, 16.0, 0, "light.garage",
        dict(color="#ffe6c8", intensity=1.6, offset_y=0.15, range=14, glow_part=G)),
    (7, STRIP, "Garage Strip SE", 14.5, 6.72, 16.0, 0, "light.garage",
        dict(color="#ffe6c8", intensity=1.6, offset_y=0.15, range=14, glow_part=G)),

    (8, DOME, "Office Dome North", 5.30, 8.09, 3.80, 0, "light.work_office_desk",
        dict(color="#ffc48f", intensity=1.4, offset_y=0.2, range=12, glow_part=G)),
    (8, DOME, "Office Dome South", 5.30, 8.09, 8.60, 0, "light.work_office_desk",
        dict(color="#ffc48f", intensity=1.4, offset_y=0.2, range=12, glow_part=G)),

    (9, DOME, "Laundry Dome", 2.20, 8.09, 3.20, 0, "switch.laundry_room",
        dict(color="#ffd7ad", intensity=1.0, offset_y=0.2, range=9, glow_part=G)),
    (10, DOME, "Pantry Dome", 1.55, 8.09, 2.85, 0, "switch.pantry",
        dict(color="#ffd7ad", intensity=0.9, offset_y=0.2, range=8, glow_part=G)),
    (22, DOME, "Printers Dome", 3.10, 7.09, 2.90, 0, "switch.office_closet",
        dict(color="#ffd7ad", intensity=0.9, offset_y=0.2, range=8, glow_part=G)),
]

if __name__ == "__main__":
    for room, model, name, x, y, z, rot, ent, cfg in JOBS:
        r = add(room, model_id=model, name=name, x=x, y=y, z=z, rot_y=rot, scale=1.0)
        oid = r["id"]
        patch(oid, entity_id=ent, light_cfg=cfg)
        print(room, oid, name, ent)
