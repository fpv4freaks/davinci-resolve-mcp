"""Per-shot highlight clipping across the look samples vs the ungraded baseline.

If a window is already flat white in the neutral render, no grade can bring it
back - the source clipped it. If the neutral holds detail and a look loses it,
that look's shoulder is at fault and is worth fixing.
"""
import json, os, subprocess

DIR = "/Volumes/Lexar/Export/_LOOKTEST"
SHOTS, CHUNK, FPS = 40, 12, 24
W, H = 320, 133
LOOKS = ["LOOK_neutral", "LOOK_opt1", "LOOK_holly_v4",
         "WRO_Look_Equalizer_v4", "WRO_Look_Burnt_v3", "WRO_Look_Ferrari_v3"]


def stats(path, ts):
    b = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", path, "-frames:v", "1",
         "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    if len(b) != W * H * 3:
        return None
    n = W * H
    hard = flat = 0
    for i in range(0, len(b), 3):
        r, g, bl = b[i], b[i + 1], b[i + 2]
        if r >= 254 and g >= 254 and bl >= 254:
            hard += 1
        if min(r, g, bl) >= 245:            # detail-free near-white
            flat += 1
    return 100.0 * hard / n, 100.0 * flat / n


rows = {}
for L in LOOKS:
    p = os.path.join(DIR, f"{L}.mp4")
    if not os.path.exists(p):
        print("missing", p); continue
    out = []
    for s in range(SHOTS):
        ts = (s * CHUNK + CHUNK // 2) / FPS
        v = stats(p, ts)
        out.append(v or (0.0, 0.0))
    rows[L] = out

print(f"{'shot':>4} " + "".join(f"{L.replace('WRO_Look_','').replace('LOOK_',''):>14}" for L in rows))
worst = []
for s in range(SHOTS):
    line = f"{s:>4} " + "".join(f"{rows[L][s][1]:13.2f}%" for L in rows)
    nb = rows["LOOK_neutral"][s][1]
    bu = rows["WRO_Look_Burnt_v3"][s][1]
    if bu > 1.0:
        worst.append((bu - nb, s, nb, bu))
    if bu > 1.0 or nb > 1.0:
        print(line)

print("\nshots where BURNT blows out most (flat-white % : neutral -> burnt)")
for d, s, nb, bu in sorted(worst, reverse=True)[:8]:
    verdict = "RECOVERABLE - source holds detail" if nb < 0.5 else "source already clipped"
    print(f"  shot {s:2d}   {nb:6.2f}% -> {bu:6.2f}%   (+{d:5.2f})   {verdict}")

print("\nwhole-reel flat-white average")
for L in rows:
    print(f"  {L:26s} {sum(v[1] for v in rows[L])/SHOTS:6.3f}%   "
          f"hard-clip {sum(v[0] for v in rows[L])/SHOTS:6.3f}%")
