"""Detect camera start/stop handling at clip heads and tails.

An operator raising the camera to frame, or lowering it before stopping, shows up
as a sustained VERTICAL drift at the very start or end of a clip. Scalar frame
difference cannot tell that apart from subject motion, so this estimates the
global vertical and horizontal shift per frame by 1-D projection matching:
row means give a vertical signature, column means a horizontal one, and the lag
that minimises SSD between consecutive frames is the camera move.

Reports, per clip, the first and last frame at which the camera has settled.
"""
import json
import sys
import subprocess

import numpy as np

BASE = sys.argv[2] if len(sys.argv) > 2 else "./"
SRC = sys.argv[1] if len(sys.argv) > 1 else "index.mp4"
IDX = json.load(open(BASE + "jura_index.json"))
W, H = 320, 134
PX = W * H * 3
MAXLAG = 8
DRIFT_WIN = 6            # frames to accumulate drift over (1/4 second)
DRIFT_PX = 3.0           # sustained shift over that window = still moving
CALM = 4                 # frames of calm needed to call it settled


def shift1d(a, b, maxlag=MAXLAG):
    """Lag that best aligns profile b onto a, sub-pixel by parabolic fit."""
    n = len(a)
    best, bl = None, 0
    for lag in range(-maxlag, maxlag + 1):
        if lag < 0:
            x, y = a[-lag:], b[:n + lag]
        elif lag > 0:
            x, y = a[:n - lag], b[lag:]
        else:
            x, y = a, b
        d = float(np.mean((x - y) ** 2))
        if best is None or d < best:
            best, bl = d, lag
    return bl


proc = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-i", SRC, "-vf", "scale=%d:%d" % (W, H),
     "-pix_fmt", "gray", "-f", "rawvideo", "-"],
    stdout=subprocess.PIPE, bufsize=W * H * 8)

edges = np.array([c["rec"] for c in IDX["clips"]] +
                 [IDX["clips"][-1]["rec"] + IDX["clips"][-1]["dur"]])
rows_prev = cols_prev = None
prev_clip = -1
dy = [[] for _ in IDX["clips"]]
dx = [[] for _ in IDX["clips"]]
n = 0
while True:
    buf = proc.stdout.read(W * H)
    if len(buf) < W * H:
        break
    k = int(np.searchsorted(edges, n, side="right")) - 1
    f = np.frombuffer(buf, dtype=np.uint8).reshape(H, W).astype(np.float32)
    r = f.mean(axis=1)
    c = f.mean(axis=0)
    if k == prev_clip and rows_prev is not None:
        dy[k].append(shift1d(rows_prev, r))
        dx[k].append(shift1d(cols_prev, c))
    elif 0 <= k < len(dy):
        dy[k].append(0)
        dx[k].append(0)
    rows_prev, cols_prev, prev_clip = r, c, k
    n += 1
proc.stdout.close()
proc.wait()
print("frames analysed: %d" % n)


def settle(v):
    """First and last frame index where the camera has stopped moving."""
    a = np.abs(np.convolve(np.array(v, dtype=np.float32),
                           np.ones(DRIFT_WIN), mode="same"))
    moving = a > DRIFT_PX
    first = 0
    run = 0
    for i, m in enumerate(moving):
        run = 0 if m else run + 1
        if run >= CALM:
            first = i - CALM + 1
            break
    else:
        first = 0
    last = len(moving) - 1
    run = 0
    for i in range(len(moving) - 1, -1, -1):
        run = 0 if moving[i] else run + 1
        if run >= CALM:
            last = i + CALM - 1
            break
    return int(first), int(min(last, len(moving) - 1))


out = []
for c, vy, vx in zip(IDX["clips"], dy, dx):
    if len(vy) < 8:
        out.append({"name": c["name"], "dur": c["dur"], "head": 0,
                    "tail": c["dur"] - 1, "head_s": 0.0, "tail_s": 0.0})
        continue
    fy, ly = settle(vy)
    fx, lx = settle(vx)
    head = max(fy, fx)
    tail = min(ly, lx)
    if tail - head < 24:                        # never leave less than a second
        head, tail = 0, c["dur"] - 1
    out.append({"name": c["name"], "dur": c["dur"], "head": head, "tail": tail,
                "head_s": round(head / 24, 2),
                "tail_s": round((c["dur"] - 1 - tail) / 24, 2)})

json.dump(out, open(BASE + "jura_settle.json", "w"), indent=1)

hs = np.array([r["head_s"] for r in out])
ts = np.array([r["tail_s"] for r in out])
print("\nclips: %d" % len(out))
print("head handling  median %.2fs  p90 %.2fs  max %.2fs  | over 0.5s: %d clips"
      % (np.median(hs), np.percentile(hs, 90), hs.max(), int((hs > 0.5).sum())))
print("tail handling  median %.2fs  p90 %.2fs  max %.2fs  | over 0.5s: %d clips"
      % (np.median(ts), np.percentile(ts, 90), ts.max(), int((ts > 0.5).sum())))
print("clips with over 1s of unusable tail: %d" % int((ts > 1.0).sum()))
print("\nworst tails (camera being lowered before stop):")
for r in sorted(out, key=lambda z: -z["tail_s"])[:12]:
    print("  %-9s dur %4.1fs  head %.2fs  TAIL %.2fs unusable"
          % (r["name"][10:18], r["dur"] / 24, r["head_s"], r["tail_s"]))
