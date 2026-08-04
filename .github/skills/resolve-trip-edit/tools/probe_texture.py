"""Read whatever the API will surrender about the timeline's texture nodes.

OFX cannot be *added* through the scripting API, but if the settings of the ones
already on the approved timeline are readable they become the recommended values
rather than generic advice.
"""
import DaVinciResolveScript as dvr

TL = "WRO_Day1_EDIT"
resolve = dvr.scriptapp("Resolve")
proj = resolve.GetProjectManager().GetCurrentProject()
tls = {proj.GetTimelineByIndex(i).GetName(): proj.GetTimelineByIndex(i)
       for i in range(1, proj.GetTimelineCount() + 1)}
tl = tls[TL]
proj.SetCurrentTimeline(tl)
g = tl.GetNodeGraph()
print(f"{TL} timeline graph: {g.GetNumNodes()} nodes\n")

for i in range(1, g.GetNumNodes() + 1):
    print(f"--- node {i}")
    for m in ("GetNodeLabel", "GetToolsInNode", "GetLUT", "GetNodeEnabled",
              "IsNodeEnabled", "GetNodeCacheMode"):
        fn = getattr(g, m, None)
        if callable(fn):
            try:
                print(f"   {m}: {fn(i)!r}")
            except Exception as e:
                print(f"   {m}: <{type(e).__name__}: {e}>")

print("\nnode graph methods available:")
print("  ", sorted(m for m in dir(g) if not m.startswith("_")))

item = tl.GetItemListInTrack("video", 1)[0]
print("\ntimeline item methods mentioning fx/ofx/plugin:")
print("  ", sorted(m for m in dir(item) if any(k in m.lower() for k in ("fx", "plugin", "tool"))))
