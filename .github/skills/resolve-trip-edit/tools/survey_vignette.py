#!/usr/bin/env python3
"""Survey a shoot for lens vignetting and report correction options.

Usage:
    survey_vignette.py <index_proxy.mp4> <index_manifest.json> [strength]

The manifest is the one written when the INDEX timeline is built: it needs
{"clips": [{"name", "rec", "dur"}, ...]} with `rec` in timeline frames.

Method, and why it is this way:
  * Measure each clip's own flat field, then take the MEDIAN ACROSS CLIPS.
    Pooling all frames lets long clips dominate and bakes their framing in.
  * Mirror into four quadrants before fitting. Top/bottom asymmetry is scene
    content (bright sky, dark ground); a lens falloff is symmetric.
  * Left/right asymmetry is the evidence it is optical at all. Report it.
  * Fit gain as a NON-NEGATIVE series in r^2 so the model cannot go
    non-monotonic and brighten the middle of the frame.

Prints measured falloff plus leave-it / halve-it / remove-it options with the
noise cost of each, so the choice goes back to the user.
"""
import json
import subprocess
import sys

import numpy as np

W, H, STEP, MIN_FRAMES = 240, 100, 6, 4
PX = W * H * 3


def per_clip_fields(src, clips):
    edges = np.array([c["rec"] for c in clips] + [clips[-1]["rec"] + clips[-1]["dur"]])
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", src,
         "-vf", "scale=%d:%d,select=not(mod(n\\,%d))" % (W, H, STEP),
         "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        stdout=subprocess.PIPE, bufsize=PX * 8)
    buckets = [[] for _ in clips]
    n = 0
    while True:
        buf = proc.stdout.read(PX)
        if len(buf) < PX:
            break
        k = int(np.searchsorted(edges, n * STEP, side="right")) - 1
        if 0 <= k < len(buckets):
            a = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3).astype(np.float32)
            y = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]
            m = float(y.mean())
            if 30 < m < 200:                     # skip near-black / near-white
                buckets[k].append(y / m)
        n += 1
    proc.stdout.close()
    proc.wait()
    return buckets


def nnls(A, b, iters=4000):
    x = np.zeros(A.shape[1])
    AtA, Atb = A.T @ A, A.T @ b
    lr = 1.0 / (np.linalg.norm(AtA, 2) + 1e-9)
    for _ in range(iters):
        x = np.maximum(0.0, x - lr * (AtA @ x - Atb))
    return x


def main():
    src, manifest = sys.argv[1], sys.argv[2]
    strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    clips = json.load(open(manifest))["clips"]

    cy, cx, k = H // 2, W // 2, 6
    raw, fields = [], []
    for buf in per_clip_fields(src, clips):
        if len(buf) < MIN_FRAMES:
            continue
        f = np.median(np.stack(buf), axis=0)
        f = f / f[cy - k:cy + k, cx - k:cx + k].mean()
        raw.append(f)
        s = (f + f[::-1, :] + f[:, ::-1] + f[::-1, ::-1]) / 4.0
        fields.append(s / s[cy - k:cy + k, cx - k:cx + k].mean())
    print("clips measured: %d of %d" % (len(fields), len(clips)))
    if not fields:
        sys.exit("no usable clips")

    yy, xx = np.mgrid[0:H, 0:W]
    nx = (xx - (W - 1) / 2) / ((W - 1) / 2)
    ny = (yy - (H - 1) / 2) / ((H - 1) / 2)

    unsym = np.median(np.stack(raw), axis=0)
    lr_asym = abs(unsym[:, nx[0] < -0.85].mean() - unsym[:, nx[0] > 0.85].mean())
    print("left/right asymmetry %.3f  %s"
          % (lr_asym, "-> symmetric, consistent with the lens" if lr_asym < 0.08
             else "-> NOT symmetric; likely content, not optics"))

    sym = np.median(np.stack(fields), axis=0)
    sym = sym / sym[cy - k:cy + k, cx - k:cx + k].mean()

    best = None
    for ky in np.arange(0.02, 1.01, 0.02):
        r2 = (nx ** 2 + ky * ny ** 2).ravel()
        A = np.stack([r2 ** j for j in (1, 2, 3, 4)], axis=1)
        coef = nnls(A, (1.0 / sym).ravel() - 1.0)
        res = float(np.sqrt(np.mean((1.0 / (1.0 + A @ coef) - sym.ravel()) ** 2)))
        if best is None or res < best[0]:
            best = (res, float(ky), coef.copy())
    res, ky, coef = best

    def falloff(x, y):
        q = x ** 2 + ky * y ** 2
        return 1.0 / (1.0 + sum(c * q ** j for j, c in zip((1, 2, 3, 4), coef)))

    print("\nmeasured falloff (median across clips):")
    for x, y, lbl in [(0.5, 0, "half width"), (0.75, 0, "3/4 width"),
                      (1.0, 0, "L/R edge"), (0, 0.9, "top/bottom"),
                      (0.85, 0.85, "corner")]:
        print("  %-14s %+.2f stops" % (lbl, np.log2(falloff(x, y))))

    edge, corner = falloff(1.0, 0), falloff(0.85, 0.85)
    onset = next(x for x in np.arange(0, 1.01, 0.01) if falloff(x, 0) < 0.95)
    print("\nfalloff starts at %.0f%% of half-width; the no-correction zone is an"
          % (onset * 100))
    print("ellipse ~%.0f%% of frame WIDTH x 100%% of HEIGHT (nearly round in pixels)."
          % (onset * 100))

    print("\noptions:")
    print("  1. leave it            - %+.2f st at edges kept as character, no noise cost"
          % np.log2(edge))
    print("  2. correct %.0f%% (rec)  - %+.2f st back at edges, %+.2f st left, "
          "corner noise x%.2f"
          % (strength * 100, np.log2((1 / edge) ** strength),
             np.log2(edge * (1 / edge) ** strength), (1 / corner) ** strength))
    print("  3. remove it           - flat field, corner noise x%.2f" % (1 / corner))
    print("\nApply on the colour GROUP's pre-clip node graph (one node covers every")
    print("shot). There is no AddNode in the API - this step is hand work.")


if __name__ == "__main__":
    main()
