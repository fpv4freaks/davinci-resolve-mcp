---
name: resolve-trip-edit
owner: dwojcik
stream: technical
description: >
  Drive a DaVinci Resolve trip-film workflow end to end - ingest, colour-space
  alignment, anamorphic desqueeze, edit assembly, and the reference film grade.
  Carries a library of eight named film looks and the tooling to profile a new
  reference film and bake it into a LUT. Use when the user points at a folder of
  camera clips, says they are adding new clips to an existing edit, or asks for a
  different grade or a look taken from a film.
argument-hint: "Path to the source clip folder; the skill asks about the material before cutting"
---

# Resolve trip edit

Take a folder of camera clips and carry it through to a graded master. Ask before
assuming; several steps below are only safe because they were measured, and the
failure modes are silent.

## Pick the mode first

- **New edit** - a fresh shoot with no existing timeline. Run steps 0-8.
- **Extend an existing edit** - the user says they are adding a clip or a folder
  to work that already exists. Jump to *Extend an existing edit*, then rejoin at
  step 6.
- **Change the look** - the user names a look, or asks for a different grade.
  Go to *The look library*, then step 8.
- **Render** - the user asks for a master. Go straight to step 8; never render
  without running that hand-off first.

If it is not obvious which, ask. Appending to the wrong timeline is tedious to
unwind.

**Every path ends at step 8.** Grain and halation are hand-work, so a render
started without asking ships a master with no texture.

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

A correct input space is necessary but **not sufficient**: a second camera's log
highlights still need a per-clip shoulder before the look, or they blow to white.
See *Mixed sources in one timeline*.

## Step 3 - anamorphic desqueeze

BRAW carries the squeeze in metadata and desqueezes itself - nothing to do.

**Lumix S9 (and any non-BRAW) footage arrives still squeezed.** It must be
desqueezed manually. Metadata will not tell you: the files report `SAR 1:1`,
`DAR 16:9` and carry no squeeze flag whatsoever.

**Always ask which squeeze factor was used. Default 1.33x.** Do not apply one
silently, and do not assume the factor.

### The transform - verified on real footage

Compress the **Y** axis by `1 / factor`. For 1.33x that is **0.751**:

```python
item.SetProperty('ZoomGang', False)   # MUST come first
item.SetProperty('ZoomX', 1.0)
item.SetProperty('ZoomY', 0.751)      # 1 / 1.33
```

`ZoomGang` is the chain-link icon between X and Y in the Inspector. It defaults
to `True`, and **while it is on, setting `ZoomX` silently changes `ZoomY` too** -
producing a uniform shrink rather than a desqueeze. Unlink first, every time.

Use **Y**, not X. Compressing Y stretches the image horizontally in relative
terms, which is the desqueeze, and it lands a 16:9 source at ~2.36:1 so it fills
a 2.40:1 timeline with almost no crop. Setting `ZoomX` to 0.751 instead makes the
picture *narrower* - black bars down both sides and everything squashed. That is
the single easiest mistake to make here.

### Verify before committing a whole shoot

Render three short versions of the same clips - untouched, `ZoomY` applied, and
`ZoomX` applied - and have the **user** judge them on a real monitor.

Do not settle this from stills yourself. It was attempted on this footage using
bottles, drinking glasses, log ends and arches as references, and the conclusion
was **wrong**: 1.33x is subtle enough that objects still look plausible squeezed,
and the person who was there recognises the faces and proportions instantly. Ask.

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

- **Clip node 1** - per-shot balance (CDL). Add a **highlight shoulder** here too
  for any clip whose DI highlights run past the look's ~0.50 clip - mandatory for
  log / second-camera clips (see *Mixed sources in one timeline*). The primary
  BRAW clips carry this as a "FILM SHOULDER" node; a bare second-camera clip has
  nothing and will blow its highlights straight through the look.
- **Group post-clip node 1** - the show look, one `.cube`.

