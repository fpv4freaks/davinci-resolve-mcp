"""Render a timeline range to a small proxy for measurement.

Format and codec are set explicitly rather than via LoadRenderPreset, which can
wedge the application (see "Verified constraints").

This process normally exits with SIGSEGV *after* the render completes and prints
its status - a Resolve API teardown crash, not a failure. Chain follow-up steps
with `;` rather than `&&` or the measurement step silently never runs.

Usage: render_range.py <name> <markin> <markout> <outdir> [width] [height]
"""
import sys
import time

sys.path.append('/Library/Application Support/Blackmagic Design/DaVinci Resolve/'
                'Developer/Scripting/Modules')
import DaVinciResolveScript as bmd  # noqa: E402

name, mi, mo, outdir = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
w = int(sys.argv[5]) if len(sys.argv) > 5 else 960
h = int(sys.argv[6]) if len(sys.argv) > 6 else 400

p = bmd.scriptapp('Resolve').GetProjectManager().GetCurrentProject()
p.DeleteAllRenderJobs()
p.SetCurrentRenderFormatAndCodec('mov', 'H264')
p.SetRenderSettings({'MarkIn': mi, 'MarkOut': mo, 'SelectAllFrames': False,
                     'TargetDir': outdir, 'CustomName': name,
                     'FormatWidth': w, 'FormatHeight': h,
                     'ExportVideo': True, 'ExportAudio': False, 'VideoQuality': 6000})
job = p.AddRenderJob()
assert job, 'render job refused - check for a modal dialog (get_page returns null)'

t0 = time.time()
p.StartRendering(job, isInteractiveMode=False)
while p.IsRenderingInProgress():
    time.sleep(5)
print('status:', p.GetRenderJobStatus(job).get('JobStatus'),
      'in', round(time.time() - t0), 's ->', f'{outdir}/{name}.mov')
