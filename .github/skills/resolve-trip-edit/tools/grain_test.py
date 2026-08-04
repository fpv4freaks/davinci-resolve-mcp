"""Render a short range near-lossless, to test whether delivery compression is
eating the film grain rather than the grain never being applied."""
import os, time
import DaVinciResolveScript as dvr

TL = os.environ.get("TL", "WRO_Day1_EDIT")
IN_F, OUT_F = int(os.environ.get("IN_F", 86400)), int(os.environ.get("OUT_F", 86484))
OUTDIR = "/Volumes/Lexar/Export/_GRAINTEST"
NAME = os.environ.get("NAME", "grain_prores")
FMT = os.environ.get("FMT", "mov")
CODEC = os.environ.get("CODEC", "ProRes422HQ")

os.makedirs(OUTDIR, exist_ok=True)
proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
tl = tls[TL]
proj.SetCurrentTimeline(tl)
print("timeline:", tl.GetName(), "graph nodes:", tl.GetNodeGraph().GetNumNodes())
for i in range(1, tl.GetNodeGraph().GetNumNodes() + 1):
    print("  node", i, tl.GetNodeGraph().GetToolsInNode(i))

proj.DeleteAllRenderJobs()
settings = {
    "SelectAllFrames": False, "MarkIn": IN_F, "MarkOut": OUT_F,
    "TargetDir": OUTDIR, "CustomName": NAME,
    "FormatWidth": 3840, "FormatHeight": 1600,
    "ExportVideo": True, "ExportAudio": False,
}
job = ""
for _ in range(10):
    print("fmt:", proj.SetCurrentRenderFormatAndCodec(FMT, CODEC),
          "settings:", proj.SetRenderSettings(settings))
    job = proj.AddRenderJob()
    if job:
        break
    time.sleep(3)
assert job, "no render job"
proj.StartRendering(job, isInteractiveMode=False)
while proj.IsRenderingInProgress():
    time.sleep(2)
print("status:", proj.GetRenderJobStatus(job))
print("files:", [f for f in os.listdir(OUTDIR) if not f.startswith("._")])
