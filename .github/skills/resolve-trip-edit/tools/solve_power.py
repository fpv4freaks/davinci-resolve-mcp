"""Solve a per-clip CDL power that brings one camera up to a reference level.

Power is the control for a camera that is dark with crushed blacks: it lifts
shadows and mids far more than highlights, so it fixes both at once, and the
highlight shoulder on clip node 1 absorbs what reaches the top. Offset and slope
were both measured and rejected - they move p99 an order of magnitude more than
p10, so they clip long before the shadows budge.

K_A/K_B describe `d(ln mean)/d(power)`, which is NOT constant - it tracks clip
brightness (measured -1.93..-2.99 across 46 clips on Marvel Olive). Re-fit per
look: render at two known powers, then
    k = (ln(m2) - ln(m1)) / (power2 - power1)
    K_A, K_B = numpy.polyfit(numpy.log(m1), k, 1)

Usage: solve_power.py <measure.json> <src_match> <out_plan.json>
                      [target_mean] [base_power] [strength] [prev_plan.json]
"""
import json
import sys

import numpy as np

MEASURE, SRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TARGET = float(sys.argv[4]) if len(sys.argv) > 4 else 0.290
BASE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.85
STRENGTH = float(sys.argv[6]) if len(sys.argv) > 6 else 0.80
PREV = sys.argv[7] if len(sys.argv) > 7 else None

FLOOR, CEIL = 0.62, 1.15
SKIP_BELOW = 0.06        # a near-black frame; lifting it only makes grey mush
K_A, K_B = 0.8203, -1.2665


def main():
    rows = [r for r in json.load(open(MEASURE)) if r['src'] and SRC in r['src']]
    if not rows:
        sys.exit(f'no clips matching src {SRC!r} in {MEASURE}')
    prev = ({int(k): v for k, v in json.load(open(PREV)).items()} if PREV else {})

    plan, pred, skipped = dict(prev), [], []
    for r in rows:
        m, base = r['mean'], prev.get(r['index'], BASE)
        if m < SKIP_BELOW:
            skipped.append(r['index'])
            plan.setdefault(r['index'], base)
            continue
        k = K_A * np.log(m) + K_B
        p = float(np.clip(base + STRENGTH * (np.log(TARGET) - np.log(m)) / k, FLOOR, CEIL))
        plan[r['index']] = p
        pred.append(m * np.exp(k * (p - base)))

    before = np.array([r['mean'] for r in rows if r['mean'] >= SKIP_BELOW])
    pred, pw = np.array(pred), np.array(list(plan.values()))
    print(f'clips {len(rows)}   skipped near-black {len(skipped)} {skipped}')
    print(f'power   median {np.median(pw):.3f}  min {pw.min():.3f}  max {pw.max():.3f}'
          f'  at floor {(pw <= FLOOR + 1e-6).sum()}')
    print(f'mean    {np.median(before):.3f} (sd {before.std():.3f})  ->  '
          f'{np.median(pred):.3f} (sd {pred.std():.3f})   target {TARGET}')
    print(f'still >25% below reference after fix: {(pred < TARGET * 0.75).sum()}')

    json.dump({str(k): v for k, v in plan.items()}, open(OUT, 'w'), indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
