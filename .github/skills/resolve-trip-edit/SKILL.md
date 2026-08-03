---
name: resolve-trip-edit
owner: dwojcik
stream: technical
description: >
  Drive a DaVinci Resolve trip-film workflow end to end - ingest, colour-space
  alignment, anamorphic desqueeze, edit assembly, and the reference film grade.
  Use when the user points at a folder of camera clips, or says they are adding
  new clips to an existing edit.
argument-hint: "Path to the source clip folder; the skill asks about the material before cutting"
---

# Resolve trip edit

Take a folder of camera clips and carry it through to a graded master. Ask before
assuming; several steps below are only safe because they were measured, and the
failure modes are silent.

## Pick the mode first

- **New edit** - a fresh shoot with no existing timeline. Run steps 0-7.
- **Extend an existing edit** - the user says they are adding a clip or a folder
  to work that already exists. Jump to *Extend an existing edit*, then rejoin at
  step 6.

If it is not obvious which, ask. Appending to the wrong timeline is tedious to
unwind.

## Step 0 - source

Ask the user for the source folder if not supplied. Do not guess a path.

## Step 1 - probe before touching anything

Read metadata for every clip: `Video Codec`, `Resolution`, `PAR`, `FPS`,
`Camera Type`, `Lens Type`, `Focal Point (mm)`, `Date Recorded`, `Duration`.

Report a summary table. Two things decide the rest of the workflow:

- **which camera** -> sets the input colour space
- **whether the squeeze is already in metadata** -> decides desqueeze

## Step 2 - align to the working colour space

The project uses Resolve Colour Management (`davinciYRGBColorManagedv2`),
timeline space **DaVinci WG/Intermediate**, output **Rec.709 (Scene) / Gamma 2.4**.
Everything must land in DWG/Intermediate before grading.

Set per clip via `SetClipProperty('Input Color Space', ...)` (verified settable):

| source | Input Color Space |
|---|---|
| Blackmagic BRAW | `Blackmagic Design Film Gen 5` |
| Lumix S9, V-Log | `Panasonic V-Gamut/V-Log` |
| Lumix S9, standard profile | `Rec.709 Gamma 2.4` |

**If the camera is not recognised, STOP and ask.** A wrong input space is not a
subtle error and it will be blamed on the grade later.

Prefer V-Log on the Lumix. A standard profile has nowhere near BRAW's range and
will not match it.

## Step 3 - anamorphic desqueeze

BRAW carries the squeeze in metadata and desqueezes itself. Other cameras do not.

Do **not** use Inspector Zoom for this. Resolve represents the squeeze as the
clip's `PAR` property, and it is settable:

```python
clip.SetClipProperty('PAR', '1.33')   # returns True
```

That is exactly what BRAW does via metadata, it survives resolution changes, and
it leaves the transform controls free for reframing or stabilisation. Accepted
values include `Square`, `1.33`, `1.5`. `Anamorphic` is rejected.

**If the lens or squeeze factor cannot be determined, STOP and ask** for the
factor rather than assuming 1.33.

Verify afterwards by checking a known-round object in frame.

## Step 4 - understand the material

Before cutting, ask the user:

1. What is this footage - family trip, sightseeing, event, something else?
2. Is there a story shape, or is it impressionistic?
3. Target length?
4. Music mood, or should existing music be reused?
5. Anything that must be included or must not appear?

Pacing follows from the answers. A family trip wants faces held longer; a
sightseeing reel wants movement and rhythm.

## Step 5 - build the edit

Import, organise into a dated bin, build the timeline. `create_timeline_from_clips`
treats `endFrame` as **exclusive** - off-by-one here leaves 1-frame gaps on every
cut. Verify with a gap/overlap check before moving on.

## Step 6 - apply the reference grade

Architecture, in this order:

- **Clip node 1** - per-shot balance only (CDL). Nothing else enabled.
- **Group post-clip node 1** - `WRO_ShowLook_REFERENCE.cube`, the show look.

The reference bundle lives at
`/Volumes/Lexar/Export/WRO_Day1_GRADE_REFERENCE/` with the LUT, its bake recipe,
and the parameters.

Per-shot exposure values are **project specific** - do not reuse old CDL numbers.
Re-derive them:

1. Render, then measure per shot.
2. Pull exposure on shots whose highlights run hot - target **p99 around 0.93**.
   Use offset for this.
3. Restore midtones with CDL **power** (~0.965), not offset. Power leaves the top
   anchored, so it does not undo the highlight protection.
4. Re-measure and confirm: no shot mean luma above 0.42, max p999 below ~0.985.

Judge burn by **highlight spread**, not by counting clipped pixels. If p99 and
p999 are nearly equal, the highlights are piling against a ceiling and will read
as burnt even though nothing hits 255.

## Step 7 - texture, by hand

Grain, vignette and halation **cannot be scripted** - OFX cannot be added to a
node through the API at all. Tell the user to add them as nodes **after** the LUT
on the **group post-clip** level (the timeline graph has 0 nodes and is not a
usable target):

