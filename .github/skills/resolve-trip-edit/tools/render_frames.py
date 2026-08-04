"""PROCESS B: render specific render-frames (1 frame each) of the current timeline
to a test dir, so a grade change can be measured. Fresh process (no SetLUT here).

Usage: render_frames.py <outdir> <rf> [rf ...]
"""
import os, sys, time
sys.path.append(os.environ["RESOLVE_SCRIPT_API"] + "/Modules")
import DaVinciResolveScript as bmd  # noqa: E402

OUTDIR = sys.argv[1]
RFS = [int(x) for x in sys.argv[2:]]
os.makedirs(OUTDIR, exist_ok=True)

p = bmd.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tl = p.GetCurrentTimeline(); TLS = tl.GetStartFrame()
p.DeleteAllRenderJobs()

jobs = []
for rf in RFS:
    tf = TLS + rf
    settings = {
        "SelectAllFrames": False, "MarkIn": tf, "MarkOut": tf,
        "TargetDir": OUTDIR, "CustomName": f"test_rf{rf}",
        "FormatWidth": 3840, "FormatHeight": 1600,
        "ExportVideo": True, "ExportAudio": False, "VideoQuality": 70000,
    }
    job = ""
    for _ in range(20):
        p.SetCurrentRenderFormatAndCodec("mov", "H264")
        p.SetRenderSettings(settings)
        job = p.AddRenderJob()
        if job:
            break
        time.sleep(2)
    assert job, f"render job refused for rf{rf}"
    jobs.append((rf, job))

t0 = time.time()
p.StartRendering([j for _, j in jobs], isInteractiveMode=False)
while p.IsRenderingInProgress():
    time.sleep(3)
for rf, job in jobs:
    st = p.GetRenderJobStatus(job)
    out = os.path.join(OUTDIR, f"test_rf{rf}.mov")
    print(f"rf{rf}: {st.get('JobStatus')}  {out}  exists={os.path.exists(out)}")
print("done %.0fs" % (time.time() - t0))
