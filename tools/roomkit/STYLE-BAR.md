# The style bar — The Sims 4 dollhouse view

Reference screenshots: `docs/ref-sims4/*.jpg|png`. **Look at them.** This file is
a checklist derived from them, not a substitute for them.

The accuracy bar is each room's photo (`tools/roomkit/photos.json`). This is the
other half: what the room has to look like as a *dollhouse*, seen from the
`doll` / `--floor-doll` pose.

## What the Sims shots actually do

1. **Two walls, not four.** The camera-side walls are gone; only the far two
   stand, meeting in a clean corner. Our rooms cull camera-facing walls already
   (FrontSide), but with every room walled on all four sides a whole floor reads
   as a maze of white fins. Rooms need to read as *rooms*, not as partitions.
2. **Every wall is trimmed.** Baseboard at the floor, crown or a picture rail at
   the top, and the wall/floor colours are clearly different values. A bare
   flat-shaded wall meeting a bare floor is the single biggest tell.
3. **Floors are materials, not colours.** Plank direction, tile grid, carpet
   nap — visible at dollhouse distance. Neighbouring rooms differ.
4. **Furniture is chunky and legible from above.** Silhouettes read at 50°:
   a fridge is a fridge from the top corner. Thin, spindly, or under-scaled
   pieces vanish. Better slightly over-scaled than under.
5. **Colour is committed.** Saturated accents (rugs, art, bedding, cabinet
   fronts) against neutral shells. Our all-beige default reads as unfinished.
6. **Contact shadow under everything.** The app renders no shadows for generated
   geometry, so pieces float. A dark soft decal under each piece's footprint is
   what sells the weight — see the master bedroom's Rug piece, which bakes the
   bed's contact shadow into the floor.
7. **Ceilings exist but do not block the shot.** In the Sims view you see down
   into the room. Our ceiling pieces must be wound to face INTO the room so they
   are solid at eye level and invisible from above — check with the `plan` pose:
   you must still see the floor.
8. **Clean neutral backdrop.** Ours is the app's single-floor studio gradient,
   which is already right. Do not fight it.

## How to shoot the dollhouse comparison

```
cd "C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY="../backend/.venv/Scripts/python.exe"
$PY -m roomkit.rooms --floor-doll 1                    # whole first floor
$PY -m roomkit.rooms 6 --poses-only                    # then take .doll
$PY -m roomkit.shot --pose-json '<that pose>' --level 1 --day --out shot.png
```

## The question the critic answers

Put our dollhouse render beside a Sims shot, labels stripped, and answer one
binary: **which of these two reads as a finished dollhouse room?** Then name the
single biggest reason. Not a score. Not a list. One winner, one gap.