- node 2 halation
- node 3 vignette
- node 4 grain (last, so it is not smeared by the halation blur)

## Extend an existing edit

Used when the user says they are adding new clips to something already cut.

### E1 - recover the convention, then confirm it

Look for a `PROJECT_CONVENTION.json` beside the project's deliverables. If it is
missing, infer what you can from the timeline (shot count, duration, average shot
length, track layout, colour group, music) and say plainly that you are inferring.

**State the convention back and get a yes before cutting anything:**

> "Chronological family-trip day, 73 shots, 3:15, average shot 2.6s, Uppbeat
> music bed, 2383 print look on the group. Adding 12 clips from 20260803.
> Same convention?"

This is the step the user asked for by name. Do not skip it, and do not bury it
in a wall of other output.

### E2 - where do the new clips belong?

Ask, unless the convention already answers it:

- **Chronological** - interleave by `Date Recorded` / timecode. Default for trip
  footage covering the same period.
- **Appended** - a later day or a new chapter.
- **At a marked point** - user nominates a position.

### E3 - prepare the new clips

Same as steps 1-3: probe, set `Input Color Space`, set `PAR` if the squeeze is
not in metadata. New clips get no special treatment - they must match.

### E4 - cut to the established pacing

Measure the existing edit's average and median shot length and match it. A run of
noticeably longer or shorter shots reads as a different edit spliced in.

### E5 - fold into the existing grade

1. Assign every new clip to the **existing colour group**. Do not create a second
   group - the look must stay identical.
2. Derive CDL for the **new shots only**, targeting the same statistics as the
   existing ones: mean luma ~0.31-0.33, p99 ~0.93, nothing above 0.42.
3. Use the same power (~0.965) as the rest of the timeline.

Do not re-derive CDL for existing shots. They are approved; leave them alone.

### E6 - fix the music

**The music bed is frame-exact to the old duration.** Any change in length breaks
it, including the fade-out. Re-cut the bed to the new length and re-apply the
fade. Check licence terms still cover the new duration.

### E7 - verify before rendering

- no gaps or overlaps introduced at the insertion points
- new shots sit inside the same brightness envelope as the old ones
- audio bed runs to the new end with its fade intact

Then render, and measure the whole timeline - not only the new section. A new
clip can shift nothing else, but a mis-set input colour space or PAR shows up as
one shot that does not belong.

## Deferred - mixed sources in one timeline

**Not the active workflow.** Single camera per project is assumed throughout.
Recorded here so the reasoning does not have to be redone if it ever changes.

What already works without any structural change:

- `Input Color Space` and `PAR` are both **per clip**, so BRAW and Lumix can sit
  in one timeline and each be tagged correctly.
- CDL derivation is driven by measurement, not by camera, so exposure matching is
  already source-agnostic - both cameras get pulled to the same brightness
  envelope automatically.
- CDL offsets are per-channel, so the same mechanism can carry white-balance
  trims (currently only residual: mean channel spread 0.0032).

What would not be handled: same colour space is not the same look. Sensors differ
in spectral response, highlight rolloff and noise, so a systematic per-camera trim
would likely still be needed.

If that day comes, the structure changes like this:

```
BMCC → group "BMCC" → pre-clip: camera match ┐
                                              ├→ TIMELINE node 1: the look
S9   → group "S9"   → pre-clip: camera match ┘   nodes 2-4: grain/vignette/halation
```

The look moves **up** to timeline level. Keeping it on the groups would mean two
copies of the same look to maintain, which drifts. Note the timeline graph
currently reports **0 nodes** and the API cannot add them - that node has to be
created once in the UI.

Do not pre-build this. Start with one group and per-clip CDL, render, then measure
per-camera statistics. Split only if the data shows a systematic offset.

## Verified constraints - do not rediscover these

- **Resolve caches LUTs by filename.** Overwriting a `.cube` in place does *not*
  reload it. Always install under a new filename, or a render will silently use
  the old look while every measurement says it changed.
- **Display white is DI 0.5138**, not 0.500. A ceiling below ~0.50 crushes
  highlights flat - burnt-looking with zero clipped pixels.
- **DCTLs do not load in a node LUT slot** in this build. The resulting error
  dialog silently blocks *every* clip-level grade write, so `SetCDL`,
  `SetNodeEnabled` and DRX applies all start failing for no visible reason.
  Self-test: set the LUT, then read `resolve_control get_page` - `null` means a
  modal is up.
- **Clip-level DRX apply is refused once a clip is in a colour group.**
- **`drx.merge` silently strips OFX plugins**; `drx.generate` keeps them but
  authors only a single node.
- Many Resolve API calls **return `None` even when they succeed** (`OpenPage` is
  one). Verify by reading state back, never by trusting the return value.
- A creative LUT here is **DI in, DI out**. RCM still applies the Rec.709 output
  transform afterwards - a display-referred LUT would be transformed twice.

## Source media safety

Never modify, transcode, or derive camera originals. Analysis output goes to
sidecars or scratch. Clip properties (`PAR`, `Input Color Space`) are Resolve
database changes, not media changes, and are safe.
