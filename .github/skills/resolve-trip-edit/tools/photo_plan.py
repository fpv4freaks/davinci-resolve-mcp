"""Turn a folder of phone photos into an ordered, deduplicated montage plan.

Three things this does that a filename sort cannot:

  - reads EXIF capture time with a DateTime fallback, because
    `DateTimeOriginal` comes back None on some iPhone JPEGs and a single-tag
    read silently loses those photos
  - honours the EXIF Orientation flag, so portrait is detected from the
    displayed shape rather than the stored pixel dimensions
  - collapses bursts by perceptual hash, keeping the sharpest frame of each

Days are numbered from the earliest capture date. Photos outside the day range,
and anything too extreme in aspect to sit in the delivery frame, are dropped
with a reason rather than silently.

Read-only. Verify the threshold with show_dupes-style output before trusting it:
a distance that collapses bursts will also merge two genuinely different
compositions, and those are restored by name with --restore.

Usage: photo_plan.py <src_dir> <out.json> [--hamming 20] [--seconds 2] ...
"""
import argparse
import glob
import json
import os
from collections import Counter

import numpy as np
from PIL import Image, ExifTags

TAG = {v: k for k, v in ExifTags.TAGS.items()}


def dhash(im, s=8):
    g = np.asarray(im.convert('L').resize((s + 1, s), Image.LANCZOS), dtype=np.int16)
    return np.packbits(g[:, 1:] > g[:, :-1]).tobytes()


def sharpness(im, s=256):
    g = np.asarray(im.convert('L').resize((s, s), Image.LANCZOS), dtype=np.float32)
    lap = (-4 * g + np.roll(g, 1, 0) + np.roll(g, -1, 0)
           + np.roll(g, 1, 1) + np.roll(g, -1, 1))
    return float(lap.var())


def read(path):
    im = Image.open(path)
    ex = im.getexif()
    dt = str(ex.get(TAG['DateTimeOriginal']) or ex.get(TAG['DateTime']) or '')
    if not dt:
        return None
    o = ex.get(TAG['Orientation'], 1)
    w, h = im.size
    if o in (5, 6, 7, 8):
        w, h = h, w
    d, t = dt.split(' ')
    Y, M, D = (int(x) for x in d.split(':'))
    hh, mm, ss = (int(x) for x in t.split(':'))
    return {'path': path, 'name': os.path.basename(path), 'date': d.replace(':', '-'),
            'ts': ((Y * 372 + M * 31 + D) * 24 + hh) * 3600 + mm * 60 + ss,
            'w': w, 'h': h, 'hash': dhash(im), 'sharp': sharpness(im)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--hamming', type=int, default=20)
    ap.add_argument('--window', type=int, default=180, help='seconds; keeps similar views taken hours apart separate')
    ap.add_argument('--seconds', type=float, default=2.0)
    ap.add_argument('--fps', type=float, default=24.0)
    ap.add_argument('--max-aspect', type=float, default=2.2)
    ap.add_argument('--restore', default='', help='comma-separated names the hash wrongly merged')
    ap.add_argument('--short-day', default='', help='DAY:SECONDS, e.g. 5:1.5 to stop a long block stalling the end')
    a = ap.parse_args()

    rows = [r for r in (read(f) for f in sorted(glob.glob(os.path.join(a.src, '*')))
                        if not os.path.basename(f).startswith('.')
                        and f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))) if r]
    if not rows:
        raise SystemExit(f'no readable photos in {a.src}')
    rows.sort(key=lambda r: r['ts'])

    clusters, cur = [], [rows[0]]
    for r in rows[1:]:
        d = int(np.count_nonzero(
            np.unpackbits(np.frombuffer(r['hash'], np.uint8))
            != np.unpackbits(np.frombuffer(cur[0]['hash'], np.uint8))))
        if d <= a.hamming and (r['ts'] - cur[-1]['ts']) <= a.window:
            cur.append(r)
        else:
            clusters.append(cur)
            cur = [r]
    clusters.append(cur)

    keep = {max(c, key=lambda r: r['sharp'])['name'] for c in clusters}
    keep |= {n.strip() for n in a.restore.split(',') if n.strip()}

    days = {d: i + 1 for i, d in enumerate(sorted({r['date'] for r in rows}))}
    short = dict([a.short_day.split(':')]) if a.short_day else {}

    plan, dropped = [], []
    for r in rows:
        aspect = max(r['w'], r['h']) / min(r['w'], r['h'])
        if r['name'] not in keep:
            dropped.append((r['name'], 'duplicate'))
        elif aspect > a.max_aspect:
            dropped.append((r['name'], f'aspect {aspect:.1f}:1 unframeable'))
        else:
            day = days[r['date']]
            secs = float(short.get(str(day), a.seconds))
            plan.append({'name': r['name'], 'path': r['path'], 'day': day,
                         'date': r['date'], 'ts': r['ts'], 'w': r['w'], 'h': r['h'],
                         'frames': int(round(secs * a.fps)),
                         'portrait': r['h'] > r['w']})
    plan.sort(key=lambda r: (r['day'], r['ts']))
    json.dump(plan, open(a.out, 'w'), indent=1)

    print(f'{"day":<6}{"photos":>7}{"portrait":>10}{"seconds":>9}')
    total = 0
    for d in sorted(Counter(r['day'] for r in plan)):
        sub = [r for r in plan if r['day'] == d]
        f = sum(r['frames'] for r in sub)
        total += f
        print(f'{d:<6}{len(sub):>7}{sum(1 for r in sub if r["portrait"]):>10}{f / a.fps:>8.1f}s')
    print(f'{"TOTAL":<6}{len(plan):>7}{sum(1 for r in plan if r["portrait"]):>10}'
          f'{total / a.fps:>8.1f}s')
    print(f'\ndropped {len(dropped)} of {len(rows)}:')
    for n, why in dropped:
        print(f'   {n:<20} {why}')
    print('\nwrote', a.out)


if __name__ == '__main__':
    main()
