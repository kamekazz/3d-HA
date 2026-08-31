p = 'preview_g1.py'
s = open(p, encoding='utf-8').read()
old = '''with open(os.path.join(OUT, "preview_g1_caption.txt"), "w") as f:
    f.write("preview_g1.png -- one row per machine, each panel drawn at the\\n"
            "real-world aspect of the quad it maps onto (ASPECT in art_g1).\\n"
            "Row order: Marvel Super Heroes / TMNT Turtles in Time /\\n"
            "Time Crisis / Pac-Man.\\n\\n")
    for r in rows:
        for k in r:
            m, sd, d1, dt = stats[k]
            f.write("%-38s A=%.2f  mean %6.1f  sd %5.1f  |d1| %5.2f  "
                    "(%.1fs)\\n" % (k, G.ASPECT[k], m, sd, d1, dt))
        f.write("\\n")'''
assert old in s
new = '''from captions import CAPTIONS                                   # noqa: E402
CAP = dict(CAPTIONS)
with open(os.path.join(OUT, "preview_g1_caption.txt"), "w") as f:
    f.write("preview_g1.png -- one row per machine, each panel drawn at the\\n"
            "real-world aspect of the quad it maps onto (ASPECT in art_g1),\\n"
            "which is how it will look once mapped.  preview_g1_tiles.png is\\n"
            "the same panels as authored square atlas tiles.\\n"
            "Row order: Marvel Super Heroes / TMNT Turtles in Time /\\n"
            "Time Crisis / Pac-Man.  Left to right within a row as listed.\\n\\n")
    for r in rows:
        for k in r:
            m, sd, d1, dt = stats[k]
            f.write("%s\\n    A=%.2f  mean %.1f  sd %.1f  |d1| %.2f  "
                    "(%.1fs)\\n    %s\\n" % (k, G.ASPECT[k], m, sd, d1, dt,
                                            CAP.get(k, "")))
        f.write("\\n")'''
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
print("patched")
