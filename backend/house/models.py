"""The house data model — the 3D layout HA does not store.

Linked to HA by ha_floor_id (floor), ha_area_id (room) and entity_id (placement).
"""
from dataclasses import dataclass, field


@dataclass
class DevicePlacement:
    id: int
    room_id: int
    entity_id: str
    x: float
    y: float
    z: float
    type: str  # domain: light / switch / sensor / ...


@dataclass
class Room:
    id: int
    floor_id: int
    name: str
    ha_area_id: str | None
    x: float
    z: float
    width: float
    depth: float
    height: float
    color: str
    devices: list = field(default_factory=list)


@dataclass
class Floor:
    id: int
    name: str
    level: int
    ha_floor_id: str | None
    floor_height: float
    rooms: list = field(default_factory=list)
