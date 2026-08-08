"""Per-clip luma statistics grouped by source camera, from a proxy render.

Answers "which camera is darker or harsher than the others" with numbers rather
than impressions. Watch `p10`: blacks crushed toward zero read as "too contrasty"
even when the `p90-p10` spread says the opposite, so a contrast metric alone can
contradict what the viewer is complaining about.

`items.json` is a list of `{index, start, end, src}` covering the rendered range,
where `src` tags the camera/run a clip came from.

Usage: measure_sources.py <proxy> <items.json> <start_frame> <span> [out.json] [ref_src]
"""
import json
import subprocess
import sys

import numpy as np

PROXY, ITEMS, START, SPAN = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
OUT = sys.argv[5] if len(sys.argv) > 5 else 'source_stats.json'
REF = sys.argv[6] if len(sys.argv) > 6 else None

W, H = 240, 100
STRIDE = 4          # sample every Nth frame; plenty for a per-clip average


def scan(items):
    edges = np.array([it['start'] - START for it in items] + [items[-1]['end'] - START])
    acc = [[] for _ in items]
    p = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', PROXY, '-vf', f'scale={W}:{H}',
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
                acc[k].append((y.mean(), np.percentile(y, 10), np.percentile(y, 90),
                               np.percentile(y, 1), np.percentile(y, 99),
                               (rgb >= 250 / 255.0).any(axis=1).mean() * 100))
        n += 1
    p.stdout.close()
    p.wait()
    return [None if not r else np.array(r).mean(axis=0) for r in acc]


def main():
    items = [it for it in json.load(open(ITEMS))
             if it['start'] >= START and it['end'] <= START + SPAN]
    if not items:
        sys.exit('no items in that range - check start/span against items.json')

    rows = []
    for it, v in zip(items, scan(items)):
        if v is None:
            continue
        mean, p10, p90, p1, p99, clip = (float(x) for x in v)
        rows.append({'index': it['index'], 'src': it.get('src'), 'mean': mean,
                     'p10': p10, 'p90': p90, 'p1': p1, 'p99': p99,
                     'contrast': p90 - p10, 'clip': clip})
    json.dump(rows, open(OUT, 'w'), indent=1)

    print(f"{'group':<14}{'n':>4}{'mean':>9}{'contrast':>11}{'p10':>8}{'p90':>8}{'p99':>8}{'clip%':>8}")
    stats = {}
    for g in sorted({r['src'] for r in rows if r['src']}):
        sub = [r for r in rows if r['src'] == g]
        stats[g] = (float(np.median([r['mean'] for r in sub])),
                    float(np.median([r['contrast'] for r in sub])),
                    float(np.median([r['p10'] for r in sub])))
        print(f"{g:<14}{len(sub):>4}{stats[g][0]:>9.3f}{stats[g][1]:>11.3f}"
              f"{stats[g][2]:>8.3f}{np.median([r['p90'] for r in sub]):>8.3f}"
              f"{np.median([r['p99'] for r in sub]):>8.3f}"
              f"{np.mean([r['clip'] for r in sub]):>8.3f}")

    if REF and REF in stats:
        rm, rc, rp = stats[REF]
        print(f'\nreference = {REF}: mean {rm:.3f}  contrast {rc:.3f}  p10 {rp:.3f}')
        for g, (m, c, p) in stats.items():
            if g == REF:
                continue
            print(f'  {g:<14} mean {m:.3f} ({"darker" if m < rm else "brighter"})'
                  f'   contrast {c / rc:.2f}x   p10 {p / rp if rp else float("nan"):.2f}x')
        dark = [r for r in rows if r['mean'] < rm * 0.75]
        print(f'\nshots more than 25% darker than the reference: {len(dark)}')
        for r in sorted(dark, key=lambda r: r['mean'])[:10]:
            print(f"   #{r['index']:<5}{r['src']:<14} mean {r['mean']:.3f}  p10 {r['p10']:.3f}")
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
