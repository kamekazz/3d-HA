"""What each panel in preview_g1.png is, in reading order."""

CAPTIONS = [
    ("marvel-super-heroes.marquee",
     "Painted character art full-bleed on near-black, rim-lit figures behind "
     "a scrim; MARVEL in white toward the left with SUPER HEROES under it. "
     "Authored DIM (mean 53) because it reads unlit in every photograph."),
    ("marvel-super-heroes.riser",
     "The separate printed riser strip below the front panel: MARVEL SUPER "
     "HEROES white over a blue/green character scene."),
    ("marvel-super-heroes.front",
     "The most typographic panel in the room: white block + CAPCOM, MARVEL, "
     "SUPER HEROES, a blue title lockup, a line of fine legal type, and the "
     "row of small warm-toned character heads. Gold T-molding both edges."),
    ("marvel-super-heroes.deck",
     "Two-player deck. GROUND ONLY -- no control layout resolves in any "
     "photograph, so none is invented: printed teal comic wash, two darker "
     "player fields, gold hairline."),
    ("marvel-super-heroes.side",
     "Comic-collage wrap: fourteen irregular panels with black gutters in "
     "teal/blue-green (bursts, halftone, silhouettes, balloons, skyline), "
     "gold T-molding on every edge."),

    ("tmnt-turtles-in-time.marquee",
     "April in the yellow jumpsuit against the brick alley at the left, the "
     "arched TEENAGE MUTANT NINJA / TURTLES lockup, then the four turtles "
     "and a Foot soldier across a New York street with shopfronts and a "
     "manhole."),
    ("tmnt-turtles-in-time.riser",
     "One turtle in green and grey over brown brick -- figure-led, where the "
     "deck is brick-led."),
    ("tmnt-turtles-in-time.front",
     "Black, the arched TURTLES logo, TURTLES IN TIME arched in blue-white "
     "beneath it, KONAMI in red, green T-molding down both edges."),
    ("tmnt-turtles-in-time.deck",
     "Four-player deck: brick street, fire escapes, a manhole, the TURTLES "
     "wordmark three times at three sizes and colours, four character-"
     "portrait decals, green edge."),
    ("tmnt-turtles-in-time.side",
     "Black flank, a dim turtle head and a low city silhouette, and the "
     "bright grass-green T-molding that makes the machine read across the "
     "room."),

    ("time-crisis.marquee",
     "Pale gold ground; TIME small on the upper line with its swash, CRISIS "
     "large beneath, both raked right in blue block italic with a heavy "
     "white outline and a drop shadow."),
    ("time-crisis.speaker",
     "The head below the marquee: deep maroon band over a tan-gold panel "
     "pierced by two round black speaker holes set wide apart."),
    ("time-crisis.front",
     "Black lower panel: two red pillars, a coin-door recess between them, "
     "the small white-and-blue italic lockup at 60% height, a pale coin "
     "plate at the bottom."),
    ("time-crisis.deck",
     "Red/orange deck with two pale blue-and-white instruction placards "
     "either side of the darker gun cradle; gold trim front and back."),
    ("time-crisis.side",
     "Red/maroon flank, pale head shroud across the top, tan-gold trim on "
     "the front edge. DECLARED: no figurative art resolves on this "
     "machine's flanks at any magnification, so none is invented."),

    ("pac-man.marquee",
     "Cream ground in a thin dark frame inside a maroon band; PAC | MAN in "
     "fat rounded yellow bubble caps with a heavy black outline, arched, "
     "with the blue ghost, Pac-Man and the dot trail between the words."),
    ("pac-man.front",
     "Yellow full height: the tall black coin-door plate with two slots and "
     "a silver return, the blue ghost, Pac-Man, and the blue maze elbows "
     "across the very bottom."),
    ("pac-man.deck",
     "Black deck with a maroon lip and a yellow keyline along the front "
     "edge. DECLARED: the joystick and buttons are geometry and the printed "
     "deck really is plain black, so this carries no game identity."),
    ("pac-man.side",
     "Plain school-bus yellow with maroon T-molding on every exposed edge. "
     "DECLARED: no large graphic appears on the sides in any view."),
]

if __name__ == "__main__":
    for k, v in CAPTIONS:
        print("%s\n    %s\n" % (k, v))