The house look is `WRO_ShowLook_REFERENCE_v2.cube`, built on Resolve's bundled
Kodak 2383 D60 print emulation, softened with `CONTRAST_SCALE = 0.92`. That
scales luma about the pivot and shifts all three channels equally, so the
warm/cool separation is untouched, and it tapers out below the toe so blacks are
not lifted into a haze. The full-strength 2383 curve read too contrasty.

Seven alternatives are built and ready - see *The look library* below. Offer
them; do not assume the house look unless the user has already chosen.

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

## The look library

Eight looks, each a single `.cube` on the group's post-clip node. Swap one for
another and nothing else in the grade changes. `tools/` and `profiles/` beside
this file rebuild any of them exactly; the baked cubes live in
`/Volumes/Lexar/Export/WRO_LOOK_OPTIONS/looks/`, 20s samples and a labelled grid
in `/Volumes/Lexar/Export/WRO_LOOK_SAMPLES/`.

| # | Name | Character |
|---|---|---|
| 1 | Print 2383 | warm, rich, deep blacks, highlights held back. Photochemical. **The approved house look.** |
| 2 | Marvel | clean and restrained; milky lifted toe, speculars to white, half the warmth of 1 |
| 3 | Equalizer | crushed blacks, cool steel exteriors, warm practicals. Urban, grim |
| 4 | Burnt | pale, cool, low saturation, softest highlights. European drama |
| 5 | Ferrari | sun-baked; strongest warm cast, high contrast, blown windows. 1960s California |
| 6 | Silo | Marvel + green-grey. Cool, industrial |
| 7 | Marvel Olive | Marvel + olive; blue pulled harder than red, softer, less colour |
| 8 | Blade Runner | amber with blue crushed hard, saturated, softest roll-off measured |

Looks 1 and 2 are hand-built (`bake_2383.py`, `bake_hollywood.py`). Looks 3-8 are
profile transfers (`bake_look.py`), so they carry a measured film's tone curve,
colour trace and saturation rather than an opinion. Recipes, exactly as shipped:

```
3 Equalizer   bake_look profiles/profile_EQ2_daylight.json
              COLOR_S=0.52 SAT_S=0.9 DELTA_MAX=0.026
4 Burnt       bake_look profiles/profile_BURNT_daylight.json
              COLOR_S=0.45 SAT_S=0.8 DELTA_MAX=0.026 CONTRAST=0.94
              MIN_BLACK=0.028 MAX_WHITE=0.935
5 Ferrari     bake_look profiles/profile_FVF_daylight.json
              COLOR_S=0.60 SAT_S=0.85 DELTA_MAX=0.030
              MIN_BLACK=0.014 MAX_WHITE=0.985
6 Silo        blend_profile CM + JOKER  MIX=0.45 SAT_MIX=0.88
              bake_look  COLOR_S=0.65 SAT_S=0.9 DELTA_MAX=0.030
              MIN_BLACK=0.020 MAX_WHITE=0.960
7 MarvelOlive blend_profile CM + JOKER  MIX_RG=0.30 MIX_BG=0.50 SAT_MIX=0.85
              bake_look  COLOR_S=0.60 SAT_S=0.9 DELTA_MAX=0.028 CONTRAST=0.93
              MIN_BLACK=0.018 MAX_WHITE=0.955
8 BladeRunner bake_look profiles/profile_BR2049_daylight.json
              COLOR_S=0.50 SAT_S=0.85 DELTA_MAX=0.032
              MIN_BLACK=0.030 MAX_WHITE=0.940
```

### Adding a look from a film

1. **Profile the reference's DAYLIGHT frames only** -
   `film_profile_daylight.py <film> <label> 600 0.22 0.45`. A film's overall
   darkness is its *content*, not its look: Captain Marvel means 0.201 because
   half of it is space, against 0.307 for its daylight frames alone. Match the
   whole film and a sunny holiday turns into a night scene.
