"""Contact sheet of a film's daylight-range frames, for visual grounding.

Usage: ref_sheet.py <path> <label> [n] [lo] [hi]
"""
import os, subprocess, sys

P, LABEL = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 12
LO = float(sys.argv[4]) if len(sys.argv) > 4 else 0.24
HI = float(sys.argv[5]) if len(sys.argv) > 5 else 0.42
W, H = 160, 67
OUT = f"/Volumes/Lexar/Export/_LOOKTEST/REF_{LABEL}.jpg"

dur = float(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", P],
    capture_output=True, text=True).stdout.strip())

picks = []
for i in range(200):
    ts = dur * 0.08 + (dur * 0.90 - dur * 0.08) * i / 199
    b = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", P, "-frames:v", "1",
         "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    if len(b) != W * H * 3:
        continue
    m = sum(0.2126 * b[j] + 0.7152 * b[j + 1] + 0.0722 * b[j + 2]
            for j in range(0, len(b), 3)) / (W * H) / 255.0
    if LO <= m <= HI:
        picks.append(ts)
    if len(picks) >= N:
        break

work = os.path.join(os.environ.get("TMPDIR", "/tmp"), f"ref_{LABEL}")
subprocess.run(["rm", "-rf", work])
os.makedirs(work, exist_ok=True)
for i, ts in enumerate(picks):
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", P,
                    "-frames:v", "1", "-vf", "scale=440:183", "-y",
                    os.path.join(work, f"{i:02d}.jpg")], capture_output=True)
subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(work, "%02d.jpg"),
                "-vf", f"tile=3x{max(1, len(picks)//3)}", "-y", OUT],
               capture_output=True)
print(f"{LABEL}: {len(picks)} frames -> {OUT}")
