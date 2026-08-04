"""Render the current timeline small+fast under a given output name."""
import os, sys, time
import DaVinciResolveScript as dvr

NAME = sys.argv[1]
TL = sys.argv[2] if len(sys.argv) > 2 else "WRO_GRADE_TEST"
OUTDIR = os.environ.get("OUTDIR", "/Volumes/Lexar/Export/_LOOKTEST")
W = int(os.environ.get("W", 960))
H = int(os.environ.get("H", 400))

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
proj.SetCurrentTimeline(tls[TL])

proj.DeleteAllRenderJobs()
settings = {
    "SelectAllFrames": True, "TargetDir": OUTDIR, "CustomName": NAME,
    "FormatWidth": W, "FormatHeight": H,
    "ExportVideo": True, "ExportAudio": False,
}
# Resolve refuses new render jobs for a while after a LUT list refresh, so poll.
job = ""
for attempt in range(15):
    proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
    proj.SetRenderSettings(settings)
    job = proj.AddRenderJob()
    if job:
        break
    time.sleep(3)
assert job, f"no render job for {NAME} after {attempt+1} attempts"
t0 = time.time()
proj.StartRendering(job, isInteractiveMode=False)
while proj.IsRenderingInProgress():
    time.sleep(2)
out = os.path.join(OUTDIR, f"{NAME}.mp4")
print(f"{NAME:26s} {proj.GetRenderJobStatus(job).get('JobStatus'):9s} "
      f"{time.time()-t0:5.1f}s  "
      f"{os.path.getsize(out)/1e6:.1f} MB" if os.path.exists(out) else "MISSING")