2. **Check the encode before trusting it.** Burned-in subtitles are white text
   and land in the top luma bin, faking a hot roll-off - crop them with `CROP`.
   A screener will have stretched contrast: Ford v Ferrari (823 kbps) clips 5%
   of pixels and crushes p5 to 0.004, which is compression damage, not a grade.
   Temper with `MIN_BLACK` / `MAX_WHITE` or you bake the artefacts in.
3. **Look at reference frames** (`ref_sheet.py`) before believing the numbers.
4. Bake, then iterate on the 20s test reel - about 10s a render.
5. **Verify, then look again.** Both, in that order, and neither alone.

### Rules the numbers do not tell you

- **An average colour error can be fine while the picture is wrong.** Equalizer
  scored 0.048 - a good number - with a cyan sky. Memory colours decide a look:
  sky, skin, foliage, white. Always put frames on screen.
- **Check the TOP luma bins, not just the mids.** A cast applied across the whole
  range turns whites the cast colour - gravel, shirts, paper. Burnt's whites hit
  R-G -0.102 against a -0.043 reference while its midtones measured perfectly.
  `WP_START` / `WP_END` / `WP_FLOOR` fade the shift out toward white; that is the
  difference between a look and a tint.
- **Apply colour after tone and saturation**, scaled by the tone ratio and solved
  against the post-saturation trace. Applied before, it lands 3-4x too strong and
  re-adds the chroma the saturation step just removed.
- **A global channel shift inflates measured saturation**, because it colours
  neutral greys. Clamp it (`DELTA_MAX` 0.02-0.03) and keep `COLOR_S` near 0.3-0.6
  for a strong cast.
- **Anchor the top of the tone curve at `MAX_WHITE`, not 1.0.** Ending at 1.0
  lets pure white through untouched however soft the reference rolls off - that
  single line was every blown window in Burnt (0.841% flat-white to 0.000%).
- Highlights are recoverable far more often than they look: the ungraded baseline
  reads 3.34% flat-white where Print 2383 reads 0.001%. Never conclude "the source
  clipped" from the neutral render - it is bright by construction, because the
  per-shot CDLs assume a look LUT sits after them.

### Swapping the look on a timeline

Give each variant **its own colour group**. Groups are project-level, so editing
a shared group's LUT repaints every timeline using it - including the approved
one. `install_look.py <cube> <group>` copies, refreshes and sets in one step.

Keep a `WRO_GRADE_TEST` timeline (`test_timeline.py`: every Nth shot, 12 frames,
its own group) for iteration. It renders in about 10 seconds against 10 minutes
for the full cut. It carries no grain - OFX is not scriptable - which is equal
across every look, so comparisons stay fair.

## Step 7 - texture, by hand

Grain, halation and vignette **cannot be scripted** - OFX cannot be added to a
node through the API at all. The user adds them on the **timeline** node graph,
which holds 0 nodes until they create them.

Order matters, and this is the physical chain: lens shading first, then emulsion
effects, grain last so it is not smeared by the halation blur.

- vignette (optional - **omitted on this project by choice**)
- halation
- grain, always last

Ask which the user wants rather than assuming all three. Confirm by reading the
node graph back before rendering: `GetToolsInNode` on the timeline graph reports
what is actually loaded, and an empty node reads as `None`.

On the approved cut that reads:

```
node 1  None                 (empty)
node 2  ['OFX: Halation']
node 3  ['OFX: Film Grain']
```

`GetToolsInNode` returns the plugin *name* only - there is no OFX parameter
reader, so previous settings cannot be recovered from the project. If the user
dials in values worth keeping, write them down; nothing else will.

## Step 8 - stop before rendering and hand off

**Never start a master render without doing this first.** It applies whenever the
user asks for a render, and whenever new clips have been added and a look chosen.
Grain, halation and vignette cannot be scripted, so a render fired off silently
ships a master with no texture - and it looks fine in stills, which is how it
gets missed.

