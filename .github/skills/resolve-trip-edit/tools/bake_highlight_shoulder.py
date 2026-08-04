"""Bake a per-channel highlight-shoulder LUT in DaVinci Intermediate (DI) space.

The shared look LUT is near-linear up to DI ~0.50 then hard-clips flat at ~0.500.
Any footage whose DI values exceed ~0.51 loses all highlight separation. This LUT
compresses highlights above a knee K so they asymptote just under a ceiling C
(< the look's clip point), restoring detail while leaving mids/shadows untouched.

Per-channel (separable) so specular highlights desaturate toward white naturally.

Usage: bake_highlight_shoulder.py <out.cube> [KNEE] [CEIL] [SIZE]
"""
import math
import sys

OUT = sys.argv[1]
KNEE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.42
CEIL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.49
SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 33
NAME = OUT.split("/")[-1].rsplit(".", 1)[0]


def shoulder(x, K=KNEE, C=CEIL):
    if x <= K:
        return x
    # smooth, C1-continuous at K (slope 1), asymptotes to C as x -> inf
    return C - (C - K) * math.exp(-(x - K) / (C - K))


lines = [f'TITLE "{NAME}"', f"LUT_3D_SIZE {SIZE}",
         "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0", ""]
n = SIZE - 1
for bi in range(SIZE):
    b = shoulder(bi / n)
    for gi in range(SIZE):
        g = shoulder(gi / n)
        for ri in range(SIZE):
            r = shoulder(ri / n)
            lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
open(OUT, "w", encoding="ascii").write("\n".join(lines) + "\n")
print(f"wrote {OUT}  KNEE={KNEE} CEIL={CEIL} SIZE={SIZE}")
print("map check: " + "  ".join(
    f"{v:.2f}->{shoulder(v):.3f}" for v in (0.30, 0.42, 0.50, 0.60, 0.80, 1.00)))
