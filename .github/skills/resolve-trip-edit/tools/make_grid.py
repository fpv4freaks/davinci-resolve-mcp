"""Build a labelled 2x3 comparison grid video from the look samples.

ffmpeg here is built without drawtext, so labels are rendered to PNG with Pillow
and composited as overlays instead.
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

OUT = "/Volumes/Lexar/Export/WRO_LOOK_SAMPLES"
WORK = os.path.join(os.environ.get("TMPDIR", "/tmp"), "grid")
CW, CH = 480, 200                       # 4x2 -> 1920x400
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
LOOKS = [
    ("SAMPLE_1_Print2383", "1  PRINT 2383"),
    ("SAMPLE_2_Marvel", "2  MARVEL"),
    ("SAMPLE_7_MarvelOlive", "7  MARVEL OLIVE"),
    ("SAMPLE_6_Silo", "6  SILO"),
    ("SAMPLE_3_Equalizer", "3  EQUALIZER"),
    ("SAMPLE_4_Burnt", "4  BURNT"),
    ("SAMPLE_5_Ferrari", "5  FERRARI"),
    ("SAMPLE_8_BladeRunner", "8  BLADE RUNNER 2049"),
]

os.makedirs(WORK, exist_ok=True)
font = ImageFont.truetype(FONT, 16)
for name, label in LOOKS:
    img = Image.new("RGBA", (CW, 26), (0, 0, 0, 190))
    ImageDraw.Draw(img).text((8, 4), label, font=font, fill=(255, 255, 255, 255))
    img.save(os.path.join(WORK, f"{name}.png"))

blank = Image.new("RGB", (CW, CH), (12, 12, 12))
d = ImageDraw.Draw(blank)
d.text((14, 100), "20s sample reel", font=font, fill=(150, 150, 150))
d.text((14, 130), "40 shots across both days", font=font, fill=(150, 150, 150))
d.text((14, 160), "no grain (OFX not scriptable)", font=font, fill=(110, 110, 110))
blank.save(os.path.join(WORK, "blank.png"))

cmd = ["ffmpeg", "-v", "error", "-y"]
for name, _ in LOOKS:
    cmd += ["-i", os.path.join(OUT, f"{name}.mp4")]
for name, _ in LOOKS:
    cmd += ["-i", os.path.join(WORK, f"{name}.png")]

N = len(LOOKS)
parts = []
for i, (name, _) in enumerate(LOOKS):
    parts.append(f"[{i}:v]fps=24,scale={CW}:{CH}[v{i}]")
    parts.append(f"[v{i}][{N+i}:v]overlay=0:{CH-26}[l{i}]")
parts.append("[l0][l1][l2][l3]hstack=inputs=4[top]")
parts.append("[l4][l5][l6][l7]hstack=inputs=4[bot]")
parts.append("[top][bot]vstack=inputs=2[out]")

cmd += ["-filter_complex", ";".join(parts), "-map", "[out]",
        "-t", "20", "-r", "24", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p", os.path.join(OUT, "COMPARE_LOOKS_GRID.mp4")]

r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stderr[-1500:] if r.returncode else "grid built")
p = os.path.join(OUT, "COMPARE_LOOKS_GRID.mp4")
if os.path.exists(p):
    print(f"{p}  {os.path.getsize(p)/1e6:.1f} MB")
