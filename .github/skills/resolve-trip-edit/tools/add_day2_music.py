"""Lay day 2's music. Tail-aligned: the track's own outro lands on the final
frame of the film, which also drops its 180s breakdown mid-act."""
import os
import sys

sys.path.append(os.environ["RESOLVE_SCRIPT_API"] + "/Modules")
import DaVinciResolveScript as bmd  # noqa: E402

SRC = ("/Users/danielwojcik/Library/CloudStorage/OneDrive-Personal/shared/"
       "Creator/Audio/with-the-winds-volo-main-version-05-15-10020.mp3")
TL = "WRO_Day1_EDIT"
REC_START = 91082          # where day 1's music ends
REC_END = 96636 + 1        # timeline end frame, inclusive
TRACK = 2

resolve = bmd.scriptapp("Resolve")
proj = resolve.GetProjectManager().GetCurrentProject()
mp = proj.GetMediaPool()

tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
proj.SetCurrentTimeline(tls[TL])
tl = proj.GetCurrentTimeline()

folders = {f.GetName(): f for f in mp.GetRootFolder().GetSubFolderList()}
mp.SetCurrentFolder(folders.get("WRO_Day1", mp.GetRootFolder()))

existing = [c for c in mp.GetCurrentFolder().GetClipList()
            if (c.GetClipProperty("File Path") or "") == SRC]
clip = existing[0] if existing else mp.ImportMedia([SRC])[0]
print("clip:", clip.GetName())

# Audio clips leave "Frames" empty; the length only comes back as a timecode.
h, m, s, f = (int(x) for x in clip.GetClipProperty("Duration").split(":"))
total = ((h * 3600 + m * 60 + s) * 24) + f
need = REC_END - REC_START
start = total - need
print("clip frames: %d | need: %d | in-point: %d (%.1fs)"
      % (total, need, start, start / 24.0))
assert start >= 0, "track too short by %d frames" % -start

info = {
    "mediaPoolItem": clip,
    "startFrame": start,
    "endFrame": total,          # exclusive
    "recordFrame": REC_START,
    "trackIndex": TRACK,
    "mediaType": 2,
}
res = mp.AppendToTimeline([info])
print("append:", bool(res))

for it in tl.GetItemListInTrack("audio", TRACK) or []:
    src = it.GetMediaPoolItem()
    p = src.GetClipProperty("File Path") if src else ""
    if p.lower().endswith((".mov", ".mp4")):
        continue
    print("  A%d %-46s %d-%d  (%.1fs-%.1fs)"
          % (TRACK, os.path.basename(p)[:46], it.GetStart(), it.GetEnd(),
             (it.GetStart() - 86400) / 24.0, (it.GetEnd() - 86400) / 24.0))
