"""Audit per-clip grade preparation across a timeline, grouped by source.

Catches the failure this exists for: one camera silently missing a preparation
step while every other camera has it. Here GoPro reached a finished grade with no
highlight shoulder and no per-clip white balance, and nothing surfaced it until
the pictures were rejected twice.

Readable from the API: input colour space, node count, node-1 LUT, colour group,
ZoomY. NOT readable: CDL. `SetCDL` is write-only and there is no `GetCDL`, so the
balance a clip carries can only be known from the plan JSON that applied it -
which is why per-clip corrections must be journalled to disk, never just pushed.

Usage: audit_prep.py <timeline> <items.json> [plan.json ...]
"""
import json
import sys
from collections import defaultdict

sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/'
                'Developer/Scripting/Modules')
import DaVinciResolveScript as bmd  # noqa: E402

TL, ITEMS = sys.argv[1], sys.argv[2]
PLANS = sys.argv[3:]

meta = {x['index']: (x.get('src') or '?') for x in json.load(open(ITEMS))}


def plan_indices(obj):
    """Plan files vary in shape - flat index map, list of shots, or wrapped."""
    if isinstance(obj, dict):
        for key in ('shots', 'clips', 'items', 'plan'):
            if key in obj:
                return plan_indices(obj[key])
        out = set()
        for k, v in obj.items():
            if str(k).lstrip('-').isdigit():
                out.add(int(k))
            elif isinstance(v, (dict, list)):
                out |= plan_indices(v)
        return out
    if isinstance(obj, list):
        return {e['index'] for e in obj if isinstance(e, dict) and 'index' in e}
    return set()


planned = set()
for f in PLANS:
    planned |= plan_indices(json.load(open(f)))

p = bmd.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
tls = {p.GetTimelineByIndex(i).GetName(): p.GetTimelineByIndex(i)
       for i in range(1, p.GetTimelineCount() + 1)}
if TL not in tls:
    sys.exit(f'no timeline named {TL!r}')
tl = tls[TL]
p.SetCurrentTimeline(tl)

by = defaultdict(lambda: {'n': 0, 'cs': defaultdict(int), 'lut': defaultdict(int),
                          'nodes': defaultdict(int), 'grp': defaultdict(int),
                          'zoomy': defaultdict(int), 'planned': 0})
for i, it in enumerate(tl.GetItemListInTrack('video', 1) or []):
    s = by[meta.get(i, '?')]
    s['n'] += 1
    g = it.GetNodeGraph()
    n = g.GetNumNodes()
    s['nodes'][n] += 1
    luts = [(k, g.GetLUT(k)) for k in range(1, n + 1)]
    hit = [f'node{k}:{v}' for k, v in luts if v]
    s['lut'][', '.join(hit) if hit else '(none)'] += 1
    grp = it.GetColorGroup()
    s['grp'][grp.GetName() if grp else '(none)'] += 1
    mp = it.GetMediaPoolItem()
    s['cs'][(mp.GetClipProperty('Input Color Space') if mp else None) or '?'] += 1
    s['zoomy'][round(float(it.GetProperty('ZoomY') or 1.0), 3)] += 1
    if i in planned:
        s['planned'] += 1


def top(d):
    return ', '.join(f'{k} x{v}' for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:3])


print(f'timeline: {TL}\n')
for src, s in sorted(by.items()):
    print(f'--- {src}  ({s["n"]} clips)')
    print(f'    colour space : {top(s["cs"])}')
    print(f'    LUTs on graph: {top(s["lut"])}')
    print(f'    node count   : {top(s["nodes"])}')
    print(f'    colour group : {top(s["grp"])}')
    print(f'    ZoomY        : {top(s["zoomy"])}')
    if PLANS:
        print(f'    in plan files: {s["planned"]}/{s["n"]}')

print('\nfindings:')
bad = False
for src, s in sorted(by.items()):
    nolut = s['lut'].get('(none)', 0)
    if nolut:
        bad = True
        print(f'  {src}: {nolut}/{s["n"]} clips carry NO LUT on any node - '
              f'no highlight shoulder, so no lift is affordable on them')
    if len(s['cs']) > 1:
        bad = True
        print(f'  {src}: mixed input colour spaces - {dict(s["cs"])}')
    if PLANS and s['planned'] not in (0, s['n']):
        bad = True
        print(f'  {src}: only {s["planned"]}/{s["n"]} clips appear in the plan files - '
              f'a per-clip pass covered some clips but not all')
    if PLANS and s['planned'] == 0:
        bad = True
        print(f'  {src}: NO clips in any plan file - this source got no per-clip '
              f'correction (white balance and exposure are per clip, no source is exempt)')
if not bad:
    print('  none - every source carries the same preparation')
print('\nNOTE: CDL cannot be read back (SetCDL is write-only, there is no GetCDL).')
print('A later pass that writes a fresh CDL to the same node ERASES the balance')
print('already there, invisibly. Trust the plan files, and recompose rather than')
print('overwrite when applying a second correction to the same node.')
