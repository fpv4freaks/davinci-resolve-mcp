"""Bake Option 2 - a clean digital-cinema look profiled from Captain Marvel.

Measured against the reference's DAYLIGHT frames only (its overall darkness is
content - space and night interiors - not look). At matched brightness the
reference differs from our 2383 print look in four specific ways:

    metric        reference   option 1
    p5 luma          0.042      0.017     lifted, milky toe (not crushed)
    p75 luma         0.429      0.480     upper mids held back
    p99.9 luma       0.996      0.936     speculars punch to white
    R-G @ mid       +0.032     +0.063     half the warm cast
    sat @ mid        0.244      0.332     markedly less saturated

So: same print machinery, but blended back, with the highlight ceiling released,
a lifted toe, and chroma pulled down. GREEN_MID is dropped - the reference has no
green push.
"""
import math
import os

LUT_2383 = ("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/"
            "Film Looks/Rec709 Kodak 2383 D60.cube")
VERSION = os.environ.get("V", "v1")
OUT = f"/Users/danielwojcik/vscode/davinci-resolve-mcp/tmp/WRO_Hollywood_{VERSION}.cube"
SIZE = 33

BLEND = float(os.environ.get("BLEND", 0.42))        # 0.78 in option 1
EXPOSURE = float(os.environ.get("EXPOSURE", -0.030))
CONTRAST_SCALE = float(os.environ.get("CONTRAST", 1.00))
SATURATION = float(os.environ.get("SAT", 0.85))
TOE_LIFT = float(os.environ.get("TOE", 0.0050))     # DI, lifts black off zero
TOE_RANGE = float(os.environ.get("TOE_RANGE", 0.16))
# The reference holds its upper mids back: p75 0.429 vs 0.479 here, p95 0.741 vs
# 0.814. Those land from DI ~0.33-0.46, nowhere near the ceiling knee, so the fix
# is a gain through the mids -- eased off at the top so speculars still reach
# white. Applied as an equal shift on all three channels so the colour trace,
# which is already matched, survives.
MID_GAIN = float(os.environ.get("GAIN", 0.918))
HL_KNEE = float(os.environ.get("HL_KNEE", 0.33))
HL_END = float(os.environ.get("HL_END", 0.52))
HL_MIN = float(os.environ.get("HL_MIN", 0.60))
# The reference's highlights are cleaner than the print chain leaves them -
# measured sat 0.109 vs 0.145 at display 0.78, and far less blue suppression.
# Pull chroma toward neutral over the top of the range only.
HD_KNEE = float(os.environ.get("HD_KNEE", 0.410))
HD_END = float(os.environ.get("HD_END", 0.473))
HD_MIN = float(os.environ.get("HD_MIN", 0.70))
# Option 1 rolls off at 0.5055 to protect large bright areas. The reference lets
# speculars reach display white, so the knee sits just under it instead.
CEILING_KNEE = float(os.environ.get("KNEE", 0.5020))
CEILING_MAX = float(os.environ.get("CMAX", 0.5136))
PIVOT = 0.336

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
    size, data = None, []
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
                w = ((f[0] if dr else 1 - f[0]) * (f[1] if dg else 1 - f[1]) *
                     (f[2] if db else 1 - f[2]))
                if w == 0.0:
                    continue
                c = at(i0[0] + dr, i0[1] + dg, i0[2] + db)
                for k in range(3):
                    out[k] += w * c[k]
    return out


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
        out = [lin2di(max(c, 0.0) ** 2.4) for c in disp]
        out = [s + (o - s) * BLEND for s, o in zip(src, out)]

        lum = 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
        if CONTRAST_SCALE != 1.0:
            shift = (PIVOT + (lum - PIVOT) * CONTRAST_SCALE) - lum
            taper = min(1.0, max(0.0, (lum - 0.02) / 0.12))
            out = [c + shift * taper for c in out]
            lum = 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]

        out = [lum + (c - lum) * SATURATION for c in out]

        if MID_GAIN != 1.0:
            t = 1.0
            if lum > HL_KNEE:
                t = 1.0 - (1.0 - HL_MIN) * min(1.0, (lum - HL_KNEE) / (HL_END - HL_KNEE))
            shift = lum * (MID_GAIN - 1.0) * t
            out = [c + shift for c in out]
            lum = 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]

        if HD_MIN != 1.0 and lum > HD_KNEE:
            k = min(1.0, (lum - HD_KNEE) / (HD_END - HD_KNEE))
            s = 1.0 - (1.0 - HD_MIN) * k
            out = [lum + (c - lum) * s for c in out]

        # Lift the toe so shadows read milky rather than crushed. Tapered so it
        # dies out by the midtones and leaves the rest of the curve alone.
        if TOE_LIFT:
            w = max(0.0, 1.0 - lum / TOE_RANGE)
            out = [c + TOE_LIFT * w * w for c in out]

        return [min(max(ceiling_roll(c), 0.0), 1.0) for c in out]

    return look


def main():
    look = build()
    lines = [f'TITLE "WRO Hollywood {VERSION}"', f"LUT_3D_SIZE {SIZE}",
             "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0", ""]
    n = SIZE - 1
    for bi in range(SIZE):
        for gi in range(SIZE):
            for ri in range(SIZE):
                o = look(ri / n, gi / n, bi / n)
                lines.append(f"{o[0]:.6f} {o[1]:.6f} {o[2]:.6f}")
    open(OUT, "w", encoding="ascii").write("\n".join(lines) + "\n")
    print(f"wrote {OUT} ({SIZE}^3)")
    print(f"BLEND={BLEND} SAT={SATURATION} TOE={TOE_LIFT} CONTRAST={CONTRAST_SCALE} "
          f"GAIN={MID_GAIN} KNEE={CEILING_KNEE} CMAX={CEILING_MAX}")

    print("\nNEUTRAL RAMP (DI in -> DI out)")
    print(f"{'in':>6} {'out':>8} {'R-B':>8} {'G-RB':>8}")
    for v in (0.02, 0.05, 0.12, 0.20, 0.28, 0.336, 0.40, 0.45, 0.50, 0.60, 0.80):
        o = look(v, v, v)
        print(f"{v:>6.3f} {sum(o)/3:>8.4f} {o[0]-o[2]:>+8.4f} "
              f"{o[1]-(o[0]+o[2])/2:>+8.4f}")

    mx = 0.0
    for r in range(17):
        for g in range(17):
            for b in range(17):
                mx = max(mx, max(look(r / 16, g / 16, b / 16)))
    print(f"\nmax output over cube: {mx:.4f} (display white = DI 0.5138)")
    lo, hi = look(0.50, 0.50, 0.50), look(0.80, 0.80, 0.80)
    print(f"highlight separation DI 0.50->0.80: {sum(hi)/3 - sum(lo)/3:.4f}")


if __name__ == "__main__":
    main()
