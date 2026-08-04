"""Install a baked look and point the test group at it. Run as its own process:
RefreshLUTList/SetLUT leave the calling session unable to queue a render job."""
import os, shutil, sys
import DaVinciResolveScript as dvr

NAME = sys.argv[1]
GROUP = sys.argv[2] if len(sys.argv) > 2 else "WRO_TEST_Look"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUT_DIR = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/MCP"

src = os.path.join(REPO, "tmp", f"{NAME}.cube")
assert os.path.exists(src), src
shutil.copy(src, os.path.join(LUT_DIR, f"{NAME}.cube"))

proj = dvr.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
proj.RefreshLUTList()
g = {x.GetName(): x for x in proj.GetColorGroupsList()}[GROUP].GetPostClipNodeGraph()
ok = g.SetLUT(1, f"MCP/{NAME}.cube")
live = g.GetLUT(1)
assert ok and live.endswith(f"{NAME}.cube"), f"LUT not applied: {live!r}"
print(f"{GROUP} -> {live}")
