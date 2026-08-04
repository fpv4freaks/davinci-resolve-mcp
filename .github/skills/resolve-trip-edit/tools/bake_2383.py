"""Bake a show look built on Resolve's real Kodak 2383 print emulation.

The hand-rolled curve was an approximation of a film print; this uses the actual
print stock response instead. Two things have to be handled:

  * 2383 expects Cineon log input, so DaVinci Intermediate is converted first.
  * 2383 outputs display-referred Rec.709, but RCM still applies its own output
    transform after this node -- so the result is converted back to DaVinci
    Intermediate, otherwise the transform is applied twice.

BLEND dials the print look against the untouched image; the earlier full-strength
version read as too yellow.
"""
import math
import os

LUT_2383 = ("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/"
            "Film Looks/Rec709 Kodak 2383 D60.cube")
OUT = "/Users/danielwojcik/vscode/davinci-resolve-mcp/tmp/WRO_Print2383.cube"
SIZE = 33

BLEND = 0.78
EXPOSURE = -0.030      # DI, pulls the print curve off its shoulder
GREEN_MID = 0.006      # extra green through the midtones
# The 2383 curve read slightly too contrasty. This softens it around the pivot by
# moving luma only and shifting all three channels equally, so the warm/cool
# separation survives untouched - scaling RGB directly would flatten it.
CONTRAST_SCALE = 0.92
# Display white is DI 0.5138. 0.492 crushed the top flat; 0.5125 let it clip.
# This sits between: speculars can still approach white, large areas cannot.
CEILING_KNEE = 0.470
CEILING_MAX = 0.5055

CINEON_OFFSET = 10.0 ** ((95.0 - 685.0) * 0.002 / 0.6)


def di2lin(y):
    if y <= 0.02740668:
        return y / 10.44426855
    return 2.0 ** (y / 0.07329248 - 7.0) - 0.0075


def lin2di(x):
    xc = max(x, -0.0074)
    if xc <= 0.00262409:
        return xc * 10.44426855
    return 0.07329248 * (math.log2(xc + 0.0075) + 7.0)


def lin2cineon(x):
    x = max(x, 0.0)
    v = x * (1.0 - CINEON_OFFSET) + CINEON_OFFSET
    return min(max((math.log10(v) * 0.6 / 0.002 + 685.0) / 1023.0, 0.0), 1.0)


def load_cube(path):
    size = None
    data = []
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        u = s.upper()
        if u.startswith("LUT_3D_SIZE"):
            size = int(s.split()[-1])
        elif u.startswith(("TITLE", "DOMAIN", "LUT_1D")):
            continue
        else:
            p = s.split()
            if len(p) == 3:
                try:
                    data.append([float(x) for x in p])
                except ValueError:
                    pass
    return size, data


def trilinear(size, data, rgb):
    def at(ri, gi, bi):
        ri = min(max(ri, 0), size - 1)
        gi = min(max(gi, 0), size - 1)
        bi = min(max(bi, 0), size - 1)
        return data[ri + gi * size + bi * size * size]

    pos = [min(max(c, 0.0), 1.0) * (size - 1) for c in rgb]
    i0 = [int(math.floor(p)) for p in pos]
    f = [p - i for p, i in zip(pos, i0)]
    out = [0.0, 0.0, 0.0]
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = ((f[0] if dr else 1 - f[0]) *
                     (f[1] if dg else 1 - f[1]) *
                     (f[2] if db else 1 - f[2]))
                if w == 0.0:
                    continue
                c = at(i0[0] + dr, i0[1] + dg, i0[2] + db)
                for k in range(3):
                    out[k] += w * c[k]
    return out


def gamma24_decode(v):
    return max(v, 0.0) ** 2.4


def ceiling_roll(d):
    if d <= CEILING_KNEE:
        return d
    r = CEILING_MAX - CEILING_KNEE
    return CEILING_KNEE + r * (1.0 - math.exp(-(d - CEILING_KNEE) / r))


def build():
    size2383, data2383 = load_cube(LUT_2383)

    def look(r, g, b):
        src = [r + EXPOSURE, g + EXPOSURE, b + EXPOSURE]
        cin = [lin2cineon(di2lin(c)) for c in src]
        disp = trilinear(size2383, data2383, cin)
        out = [lin2di(gamma24_decode(c)) for c in disp]
        out = [s + (o - s) * BLEND for s, o in zip(src, out)]
        lum = 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
        w = max(0.0, 1.0 - abs(lum - 0.336) / 0.30)
        out[1] += GREEN_MID * w

        lum = 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
        shift = (0.336 + (lum - 0.336) * CONTRAST_SCALE) - lum
        # Scaling about the pivot moves the darkest values most, which would lift
        # blacks into a haze. Taper the shift out below the toe.
        taper = min(1.0, max(0.0, (lum - 0.02) / 0.12))
        out = [c + shift * taper for c in out]

        return [min(max(ceiling_roll(c), 0.0), 1.0) for c in out]

    return look, size2383, data2383


def main():
    look, _, _ = build()
    lines = ['TITLE "WRO Day1 Print 2383"', f"LUT_3D_SIZE {SIZE}",
             "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0", ""]
    n = SIZE - 1
    for bi in range(SIZE):
        for gi in range(SIZE):
            for ri in range(SIZE):
                o = look(ri / n, gi / n, bi / n)
                lines.append(f"{o[0]:.6f} {o[1]:.6f} {o[2]:.6f}")
    with open(OUT, "w", encoding="ascii") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {OUT} ({SIZE}^3)")

    print("\nNEUTRAL RAMP (DI in -> DI out)")
    print(f"{'in':>6} {'R':>7} {'G':>7} {'B':>7} {'R-B':>8} {'G-RB':>8}")
    for v in (0.05, 0.12, 0.20, 0.28, 0.336, 0.40, 0.45, 0.50, 0.60, 0.80):
        o = look(v, v, v)
        print(f"{v:>6.3f} {o[0]:>7.4f} {o[1]:>7.4f} {o[2]:>7.4f} "
              f"{o[0] - o[2]:>+8.4f} {o[1] - (o[0] + o[2]) / 2:>+8.4f}")

    mx = 0.0
    for r in range(0, 17):
        for g in range(0, 17):
            for b in range(0, 17):
                mx = max(mx, max(look(r / 16, g / 16, b / 16)))
    print(f"\nmax output over cube: {mx:.4f} -> "
          f"{'SAFE' if mx < 0.5135 else 'WILL CLIP'} (display white = DI 0.5138)")

    lo, hi = look(0.50, 0.50, 0.50), look(0.80, 0.80, 0.80)
    print(f"highlight separation DI 0.50->0.80: {sum(hi) / 3 - sum(lo) / 3:.4f} "
          f"(was 0.024 with the old ceiling)")


if __name__ == "__main__":
    main()