Prepare everything else first - clips in, desqueezed, grouped, CDLs derived, look
LUT set, render settings staged - then stop and tell the user, in this shape:

> Everything is ready to render: 159 shots, 7:06, look = *Marvel*, delivery
> `2.4-1.4K.70M`.
>
> **The timeline node graph is still empty, so this render would have no texture.**
> Add these by hand on the timeline graph (Color page, timeline clip selected),
> in this order, then tell me to go:
>
> 1. **Halation** - node 2
> 2. **Film Grain** - node 3
>
> Recommended starting points below. Or say "render without texture" and I will.

Confirm with `GetToolsInNode` after they say go. Do not take "done" on trust -
the check costs one call and catches an effect added to the wrong graph.

### Verify the texture actually reached the render

`GetToolsInNode` proves a plugin is *present*. It does not prove it is *doing
anything*, and on this project it was not: the approved master carries an
`OFX: Film Grain` node that contributes exactly zero. Measured, not guessed -

```
timeline mean, same frames, ProRes 422 HQ
  halation ON  + grain ON    49.67
  halation OFF + grain ON    49.21     <- halation works
  halation OFF + grain OFF   49.21     <- grain changes nothing at all
```

Disabling halation moves the image, so `SetNodeEnabled` works on a timeline
graph; disabling grain moves nothing. High-frequency noise in flat areas sits at
1.2-1.5 where visible 4K grain would read 3-8, and a near-lossless ProRes render
of the same frames has *no more* fine detail than the 70 Mbps H.264 (ratio 0.81),
so delivery compression is not the culprit either.

To test any texture effect, in order:

1. Render a few seconds **ProRes 422 HQ at full raster** - never judge grain from
   a scaled preview or a compressed proxy; both destroy it.
2. Crop 1:1 (`crop=520:400:...`) from a flat area - sky, wall, water - and look.
3. `SetNodeEnabled(n, False)`, render again, compare. Identical output means the
   node contributes nothing.
4. Always toggle a **known-good** node as a control. Without the halation control
   above, "grain off changes nothing" would have been indistinguishable from
   "timeline-graph toggling does not work".

If grain measures zero, the likely causes, in order: its strength or blend is at
zero; **the node is not wired into the chain** (a node can sit in the graph
unconnected - the API cannot read wiring, so check it on the Color page); or the
effect was added to a clip graph rather than the timeline graph.

There is no OFX parameter reader in the API, so none of this can be diagnosed
from settings - only from rendered pixels.

Two ways to measure this wrongly, both of which produced a confident wrong answer
here before being caught:

- **Compare like with like.** Noise measured on an H.264 master against a ProRes
  reference says nothing about grain - 70 Mbps H.264 already carries only ~0.81x
  the high-frequency detail of ProRes on the same frames, so the grainy file can
  measure *lower*. Same codec, same bitrate, same timecodes, or the number is
  meaningless. Two different timecodes is the same error wearing a hat.
- **Grain adds in quadrature**, being independent noise: its own magnitude is
  `sqrt(on**2 - off**2)`, not `on - off`. Subtracting the standard deviations
  understates it badly - 2.947 vs 2.301 is a grain RMS of 1.84, not 0.65.
- **A highlight shoulder hides grain from this measurement.** Measuring a bright
  crop on shouldered clips read 1.00x and 0.78x against a grainless reference,
  while unshouldered clips in the same render read 1.11x-1.72x - the shoulder
  rolls off exactly the highlight micro-contrast the test samples. Measure grain
  in mids and shadows, and check which clips carry a shoulder LUT before reading
  anything into a flat result.

### Recommended settings

Starting points for 3840x1600 at 24p, tuned for a family film that should read as
photochemical rather than as an effect. Resolve's defaults are built for a 1080p
timeline and are consistently too strong at this raster.

