"""Measure high-frequency noise in flat areas - the objective grain check.
Compares the new Look 7 render against the grainless v12 master."""
import os
import subprocess
import sys

from PIL import Image, ImageFilter

FILES = {
    "v12 master (no grain)": "/Volumes/Lexar/Export/WRO_Trip_Day1-2_v12.mov",
    "Look 7 + 16mm grain": "/Volumes/Lexar/Export/_VERIFY/VERIFY_Look7_grain.mov",
}
TMP = "/tmp/_grainmeas"
os.makedirs(TMP, exist_ok=True)


def hf_std(path, ts, tag):
    out = os.path.join(TMP, "%s_%s.png" % (tag, ts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ts), "-i", path,
                    "-frames:v", "1", "-vf", "crop=600:400:1600:500", out],
                   check=True)
    im = Image.open(out).convert("L")
    hf = Image.eval(im, lambda p: p)
    blur = im.filter(ImageFilter.GaussianBlur(1.6))
    px, bx = list(hf.getdata()), list(blur.getdata())
    d = [a - b for a, b in zip(px, bx)]
    n = len(d)
    mean = sum(d) / n
    var = sum((x - mean) ** 2 for x in d) / n
    return var ** 0.5


for label, path in FILES.items():
    if not os.path.exists(path):
        print("%-24s MISSING %s" % (label, path))
        continue
    # the verify clip starts at 1:40 of the cut, so sample its own timebase
    offs = [2, 8, 14] if "_VERIFY" in path else [102, 108, 114]
    vals = [hf_std(path, t, label.split()[0]) for t in offs]
    print("%-24s HF std: %s  mean %.2f"
          % (label, " ".join("%.2f" % v for v in vals), sum(vals) / len(vals)))

print("\nreference: visible 4K film grain reads ~3-8; below ~1.5 is clean digital")
