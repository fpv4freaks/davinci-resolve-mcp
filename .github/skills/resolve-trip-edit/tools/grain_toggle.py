"""Does the Film Grain node actually contribute anything to the render?

There is no API to read an OFX's parameters or its enabled state, so infer it:
render a range, disable the grain node, render again, compare. Identical output
means the node is contributing nothing - disabled, or set to zero strength.

Runs on the Option-2 timeline so the approved cut is never modified, and restores
the node afterwards either way.
"""
import os, subprocess, statistics, io, time
from PIL import Image, ImageFilter
import DaVinciResolveScript as dvr

TL = "WRO_TRIP_OPT2_HOLLYWOOD"
IN_F, OUT_F = 88700, 88730
OUTDIR = "/Volumes/Lexar/Export/_GRAINTEST"
os.makedirs(OUTDIR, exist_ok=True)

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
tl = tls[TL]
proj.SetCurrentTimeline(tl)
g = tl.GetNodeGraph()
grain_node = next((i for i in range(1, g.GetNumNodes() + 1)
                   if (g.GetToolsInNode(i) or []) and "Grain" in str(g.GetToolsInNode(i))), None)
print("timeline:", TL, "| grain node:", grain_node,
      "| tools:", [g.GetToolsInNode(i) for i in range(1, g.GetNumNodes() + 1)])
assert grain_node, "no Film Grain node found"


def render(name):
    proj.DeleteAllRenderJobs()
    s = {"SelectAllFrames": False, "MarkIn": IN_F, "MarkOut": OUT_F,
         "TargetDir": OUTDIR, "CustomName": name,
         "FormatWidth": 3840, "FormatHeight": 1600,
         "ExportVideo": True, "ExportAudio": False}
    job = ""
    for _ in range(10):
        proj.SetCurrentRenderFormatAndCodec("mov", "ProRes422HQ")
        proj.SetRenderSettings(s)
        job = proj.AddRenderJob()
        if job:
            break
        time.sleep(3)
    assert job, f"no render job for {name}"
    proj.StartRendering(job, isInteractiveMode=False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    return os.path.join(OUTDIR, f"{name}.mov")


def hf(path, crop="500:400:1500:600"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.3", "-i", path,
                          "-frames:v", "1", "-vf", f"crop={crop}",
                          "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True).stdout
    im = Image.open(io.BytesIO(raw)).convert("L")
    px = list(im.getdata())
    bl = list(im.filter(ImageFilter.GaussianBlur(1.6)).getdata())
    return statistics.pstdev([a - b for a, b in zip(px, bl)])


a = render("grain_as_is")
print("grain node as-is  HF std:", round(hf(a), 3))

print("SetNodeEnabled(%d, False):" % grain_node, g.SetNodeEnabled(grain_node, False))
b = render("grain_off")
print("grain node OFF    HF std:", round(hf(b), 3))

print("restore:", g.SetNodeEnabled(grain_node, True))
c = render("grain_forced_on")
print("grain node ON     HF std:", round(hf(c), 3))

print("\nif as-is == OFF, the node was contributing nothing;"
      "\nif ON > OFF, the node works and was simply disabled or too weak")
