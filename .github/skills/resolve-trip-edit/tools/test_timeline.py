"""Build a short grade-test timeline that samples the whole film.

Iterating a look against the full 7-minute timeline costs ~10 minutes a render.
This takes every Nth shot, 12 frames from its centre, into one ~20s timeline in
its OWN colour group - so the look LUT can be swapped freely without touching
either delivery timeline. Per-shot CDLs are copied so the test sees the same
image the real timelines do.
"""
import json, os, sys
import DaVinciResolveScript as dvr

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_TL = "WRO_GRADE_TEST"
TEST_GROUP = "WRO_TEST_Look"
EVERY = int(os.environ.get("EVERY", 4))
CHUNK = int(os.environ.get("CHUNK", 12))
POWER = 0.965
D1_BIN, D2_BIN = "01_Wroclaw_Day1", "02_Day2_SrebrnaGora_Lasowka"

resolve = dvr.scriptapp("Resolve")
proj = resolve.GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool()
tls = lambda: {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
               for i in range(1, proj.GetTimelineCount() + 1)}

if TEST_TL in tls():
    print(f"{TEST_TL} already exists - reusing")
    tl = tls()[TEST_TL]
    proj.SetCurrentTimeline(tl)
    print("items:", len(tl.GetItemListInTrack("video", 1) or []))
    sys.exit(0)

d1 = json.load(open(os.path.join(REPO, "tmp/wro_edit.json")))
d1 = d1.get("manifest") if isinstance(d1, dict) else d1
d2 = json.load(open(os.path.join(REPO, "tmp/day2_manifest.json")))
cdl1 = json.load(open(os.path.join(REPO, "tmp/cdl_v14.json")))
cdl2 = json.load(open(os.path.join(REPO, "tmp/day2_cdl.json")))

root = mp.GetRootFolder()
pool = {}
for f in root.GetSubFolderList():
    if f.GetName() in (D1_BIN, D2_BIN):
        for c in f.GetClipList():
            pool[c.GetName()] = c
print("pool clips:", len(pool))

shots = []
for i, s in enumerate(d1):
    shots.append({"name": s["name"], "start": s["start"], "dur": s["dur"],
                  "offset": cdl1[i]["offset"]})
for i, m in enumerate(d2):
    shots.append({"name": m["name"], "start": m["start"], "dur": m["tl_dur"],
                  "offset": cdl2[i]["offset"]})
print("total shots:", len(shots))

sel = [s for i, s in enumerate(shots) if i % EVERY == 0]
sel = [s for s in sel if s["name"] in pool]
print(f"selected: {len(sel)}  ({CHUNK} frames each = {len(sel)*CHUNK} frames, "
      f"{len(sel)*CHUNK/24:.1f}s)")

infos = []
for s in sel:
    mid = s["start"] + max(0, (s["dur"] - CHUNK) // 2)
    infos.append({"mediaPoolItem": pool[s["name"]], "startFrame": mid,
                  "endFrame": mid + CHUNK, "mediaType": 1})

tl = mp.CreateEmptyTimeline(TEST_TL)
assert tl, "CreateEmptyTimeline failed"
proj.SetCurrentTimeline(tl)
added = mp.AppendToTimeline(infos)
items = tl.GetItemListInTrack("video", 1) or []
print(f"appended: {len(added) if added else 0}   items: {len(items)}")
assert len(items) == len(sel), "item count mismatch"

groups = {g.GetName(): g for g in proj.GetColorGroupsList()}
grp = groups.get(TEST_GROUP) or proj.AddColorGroup(TEST_GROUP)
ok_g = ok_c = ok_z = 0
for it, s in zip(items, sel):
    if it.AssignToColorGroup(grp):
        ok_g += 1
    o = s["offset"]
    if it.SetCDL({"NodeIndex": "1", "Slope": "1 1 1",
                  "Offset": f"{o[0]:.6f} {o[1]:.6f} {o[2]:.6f}",
                  "Power": f"{POWER} {POWER} {POWER}", "Saturation": "1"}):
        ok_c += 1
    if s["name"].upper().endswith(".MOV"):          # Lumix needs the desqueeze
        it.SetProperty("ZoomGang", False)
        it.SetProperty("ZoomX", 1.0)
        if it.SetProperty("ZoomY", 0.751):
            ok_z += 1

print(f"grouped {ok_g}/{len(items)}  cdl {ok_c}/{len(items)}  desqueezed {ok_z}")
print("timeline:", tl.GetStartFrame(), "->", tl.GetEndFrame())
json.dump([s["name"] for s in sel],
          open(os.path.join(REPO, "tmp/test_shots.json"), "w"), indent=1)