These are craft starting points, **not** recovered from the project - there is no
way to read an OFX's parameters back. The authoritative control reference is the
[DaVinci Resolve 21 manual](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_21_Reference_Manual.pdf);
control names shift between versions, so dial by eye against a 1:1 crop and
verify with the toggle test above.

**Film Grain** (last in the chain, so the halation blur cannot smear it)

| control | value | why |
|---|---|---|
| preset | `35mm` | 16mm is too coarse at 4K, 65mm too fine to register |
| grain size | 0.4 - 0.6 | the default reads as noise at this raster |
| shadow strength | ~0.35 | grain lives in the shadows and low mids |
| midtone strength | ~0.25 | |
| highlight strength | ~0.10 | dense highlights suppress grain on real stock |
| saturation | 0.3 - 0.5 | near-monochrome grain reads filmic; coloured speckle reads digital |
| blend / mix | 0.5 - 0.7 | full strength is a period effect, not a finish |

**Halation** (before grain)

| control | value | why |
|---|---|---|
| threshold | 0.75 - 0.85 | only genuine highlights should bloom |
| size / spread | 0.15 - 0.30 | |
| strength | 0.15 - 0.25 | above ~0.4 it reads as fog over the whole image |
| tint | warm red-orange | the physical effect is red light scattering off the film backing |

With **Print 2383** or **Ferrari** the image is already warm - keep halation at
the bottom of that range or the warmth compounds. With **Equalizer**, **Burnt**
or **Silo** the warm bloom is what stops a cool look going clinical, so the top
of the range suits them.

**Vignette** (first, if used at all - it is lens shading, so it belongs before the
emulsion effects)

| control | value | why |
|---|---|---|
| size | 0.7 - 0.8 | |
| softness | 0.5 - 0.6 | |
| strength | -0.15 to -0.25 | subtle darkening; anything stronger draws attention |

Check roundness on a 2.4:1 frame: a circular falloff darkens the short edges long
before the corners. **Omitted on this project by choice** - offer it, do not add it.

### Render settings

`2.4-1.4K.70M` - 3840x1600, 24p, QuickTime H.264 ~70 Mbps, PCM 16-bit 48 kHz.
Render mode **1** (single clip); mode 0 is *individual clips* and quietly writes
one file per shot. Set format, codec and settings explicitly rather than calling
`LoadRenderPreset`, which can wedge the application (see *Verified constraints*).

After the render, measure the whole timeline, not only the new part.

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
2. Derive CDL for the **new shots only**.
3. Use the same power (~0.965) as the rest of the timeline.

Do not re-derive CDL for existing shots. They are approved; leave them alone.

**Match the existing day's brightness DISTRIBUTION, not a single target mean.**
Driving every new shot toward one number ("mean luma ~0.32") converges the whole
day onto that number and kills its tonal variety. Measured on the 20260803
ingest: the approved day spanned 0.166-0.435 with an IQR of 0.098, while the new
day had collapsed to an IQR of **0.015** - statistically "on target", visually
monotone next to it.

Do this instead:

1. Measure per-shot mean luma of the **approved master** - that is the reference
   distribution, not the aspiration written in a convention file.
2. Rank each new shot by its **ungraded** brightness, and give it the approved
   day's brightness at the same fractional rank. Relative light is preserved (the
   darkest tunnel stays the darkest shot) and the spread becomes the reference
   spread by construction.
3. Solve the offset in one step from a measured slope. Verify by re-rendering and
   comparing min/p25/median/p75/max/IQR against the reference.

Two traps in the solve:

- **A measured slope is only trustworthy when the step that produced it was
   large.** Dividing a small luma delta by a small offset delta amplifies noise
   into wild corrections. Require `|Δoffset| >= 0.02` before trusting it, clamp
   the slope to a sane band, and keep the previous offsets so a bad pass can be
   backed out.
