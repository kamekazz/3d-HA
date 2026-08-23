"""Drop the pieces the v3 photos contradict.

Room 7 was furnished with NO interior photograph (rooms/7.json's own _evidence
says so): a car in the bay, a workbench, a water heater, a chest freezer, a
mower, wheelie bins, a bike, a ladder, tote storage and painted floor bay
markings were all inferred from "normal construction sense".  All six v3 photos
show an EMPTY bay over black interlocking rubber coin tile, grey metal cabinets
where the workbench was, and nothing at all where the east-wall blobs were read
as a water heater and bins.  These are replaced, not merely removed.
"""
from gk import drop

GONE = [
    "Garage Car",            # bay is empty in photos 1,2,3,4,5
    "Garage Workbench",      # -> Garage Cabinets (grey metal, photos 1,2,4,5)
    "Garage Cabinets Tall",  # -> Garage Cabinets
    "Garage Shelving",       # -> the wire shelf in Garage Brooms
    "Garage Water Heater",   # not in any photo
    "Garage Freezer",        # not in any photo
    "Garage Mower",          # not in any photo
    "Garage Bins",           # not in any photo
    "Garage Bike",           # not in any photo
    "Garage Ladder",         # not in any photo
    "Garage Bay Storage",    # not in any photo
    "Garage Floor Marks",    # painted concrete; the real floor is rubber tile
    "Garage Step",           # -> Garage Steps (two treads + rails, photo 6)
    "Garage Opener",         # -> merged into Garage Ceiling so it fades with it
]

if __name__ == "__main__":
    for n in GONE:
        drop(n)
