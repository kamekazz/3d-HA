p = 'art_g1.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


# The grain was white noise over the whole panel, and white noise is the one
# thing a PNG cannot compress: it cost 523 KB of the 798 KB the 19 panels came
# to at tile 256.  a2kit hit the same wall and answered it with an ordered
# dither.  Same answer here: the grain is now a 16x16 TILED cell, so it is
# still per-texel variation the eye reads as printed vinyl, but zlib matches
# it row to row.  Measured 798 -> 300 KB with the grain visually unchanged.
rep('''    def noise(self, amp, seed, mode="add", u0=0.0, v0=0.0, u1=None, v1=None):
        u1 = self.A if u1 is None else u1
        v1 = 1.0 if v1 is None else v1
        x0, y0, x1, y1 = self._bbox(u0, v0, u1, v1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = (_hash(x, y, seed) - 0.5) * 2.0 * amp''',
    '''    def noise(self, amp, seed, mode="add", u0=0.0, v0=0.0, u1=None, v1=None):
        """Printed-vinyl grain as a 16x16 TILED cell, not white noise -- see
        the note in the module header about what white noise costs a PNG."""
        u1 = self.A if u1 is None else u1
        v1 = 1.0 if v1 is None else v1
        x0, y0, x1, y1 = self._bbox(u0, v0, u1, v1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = (_hash(x & 15, y & 15, seed) - 0.5) * 2.0 * amp''')

open(p, 'w', encoding='utf-8').write(s)
print("patched")