- **Do not white-balance by matching channel means.** It neutralises real scene
   colour - warm fortress brick gets "corrected" to cyan. The approved day's own
   CDLs kept per-channel deviation to ~0.004; leave native balance alone.

Highlights are the exception - `p99` and clipping ARE hard limits, not a
distribution to match. Keep p999 under ~0.985.

### E6 - fix the music

**The music bed is frame-exact to the old duration.** Any change in length breaks
it, including the fade-out. Re-cut the bed to the new length and re-apply the
fade. Check licence terms still cover the new duration.

**Check the original download still exists before promising to extend it.** A bed
rendered out to the old length, with its fade baked in, cannot be lengthened from
itself - and the source it came from may be long gone. If it is missing, say so
and offer the real choices (supply a second cue / accept a looped reprise / ship
on nat sound); do not invent a musical judgement you cannot verify by listening.

Nat sound is the fallback worth checking: internal BRAW audio is often unusable
(~-49 dB), but Lumix PCM has come in at -22.7 dB mean / -4.2 dB peak - fine as a
real bed. Put it on its own named track so it can be muted without disturbing the
approved day.

**Match the level to the bed already on the timeline, never to the source track.**
The prepared day 1 bed measured **-14.4 LUFS** against **-10.2** for the mp3 it
came from - it had been pulled down 4.2 dB. A second cue dropped in at unity
(-10.5 LUFS) would have played ~4 dB louder than day 1, at the act change, where
it is most audible. Measure the existing `.wav` with `ebur128`, measure the
section you are about to use, and apply the difference as a fixed `volume=NdB`.
A fixed gain preserves the dynamics; `loudnorm` will not.

**Place a cue tail-aligned when it has to end with the film.** Read the track's
energy envelope in 10s blocks first, then start it at `len - need` so its own
outro lands on the final frame instead of fading out mid-phrase. On a 316s track
against a 231.4s hole this also dropped the track's natural breakdown into the
middle of the act. Check the handover measures clean afterwards: day 1 fading to
-30.8 dB into day 2 entering at -18.2 dB is a cut you cannot hear.

**`-ss` before `-i` seeks inaccurately on mp3** - asking for 84.5s produced a
file starting ~20s early *and* the wrong length, while reporting success. Decode
to wav first, then cut with `atrim=start_sample=`, and verify the result is the
exact frame count you need (`duration * fps`) before laying it.

### E7 - verify before rendering

- no gaps or overlaps introduced at the insertion points
- new shots sit inside the same brightness envelope as the old ones
- audio bed runs to the new end with its fade intact

Then go to **step 8** - confirm the look, hand off the texture work, and only
render once the user says go. Measure the whole timeline afterwards, not only the
new section. A new clip can shift nothing else, but a mis-set input colour space
or PAR shows up as one shot that does not belong.

## Mixed sources in one timeline - ACTIVE, verified

**This is now a real workflow** (20260803 cut: Day 1 BMCC BRAW + Day 2 Lumix S9
V-Log in one timeline, one look). Single-camera is no longer a safe assumption -
detect a second camera in Step 1 and handle its highlights explicitly.

### Highlight handling is per camera, and it is mandatory

Correct `Input Color Space` per clip is necessary but **not sufficient**. The show
look is DI-in/DI-out and clips flat at DI ~0.50 (see constraints). The primary
BRAW clips carry a per-clip highlight shoulder ("04 FILM SHOULDER" node) that
holds highlights under that ceiling. A second camera dropped in as a single bare
node has no shoulder, so its V-Log highlights arrive well above 0.50 and render as
flat white - even though the source holds full detail.

Measured on the real cut, worst Lumix shot: source V-Log peaks 205/255 with **0%
clipped**, but the v14 grade clipped a channel across **14% of the frame** and
back-lit hair became a featureless yellow blob. The BMCC never passed ~9% on its
brightest frame, because of its shoulder. Fixed in v15 (below) -> ~0% clipped.

**Symptom / diagnosis / fix:**

