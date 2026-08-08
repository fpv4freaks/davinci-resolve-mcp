"""Per-clip white balance measurement from a look-BYPASSED plate.

The look is a strong non-linear transform, so a cast measured through it cannot be
inverted back to a clip-level slope - that is what pushed WRO's shots into red.
Render the plate with the group's post-clip look node disabled, then measure here.

Reports R/G and B/G per clip against the shoot's own median, not against 1.0:
grey-worlding a graded film strips the look's character, and on a fixed-Kelvin
single-camera shoot the per-shot scatter (open shade, sun, cave) is the signal.

A slope is NOT the measured ratio. Ratios are display-referred; a CDL slope acts
in the log working space, so it must go through the calibrated response k:

    slope = (deviation ** damp) ** (1 / k)

Usage: measure_wb.py <plate.mov> <items.json> <out.json> [damp] [clamp] [k]
"""
import json
import subprocess
import sys

import numpy as np

PLATE, ITEMS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DAMP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.65     # BRAW row in the skill
CLAMP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.32
K = float(sys.argv[6]) if len(sys.argv) > 6 else 3.764       # Marvel Olive, WRO-probed

W, H = 240, 100
STRIDE = 4
LO, HI = 0.12, 0.65          # mid-tone mask; sky and shadow decide nothing here
EXTREME = 3.0                # beyond this the channel is too empty to gain back


def scan(items, start):
    edges = np.array([it['start'] - start for it in items] + [items[-1]['end'] - start])
    acc = [[] for _ in items]
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', PLATE, '-vf', f'scale={W}:{H}',
         '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
        stdout=subprocess.PIPE, bufsize=W * H * 3 * 8)
    n = 0
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        if n % STRIDE == 0:
            k = int(np.searchsorted(edges, n, side='right')) - 1
            if 0 <= k < len(items):
                rgb = np.frombuffer(b, dtype=np.uint8).reshape(-1, 3).astype(np.float32) / 255.0
                y = rgb @ np.array([.2126, .7152, .0722], dtype=np.float32)
                m = (y > LO) & (y < HI)
                if m.sum() > 200:
                    sel = rgb[m]
                    acc[k].append((sel[:, 0].mean(), sel[:, 1].mean(), sel[:, 2].mean(),
                                   float(y.mean()), float(m.mean())))
        n += 1
    p.stdout.close()
    p.wait()
    return [None if not r else np.array(r).mean(axis=0) for r in acc]


def main():
    items = json.load(open(ITEMS))
    rows = []
    for it, v in zip(items, scan(items, items[0]['start'])):
        if v is None:
            continue
        r, g, b, mean, cover = (float(x) for x in v)
        rows.append({'index': it['index'], 'name': it.get('name'), 'src': it.get('src'),
                     'mean': mean, 'midtone_cover': cover,
                     'rg': r / g, 'bg': b / g})
    if not rows:
        sys.exit('no clip produced a usable mid-tone sample')

    ref_rg = float(np.median([x['rg'] for x in rows]))
    ref_bg = float(np.median([x['bg'] for x in rows]))
    print(f'shoot reference (median of {len(rows)} clips, look bypassed): '
          f'R/G {ref_rg:.4f}  B/G {ref_bg:.4f}')

    for x in rows:
        # deviation >1 means the clip is warmer than the shoot, <1 cooler
        dev_rg, dev_bg = x['rg'] / ref_rg, ref_bg / x['bg']
        x['dev_rg'], x['dev_bg'] = dev_rg, dev_bg
        x['severity'] = ('extreme' if max(dev_bg, 1 / dev_bg) > EXTREME else
                         'moderate' if max(dev_bg, 1 / dev_bg) > 1.4 else 'mild')
        sr = (dev_rg ** -DAMP) ** (1 / K)
        sb = (dev_bg ** DAMP) ** (1 / K)
        sr, sb = (float(np.clip(s, 1 - CLAMP, 1 + CLAMP)) for s in (sr, sb))
        gm = (sr * 1.0 * sb) ** (1 / 3)      # normalise: WB must not move exposure
        x['wb_slope'] = {'r': sr / gm, 'g': 1.0 / gm, 'b': sb / gm}

    json.dump({'plate': PLATE, 'reference': {'rg': ref_rg, 'bg': ref_bg},
               'damp': DAMP, 'clamp': CLAMP, 'k': K,
               'k_note': 'k measured on WRO with the same look; re-probe on this '
                         'project before applying - it is a property of look+space',
               'clips': rows}, open(OUT, 'w'), indent=1)

    dev = np.array([max(x['dev_bg'], 1 / x['dev_bg']) for x in rows])
    print(f'B/G deviation: p50 {np.median(dev):.3f}  p90 {np.percentile(dev, 90):.3f}  '
          f'max {dev.max():.3f}')
    for s in ('mild', 'moderate', 'extreme'):
        n = sum(1 for x in rows if x['severity'] == s)
        print(f'  {s:9} {n:>4} clips')
    print('\nworst casts (dev_bg >1 = too warm/yellow, <1 = too cool/blue):')
    for x in sorted(rows, key=lambda x: -max(x['dev_bg'], 1 / x['dev_bg']))[:12]:
        s = x['wb_slope']
        print(f"  #{x['index']:<4}{(x['name'] or '')[:26]:<28}mean {x['mean']:.3f}  "
              f"R/G {x['rg']:.3f} B/G {x['bg']:.3f}  devB {x['dev_bg']:.2f}  "
              f"slope {s['r']:.3f}/{s['g']:.3f}/{s['b']:.3f}  {x['severity']}")
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
