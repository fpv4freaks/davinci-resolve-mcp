"""Measure texture at NATIVE resolution, 1:1 crops - never on a scaled image.

Downscaling averages grain away: the same comparison at 1280x534 reported the
textured master as having LESS high-frequency energy than the untextured one,
which is a scaling artefact, not a result. Crops are taken at full raster.
"""
import subprocess
import sys

import numpy as np

A = sys.argv[1]
B = sys.argv[2]
# three 1:1 windows away from frame centre-weighting, at native 3840x1600
CROPS = ["640:480:600:560", "640:480:1600:400", "640:480:2600:700"]
STEP = 48


def hf_series(path, crop):
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path,
         "-vf", "crop=%s,select=not(mod(n\\,%d))" % (crop, STEP),
         "-fps_mode", "passthrough", "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        stdout=subprocess.PIPE, bufsize=640 * 480 * 8)
    px = 640 * 480
    hf, mean = [], []
    while True:
        buf = proc.stdout.read(px)
        if len(buf) < px:
            break
        f = np.frombuffer(buf, dtype=np.uint8).reshape(480, 640).astype(np.float32)
        m = (f > 25) & (f < 170)                       # mids and shadows
        mm = m[1:-1, 1:-1]
        if mm.sum() < 3000:
            continue
        hp = f[1:-1, 1:-1] - 0.25 * (f[:-2, 1:-1] + f[2:, 1:-1] +
                                     f[1:-1, :-2] + f[1:-1, 2:])
        hf.append(float(hp[mm].std()))
        mean.append(float(f.mean()))
    proc.stdout.close()
    proc.wait()
    return np.array(hf), np.array(mean)


print("native 1:1 crops, mids/shadows only")
tot_a, tot_b = [], []
for crop in CROPS:
    ha, ma = hf_series(A, crop)
    hb, mb = hf_series(B, crop)
    n = min(len(ha), len(hb))
    if not n:
        continue
    ha, hb = ha[:n], hb[:n]
    tot_a.append(ha)
    tot_b.append(hb)
    g = np.sqrt(max(hb.mean() ** 2 - ha.mean() ** 2, 0.0))
    print("  crop %-20s A %.3f   B %.3f   grain RMS %.2f   (%d frames)"
          % (crop, ha.mean(), hb.mean(), g, n))

a = np.concatenate(tot_a)
b = np.concatenate(tot_b)
grain = np.sqrt(max(b.mean() ** 2 - a.mean() ** 2, 0.0))
print("\noverall   A(no texture) %.3f    B(textured) %.3f" % (a.mean(), b.mean()))
print("grain RMS (quadrature) %.2f" % grain)
print("verdict: %s" % ("VISIBLE - in the 3-8 band" if 3 <= grain <= 8 else
                       "STRONG - above 8, likely too much" if grain > 8 else
                       "present but subtle" if grain > 1.0 else
                       "contributes ~nothing"))
print("frames where B has more HF: %d%%" % round(100 * float((b > a).mean())))
