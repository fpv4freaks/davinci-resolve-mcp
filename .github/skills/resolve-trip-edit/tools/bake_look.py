"""Bake a look by transferring a measured film profile onto our footage.

The Hollywood LUT was hand-tuned by blending a print stock, which only ever adds
warmth - useless for a cool reference like The Equalizer 2 or a green one like
Burnt. This instead transfers three measured things directly:

  tone    baseline luma percentiles -> target luma percentiles
  colour  the R-G / B-G trace, per luma bin
  sat     the saturation vs luma curve

The LUT is DI in, DI out; RCM applies the Rec.709 output transform afterwards.
Display values here are estimated per-channel and so ignore the DWG->709 matrix,
which is why one measured iteration follows the bake rather than trusting it.

TEMPER matters: a bad transfer reproduces a reference's *encode* as well as its
grade. The Ford v Ferrari screener clips 5% of pixels to white and crushes p5 to
0.004; those are compression artefacts, so the target percentiles are clamped
into a sane range before fitting.

Usage:  bake_look.py <target_profile.json> <name>
"""
import json, math, os, sys

TARGET = sys.argv[1]
NAME = sys.argv[2]
SIZE = 33
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.environ.get("OUT_DIR", os.path.join(REPO, "tmp")), f"{NAME}.cube")

BASE = os.environ.get("BASE", os.path.join(REPO, "tmp/profile_LOOK_neutral.json"))
TONE_S = float(os.environ.get("TONE_S", 1.0))
COLOR_S = float(os.environ.get("COLOR_S", 1.0))
SAT_S = float(os.environ.get("SAT_S", 1.0))
# <1 flattens the tone curve about its own median; the reference's contrast is a
# starting point, not an obligation.
CONTRAST = float(os.environ.get("CONTRAST", 1.0))
# floors/ceilings that keep a damaged reference from becoming a damaged grade
MIN_BLACK = float(os.environ.get("MIN_BLACK", 0.012))
MAX_WHITE = float(os.environ.get("MAX_WHITE", 0.990))
SAT_LO, SAT_HI = 0.45, 1.75
# A global channel shift colours neutral greys, so it inflates measured
# saturation as well as moving the mean. Cap it or a strong cast runs away.
DELTA_MAX = float(os.environ.get("DELTA_MAX", 0.045))
# A cast that runs all the way to white turns paper, shirts and gravel a colour -
# the fault that made Burnt's whites read green. Fade the shift out over the top
# of the range so near-whites stay neutral.
WP_START = float(os.environ.get("WP_START", 0.66))
WP_END = float(os.environ.get("WP_END", 0.94))
WP_FLOOR = float(os.environ.get("WP_FLOOR", 0.15))
# Chroma noise in a dark, heavily-compressed reference reads as huge shadow
# saturation. Below this luma the reference's sat figure is not trustworthy.
SAT_FLOOR_LUMA = float(os.environ.get("SAT_FLOOR_LUMA", 0.10))

PCTS = ["p0.1", "p1", "p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99", "p99.9"]


def di2lin(y):
    if y <= 0.02740668:
        return y / 10.44426855
    return 2.0 ** (y / 0.07329248 - 7.0) - 0.0075


def lin2di(x):
    xc = max(x, -0.0074)
    if xc <= 0.00262409:
        return xc * 10.44426855
    return 0.07329248 * (math.log2(xc + 0.0075) + 7.0)


def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            f = (x - xs[i]) / (xs[i + 1] - xs[i]) if xs[i + 1] > xs[i] else 0.0
            return ys[i] + (ys[i + 1] - ys[i]) * f
    return ys[-1]


base = json.load(open(BASE))
tgt = json.load(open(TARGET))

bx = [0.0] + [base["luma"][p] for p in PCTS] + [1.0]
ty = [0.0] + [tgt["luma"][p] for p in PCTS] + [1.0]
# The floor guards against a crushed reference, but applying it to p0.1/p1 would
# lift true black into a haze, so it starts at p5.
floor_from = 1 + PCTS.index("p5")
ty = [min(MAX_WHITE, max(MIN_BLACK, v)) if floor_from <= i < len(ty) - 1 else v
      for i, v in enumerate(ty)]
ty[0], ty[-1] = 0.0, 1.0
for i in range(1, len(ty)):                     # keep it monotone after clamping
    ty[i] = max(ty[i], ty[i - 1] + 1e-4)
ty = [min(v, 1.0) for v in ty]