- *Symptom* - one camera's bright regions blow to white; the other is fine.
- *Diagnose* - compare clip-node COUNT per camera (the primary has a shoulder
  node; the second camera is a single empty node); scan the render for
  per-channel clip% split by each camera's frame range; confirm the second
  camera's SOURCE is not clipped (peaks well below 255) so the loss is in the
  grade and recoverable.
- *Fix* - give every second-camera clip its own highlight shoulder at **clip
  node 1, before the group look**. Bake a per-channel DI shoulder LUT and
  `SetLUT` it on each clip:

  ```
  python tools/bake_highlight_shoulder.py shoulder.cube 0.42 0.49   # knee, ceiling
  python tools/apply_shoulder.py shoulder.cube LUMIX                 # all non-BRAW clips
  # render in a SEPARATE process (SetLUT/RefreshLUTList poison the render queue):
  python tools/render_frames.py /scratch 7320 5896 9976             # QC frames first
  ```

  Knee 0.42 / ceiling 0.49 sits just under the look's 0.50 clip: everything below
  the knee (mids, shadows, well-exposed shots) is untouched, only highlights roll
  off. Verify by re-render - target any-channel clip -> ~0% AND confirm the
  picture is not dulled (mean luma below the knee unchanged). **Do not judge by
  the std of the top 3% of pixels** - compression lowers it even when detail is
  fully restored. Judge by eye and by clip%.

### Exposure matching still works source-agnostically

What already works without any structural change:

- `Input Color Space` and `PAR` are both **per clip**, so BRAW and Lumix can sit
  in one timeline and each be tagged correctly.
- CDL derivation is driven by measurement, not by camera, so exposure matching is
  already source-agnostic - both cameras get pulled to the same brightness
  envelope automatically.
- CDL offsets are per-channel, so the same mechanism can carry white-balance
  trims (currently only residual: mean channel spread 0.0032).

What the shoulder does **not** fix: same colour space is not the same look. Sensors
differ in spectral response, highlight rolloff and noise, so a systematic
per-camera trim may still be needed on top of the shoulder and the shared CDL.

If a per-camera look difference remains after shouldering, the structure can
escalate like this:

```
BMCC → group "BMCC" → pre-clip: camera match ┐
                                              ├→ TIMELINE node 1: the look
S9   → group "S9"   → pre-clip: camera match ┘   nodes 2-4: grain/vignette/halation
```

The look moves **up** to timeline level. Keeping it on the groups would mean two
copies of the same look to maintain, which drifts. Note the timeline graph
currently reports **0 nodes** and the API cannot add them - that node has to be
created once in the UI.

Do not pre-build the split. Start with one group, per-clip CDL, AND the
per-camera highlight shoulder above; render, then measure per-camera statistics.
Escalate to per-camera groups only if a systematic look offset remains after that.

## Verified constraints - do not rediscover these

- **Resolve caches LUTs by filename.** Overwriting a `.cube` in place does *not*
  reload it. Always install under a new filename, or a render will silently use
  the old look while every measurement says it changed.
- **A newly copied `.cube` is invisible until `Project.RefreshLUTList()`.**
  `SetLUT` simply returns `False` and the previous LUT stays live. The sequence
  is copy -> `RefreshLUTList()` -> `SetLUT` -> read back.
- **LUTs *can* be read back: `nodeGraph.GetLUT(i)` exists.** Call it on a colour
  group's `GetPostClipNodeGraph()` and it returns e.g.
  `MCP/WRO_Look_MarvelOlive_final1.cube`. Timeline and clip graphs return `''`
  when the look lives on the group, which reads like "no getter" but is not.
  This is the only reliable way to answer "which look is loaded right now".
- **Exporting a grade to `.drx` to identify a look does not work.**
  `album.ExportStills([still], dir, name, "drx")` returns without error and
  writes **nothing**. Use `GetLUT`.
