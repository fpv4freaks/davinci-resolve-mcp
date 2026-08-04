#!/usr/bin/env python
"""Profile a film's look: tonal placement + how colour moves with brightness.

The thing that separates a Hollywood digital-intermediate look from a print-film
look is not average brightness - it is the *colour trace*: how the R/G/B balance
shifts across the tonal range (teal shadows, neutral mids, warm skin/highlights)
and how hard the toe and shoulder are. This measures exactly that so a look can
be matched on evidence instead of adjectives.

Usage:  film_profile.py <path> <label> [frames]
"""
import json, os, subprocess, sys

PATH = sys.argv[1]
LABEL = sys.argv[2]
NFRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else 240
W, H = 160, 67
STEP = 2          # sample every Nth pixel
BINS = 16
HEAD, TAIL = 0.06, 0.92   # skip logos and credits


def duration(p):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())


def grab(ts):
    b = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", PATH, "-frames:v", "1",
         "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    return b if len(b) == W * H * 3 else None


dur = duration(PATH)
t0, t1 = dur * HEAD, dur * TAIL
times = [t0 + (t1 - t0) * i / (NFRAMES - 1) for i in range(NFRAMES)]

lum_all = []
bin_r = [0.0] * BINS
bin_g = [0.0] * BINS
bin_b = [0.0] * BINS
bin_sat = [0.0] * BINS
bin_n = [0] * BINS
used = 0

for k, ts in enumerate(times):
    buf = grab(ts)
    if not buf:
        continue
    used += 1
    stride = 3 * STEP
    for i in range(0, len(buf) - 2, stride):
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        lum_all.append(y)
        idx = int(y / 256.0 * BINS)
        idx = BINS - 1 if idx >= BINS else idx
        bin_r[idx] += r
        bin_g[idx] += g
        bin_b[idx] += b
        mx, mn = max(r, g, b), min(r, g, b)
        bin_sat[idx] += (mx - mn) / mx if mx else 0.0
        bin_n[idx] += 1
    if (k + 1) % 60 == 0:
        print(f"  {k+1}/{len(times)}", file=sys.stderr)

lum_all.sort()
n = len(lum_all)


def pct(f):
    return lum_all[min(int(f * n), n - 1)] / 255.0


prof = {
    "label": LABEL, "path": PATH, "frames": used, "pixels": n,
    "luma": {f"p{int(f*1000)/10:g}": round(pct(f), 4) for f in
             (0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999)},
    "mean": round(sum(lum_all) / n / 255.0, 4),
    "bins": [],
}
for i in range(BINS):
    if bin_n[i] < 200:
        continue
    c = bin_n[i]
    r, g, b = bin_r[i] / c, bin_g[i] / c, bin_b[i] / c
    y = (i + 0.5) / BINS
    prof["bins"].append({
        "luma": round(y, 3), "share": round(100.0 * c / n, 2),
        "r_g": round((r - g) / 255.0, 4),      # + = warm
        "b_g": round((b - g) / 255.0, 4),      # + = cool
        "sat": round(bin_sat[i] / c, 4),
    })

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"profile_{LABEL}.json")
json.dump(prof, open(out, "w"), indent=1)

print(f"\n=== {LABEL}   {used} frames, {n:,} px ===")
L = prof["luma"]
print("luma  " + "  ".join(f"{k} {v:.3f}" for k, v in L.items()))
print(f"mean {prof['mean']:.4f}")
print(f"\n{'luma':>6}{'share%':>8}{'R-G':>9}{'B-G':>9}{'sat':>8}   cast")
for b in prof["bins"]:
    warm = b["r_g"] - b["b_g"]
    tag = ("warm" if warm > 0.012 else "cool" if warm < -0.012 else "neutral")
    bar = "#" * min(30, int(b["share"]))
    print(f"{b['luma']:6.3f}{b['share']:8.2f}{b['r_g']:+9.4f}{b['b_g']:+9.4f}"
          f"{b['sat']:8.3f}   {tag:7s} {bar}")
print(f"\nwrote {out}")
