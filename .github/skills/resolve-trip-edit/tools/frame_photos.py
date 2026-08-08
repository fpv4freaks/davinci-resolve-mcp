"""Render each photo in a plan as a clip that fills a wide frame.

A still in a 2.40:1 frame leaves a lot of empty width - a landscape photo fills
about 52% of it, a portrait only about 29%. So the photo sits sharp on top of a
blurred, darkened copy of itself, and **the background is suppressed in
proportion to how much of the frame it occupies**: the blur and brightness that
flatter a landscape leave a portrait competing with its own wallpaper.

Composited in PIL and pushed in ffmpeg rather than built with Resolve nodes,
because the scripting API cannot author OFX or add nodes - a two-track blur is
hand-work on every clip.

Two details that matter:
  - the composite is built at 1.1x the delivery raster, so the slow push always
    samples DOWN and never upscales
  - portrait stills need the motion most; at 29% of the width a static strip for
    two seconds reads as dead air

In a colour-managed project the output must be tagged on import
(`Input Color Space` -> `Rec.709 Gamma 2.4`) or it inherits the project default,
which on a BRAW show is a log space and renders violently oversaturated.

Usage: frame_photos.py <plan.json> <outdir> [--width 3840] [--height 1600]
"""
import argparse
import json
import os
import subprocess

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

BLUR = {'wide': 45, 'narrow': 80}
DARK = {'wide': 0.55, 'narrow': 0.38}
DESAT = {'wide': 0.70, 'narrow': 0.45}
NARROW_BELOW = 0.42


def composite(path, dst, cw, ch, fw, fh):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    fg = im.copy()
    fg.thumbnail((fw, fh), Image.LANCZOS)
    k = 'narrow' if fg.width / cw < NARROW_BELOW else 'wide'
    bg = ImageOps.fit(im, (cw, ch), method=Image.LANCZOS, centering=(0.5, 0.5))
    bg = bg.filter(ImageFilter.GaussianBlur(BLUR[k]))
    bg = ImageEnhance.Brightness(bg).enhance(DARK[k])
    bg = ImageEnhance.Color(bg).enhance(DESAT[k])
    bg.paste(fg, ((cw - fg.width) // 2, (ch - fg.height) // 2))
    bg.save(dst)
    return fg.width


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('plan')
    ap.add_argument('outdir')
    ap.add_argument('--width', type=int, default=3840)
    ap.add_argument('--height', type=int, default=1600)
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--zoom', type=float, default=0.08)
    ap.add_argument('--oversize', type=float, default=1.1)
    a = ap.parse_args()

    cw, ch = int(a.width * a.oversize), int(a.height * a.oversize)
    fw, fh = int((a.width - 40) * a.oversize), int((a.height - 100) * a.oversize)
    os.makedirs(a.outdir, exist_ok=True)
    plan = json.load(open(a.plan))
    tmp = os.path.join(a.outdir, '_composite.png')

    for n, r in enumerate(plan, 1):
        dst = os.path.join(a.outdir, f"D{r['day']}_{os.path.splitext(r['name'])[0]}.mov")
        width = composite(r['path'], tmp, cw, ch, fw, fh)
        frames = r['frames']
        subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', str(a.fps),
             '-t', f'{frames / a.fps:.4f}', '-i', tmp,
             '-vf', f"zoompan=z='1+{a.zoom}*on/{frames - 1}':d=1"
                    f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                    f":s={a.width}x{a.height}:fps={a.fps},format=yuv422p10le",
             '-frames:v', str(frames),
             '-c:v', 'prores_ks', '-profile:v', '1', dst], check=True)
        print(f"  {n:>3}/{len(plan)}  D{r['day']} {r['name']:<18} "
              f"picture fills {100 * width / cw:>4.0f}% of width  {frames}f")

    if os.path.exists(tmp):
        os.remove(tmp)
    print(f'\nwrote {len(plan)} clips to {a.outdir}')
    print('remember to tag Input Color Space on import in a colour-managed project')


if __name__ == '__main__':
    main()