- **Audio clips leave `Frames` empty** (`""`, so `int(... or 0)` gives 0 and any
  in-point maths goes negative). The length only comes back as the `Duration`
  timecode - parse `HH:MM:SS:FF` at timeline fps.
- **There is no fade or clip-gain API on `TimelineItem`** - the only method
  matching `*ade*`/`*olume*` is `CopyGrades`. Fades and per-clip level are
  hand-work, like the OFX. Bake level into the bed file instead.
- **`LoadRenderPreset` can wedge the application.** Seen on 21.0.3.7: the call
  returns `None`, then every *setter* starts failing - format/codec, `AddRenderJob`,
  `SaveProject`, `OpenPage` - while every *reader* keeps working and
  `GetCurrentPage()` goes `null`. A graceful `Quit()` reports success and does not
  exit. Only a human dismissing the dialog clears it, so prefer setting format,
  codec and settings explicitly over loading a preset in an unattended run.
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
- **`ZoomGang` defaults to `True`** and gangs the zoom axes. Setting `ZoomX`
  while it is on silently moves `ZoomY` with it. Always set it `False` before
  scaling one axis.
- **Do not judge anamorphic squeeze from stills yourself** - 1.33x is subtle
  enough to look plausible either way. Render options and let the user decide.
- Many Resolve API calls **return `None` even when they succeed** (`OpenPage` is
  one). Verify by reading state back, never by trusting the return value.
- **`AppendToTimeline` clipInfo `endFrame` is EXCLUSIVE**, same as
  `create_timeline_from_clips`. Passing `end - 1` costs one frame per shot.
  Pass `recordFrame` + `trackIndex` in the same dict to place an item exactly -
  that is how a new audio track gets aligned to picture already on the timeline.
- **`DuplicateTimeline(name)` lives on the Timeline object, not MediaPool.**
  `mp.DuplicateTimeline` is `None`, so calling it raises
  `TypeError: 'NoneType' object is not callable`. Probe both owners.
- **Render mode 0 is *individual clips*, mode 1 is *single clip*.** A whole
  timeline render that quietly produces one file per shot is this setting.
  Mode 0 is genuinely useful for measurement, though: one file per shot maps
  1:1 to the shot list with no frame arithmetic.
- **`AddRenderJob()` returning `''` is a settings rejection, not a modal.** Check
  `resolve_control get_page` first to rule a modal out, then validate the
  settings dict - e.g. `SelectAllFrames` must be a real bool, not `0`.
- `GetRenderSettings` is unavailable in this build; you cannot read back what you
  set. Verify from the rendered file instead.
- A creative LUT here is **DI in, DI out**. RCM still applies the Rec.709 output
  transform afterwards - a display-referred LUT would be transformed twice.
- **The show look clips flat at DI ~0.50.** Measured on the neutral diagonal, the
  cube is near-linear to ~0.50 then pins every higher input to ~0.500 (Rec.709
  white). Any clip whose DI highlights exceed that loses all separation. Shoulder
  highlights below it at clip level; a per-channel DI shoulder LUT (knee ~0.42,
  ceiling ~0.49) is the scriptable film-shoulder - the API cannot author primary
  wheels/curves, but `SetLUT` on clip node 1 works. See `tools/bake_highlight_shoulder.py`.
- **`SetLUT` + `RefreshLUTList` poison render queuing in the same process.** After
  installing/assigning a LUT, `AddRenderJob`/`StartRendering` fail in that same
  interpreter. Do the grade write in one process and the render in a fresh one.
- **Highlight recovery is not measurable by the std of the top 3% of pixels** -
  compression lowers that std even when detail is fully restored. Verify with
  any-channel clip% (-> ~0), unchanged mean luma below the knee, and the eye.

## Source media safety

Never modify, transcode, or derive camera originals. Analysis output goes to
sidecars or scratch. Clip properties (`PAR`, `Input Color Space`) are Resolve
database changes, not media changes, and are safe.