if CONTRAST != 1.0:
    med = ty[1 + PCTS.index("p50")]
    ty = [max(0.0, min(1.0, med + (v - med) * CONTRAST)) for v in ty]
    ty[0] = 0.0

# The baseline's top percentiles are all 1.000, so anchoring the curve's end at
# (1.0 -> 1.0) lets pure white through untouched no matter how soft the reference
# rolls off. Ending at MAX_WHITE is what actually tames a blown window.
ty[-1] = min(ty[-1], MAX_WHITE)
for i in range(len(ty) - 1):
    ty[i] = min(ty[i], ty[-1])
for i in range(1, len(ty)):
    ty[i] = max(ty[i], ty[i - 1])
if TONE_S != 1.0:
    ty = [b + (t - b) * TONE_S for b, t in zip(bx, ty)]

bl = [b["luma"] for b in base["bins"]]
b_rg = [b["r_g"] for b in base["bins"]]
b_bg = [b["b_g"] for b in base["bins"]]
b_sat = [b["sat"] for b in base["bins"]]
tl = [b["luma"] for b in tgt["bins"]]
t_rg = [b["r_g"] for b in tgt["bins"]]
t_bg = [b["b_g"] for b in tgt["bins"]]
t_sat = [b["sat"] for b in tgt["bins"]]


def look(r, g, b):
    d = [max(di2lin(c), 0.0) ** (1 / 2.4) for c in (r, g, b)]
    y = 0.2126 * d[0] + 0.7152 * d[1] + 0.0722 * d[2]

    y2 = interp(bx, ty, y)
    k = y2 / y if y > 1e-5 else 1.0
    if y > 1e-5:
        d = [c * k for c in d]
    else:
        d = [c + (y2 - y) for c in d]

    ys = max(y2, SAT_FLOOR_LUMA)
    s = interp(tl, t_sat, ys) / max(interp(bl, b_sat, max(y, SAT_FLOOR_LUMA)), 1e-4)
    s = max(SAT_LO, min(SAT_HI, 1.0 + (s - 1.0) * SAT_S))
    ly = 0.2126 * d[0] + 0.7152 * d[1] + 0.0722 * d[2]
    d = [ly + (c - ly) * s for c in d]

    # Aim at the target trace from where the image actually sits now - after the
    # tone map scaled it by k and the saturation scale by s.
    d_rg = (interp(tl, t_rg, y2) - s * k * interp(bl, b_rg, y)) * COLOR_S
    d_bg = (interp(tl, t_bg, y2) - s * k * interp(bl, b_bg, y)) * COLOR_S
    if y2 > WP_START:
        t = min(1.0, (y2 - WP_START) / (WP_END - WP_START))
        w = 1.0 - (1.0 - WP_FLOOR) * (t * t * (3.0 - 2.0 * t))
        d_rg *= w
        d_bg *= w
    d_rg = max(-DELTA_MAX, min(DELTA_MAX, d_rg))
    d_bg = max(-DELTA_MAX, min(DELTA_MAX, d_bg))
    d[0] += d_rg
    d[2] += d_bg
    comp = 0.2126 * d_rg + 0.0722 * d_bg          # hold luma after the shift
    d = [c - comp for c in d]

    d = [min(max(c, 0.0), 1.0) for c in d]
    return [min(max(lin2di(c ** 2.4), 0.0), 0.5138) for c in d]


lines = [f'TITLE "{NAME}"', f"LUT_3D_SIZE {SIZE}",
         "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0", ""]
n = SIZE - 1
for bi in range(SIZE):
    for gi in range(SIZE):
        for ri in range(SIZE):
            o = look(ri / n, gi / n, bi / n)
            lines.append(f"{o[0]:.6f} {o[1]:.6f} {o[2]:.6f}")
open(OUT, "w", encoding="ascii").write("\n".join(lines) + "\n")

print(f"wrote {OUT}   target={os.path.basename(TARGET)}  "
      f"TONE_S={TONE_S} COLOR_S={COLOR_S} SAT_S={SAT_S}")
print(f"tone map (baseline -> target display luma)")
for p, b, t in zip(["min"] + PCTS + ["max"], bx, ty):
    print(f"   {p:>6} {b:.3f} -> {t:.3f}")
print("neutral ramp DI->DI:", "  ".join(
    f"{v:.2f}:{sum(look(v, v, v))/3:.4f}" for v in (0.05, 0.2, 0.336, 0.45, 0.6)))
