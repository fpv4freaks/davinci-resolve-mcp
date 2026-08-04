"""Decisive grain check: same 20s range, grain node off then on, identical frames.
Any difference in high-frequency noise is the grain and nothing else."""
import os
import sys
import time

sys.path.append(os.environ["RESOLVE_SCRIPT_API"] + "/Modules")
import DaVinciResolveScript as bmd  # noqa: E402

TL = "WRO_Day1_EDIT"
GRAIN_NODE = 3
OUTDIR = "/Volumes/Lexar/Export/_VERIFY"
START, DUR = 88800, 480

proj = bmd.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
proj.SetCurrentTimeline(tls[TL])
g = proj.GetCurrentTimeline().GetNodeGraph()


def render(name):
    proj.DeleteAllRenderJobs()
    settings = {
        "SelectAllFrames": False, "MarkIn": START, "MarkOut": START + DUR - 1,
        "TargetDir": OUTDIR, "CustomName": name,
        "FormatWidth": 3840, "FormatHeight": 1600,
        "ExportVideo": True, "ExportAudio": False,
    }
    job = ""
    for _ in range(20):
        proj.SetCurrentRenderFormatAndCodec("mov", "ProRes422HQ")
        proj.SetRenderSettings(settings)
        job = proj.AddRenderJob()
        if job:
            break
        time.sleep(3)
    assert job, "no render job for " + name
    proj.StartRendering(job, isInteractiveMode=False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    print(name, "->", proj.GetRenderJobStatus(job).get("JobStatus"))


print("grain OFF:", g.SetNodeEnabled(GRAIN_NODE, False))
render("VERIFY_Look7_NOGRAIN")
print("grain ON :", g.SetNodeEnabled(GRAIN_NODE, True))
print("done - node restored")
