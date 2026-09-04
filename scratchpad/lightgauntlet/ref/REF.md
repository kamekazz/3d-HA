# Sims 4 night-interior lighting reference set

12 genuine in-game Sims 4 screenshots (no concept art, no renders from other engines).
All were opened and visually confirmed: Sims 4, interior, night, fixture visibly on
(except the deliberate unlit references, noted below).

Luminance figures below are 0-255 on the 0.299R+0.587G+0.114B scale, measured with PIL
over the stated region. "Mean" = whole-image mean.

---

## Lamp-lit rooms

### sims4_bedroom_floorlamp_night.png  (1920x1080)
Bedroom / dressing corner at night, single torchiere floor lamp, night city through the window.
The single clearest falloff sample in the set. **Wall wash is hot and tight; the floor pool is
broad and weak.** Wall band at lamp height: 242 directly behind the shade, 180 one metre out,
99 at two metres, 25 at the far corner. Floor band directly under the lamp only reaches **66**,
and decays gently to 38 across the rest of the room — i.e. the floor never gets a bright disc,
it gets a wide low plateau. Unlit ceiling/upper-wall reference: 27. Lamp core RGB (189,190,150) —
only slightly warm, near-white. Ambient everywhere else is a desaturated brown-grey (28,24,18),
NOT blue. Whole-image mean 36; 56% of pixels below L=40.

### sims4_vanilla_maxis_night_floorlamp_panel.png  (640x270)
Cropped "Maxis Lighting" quadrant of a lighting-mod comparison — i.e. **unmodded vanilla night
lighting, labelled as such**. Same torchiere in a plain bedroom. Vanilla night ambient here is
distinctly **blue-violet** (dark pixels RGB 26,26,40) while the lamp is cool white (227,226,228).
Wall vertical profile at the lamp: 32 near the ceiling, peaks 102 at lamp-shade height, back to
24 at the skirting — the wash is a vertical band roughly the height of the fixture, not a
whole-wall lift. Useful calibration point for how *little* one lamp changes the room.

### sims4_bedroom_bedside_lamp_night.png  (1950x1050)
Gothic bedroom, one small fringed table lamp on a nightstand plus a wall sconce, windows dark.
Lamp core RGB (126,85,42) — strongly **amber/orange**, much warmer than the torchiere. The lit
zone is a ~1.5-2 tile bubble: the nightstand, the head of the bed and the wall behind it. The
foot of the bed and the opposite wall drop straight to L~30-40. Mean 42, 48% below L=40.

### sims4_bedroom_candles_night.png  (1950x1050)
Same manor, bedroom lit by a candelabra beside the bed. Candle flames themselves are
near-blown-out (core RGB 125,114,56 over a large area, p99=188) and act as **emissive props**:
the fixture reads as a bright shape, and the light it throws only really lands on the bedspread
and the nearest curtain. The far wall keeps its own dark blue wallpaper colour (27,27,21). Good
example of "the source glows more than the room does".

### sims4_bedroom_stringlights_night.png  (1920x1009)
Autumn bedroom at night lit by a string of bulbs plus jack-o'-lanterns. Many tiny emissive
sources rather than one. Each bulb is a small blown-out white dot (bright RGB 215,213,204) with
almost **no measurable wash** on the wall behind it; the pumpkins throw a small warm patch onto
the floorboards under them (an ellipse maybe 2 tiles across). Everything more than ~3 tiles from
a source sits at L=20-40. Mean 38, 51% below L=40.

### sims4_bedroom_roombox_lamp_night.jpg  (1536x1024)
Dollhouse "room box" bedroom at night (walls-down, dark lawn outside). One orange table lamp on
the sideboard, three wall sconces, one clip lamp. Darkest of the lit rooms: mean 27, **66% of
pixels below L=40**, p95 only 129. Shows the game happily leaving most of a furnished room in
near-black while the fixtures read as bright pinpoints.

### sims4_kitchen_chandelier_night.png  (1950x1050)
Kitchen at night under two candle chandeliers (ceiling fixture case). Chandelier candles are the
warmest sample in the set: core RGB (60,57,29) in the arm region, with individual flames pushing
(247,215,69) — a strong yellow. The counter directly under the fixture lifts to ~130 while the
floor tiles two tiles away sit at ~50. Mean 36, 54% below L=40. Note the **ceiling itself stays
dark** — the fixture does not light the plane it hangs from.

### sims4_dining_pendant_night.jpg  (1920x1080)
Night restaurant/dining room: pendant lamps, table candles, backlit bar shelving, neon signs.
The brightest thing in frame is the **self-illuminated bar shelf**, not anything it lights.
Brightest-pixel mean RGB (230,216,127) = warm amber. Mean 47 with 40% below L=40 — the least
dark image here, because it has many small sources rather than one. Table candles cast a visible
warm ellipse ~1 tile across on the tabletop and nothing on the floor.

## Wide / multi-room night shots

### sims4_dollhouse_multiroom_night.png  (1950x1050)
Two-panel top-down of a manor at night, ground floor and upper floor. **The single best "lit
rooms glow, unlit rooms are dark" reference.** Grid scan of the ground-floor panel: the
brightly-lit tiled bathroom runs **L=130-153**; the warm chandelier-lit dining/living half runs
**L=45-78**; unlit roof and out-of-room structure runs **L=19-33**. So one lot at one moment
spans roughly 20 -> 150, a **7x** range, and the transitions are per-room, not gradients.
Moonlit exterior stone reads cool blue (43,51,93) while every interior lit patch reads warm
yellow — the **warm-interior / cool-exterior split is the whole look**. Mean 29, 66% below L=40.

### sims4_dollhouse_onelitroom_night.png  (1950x1050)
Same manor, top-down, with essentially **one room lit and the rest of the house black**. Lit room
box L=50.4 (RGB 63,48,29); unlit roof/rooms L=30.1 (32,30,26); moonlit garden path L=53.2
(43,51,93 — blue). Ratio lit:unlit is only about **1.7:1**, yet it reads as "one room is on"
because of hue, not brightness: the lit room is orange, everything else is neutral or blue.
Darkest image in the set apart from the club: mean 22, **74% below L=40**.

### sims4_apartment_cutaway_unlit_rooms_night.png  (1920x1080)
Live gameplay, Mon 2:30 AM, walls-down apartment cutaway. Three states side by side:
**lit bathroom L=123.6** (RGB 126,127,100, near-white ceiling light), **dim occupied living/bed
area L=36.3** (38,34,42 — lit only by ambient/moonlight, cool), and **two completely unlit empty
rooms L=27.7** (33,25,28 — the bare floorboards are visible but nearly monochrome brown-black).
Lit:unlit ratio here is **4.5:1**. This is the reference for what "genuinely dark but not pure
black" looks like — an unlit room still shows its floor texture at L≈28.

## Unlit / dark reference

### sims4_unlit_dark_interior_night.png  (1920x1080)
The Lux nightclub interior at night — a large, deliberately unlit room. Mean 15, **87% of pixels
below L=40**, p5=5. Booths, tables and the floor are essentially black silhouettes. The only
bright things are the emissive objects themselves: neon signs, filament bulbs (bright-pixel mean
RGB 216,216,197) and the backlit bottle shelf, and **none of them wash the surfaces around them**
— the wall behind the neon "LUX" stays black. Best available reference for "the fixture glows,
the room does not".
