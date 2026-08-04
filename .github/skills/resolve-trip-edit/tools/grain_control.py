"""Control test: does SetNodeEnabled do anything on a TIMELINE node graph?

The grain node measured identical with the node on and off, which has two very
different explanations - the grain is set to nothing, or timeline-graph toggling
simply does not work through the API. Halation is a visibly strong effect, so if
disabling it also changes nothing, the toggle is the thing that is broken.
"""
import os, subprocess, statistics, io, time
from PIL import Image
import DaVinciResolveScript as dvr

TL = "WRO_TRIP_OPT2_HOLLYWOOD"
IN_F, OUT_F = 88700, 88712
OUTDIR = "/Volumes/Lexar/Export/_GRAINTEST"

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
tl = tls[TL]
proj.SetCurrentTimeline(tl)
g = tl.GetNodeGraph()


def render(name):
    proj.DeleteAllRenderJobs()
    s = {"SelectAllFrames": False, "MarkIn": IN_F, "MarkOut": OUT_F,
         "TargetDir": OUTDIR, "CustomName": name,
         "FormatWidth": 1920, "FormatHeight": 800,
         "ExportVideo": True, "ExportAudio": False}
    job = ""
    for _ in range(10):
        proj.SetCurrentRenderFormatAndCodec("mov", "ProRes422HQ")
        proj.SetRenderSettings(s)
        job = proj.AddRenderJob()
        if job:
            break
        time.sleep(3)
    proj.StartRendering(job, isInteractiveMode=False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    return os.path.join(OUTDIR, f"{name}.mov")


def stats(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.2", "-i", path,
                          "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True).stdout
    im = Image.open(io.BytesIO(raw)).convert("L")
    px = sorted(im.getdata())
    n = len(px)
    return (sum(px) / n, px[int(n * 0.99)], px[int(n * 0.999)])


for label, hal, gr in (("both ON", True, True),
                       ("halation OFF", False, True),
                       ("both OFF", False, False),
                       ("restored", True, True)):
    print(f"  SetNodeEnabled(2,{hal}) -> {g.SetNodeEnabled(2, hal)}   "
          f"SetNodeEnabled(3,{gr}) -> {g.SetNodeEnabled(3, gr)}")
    m, p99, p999 = stats(render(f"ctl_{label.replace(' ', '_')}"))
    print(f"{label:14} mean {m:7.2f}   p99 {p99:4d}   p999 {p999:4d}")
