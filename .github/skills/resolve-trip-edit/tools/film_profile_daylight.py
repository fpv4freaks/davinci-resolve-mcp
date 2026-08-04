#!/usr/bin/env python
"""Profile only the frames whose brightness matches our film's own range.

A reference film's overall luma says as much about its content as its look -
Captain Marvel reads dark because half of it is space and night interiors. To
extract the LOOK, keep only the frames that sit in the same tonal territory as
the target footage, then measure the colour trace and contrast on those.

Usage:  film_profile_daylight.py <path> <label> <nframes> <lo> <hi>
"""
import json, os, subprocess, sys

PATH, LABEL = sys.argv[1], sys.argv[2]
NFRAMES = int(sys.argv[3]) if len(sys.argv) > 3 else 600
LO = float(sys.argv[4]) if len(sys.argv) > 4 else 0.22
HI = float(sys.argv[5]) if len(sys.argv) > 5 else 0.45
W, H = 160, 67
STEP = 2
BINS = 16
HEAD, TAIL = 0.06, 0.92
# Burned-in subtitles are white text and land straight in the top luma bin, which
# fakes a hot highlight roll-off. CROP trims that band before measuring.
CROP = os.environ.get("CROP", "")
VF = (f"{CROP},scale={W}:{H}" if CROP else f"scale={W}:{H}")

dur = float(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
     PATH], capture_output=True, text=True).stdout.strip())
times = [dur * HEAD + (dur * TAIL - dur * HEAD) * i / (NFRAMES - 1) for i in range(NFRAMES)]

lum_all = []
bin_r = [0.0] * BINS; bin_g = [0.0] * BINS; bin_b = [0.0] * BINS
bin_sat = [0.0] * BINS; bin_n = [0] * BINS
kept = scanned = 0
frame_means = []

for k, ts in enumerate(times):
    buf = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", PATH, "-frames:v", "1",
         "-vf", VF, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    if len(buf) != W * H * 3:
        continue
    scanned += 1
    px = [(buf[i], buf[i + 1], buf[i + 2]) for i in range(0, len(buf) - 2, 3 * STEP)]
    lums = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in px]
    fm = sum(lums) / len(lums) / 255.0
    frame_means.append(fm)
    if not (LO <= fm <= HI):
        continue
    kept += 1
    for (r, g, b), y in zip(px, lums):
        lum_all.append(y)
        idx = min(int(y / 256.0 * BINS), BINS - 1)
        bin_r[idx] += r; bin_g[idx] += g; bin_b[idx] += b
        mx, mn = max(r, g, b), min(r, g, b)
        bin_sat[idx] += (mx - mn) / mx if mx else 0.0
        bin_n[idx] += 1
    if kept and kept % 50 == 0:
        print(f"  kept {kept} of {scanned}", file=sys.stderr)

lum_all.sort()
n = len(lum_all)
pct = lambda f: lum_all[min(int(f * n), n - 1)] / 255.0

prof = {
    "label": LABEL, "path": PATH, "window": [LO, HI],
    "frames_scanned": scanned, "frames_kept": kept, "pixels": n,
    "luma": {f"p{int(f*1000)/10:g}": round(pct(f), 4) for f in
             (0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999)},
    "mean": round(sum(lum_all) / n / 255.0, 4), "bins": [],
}
for i in range(BINS):
    if bin_n[i] < 200:
        continue
    c = bin_n[i]
    r, g, b = bin_r[i] / c, bin_g[i] / c, bin_b[i] / c
    prof["bins"].append({
        "luma": round((i + 0.5) / BINS, 3), "share": round(100.0 * c / n, 2),
        "r_g": round((r - g) / 255.0, 4), "b_g": round((b - g) / 255.0, 4),
        "sat": round(bin_sat[i] / c, 4),
    })

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"profile_{LABEL}.json")
json.dump(prof, open(out, "w"), indent=1)

fm = sorted(frame_means)
print(f"\n=== {LABEL}  kept {kept}/{scanned} frames in [{LO},{HI}] ===")
print(f"frame-mean spread of the whole film: {fm[0]:.3f} / "
      f"{fm[len(fm)//4]:.3f} / {fm[len(fm)//2]:.3f} / {fm[3*len(fm)//4]:.3f} / {fm[-1]:.3f}")
print("luma  " + "  ".join(f"{k} {v:.3f}" for k, v in prof["luma"].items()))
print(f"mean {prof['mean']:.4f}")
print(f"\n{'luma':>6}{'share%':>8}{'R-G':>9}{'B-G':>9}{'sat':>8}")
for b in prof["bins"]:
    print(f"{b['luma']:6.3f}{b['share']:8.2f}{b['r_g']:+9.4f}{b['b_g']:+9.4f}{b['sat']:8.3f}")
print(f"\nwrote {out}")
