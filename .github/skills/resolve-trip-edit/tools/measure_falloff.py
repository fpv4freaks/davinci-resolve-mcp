"""Measure the residual lens falloff on a rendered plate.

Per-clip flat field, median ACROSS clips - pooling every frame lets long clips
dominate and bakes their framing in. Mirrored into four quadrants before reading,
because top/bottom asymmetry is scene content (bright sky, dark ground) while a
lens falloff is symmetric. Gives a before/after number for the anti-vignette node.

Usage: measure_falloff.py <plate.mov> <items.json>
"""
import json
import subprocess
import sys

import numpy as np

PLATE, ITEMS = sys.argv[1], sys.argv[2]
W, H, STRIDE = 192, 80, 8

items = json.load(open(ITEMS))
start = items[0]['start']
edges = np.array([it['start'] - start for it in items] + [items[-1]['end'] - start])

acc = [np.zeros((H, W)) for _ in items]
cnt = [0] * len(items)
proc = subprocess.Popen(
    ['ffmpeg', '-v', 'error', '-i', PLATE, '-vf', f'scale={W}:{H}',
     '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
    stdout=subprocess.PIPE, bufsize=W * H * 3 * 8)
n = 0
while True:
    b = proc.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    if n % STRIDE == 0:
        k = int(np.searchsorted(edges, n, side='right')) - 1
        if 0 <= k < len(items):
            rgb = np.frombuffer(b, dtype=np.uint8).reshape(H, W, 3).astype(np.float64) / 255
            acc[k] += rgb @ [.2126, .7152, .0722]
            cnt[k] += 1
    n += 1
proc.stdout.close()
proc.wait()

fields = []
for a, c in zip(acc, cnt):
    if c < 3:
        continue
    f = a / c
    if f.mean() < 1e-4:
        continue
    fields.append(f / f.mean())          # normalise so brightness does not weight it
raw = np.median(np.stack(fields), axis=0)
field = (raw + raw[::-1] + raw[:, ::-1] + raw[::-1, ::-1]) / 4

cy, cx = H // 2, W // 2
centre = field[cy - 4:cy + 4, cx - 8:cx + 8].mean()
left = field[cy - 4:cy + 4, :4].mean()
right = field[cy - 4:cy + 4, -4:].mean()
top = field[:3, cx - 8:cx + 8].mean()
bot = field[-3:, cx - 8:cx + 8].mean()
corner = np.mean([field[:4, :4].mean(), field[:4, -4:].mean(),
                  field[-4:, :4].mean(), field[-4:, -4:].mean()])

# asymmetry has to come off the UNMIRRORED field - mirroring forces it to zero
raw_c = raw[cy - 4:cy + 4, cx - 8:cx + 8].mean()
raw_l = raw[cy - 4:cy + 4, :4].mean() / raw_c
raw_r = raw[cy - 4:cy + 4, -4:].mean() / raw_c


def stops(v):
    return float(np.log2(v / centre))


print(f'{len(fields)} clips, field normalised to centre = 1.000')
print(f'  left  edge  {left / centre:.3f}   {stops(left):+.2f} st')
print(f'  right edge  {right / centre:.3f}   {stops(right):+.2f} st')
print(f'  corners     {corner / centre:.3f}   {stops(corner):+.2f} st')
print(f'  top         {top / centre:.3f}   {stops(top):+.2f} st')
print(f'  bottom      {bot / centre:.3f}   {stops(bot):+.2f} st')
print(f'\nunmirrored left {raw_l:.3f} vs right {raw_r:.3f} -> asymmetry '
      f'{abs(raw_l - raw_r):.3f} absolute, '
      f'{abs(raw_l - raw_r) / max(1e-6, 1 - (raw_l + raw_r) / 2):.0%} of the falloff')
print('  (relative, not absolute, is the meaningful figure - and this is a GRADED\n'
      '   plate, so per-shot gains inflate it. For the optical/content verdict use\n'
      '   survey_vignette.py on the ungraded index, which fits properly.)')
print(f'horizontal falloff {abs(stops((left + right) / 2)):.2f} st vs '
      f'vertical {abs(stops((top + bot) / 2)):.2f} st')
