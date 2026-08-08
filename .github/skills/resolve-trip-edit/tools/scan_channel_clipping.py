"""Per-CHANNEL clipping scan on a rendered master.

Luma percentiles are blind to channel clipping: R+G pegged with B free reads as
yellow/green blown colour while luma p999 stays under the legal limit. This
measures each channel separately, per shot.
"""
import json
import subprocess
import sys

import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    "/Volumes/Lexar/Export/JURA_Trip_Day1-3_v1_Look7.mov"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "/Users/danielwojcik/vscode/davinci-resolve-mcp/tmp/jura_clipscan.json"
PLAN = json.load(open(sys.argv[3] if len(sys.argv) > 3 else "shots.json"))
W, H, STEP = 320, 133, 3
PX = W * H * 3
HOT = 250.0            # per-channel "pegged" threshold out of 255

proc = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-i", SRC,
     "-vf", "scale=%d:%d,select=not(mod(n\\,%d))" % (W, H, STEP),
     "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
    stdout=subprocess.PIPE, bufsize=PX * 8)

shots = PLAN["shots"]
edges = np.array([s["rec"] for s in shots] + [shots[-1]["rec"] + shots[-1]["dur"]])
acc = [[] for _ in shots]
n = 0
while True:
    buf = proc.stdout.read(PX)
    if len(buf) < PX:
        break
    k = int(np.searchsorted(edges, n * STEP, side="right")) - 1
    if 0 <= k < len(shots):
        a = np.frombuffer(buf, dtype=np.uint8).reshape(-1, 3).astype(np.float32)
        hot = a >= HOT
        anyhot = hot.any(axis=1)
        allhot = hot.all(axis=1)
        acc[k].append((
            hot[:, 0].mean(), hot[:, 1].mean(), hot[:, 2].mean(),
            anyhot.mean(), allhot.mean(),
            (anyhot & ~allhot).mean(),           # clipped in SOME but not all -> colour shift
            np.percentile(a[:, 0], 99.9), np.percentile(a[:, 1], 99.9),
            np.percentile(a[:, 2], 99.9),
        ))
    n += 1
proc.stdout.close()
proc.wait()
print("frames decoded: %d" % n)

rows = []
for j, (s, buf) in enumerate(zip(shots, acc), 1):
    if not buf:
        continue
    v = np.array(buf).mean(axis=0)
    rows.append({"i": j, "name": s["name"], "note": s["note"], "rec": s["rec"],
                 "dur": s["dur"],
                 "R": round(float(v[0]) * 100, 3), "G": round(float(v[1]) * 100, 3),
                 "B": round(float(v[2]) * 100, 3),
                 "any": round(float(v[3]) * 100, 3), "all": round(float(v[4]) * 100, 3),
                 "colour_clip": round(float(v[5]) * 100, 3),
                 "p999R": round(float(v[6]), 1), "p999G": round(float(v[7]), 1),
                 "p999B": round(float(v[8]), 1)})
json.dump(rows, open(OUT, "w"), indent=1)

anyc = np.array([r["any"] for r in rows])
colc = np.array([r["colour_clip"] for r in rows])
print("\nshots: %d" % len(rows))
print("ANY-channel pegged   mean %.3f%%  max %.2f%%  | shots over 1%%: %d, over 3%%: %d"
      % (anyc.mean(), anyc.max(), int((anyc > 1).sum()), int((anyc > 3).sum())))
print("COLOUR clip (some channels only, not all) mean %.3f%%  max %.2f%%  "
      "| shots over 1%%: %d"
      % (colc.mean(), colc.max(), int((colc > 1).sum())))
print("\nworst 15 by colour clip (these are the yellow/green blown ones):")
for r in sorted(rows, key=lambda z: -z["colour_clip"])[:15]:
    print("  %3d %-9s colourclip %5.2f%%  any %5.2f%%  all %5.2f%%  "
          "p999 R%3.0f G%3.0f B%3.0f  %s"
          % (r["i"], r["name"][10:18], r["colour_clip"], r["any"], r["all"],
             r["p999R"], r["p999G"], r["p999B"], r["note"][:22]))
