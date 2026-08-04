"""PROCESS A: install a shoulder LUT and SetLUT it on clip node 1 of matching
clips. Must run in its OWN process — RefreshLUTList/SetLUT poison render queuing.

Usage: apply_shoulder.py <cube_path> <MODE> [name_prefix...]
  MODE = LUMIX   -> all V-Log (non-BRAW) clips
  MODE = NAMES   -> only clips whose name starts with one of name_prefix
  MODE = CLEAR   -> clear node-1 LUT on the selected clips (revert)
"""
import os, sys, shutil
sys.path.append(os.environ["RESOLVE_SCRIPT_API"] + "/Modules")
import DaVinciResolveScript as bmd  # noqa: E402

CUBE = sys.argv[1]
MODE = sys.argv[2]
PREFIXES = tuple(sys.argv[3:])
LUT_DIR = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/MCP"
os.makedirs(LUT_DIR, exist_ok=True)
name = os.path.basename(CUBE)
rel = "MCP/" + name
if MODE != "CLEAR":
    shutil.copy(CUBE, os.path.join(LUT_DIR, name))

p = bmd.scriptapp("Resolve").GetProjectManager().GetCurrentProject()
tl = p.GetCurrentTimeline(); TLS = tl.GetStartFrame()
print("RefreshLUTList:", p.RefreshLUTList())


def is_lumix(it):
    mp = it.GetMediaPoolItem()
    cp = (mp.GetClipProperty() if mp else {}) or {}
    return ".braw" not in str(cp.get("File Name", "")).lower()


def want(it):
    if MODE == "LUMIX":
        return is_lumix(it)
    if MODE in ("NAMES", "CLEAR"):
        return it.GetName().startswith(PREFIXES) if PREFIXES else False
    return False


def set_lut(it, path):
    g = it.GetNodeGraph()
    for target, args in ((g, (1, path)), (it, (1, path))):
        fn = getattr(target, "SetLUT", None)
        if callable(fn):
            try:
                if fn(*args):
                    return True
            except Exception:
                pass
    return False


n = 0
for it in tl.GetItemListInTrack("video", 1):
    if not want(it):
        continue
    ok = set_lut(it, "" if MODE == "CLEAR" else rel)
    n += 1
    if n <= 3 or not ok:
        print(f"  {'CLEAR' if MODE=='CLEAR' else 'SET'} {it.GetName()} r{it.GetStart()-TLS} -> {ok}")
print(f"{'cleared' if MODE=='CLEAR' else 'applied'} on {n} clips  ({rel})")
