"""Apply shoulder LUT + pivoted contrast + per-clip power to one camera's clips.

The full correction for a camera that reads dark and harsh next to the others:

  1. the shared highlight shoulder on clip node 1 - structural headroom every
     camera needs, and without it no lift is affordable
  2. a pivoted contrast reduction, `slope = c`, `offset = pivot*(1-c)`, which
     raises shadow input into a less compressive part of the look's toe while mid
     grey stays put (a flat offset big enough to move p10 hauls the whole image up)
  3. the per-clip power from solve_power.py, which sets the level

CDL order inside a node is `(in*slope + offset)^power`, so the softening lands
before the power lift, which is the order wanted.

`--wb` composes a per-clip white balance into the same node instead of erasing it.
One node holds ONE CDL and `SetCDL` replaces all of it, so a tone pass written on
its own silently wipes the balance - and with no `GetCDL` to read back, that
erasure is invisible. Slopes become `c * w` per channel, with `w` normalised to
geometric mean 1 so the balance stays chroma-only and does not disturb exposure.

`--power-scale` pre-compensates the level when stepping the contrast down again,
instead of re-probing: softening raises mean, and the shift scales with the step.
"""
import argparse
import json
import sys

sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/'
                'Developer/Scripting/Modules')
import DaVinciResolveScript as bmd  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('timeline')
ap.add_argument('items')
ap.add_argument('src')
ap.add_argument('plan', help='per-clip power plan from solve_power.py')
ap.add_argument('contrast', type=float)
ap.add_argument('pivot', type=float)
ap.add_argument('--power-scale', type=float, default=1.0)
ap.add_argument('--shoulder', default='')
ap.add_argument('--wb', help='per-clip WB plan to compose in, not overwrite')
a = ap.parse_args()

offset = a.pivot * (1.0 - a.contrast)
plan = {int(k): v for k, v in json.load(open(a.plan)).items()}
meta = {x['index']: (x.get('src') or '') for x in json.load(open(a.items))}

wb = {}
if a.wb:
    d = json.load(open(a.wb))
    for s in (d['shots'] if isinstance(d, dict) else d):
        if 'slope' in s:
            wb[s['index']] = s['slope']

p = bmd.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i)
       for i in range(1, p.GetTimelineCount() + 1)}
if a.timeline not in tls:
    sys.exit(f'no timeline named {a.timeline!r}')
tl = tls[a.timeline]
p.SetCurrentTimeline(tl)

ok = bad = balanced = 0
for i, it in enumerate(tl.GetItemListInTrack('video', 1) or []):
    if a.src not in meta.get(i, '') or i not in plan:
        continue
    pw = round(plan[i] * a.power_scale, 4)
    w = wb.get(i, [1.0, 1.0, 1.0])
    gm = (w[0] * w[1] * w[2]) ** (1.0 / 3.0)         # keep the balance chroma-only
    sl = [a.contrast * c / gm for c in w]
    if max(abs(c / gm - 1) for c in w) > 0.005:
        balanced += 1
    if a.shoulder:
        it.GetNodeGraph().SetLUT(1, a.shoulder)
    if it.SetCDL({'NodeIndex': '1',
                  'Slope': f'{sl[0]:.5f} {sl[1]:.5f} {sl[2]:.5f}',
                  'Offset': f'{offset:.5f} {offset:.5f} {offset:.5f}',
                  'Power': f'{pw} {pw} {pw}', 'Saturation': '1.0'}):
        ok += 1
    else:
        bad += 1

bmd.scriptapp('Resolve').GetProjectManager().SaveProject()
print(f'{a.src}: contrast {a.contrast} pivot {a.pivot} -> offset {offset:.4f}, '
      f'power x{a.power_scale}   applied {ok} failed {bad}'
      + (f', carrying per-clip WB on {balanced}' if a.wb else ', NO WB composed'))
if bad:
    print('failed writes usually mean a modal dialog is up - check get_page for null')
