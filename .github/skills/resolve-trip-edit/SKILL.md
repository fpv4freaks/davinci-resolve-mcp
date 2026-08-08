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

**Any path that ingests new material runs step 1b.** Systematic optical problems
- vignette above all - are invisible in a contact sheet and get blamed on the
grade months later. Measure them, then put the options to the user.

## Step 0 - source

Ask the user for the source folder if not supplied. Do not guess a path.

## Step 1 - probe before touching anything

Read metadata for every clip: `Video Codec`, `Resolution`, `PAR`, `FPS`,
`Camera Type`, `Lens Type`, `Focal Point (mm)`, `Date Recorded`, `Duration`.

Report a summary table. Two things decide the rest of the workflow:

- **which camera** -> sets the input colour space
- **whether the squeeze is already in metadata** -> decides desqueeze

For GoPro material, add one mandatory decision before grading:

- **Is this GoPro Log/Flat (GP-Log/Protune Flat) or already processed Standard/Auto color?**

If metadata does not state it clearly, infer from clip behavior and ask for confirmation:

- processed/standard signals: strong contrast, saturated yellows, quick highlight roll-off
- log/flat signals: lower contrast, muted saturation, wider highlight headroom

**Do not make that call from a TILED contact sheet.** The black padding between
tiles fakes contrast and a log plate reads as processed - this was got wrong here
and only a single FULL-SIZE frame corrected it. The measurement that settles it
is the bottom of the distribution, not the eye: log has **crush% at 0.00 on every
clip** with p1 well off the floor (0.11 measured on D-Log M) and low saturation.
Clipped highlights are NOT evidence against log - D-Log M is only ~10-11 stops,
so a blown sky clips in-camera.

Rule: processed GoPro gets a **gentle** match only (mostly chroma/look alignment, minimal tone push).
Gentle means no contrast push. It does **not** mean skipping the highlight
shoulder - that is structural headroom every camera needs on clip node 1, and
leaving it off GoPro is precisely what made it impossible to lift and left it dark
with the blacks crushed. See "Too dark AND too contrasty means crushed blacks".

**Processed GoPro arrives finished. Do not add contrast to it - ever.** The camera
has already applied its own tone curve, so the only job left is aligning it to the
chosen look. The user's standing instruction:

> GoPro clips usually come already ready to use. Only what we need is to align
> the final touch of colour look from the selected look, but do not crank up
> contrast - keep as it was, or even softer than the non-GoPro clips.

So for GoPro: no contrast push, no S-curve, no added saturation. If it still reads
harsher than the BRAW/V-Log around it, the correction is to go **softer** - lift
the toe or reduce contrast slightly - never to push the other clips up to match it.
The measured recipe for doing that is shoulder -> per-clip power -> pivoted
contrast reduction, landing GoPro's spread level with the *second* camera.

### Ask how the camera was DRIVEN, not just which camera it was

Metadata names the camera. It does not say how it was set, and three settings
change the whole grade plan. Ask before ingesting - once for a bulk folder, per
clip where the shoot is mixed:

1. **Was auto white balance on?**
2. **Was auto exposure on?**
3. **Is this log/raw, or already-processed "ready to use" colour?**

**Auto WB on -> do NOT correct white balance per clip.** Auto WB drifts *within* a
take: the camera keeps re-deciding as the framing and the light change. A clip-level
slope is one number for the whole shot, so balancing the head is exactly what wrecks
the tail - a clip that starts warm and ends neutral gets a correction sized for its
first second and dragged across the rest. This is the one documented exception to
step 4 of the per-clip preparation contract. Leave the balance alone and let the
look carry the chroma. If a single shot really cannot be left, it is a keyframed or
tracked job by hand, not a CDL.

**Auto exposure on -> expect it to be about right, and check it anyway.** Auto
exposure usually lands a usable level, so do not assume a correction is owed. But it
also rides the level mid-shot, so verify against the per-shot measurement before
trusting it, and treat a clip whose mean moves a lot across its own length as one to
leave alone rather than one to solve - the same head-versus-tail trap as auto WB.

**Already-processed, not log -> take the GoPro route.** A baked-in tone curve has
spent the headroom, so there is no real grading latitude left - and the show look is
still going on top of it. Do not treat it like log:

- judge **general contrast** against the log sources on `p10`, not on `p90-p10`
  (see *"Too dark AND too contrasty" means crushed blacks*)
- **soften** it with a pivoted slope/offset, never a flat offset
- **lift it out of the dark** with CDL `power`, which moves shadows and mids far
  more than highlights
- **never add contrast or saturation** - the look supplies both

It still gets the highlight shoulder and the per-clip exposure; "arrives finished"
governs how gently it is corrected, never whether it is.

### A fixed-WB single camera has no per-clip WB error to find

The opposite trap to auto WB, and it is easy to walk into after a multi-camera job.
When one camera shot the whole film at a locked Kelvin, per-shot cast variation is
the *locations*, not the camera - and correcting it toward any global reference
flattens the trip into one room.

Measured on Jura (261 shots, one BMCC 6K locked at 5600K, look bypassed): B/G
deviation p50 1.152, p90 1.617, max 2.426, and **zero** clips in the extreme band -
against WRO's multi-camera BRAW, which sat at 1.609 as its *median*. Every large
deviation resolved to a place:

| beat | B/G | R/G | what it actually is |
|---|---|---|---|
| the old cottage | 0.418 | 1.572 | warm wood interior |
| Adrenalina Park | 0.375 | 0.778 | green forest canopy |
| Jaskinia Gleboka | 0.535 | 1.013 | warm cave |

Split the variance before concluding anything: **between-beat sd 0.1200 vs
within-beat 0.1073** - 52% of the cast in that film *is* the itinerary. Then test
the harder question, whether any shot fails to match the shots it is *cut against*,
using a local reference (the median of +/-3 neighbours inside the same beat) rather
than the film median. On Jura that flagged 12 shots past 1.65x, but they came in
consecutive alternating runs - #160 to #164 read 0.53, 0.59, 1.60, 1.68, 0.63 -
which is a castle cutting sunlit exterior against tungsten interior, shot by shot.
The alternation was the location, not the camera, and the contact sheet confirmed it.

So: measure, decompose, look at frames, and be willing to conclude there is nothing
to correct. `tools/measure_wb.py` does the measurement and reports both references.

## Step 1b - survey what is wrong with the pictures, then offer options

Before cutting, **measure the shoot for systematic defects and come back to the
user with choices**. Do not silently correct, and do not silently ignore. The
user cannot ask for a fix to something they have not been told about - on the
Jura shoot a 0.87-stop lens vignette sat on all 344 clips and was only raised
after the grade was already approved.

Run this off the ungraded index proxy (step 5 builds one anyway - build it early):

| survey | how | flag when |
|---|---|---|
| **lens vignette** | per-clip flat field, median across clips | corner falloff > ~0.4 stops |
| **soft / out of focus** | `blurdetect` per clip vs the shoot median | > 1.6x median blur |
| **camera shake** | `signalstats` YDIF mean per clip | > ~2.5x median |
| **exposure outliers** | per-clip YAVG | very dark clips that no grade will recover |
| **noise** | ISO spread from clip metadata | a cluster at high ISO |
| **odd rasters** | `Resolution` / `PAR` tally | anything that is not the dominant raster |
| **mixed white balance** | `White Point (Kelvin)` tally | more than one value |

And on every rendered pass, not just at ingest (`tools/scan_channel_clipping.py`):

| survey | how | flag when |
|---|---|---|
| **channel clipping** | % pixels with ANY channel >= 250, per shot | > 1% on any shot |
| **underexposure** | p25 of per-shot mean luma vs the reference film | p25 below the reference's |

### Measuring a vignette without fooling yourself

- **Per clip, then take the median ACROSS clips.** Pooling every frame into one
  field lets long clips dominate and bakes their framing in. On Jura the pooled
  field said 1.28 stops at the corners; the per-clip median over 323 clips said
  **0.87** - the pooled number was inflated by content.
- **Left/right asymmetry is the proof.** A lens falloff is symmetric; scene
  content is not. Jura measured 0.510 left vs 0.485 right - an asymmetry of
  0.026 - which is what established it was optical.
- **Top/bottom asymmetry is content**, not lens: bright sky above, dark ground
  below. Mirror the field into all four quadrants before fitting, or you will
  "correct" the sky.
- On a 2.4:1 crop the falloff is **almost entirely horizontal**, because the
  horizontal extremes are ~2.4x further off-axis than the vertical. Jura needed
  +0.87 stops at the left/right edges and **+0.01 at top and bottom**. A round
  vignette tool sized to the frame will wrongly brighten the top and bottom.
- Fit gain as a **non-negative** series in r^2. A plain 2-term r^2/r^4 polynomial
  went non-monotonic (negative leading coefficient) and brightened the middle.

### Come back with options, not a decision

State the measurement, the cost of each option, and let the user choose. Costs
are real: correcting a vignette amplifies corner noise by the same factor it
brightens. Offer at least *leave it*, *partial*, and *full*:

> Lens vignette measured at 0.87 stops down at the frame edges (323 clips, median).
> Top and bottom need nothing - it is almost entirely horizontal.
>
> 1. **Leave it** - it reads as anamorphic character. No noise cost.
> 2. **Halve it** (recommended) - +0.4 stops back at the edges, 0.4 stops of
>    falloff left as character, corner noise up 1.37x.
> 3. **Remove it** - flat field, corner noise up ~1.9x.

Default to the **minimal** option unless the user asks for more. Partial beats
full: it keeps the lens character, keeps the noise down, and hides model error.

### Applying an anti-vignette - manual, and there is no way round it

Every scriptable route is closed: the node graph has **no `AddNode`**, per-clip
Fusion renders black, and `.drx` stores its node graph as a **zstd-compressed
binary blob** (`28b52ffd` magic), so `ApplyGradeFromDRX` cannot be fed a
hand-authored window either. It is one node, added by hand, once.

Put it on the colour **group's pre-clip graph** - one node covers every shot, it
runs before the clip CDLs and the look, and it costs nothing at render time.

The geometry is the part people get wrong. On a 2.4:1 crop the falloff is almost
entirely **horizontal**, so the no-correction zone is an ellipse roughly **64% of
frame width x 100% of frame height** - on 3840x1600 that is 2457 x 1600 px, an
aspect of **1.54:1**. It must look close to ROUND on screen, not stretched to the
frame. A round window sized to the frame will wrongly brighten the top and bottom,
which need nothing.

1. Circular power window, **inverted** so the correction acts outside it.
2. Size it round, just touching the top and bottom edges (~64% of the width).
3. **Softness high** - the real falloff is flat to ~64% then drops steeply.
4. Raise that node's gain by the amount in the table.

Measured average across 323 clips: -1.48 stops at the very edge, -0.91 at the
corners, **-0.00 at top and bottom**.

| strength | edge lift | corner lift | falloff kept | corner noise |
|---|---|---|---|---|
| 0.25 | +0.37 st | +0.23 st | 1.11 st | x1.17 |
| **0.35** | **+0.52 st** | **+0.32 st** | **0.96 st** | **x1.25** |
| 0.50 | +0.74 st | +0.46 st | 0.74 st | x1.37 |
| 1.00 | +1.48 st | +0.91 st | 0.00 st | x1.88 |

**0.35 is the subtle setting** and the right default: it takes the edge off
without flattening the frame, and costs only 1.25x corner noise. Full correction
is almost never wanted - it removes the depth the falloff gives and nearly doubles
corner noise.

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
| DJI Osmo Pocket 3, D-Log M | `Rec.709 (Scene)` **plus a conversion LUT** - see below |
| DJI Osmo Pocket 3, Normal | `Rec.709 Gamma 2.4` |

**If the camera is not recognised, STOP and ask.** A wrong input space is not a
subtle error and it will be blamed on the grade later.

### When Resolve has no colour space for the format - the DJI D-Log M case

Resolve 21.0.3 ships **only** `DJI D-Gamut/D-Log`. There is no D-Log M entry at
all (`strings` on the binary confirms it), and `SetClipProperty` rejects
`DJI D-Gamut/D-Log M`. Two more doors are shut: the clip property **`Input LUT`
is not settable** - it returns `False` even for a known-good bundled LUT path -
and **`Bypass` is not accepted** as an Input Color Space value.

Do not reach for the nearest log space. Decoding D-Log M with the D-Log inverse
was rendered and compared: the underpass crushed to black, the sky blew to pure
white with one fragment of cloud surviving, blues over-saturated. Unusable.

The chain that works, verified by render:

1. clip `Input Color Space` = **`Rec.709 (Scene)`**
2. the vendor's own conversion cube on the colour **GROUP's pre-clip node**, via
   `graph.set_lut(source="color_group_pre", node_index=1, ...)` - one node covers
   every shot and it runs before the clip CDLs, so clip node 1 stays free for the
   shoulder and the per-clip CDL exactly as step 6 wants
3. the look on the group's post-clip node as usual

Marvel Olive stacks on top of that cleanly. Get the cube from the manufacturer's
downloads page - DJI's CDN returns **403** to a bare `curl`, so send a browser
User-Agent and Referer. Note the file may be labelled for a different body (DJI
ships one D-Log M curve across cameras); that is expected, not the wrong file.

`graph.set_lut` does not resolve the *user* LUT directory - stage the cube in the
master LUT dir and reference it from there.

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
6. Cut style preference: selective highlights vs fuller documentary coverage?
7. Shot duration preference: mostly short cuts, medium cuts, or longer holds?
8. **Which look?** Name the eight from *The look library* by number and character,
   and say which one the existing edit is already on. Do not carry a look over
   silently just because the material is being extended - "keep the current look"
   has to be the user's answer, not the default.

Ask these **before importing**, not after. Ingesting first and asking later
throws the answers away: the bins, the trims and the shot count all follow from
them, so an import that has already happened is work that has to be redone.

Pacing follows from the answers. A family trip wants faces held longer; a
sightseeing reel wants movement and rhythm.

If answers 6-7 are missing, ask before appending a new day. Do not default to
full-clip dumps for GoPro days; prefer selective picks unless the user asks for
full coverage.

### The default is EVERY clip, in chronological order

Unless the user has asked for selective highlights, **keep every clip and keep
them in shooting order**. Trimming a clip that runs long is expected; dropping a
clip is not. This user's standing instruction:

> I want to have all, unless you will clearly say that some clip is completely
> useless. Otherwise the assumption is that you take all clips, in chronological
> order.

So:

- **Never silently drop a clip.** A short settled span is a reason to make the
  shot shorter, not a reason to bin it. Only a genuinely unusable clip may go -
  and it must be **named in the report with its reason**, not quietly filtered.
- Do not "decimate to a target count" for pacing. Runtime comes from trimming,
  not from throwing material away.
- "Best clip per chronological block" is a **selective-highlights** tool. It is
  wrong for a full-coverage cut and it silently discards most of the shoot.

## Step 5 - build the edit

Import, organise into a dated bin, build the timeline. `create_timeline_from_clips`
treats `endFrame` as **exclusive** - off-by-one here leaves 1-frame gaps on every
cut. Verify with a gap/overlap check before moving on.

### Never cut into the camera being picked up or put down

The first and last seconds of a take are the operator framing up and then
lowering the camera before hitting stop. Cutting into either reads as an amateur
mistake instantly - the frame tilts to the ground, or swings up off a subject -
and no grade or pacing fixes it.

**This is not a small trim.** Measured across the 344 Jura clips:

| | median | p90 | worst | clips over 0.5s |
|---|---|---|---|---|
| head | 0.00s | 0.41s | 4.54s | 23 |
| tail | 0.12s | 0.62s | **9.04s** | 40 |

Tails are far worse than heads - people lower the camera long before they press
stop. A fixed guard of a few frames is nowhere near enough; the first cut of this
film shipped **61.5 seconds** of camera handling across **103 of 263 shots**.

Detect it, do not guess it (`tools/detect_camera_handling.py`): estimate the
global per-frame vertical and horizontal shift by 1-D projection matching (row
means give the vertical signature, column means the horizontal; the lag that
minimises SSD between consecutive frames is the camera move). Sustained drift at
the head or tail is handling; a scalar frame difference cannot tell it apart from
subject motion.

**That detector does NOT transfer to a gimbal camera. Check frames before you
trust it.** It was calibrated on handheld, where sustained drift means the
operator is raising or lowering the camera. On a gimbal the operator walks and
pans continuously, so drift *is* the shot. Measured on an Osmo Pocket 3 day: it
reported **5.29 s of head and 17.08 s of tail unusable on a 26.0 s clip** - 22 of
26 seconds - and the frames showed a deliberate move around a car interior.
Across that shoot **all 15 heads and all 15 tails were composed** and nothing
needed trimming at all. A stabilised camera plus a deliberate press of the record
button removes most of what this step exists to catch. Sample the first and last
frame of every clip into two contact sheets and look; that is 30 frames and it
overrules the detector outright.

Then make the settled span a **hard constraint on the planner**, not a
post-hoc trim:

- a clip whose settled span is shorter than the minimum shot is not a candidate
- a shot's duration is capped by its clip's settled span
- if a beat cannot be filled from settled footage, pick more shots from that beat
- absorb any remaining shortfall **at ACT level, not beat level** - the music is
  locked to act boundaries, so act totals must stay frame-exact while beats
  inside them flex

Moving in-points alone will not do it: on this film that still left 835 frames of
handling because 60 clips had no settled window long enough for the duration the
planner had already committed to. Constrain first, then allocate.

Also worth avoiding for the same reason: the audible click of the record button
at the head/tail of a take, if nat sound is in use.

## Step 6 - apply the reference grade

Architecture, in this order:

- **Clip node 1** - per-shot balance (CDL). Add a **highlight shoulder** here too
  for any clip whose DI highlights run past the look's clip point - and that
  means **every clip, including BRAW**, not just a second camera. A fresh project
  has no shoulder on anything; nothing adds one for you.
- **Group post-clip node 1** - the show look, one `.cube`.

### The per-clip preparation contract - every clip, every source, no exceptions

Apply all of these without being asked. Every one was, at some point on this film,
requested by the user *after* they saw a bad render - which means the run that
skipped it had decided it was optional. None of them are.

| # | step | applies to | verify with |
|---|---|---|---|
| 1 | `Input Color Space` tagged per clip | every clip | `GetClipProperty('Input Color Space')` |
| 2 | anamorphic desqueeze | squeezed sources | `GetProperty('ZoomY')` |
| 3 | highlight shoulder LUT | **every clip, every camera** | `GetLUT(k)` across all nodes |
| 4 | per-clip WHITE BALANCE, look bypassed | **every clip, every camera** | the plan JSON - CDL is unreadable |
| 5 | per-clip exposure, composed onto 4 | **every clip, every camera** | the plan JSON |
| 6 | soften a camera that reads harsher | processed cameras | `p10` vs the reference camera |

Run `tools/audit_prep.py <timeline> <items.json> <plans...>` **before every
render**. It groups all of the above by source and names any camera missing a
step - the check that would have caught GoPro sitting in a finished grade with no
shoulder and no balance, instead of two rounds of rejected pictures.

**No camera is exempt from 3, 4 or 5.** "Processed GoPro arrives finished" governs
*how gently* it is corrected - see the per-source damping table - never *whether*
it is. GoPro was skipped on this film and the measured cost was a per-clip cast
spread three times that of the camera that got balanced:

| source | per-clip WB applied? | `R/G` spread | `B/G` spread |
|---|---|---|---|
| Lumix | yes | ±5% | ±9% |
| GoPro | no | ±20% | ±26% |

Step 4 has exactly two documented exceptions, and both are answers to the questions
in *Ask how the camera was DRIVEN*: **auto WB was on** (the cast moves inside the
take, so a clip-level slope fixes the head and wrecks the tail), or **one camera
shot everything at a locked Kelvin** and the measurement shows the variation is the
locations rather than the camera. Neither is a reason to skip 3 or 5. Establish an
exception by measuring, not by assuming.

### One node holds ONE CDL - recompose, never overwrite

`SetCDL` replaces the *entire* correction on that node - slope, offset, power and
saturation together. A later pass that writes only the values it cares about
silently erases everything already there. That is exactly how balanced GoPro clips
ended up unbalanced here: white balance was measured, solved and applied, then
wiped by a tone pass that wrote a fresh neutral-chroma CDL to the same node.

It cannot be caught by reading it back, because **there is no `GetCDL`**. Resolve
will not tell you what balance a clip carries.

- **Journal every per-clip pass to a plan JSON on disk.** That file, not the
  project, is the record of what each clip carries.
- **Compose onto the previous pass instead of writing fresh.** For a WB slope `w`
  (normalised to geometric mean 1) and a tone contrast `c`, node 1 wants
  `slope = c * w` per channel - `w` carries the chroma, `c` carries the tone, and
  neither destroys the other.
- **Re-run `audit_prep.py` after any second pass** over clips that already had one.

### Measure the look's own transfer before choosing a shoulder ceiling

Do not take "the look clips at DI ~0.50, so use ceiling 0.49" on trust - that is
a statement about one look. Read the `.cube`'s neutral axis and find (a) the
input DI where its output goes flat, and (b) what its flat-top output value is
per channel.

On `WRO_Look_MarvelOlive_final1` those are **input DI 0.5312**, output
**R 0.500 / G 0.501 / B 0.499**. That green 0.501 is *above* display white
(DI 0.5138) while blue 0.499 is below it - so every highlight that reaches the
look's flat top pegs G at 255 and leaves B at ~254. **That is the yellow-green
blown colour**, and it is baked into the look itself, not the footage.

So the ceiling must sit just under the input where the flat top begins, and the
knee high enough not to dull normal highlights. Measured on this look:

| ceiling | highlights land at (Rec.709) | verdict |
|---|---|---|
| 0.49 | 0.71 | far too dark - p99 collapsed 0.936 -> 0.617 |
| 0.51 | 0.81 | still dull |
| **0.525** | **0.940 / 0.942 / 0.931** | correct, all channels clear of the peg |
| 0.5312 | 0.998 / 0.999 / 0.994 | on the edge, pegs again |

Bake with `bake_highlight_shoulder.py <out.cube> <knee> <ceiling> 33`, install
under a **new filename**, `RefreshLUTList()`, then `SetLUT(1, ...)` on each clip
- node 1 can hold the CDL *and* a LUT, and the node's LUT runs after its primary
corrections, which is the order you want (expose, then shoulder).

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

### Never derive the exposure target from the existing edit

**p99 ~0.93 is the target. It is an absolute, not something to be inferred.**

Measuring the current edit and aiming new shots at *its* median p99 feels like
"matching the approved base" and is the most destructive mistake in this
workflow. A whole-film median is dragged down by every legitimately dark shot in
it, so the target lands far below display white - and the solver then applies
**negative** offsets to correctly-exposed daylight shots.

Measured failure on this trip film: the base median came out at **p99 0.605**,
was used as the target, and **38 of 80 new shots were pushed darker** (23 BRAW,
12 V-Log), reported by the user as "plenty of BRAW completely dark".

- Use the base for **sanity only**, never as the target. If the base median p99
  sits far below 0.93, that is a finding to REPORT, not a number to copy.
- A correction that darkens a daylight shot is almost always the solver being
  wrong, not the shot. Print the count of darkened shots and challenge it.
- The shoulder on node 1 runs AFTER the CDL, so lifting a dark shot is safe - the
  top is caught before it can blow. Lift with confidence.

### Drive the exposure match on MEAN, and calibrate the gain instead of guessing

**p99 is a highlight guard, not a brightness control.** A shot with a specular
highlight puts p99 somewhere plausible while the bulk of the frame sits far too
dark, so a p99-only solver reports success and changes nothing that matters.
Measured here: day 3 BRAW read **p99 0.559 (fine) against mean 0.119 (very
dark)** - what the user saw as "completely dark" was invisible to p99.

- Match **mean luma** to the chosen look's own reference mean (Marvel Olive =
  0.2823; the approved base independently sat at 0.276). Keep p99/clip% as
  guards that veto a lift, not as the thing being solved.
- **Never guess the gain.** One offset is one data point: render a proxy, apply a
  known offset, render again, and the per-shot sensitivity `d(mean)/d(offset)`
  falls out directly. Invert it and the remaining error lands in a single step.
  Measured median on this film: **1.53**. A guessed gain plus a tight clamp is
  why pass two only got a third of the way there.
- Report the per-source medians before and after. Sources need very different
  corrections - BRAW wanted +0.13 offset, GoPro only +0.04, and V-Log was already
  slightly over and needed easing back.

### "Too dark AND too contrasty" means crushed blacks - check the shoulder first

When one camera reads dark and harsh next to the others, measure `p10` against the
reference camera before touching anything. Measured here through Marvel Olive:
BRAW `p10 0.039`, Lumix `0.057`, GoPro **`0.003-0.006`** - the GoPro shadows were
pinned to black. That crush, not the `p90-p10` spread, is what the user sees as
"too contrasty"; GoPro's spread was actually *lower* than the reference (`0.442`
vs `0.586`), so a contrast metric alone says the opposite of the complaint.

The cause was structural: **BRAW and Lumix carried the shoulder LUT on clip node 1
and GoPro carried none.** Confirm with `GetNodeGraph().GetLUT(1)` per source - a
camera missing the shoulder cannot be lifted, because every control hits the
highlight ceiling long before the shadows move. Both were measured and rejected:

| control | `p10` gain | `p99` gain | verdict |
|---|---|---|---|
| offset `+0.03` | `+0.007` | `+0.181` | clips at `0.126%`, shadows barely move |
| power `0.85`, no shoulder | `+0.011` | `+0.308` | `2.8%` clipped |
| power `0.85`, **with shoulder** | `+0.011` | `+0.099` | **`0%` clipped** |

- **Give every camera the same shoulder, then lift with CDL `power`.** Power lifts
  shadows and mids far more than highlights, which fixes "dark" and "crushed" in
  one control; the shoulder absorbs what reaches the top. Reaching `p10 0.039`
  with offset alone would have needed `+0.14`, driving `p99` past `1.4`.
- The shoulder on its own changes almost nothing (`p99 0.614 -> 0.580`) because a
  dark camera never reaches the knee. It is not the fix - it is the *headroom that
  makes the fix affordable*. Do not judge it by its own before/after.
- Calibrate `d(ln mean)/d(power)` from two rendered probes. It is not constant -
  measured `-1.93` to `-2.99` across 46 clips, tracking clip brightness, so fit it
  against `ln(mean)` rather than applying one value to every shot.
- **Correct partially and skip near-black clips.** Closing 80% of the log distance
  to the reference fixed every "way too dark" shot (`0` left >25% below reference)
  while keeping genuinely dark shots darker than bright ones. A clip at
  `mean 0.003` is a black frame - lifting it only makes grey mush.

**Matching the reference contrast is not enough - processed GoPro must sit below
it.** After the power pass the spread matched (`0.581` vs `0.586`) and the user
still reported it as too contrasty, because `p10` was only back to `0.017` against
the reference `0.039`. Judge this on `p10`, not on `p90-p10`.

- Soften with a **pivoted** slope/offset, never a flat offset: `slope = c`,
  `offset = pivot*(1-c)`. At `c 0.85, pivot 0.40` this took `p10` to `0.042/0.052`
  while mid grey stayed put. A flat offset of the size needed to move `p10` that
  far would have hauled the whole image up with it.
- Softening raises the level (mean `0.290 -> 0.313`), so **re-solve power against
  the same reference afterwards**. That pass pays for itself: raising power lowers
  contrast further, so the level fix is also a second softening.
- **Expect to soften twice.** Landing one step under the primary reference was
  still called too contrasty. The accepted end point was contrast *level with the
  second camera*, not merely below the primary:

  | pass | contrast | `p10` | against BRAW `0.586`, Lumix `0.505` |
  |---|---|---|---|
  | power only | `0.581/0.557` | `0.017/0.014` | matched BRAW - rejected |
  | `c 0.85` | `0.527/0.513` | `0.035/0.043` | ~11% under BRAW - rejected |
  | `c 0.80` | `0.504/0.492` | `0.043/0.059` | level with Lumix - accepted |

- **Pre-compensate the power when stepping `c` again** rather than re-probing. The
  first softening's measured level shift scales with the size of the `c` step, so a
  power multiplier of `1.013` held mean at `0.289/0.292` across `0.85 -> 0.80` and
  saved a render. It costs nothing to try - the verification render was happening
  anyway.
- **Stop around `c 0.80`.** By `0.75` `p10` passes `0.07` and reads hazy rather
  than soft, and `p99` has already fallen to `0.616/0.668` against BRAW `0.761` -
  highlights tame faster than shadows open. Past that point, suspect saturation
  rather than tone.
- `p10` moved `0.003 -> 0.043` across the whole job. That single number, not the
  `p90-p10` spread, is what tracked the complaint from start to finish.

The recipe, executable:

```bash
python tools/render_range.py base 103837 119307 /tmp/qc
python tools/measure_sources.py /tmp/qc/base.mov items.json 103837 15600 stats.json day3_braw
python tools/solve_power.py stats.json gopro plan.json 0.290 0.85 0.80
python tools/soften_camera.py "<timeline>" items.json gopro plan.json 0.80 0.40 1.0 MCP/shoulder.cube
```

Measure the **whole** span the camera covers, not one region - per-clip
sensitivity varies far too much to extrapolate a solve from a sample. Re-solve
against the same measurement JSON by passing the previous plan as the last
argument to `solve_power.py`.

### White balance comes FIRST, and is measured with the look BYPASSED

The order is not negotiable:

    clip node 1:   white balance  ->  exposure
    group post:    the look (Marvel Olive)

**Never solve WB from the graded output.** The look is a strong non-linear
transform, so inverting it to get a clip-level slope is unstable: on this film
that inverse over-corrected and pushed shots into red, and a "refinement" then
swung V-Log from too blue (0.907) straight past neutral to too yellow (1.122).

Measure properly instead - `group.GetPostClipNodeGraph().SetNodeEnabled(1, False)`
bypasses the look (the graph's *readers* are unavailable, but `SetNodeEnabled`
works), then render a small proxy. That plate answers a straight question - is
this clip warm or cool - and the answer maps directly onto a clip-level slope.
Re-enable the look afterwards, then solve exposure, which is a separate axis and
must be merged onto the WB slope rather than overwriting it.

Measure on a mid-tone mask (0.12 < luma < 0.65). Measure **every clip** and emit
a per-clip CSV; a group median hides exactly the shots the user is complaining
about.

### CALIBRATE the WB response - a display-referred ratio is NOT a CDL slope

This is the single most destructive mistake in this workflow, and it is silent.

Ratios get measured on a rendered proxy, which is **display-referred** (Rec.709).
A CDL slope acts in the **log/DI working space**. They are different units, so
writing a measured ratio straight back as a slope over-corrects massively:
foliage turns purple, shots go cyan or blue, and the numbers still look plausible
because everything moved in the right *direction*.

Probe it instead of assuming. Apply a known slope, render, and measure:

    k = d ln(B/G out) / d ln(slope)

Measured on this project with Marvel Olive: a slope of **1.05 moved the output
ratio by 1.202**, so **k = 3.764** - the response is nearly **4x** the input.
A 1.41 slope therefore produced a 3.6x colour shift, which is what wrecked the
grade. The inverse is then exact:

    slope = (desired output ratio) ** (1 / k)        # 1/k = 0.266 here

Rules that follow:

- **Damp the desired OUTPUT, not the slope.** `dev ** damp` first, then raise to
  `1/k`. Damping the slope means the damping factor is itself 4x too strong.
- **Clamp the slope tightly** (~0.12 for the worst source, less elsewhere). After
  calibration the useful range across 201 clips was **0.904 - 1.113**; anything
  near 1.4 is a bug, not a strong correction.
- **Re-probe if the look changes.** k is a property of the look plus the working
  space, not a constant.
- The same trap applies to exposure - that is why `d(mean)/d(offset)` is measured
  too. Any correction solved in one space and applied in another must be
  calibrated, never assumed.

Cheap way to iterate: render a **short MarkIn/MarkOut region** over the problem
shots (~2 min) instead of the whole timeline (~10 min), and put the frames on
screen as a contact sheet. Numbers alone hide this failure - the statistics said
"yellow reduced" while the picture was purple.

### A cast can be too extreme to gain back - accept it or desaturate

Check what is actually in the channel before trying to correct it. The underground
BRAW on this shoot measured **B/G 0.048** - the blue channel is essentially empty
because the lighting is sodium/tungsten. Multiplying an empty channel by 18x
invents no detail, amplifies noise, and skews the image toward whatever the gain
lands on.

| severity | B/G deviation | treatment |
|---|---|---|
| mild | < 1.4 | calibrated ratio correction |
| moderate | 1.4 - 3.0 | calibrated correction, damped |
| extreme | > 3.0 | correct PARTIALLY and leave it warm |

The important judgement: **a sodium-lit cellar is supposed to look warm.** After
the calibrated pass those shots still measured B/G deviation ~1.27 and the client
called them "ok-ish" - correct. Driving them to neutral is what made the rest of
the film purple. Desaturation is available for a residual cast that still reads
as screaming orange, but it is a last resort on individual shots, never a
blanket move, and it was NOT needed once the response was calibrated properly.


The look is deliberately not neutral - Marvel Olive measured **R/G 1.011,
B/G 0.764** on the approved base. Gray-worlding the graded output would drag
those ratios to 1.0 and strip the look's whole character. So the approved base
defines "correct", and each new shot is corrected only by how far it sits from
that reference. Measure on a **mid-tone mask** (0.10 < luma < 0.80); sky and
shadow decide nothing about a cast.

Per-source damping and clamps, because the causes differ:

| source | cause | damp | clamp |
|---|---|---|---|
| BRAW | systematic camera/underground cast | 0.65 | 0.32 |
| V-Log | auto WB, usually close | 0.55 | 0.15 |
| GoPro | arrives finished | 0.35 | 0.08 |

Measured on this film: BRAW sat at **B/G deviation 1.609** (very yellow, 55 of 76
shots) and came back to **1.038** in one pass.

Two traps:

- **Normalise the slope triple to a geometric mean of 1.** A raw WB slope changes
  exposure too: correcting BRAW's yellow pulled red down and dropped mean luma
  0.304 -> 0.249, undoing the exposure solve. Normalising keeps WB chroma-only.
- **One pass overshoots, because the look is non-linear.** A slope applied at clip
  level does not map 1:1 to the measured output - V-Log went from 0.907 (too
  blue) straight past neutral to 1.122 (too yellow). Always re-measure and
  compose a refinement onto the slopes already applied,
  `new = applied * residual**damp`, with a LOWER damp so it converges.

### Scan per CHANNEL, not per luma - luma QC is blind to this

**A luma percentile cannot see channel clipping.** On the Jura master, luma p999
read a legal 0.977 while **106 of 263 shots** had over 1% of pixels with at least
one channel pegged, worst 13.15%. The tell: `all-three-channels` clipping was
**0.00% everywhere** - it is *always* partial, which is exactly why it reads as
yellow or green rather than white.

Measure, per shot: `%` pixels with any channel >= 250, with all channels >= 250,
and the difference between them (the colour-shifted ones). Look at per-channel
p999 signatures - `R255 G251 B227` is yellow, `R255 G249 B182` is strong yellow.
Target after the shoulder: **0.00%**.

### Check the bottom of the distribution too, not just the median

"Some clips are underexposed" shows up as a low **p25**, not a low median. The
Jura master matched the reference on median (0.302 vs 0.276) while its p25 sat at
**0.194 against 0.233** - a whole quartile darker. Compare min/p25/median/p75
against the reference film, and lift with a term that works hardest near black
and fades out by the mids, so the middle of the range keeps its variety.

### A dark shot is not automatically an underexposed shot

Judge darkness on **mean AND p99 together**, or you will "fix" scenes that are
correct. On the finished Jura master the six darkest shots split cleanly into two
kinds:

| shot | mean | p99 | verdict |
|---|---|---|---|
| Filmowy Ogrodzieniec | 0.058 | **0.595** | dark room, bright practicals - correct |
| Jaskinia Gleboka | 0.063 | **0.601** | cave with a lantern - correct |
| the old cottage | 0.101 | 0.256 | genuinely dim interior - deliberate |

Low mean **with a high p99** is a lit subject in a dark room: it has highlights,
it reads on screen, and lifting it would flatten the very contrast that makes it.
Low mean **with a low p99** is the one to question. Only the second kind belongs
in an underexposure count.

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

Texture **cannot be scripted** - OFX cannot be added to a node through the API at
all. The user adds it on the **timeline** node graph, which holds 0 nodes until
they create it.

### Film Look Creator, one node - this is the route

One node gives halation, grain and gate weave together, already balanced against
each other, and it beats hand-matching separate plugins:

1. Add **ResolveFX Film Look Creator** to a timeline node.
2. Preset: **Cinematic**.
3. **Colour Blend -> 0** and **Film Look blend -> 0** - the show LUT is already
   doing the colour, and leaving these up double-grades the picture.
4. **Vignette -> off** - it darkens the edges, which fights the anti-vignette in
   step 1b and re-creates the very fault being corrected.
5. **Grain: `16mm`** - see *Use 16mm at 4K* below.

What survives is the emulsion behaviour on its own: halation, grain and gate
weave. Verify it the same way as any texture - in the delivery codec, at native
1:1, never on a scaled image.

Confirm by reading the node graph back before rendering: `GetToolsInNode` on the
timeline graph reports what is actually loaded, and an empty node reads as `None`.
A healthy graph is one node:

```
node 1  ['OFX: Film Look Creator']
```

`GetToolsInNode` returns the plugin *name* only - there is no OFX parameter
reader, so previous settings cannot be recovered from the project. If the user
dials in values worth keeping, write them down; nothing else will.

**If separate `OFX: Halation` or `OFX: Film Grain` nodes are also present, ask
whether they are enabled before concluding anything** - a disabled node still
shows up here. See *Do not stack Film Look Creator with separate halation and
grain nodes*.

## Step 8 - stop before rendering and hand off

### QC the AUDIO on every render, not just the picture

Five masters were rendered on this film before anyone noticed that **days 3-5
were completely silent**. The nat-sound track had been left disabled, so 200
audio items sat muted while every picture QC passed clean.

Check on each render, from the rendered file:

- **per-region RMS** - a region at -140 dB is digital silence, not quiet
- **true peak** - days 1-2 measured **+3.3 dB**, i.e. clipping above full scale
- **per-clip spread** - measured 48.5 dB p10-p90 here, with GoPro nat sound
  ~20 dB below the BRAW it is intercut with
- **track enable state** - `GetIsTrackEnabled('audio', n)` before rendering

**When it clips, isolate WHICH track before touching anything.** Measure the
music source file on its own and compare it with the mix - the source is on disk,
so this costs one `ebur128` run and no render. Measured on the Zachodni cut:
music alone **-0.1 dBFS / -13.2 LUFS**, the mix **+1.1 dBFS / -13.1 LUFS**. The
nat sound therefore contributed the **entire** 1.2 dB of overshoot while adding
0.1 LU of loudness - transient peaks (wind, station rumble, the record-button
click) on top of an already-full mastered track. Integrated loudness barely
moving while true peak jumps is the signature of a track that belongs well down
under the music, or off.

With no clip-gain API the scriptable fallback is `set_track_enable(False)` on the
nat-sound track: reversible in one call, and it ships a clean master instead of a
clipping one. Say so prominently in the hand-off, with the level to restore it at
(-12 to -15 dB on the fader), because it is a creative choice made for a
technical reason.

Two API limits shape what can be fixed in script:

- **There is no clip-gain / volume / normalise API.** The audio `TimelineItem`
  exposes no volume method at all, and `MediaPoolItem` has no normalise. Per-clip
  levelling is Fairlight hand-work (select clips -> Normalize Audio Levels), or
  it means rebuilding the track from pre-normalised files.
- **Audio clips return an empty `Frames`** - `int(GetClipProperty('Frames') or 0)`
  yields 0 and `AppendToTimeline` silently refuses. Parse the `Duration`
  timecode instead: `((h*3600 + m*60 + s) * 24) + f`.

To restore a muted nat-sound track without doubling audio that other tracks
already carry, disable the overlapping items with `SetClipEnabled(False)` rather
than deleting them - reversible, and it leaves the approved mix untouched.


**Never start a master render without doing this first.** It applies whenever the
user asks for a render, and whenever new clips have been added and a look chosen.
Grain, halation and vignette cannot be scripted, so a render fired off silently
ships a master with no texture - and it looks fine in stills, which is how it
gets missed.

Before final render, run a stabilization gate by source type:

- **BRAW clips** - confirm gyro stabilization has been applied where needed.
  Do not assume this was done during ingest or grading.
- **Lumix clips** - no extra stabilization pass by default (in-camera
  stabilization is the baseline). Only add extra stabilization if the user asks.

Prepare everything else first - clips in, desqueezed, grouped, CDLs derived, look
LUT set, render settings staged - then stop and tell the user, in this shape:

> Everything is ready to render: 159 shots, 7:06, look = *Marvel*, delivery
> `2.4-1.4K.70M`.
>
> **The timeline node graph is still empty, so this render would have no texture.**
> Add one node by hand on the timeline graph (Color page, timeline clip selected),
> then tell me to go:
>
> **ResolveFX Film Look Creator** - preset *Cinematic*, colour blend **0**,
> film look blend **0**, vignette **off**, grain **16mm**.
>
> That one node covers halation, grain and gate weave. Or say "render without
> texture" and I will.

Confirm with `GetToolsInNode` after they say go. Do not take "done" on trust -
the check costs one call, catches an effect added to the wrong graph, and catches
separate halation/grain nodes left alongside Film Look Creator.

### Verify the texture actually reached the render

`GetToolsInNode` proves a plugin is *present*. It does not prove it is *doing
anything* - and it cannot, because node enabled state has no getter. A node in
the readback may be switched off, unwired, or set to zero strength, and all three
look identical from the API. This cuts both ways: on this project an
`OFX: Film Grain` node contributed exactly zero. Measured, not guessed -

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

If grain measures zero, the likely causes, in order: **the node is disabled** -
the cheapest thing to rule out and invisible to every reader in the API, so ask;
its strength or blend is at zero; **the node is not wired into the chain** (a node
can sit in the graph unconnected - the API cannot read wiring, so check it on the
Color page); or the effect was added to a clip graph rather than the timeline
graph.

### Grain that survives ProRes but not H.264 is not in the master

Measure it in the **delivery codec**, not only in ProRes. On the Jura master the
same grain setting measured:

| | grain RMS |
|---|---|
| ProRes 422 HQ, full raster | 0.31 |
| delivered 70 Mbps H.264 | **0.00** |

Weak grain is exactly the kind of low-amplitude high-frequency signal a delivery
encoder spends no bits on, so it is removed completely. A ProRes toggle test can
report "grain IS working" for grain the audience will never see.

The cheapest valid check needs no extra render: if two masters of the **same cut**
exist with and without the texture nodes, compare their high-frequency energy
directly - same codec, same bitrate, same timecodes. Jura v3 (no texture) read
4.56 and v4 (halation + grain) read **4.28** - *lower*, because halation's bloom
softens fine detail and the grain added nothing back.

Target a grain RMS of **3-8** at 4K in the delivered file. If it measures under
~1.5 there, raise the strength until it does not - or drop the node, because it
is costing render time for nothing. Halation is separate and easy to confirm: it
lifts overall mean luma (+1.02 here), so it shows up even when grain does not.

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

**Film Look Creator** - the single texture node

| control | value | why |
|---|---|---|
| preset | `Cinematic` | |
| colour blend | **0** | the show LUT already does the colour; above 0 double-grades |
| film look blend | **0** | same reason |
| vignette | **off** | it darkens edges and fights the step 1b anti-vignette |
| grain | `16mm` | finer presets vanish in the delivery encode - see below |

Everything else is emulsion behaviour and can stay at the preset's values. The
plugin balances halation, grain and gate weave against each other, which is the
main reason to prefer it over hand-matching separate plugins.

For lens vignetting, do **not** add a darkening vignette here - that is the
opposite of what this footage needs. See *Applying an anti-vignette* in step 1b,
which corrects the falloff on the colour group's pre-clip graph.

### Use 16mm at 4K - and expect the 70 Mbps encode to eat most of it

This reverses the intuition that 16mm is "too coarse at 4K". It would be, if the
audience saw the timeline. They see a 70 Mbps H.264, and fine grain is exactly
the low-amplitude high-frequency signal a delivery encoder spends no bits on.
Coarser grain has larger spatial features, so it stands a better chance.

Measured on this film, native 1:1 crops in mids and shadows, same cut throughout:

| master | texture | HF energy |
|---|---|---|
| v3 | none | **2.058** |
| v5 | Film Look Creator `16mm` alone | **1.418** |

The textured master has **31% LESS** fine detail than the untextured one. Grain
RMS in quadrature: **0.00**, on all three crops independently. Going coarser did
not rescue it.

**That result is not universal - measure it per project.** The same test at the
same bitrate and raster on a later film (Osmo Pocket 3, Film Look Creator, 2:27
at 3840x1600) came out the other way:

| film | HF texture ON | HF OFF | ratio | grain RMS |
|---|---|---|---|---|
| Jura | 1.418 | 2.058 | **0.69** | **0.00** |
| Zachodni | 1.161 | 0.813 | **1.43** | **0.702** |

So the encode does not reliably zero the grain; it attenuates it heavily, and how
much survives depends on the grain setting and on how much real detail the
content gives the encoder to spend bits on. Neither number reaches the 3-8 target,
so in both cases the audience sees little or nothing - but "there is no point
adding grain at 70 Mbps" is the wrong lesson to carry forward. Run the matched
toggle test on the actual master before concluding either way.

The honest conclusion: **at ~70 Mbps H.264 the delivery encode usually wins.** It
strips most of the grain and, because grain forces it to spend bits on noise, it
smooths real detail too - film-look softening then compounds that. If grain
genuinely matters, raise the delivery bitrate, ship a higher-bandwidth codec, or
raise the plugin's grain strength until it measures above ~1.5 in the delivered
file. One Film Look Creator node cost 21.0 min against 5.5 with an empty graph
(and 170 s against 43 s on the 2:27 film), so this texture is not free.

### Measure texture at NATIVE resolution - never on a scaled image

The rule about not judging grain from a scaled preview applies to the measuring
script too, not just to eyeballing. Measuring the same pair at 1280x534 instead
of 1:1 crops gave 4.56 vs 3.89 - different absolute numbers and a different sense
of the gap, because downscaling averages grain away before it is measured. Take
1:1 crops at full raster from several positions, in mids and shadows.

### Do not stack Film Look Creator with separate halation and grain nodes

Film Look Creator already contains both. Adding `OFX: Halation` and
`OFX: Film Grain` after it *applies* each a second time - but only if those nodes
are enabled. Read the timeline graph back before rendering:

```
node 1  OFX: Film Look Creator     <- already has halation + grain + gate
node 2  OFX: Halation              <- second pass, IF enabled
node 3  OFX: Film Grain            <- second pass, IF enabled
```

**A readback like this is not proof of double texture.** `GetToolsInNode` lists a
node's tools whether the node is enabled or bypassed, and the API has no
`GetNodeEnabled` to disambiguate - `SetNodeEnabled` is write-only. Leftover
disabled nodes parked in a graph are normal working practice, and they cost
neither render time nor image change.

So treat extra texture nodes as a **question for the user, not a finding**: "I can
see Halation and Film Grain after Film Look Creator - are those enabled?" Do not
announce that the master is double-textured, and do not claim dropping them will
save render time, until the answer comes back. Both statements were made wrongly
on this film against a graph whose extra nodes were switched off.

### Render settings

`2.4-1.4K.70M` - 3840x1600, 24p, QuickTime H.264 ~70 Mbps, PCM 16-bit 48 kHz.
Render mode **1** (single clip); mode 0 is *individual clips* and quietly writes
one file per shot. Set format, codec and settings explicitly rather than calling
`LoadRenderPreset`, which can wedge the application (see *Verified constraints*).

After the render, measure the whole timeline, not only the new part.

## Adding phone photos or stills to a cut

Triggered when the user points at a folder of phone photos to fold into an edit.
Everything below was measured on an 89-photo iPhone folder.

### Recognise what is in the folder before promising anything

- **Count by extension first.** JPEG imports natively; HEIC generally does not
  and needs a conversion step, which changes the whole plan. This folder was
  all JPEG, so no conversion was needed.
- **Read `DateTimeOriginal` with a `DateTime` fallback.** Measured: `getexif()`
  returned `None` for `DateTimeOriginal` on some iPhone JPEGs while `DateTime`
  was populated. A single-tag read silently loses photos, and they were the ones
  being restored by name at the time.
- **Honour the EXIF `Orientation` flag** (values 5-8 swap width and height).
  Judging portrait from raw pixel dimensions is wrong for phone photos.
- **Group by capture DATE to map photos onto days, then check the edges.** One
  MOV here was stamped the day *after* the trip ended - it does not belong to any
  day and needs a decision rather than a silent placement.
- `mdls` does not work on external volumes that Spotlight has not indexed. Use
  Pillow's EXIF, not Spotlight metadata.

### Near-duplicates are the rule - cluster, then LOOK

Phone folders are full of bursts. Measured: 89 photos held 14 clusters, almost
all selfie repeats.

- Cluster on a **perceptual hash** (dHash), never on filename or timestamp -
  neither knows what the picture looks like.
- Also require members to be close in **time**, so two similar views taken hours
  apart stay separate.
- Keep the **sharpest** member, by variance of a Laplacian. That is what picks
  the in-focus frame out of a burst.
- **The threshold has a knee. Find it by sweeping, then render the clusters as a
  labelled sheet and look.** Measured sweep: distance `<=12` dropped 5, `<=16`
  dropped 6, `<=20` dropped **16**, `<=24` dropped 18. Twenty was the knee - and
  the sheet showed 11 of 14 clusters genuine, 3 false positives where the
  composition had actually changed (someone sat up; a different rock face).
  **Restore those by name; do not lower the threshold to accommodate them** or
  the selfie bursts all come back.

### Reject what cannot be framed

Check aspect ratio before framing anything. A stitched panorama or screenshot
(measured 3.1:1) cannot sit in a 2.40:1 frame at any setting. Drop it and say
so, rather than shipping one broken-looking shot in a good montage.

### Framing stills in a wide frame

Build the blur-fill composite **outside Resolve**. The API cannot author OFX or
add nodes, so a two-track background blur is hand-work on every clip.

- Composite at ~**1.1x the delivery raster** so a slow push always samples *down*
  and never upscales.
- **Suppress the background in proportion to how much of the frame it occupies.**
  A landscape photo fills ~52% of a 2.40:1 frame; a portrait only ~**29%**. The
  blur and brightness that flatter the first leave the second competing with its
  own wallpaper. Measured: wide fill `blur 45 / brightness 0.55 / saturation
  0.70`; narrow fill `blur 80 / brightness 0.38 / saturation 0.45`.
- **Portrait stills need motion.** At 29% of the width a static strip for two
  seconds reads as dead air; a slow push carries it.
- **Vary duration by block length rather than using one number.** 32 stills at 2s
  is over a minute of montage - enough to stall an ending. Dropping the largest
  day to 1.5s took the total from 2m32s to 2m14s.

The plan and the framing are both tooled:

```bash
python tools/photo_plan.py <src_dir> photo_plan.json --hamming 20 \
       --restore IMG_1646.jpeg,IMG_1655.jpeg --short-day 5:1.5
python tools/frame_photos.py photo_plan.json "<project media>/Photos"
```

`photo_plan.py` prints every drop with its reason - read that list before
building anything. ffmpeg here has no `drawtext`, so label contact sheets with
Pillow (`ImageDraw`) as `make_grid.py` does.

### Write rendered stills where the project can keep them

They become live project media the moment they are imported. Put them next to
the other project media, never in a scratch or renders dir.

### Tag imported stills for the project's colour management, or they go neon

In a **DaVinci YRGB Color Managed** project, an imported clip whose
`Input Color Space` reads `Project` inherits the project default - which on a
BRAW show is `Blackmagic Design Film Gen 5`. Feeding a Rec.709 still through a
log input transform produces violently oversaturated, posterised colour. It looks
like a broken grade and is nothing of the sort.

Set `SetClipProperty('Input Color Space', 'Rec.709 Gamma 2.4')` on every rendered
still after import, and check one back. Note `CreateEmptyTimeline` drops the new
timeline into the *current bin*, so a bin clip count can be one higher than the
media count - that entry is the timeline, not a clip.

### Rebuilding a cut from media-pool clips: three frame conventions collide

A timeline built with `AppendToTimeline` does not inherit grades, colour-group
membership or transforms - replay them afterwards with `CopyGrades`,
`AssignToColorGroup` and `SetProperty`. `CopyGrades` is faithful: a rebuilt
region measured **0.006** mean absolute difference against the source cut, with
identical mean luma and zero frames differing by more than 2%.

The frame maths is where it goes wrong, and it goes wrong silently:

- **`clipInfo` `startFrame`/`endFrame` are SOURCE frames.**
- **`GetLeftOffset()` and `GetDuration()` are TIMELINE frames.** On mixed-rate
  timelines they are not interchangeable - 59.94 fps GoPro on a 24 fps timeline
  is out by 2.4975x, which silently shortened every one of those shots to 40% of
  its length while reporting success.
- **`GetSourceStartFrame()` is the correct source position** and needs no scaling.
- **`GetSourceEndFrame()` does NOT reliably reproduce the duration** - measured
  +/-1 frame on 94 of the 24 fps clips. Take the *start* from the source getter
  and derive the *span* from `GetDuration() * fps / timeline_fps`, rounded up:
  Resolve floors the conversion, so `round()` lands a frame short.
- A residual of 1 source frame (17 ms, 0.4 of a timeline frame) on some 59.94 fps
  clips is unavoidable when snapping to 24 and is not worth chasing.

### Inserting a block mid-film is an AUDIO problem, not a picture problem

Check where each insert point falls **relative to audio item boundaries** before
agreeing to anything. Measured here: day 1 and day 2 inserts landed exactly on
music item boundaries and were clean, but the day 3 and day 4 points fell inside
a single continuous 944.6s music bed and a 944.6s nat bed, so both had to be
split, re-timed and lengthened. The day 1 and day 2 music files had **zero
unused tail**, so nothing could simply be extended.

**Do the music arithmetic before promising continuous music.** Required length
minus available material is the whole question. Here the longer cut needed
~1068s across days 3-5 against ~1011s of bed sources - and **an unused fifth
track was sitting in the music folder** that covered the shortfall exactly. Look
for unused material before looping anything; looping is audible and is the thing
a viewer notices in a quiet montage.

Three techniques that made this work without new material:

- **Carry the transition with the incoming day's music.** Starting day 2's music
  under the day 1 photo block turns the montage into the transition *into* day 2
  and removes the gap, instead of leaving 12s of silence where the outgoing track
  has run out.
- **Slice an existing contiguous nat bed rather than rebuilding it.** The days
  3-5 bed was cut into three per-day slices placed at the new day positions, so
  the photo blocks fall into the gaps between them and are naturally quiet under
  stills. No re-render, and the levelling work is preserved exactly.
- **Reuse the clips' own audio that arrives with a rebuild.** `AppendToTimeline`
  brings each clip's audio onto A1, already in sync. Enable that track and mute
  everything except the day you want per clip with `SetClipEnabled` - which is
  cheaper and safer than re-importing separate nat items, and reversible.

Verify by rendering a short region across a block **with audio** and reading
second-by-second RMS. Continuous music shows as a steady level with a dip only
where one track crossfades into the next.

## Maps and chapter cards from photo GPS

A trip film can carry its own itinerary. Everything below was measured on the
same 89-photo folder.

### Photo EXIF is the reliable GPS source - verify the camera before promising a track

**87 of 89 iPhone photos carried GPS. All 103 GoPro clips carried none.** The
GoPro files *do* have a `gpmd` telemetry stream, which looks promising until you
read it: `GPSF` (fix quality) was `0`, every `GPS5` sample was `(0, 0, ...)` and
`GPSU` reported a 2021 date. The camera never acquired a lock. Extract and check
before designing anything around a continuous track.

Two traps when reading GPMF:

- **`-map 0:d:0` selects the 4-byte `tmcd` timecode track, not the telemetry.**
  Find the stream whose `codec_tag_string` is `gpmd` with ffprobe and map it by
  absolute index - 71 KB instead of 4 bytes.
- GPMF is KLV: 4-byte FourCC, 1-byte type, 1-byte struct size, 2-byte repeat
  count, payload padded to 4 bytes, type `\x00` meaning nested. Guard the final
  packet - it is usually ragged and will throw on a fixed-width unpack.

Also: `DateTimeOriginal` needs a `DateTime` fallback, and `mdls` returns nothing
for files on an external volume Spotlight has not indexed.

### Geocode the stops, not the photos

Cluster photos into stops first (points more than ~1.5 km apart), then reverse
geocode those - 11 requests instead of 87. Nominatim requires an identifying
User-Agent and at most **one request per second**; cache the result so a rerun
costs nothing, and put `place names © OpenStreetMap contributors` on the card.

The returned address fields classify each stop for free, and that is what makes
the symbols honest rather than decorative: `Ostrów Tumski` came back as a quarter
of Wrocław, `Srebrna Góra` and `Kłodzko` as fortress towns, the `-Zdrój` suffix
marks a spa, and `Karłów` sits in the Table Mountains.

### Drawing the card

PIL is enough - no matplotlib needed, and macOS ships **Futura**, which suits a
travel film and carries Polish diacritics. Equirectangular with a `cos(lat)`
correction is fine at trip scale.

- **Two maps, not one.** The main map scaled to the DAY, plus a small inset of the
  whole trip with that day picked out. Scaling everything to the trip bounding box
  turns each day into an unreadable speck - a 3 km walk and a 66 km drive cannot
  share one scale.
- **Pixels per km is `s / 111`, where `s` is pixels per degree.** Inverting that
  put `1 km` on every card regardless of scale.
- **Reserve the furniture before placing labels.** Seed the collision list with
  the scale bar and compass, clamp labels inside the map box, and when a cluster
  has no free slot **drop the label and keep the symbol** rather than overlapping.
  Sort by notability first so the destination keeps its name while a waypoint
  yields - otherwise Karłów, the whole point of the trip, silently loses out.
- Tie ornament to data where possible: hill hachures were placed at photos taken
  above 600 m, so the relief drawn is relief that was walked.

### Offer a language, and treat the fun facts as unverified

Put every display string behind a language table (`--lang en|pl`) rather than
hard-coding English; dates and stat words need translating too, not just labels.

Short notable-place notes ("Chopin played here in 1826", "the Skull Chapel at
Czermna") come from **general knowledge, not from the geocoder**. Keep them in one
table, mark them as needing a check, and show the user before delivery - a wrong
fact burnt into a family film is worse than no fact.

```bash
python tools/photo_gps.py photo_gps.json <photo_dir>          # EXIF GPS
python tools/geocode_stops.py photo_gps.json trip_stops.json  # 1 req/sec, cached
python tools/chapter_cards.py cards --lang pl                 # per-day
python tools/chapter_cards.py cards --lang pl --summary       # closing card
```

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

Ask the three recording-settings questions from *Ask how the camera was DRIVEN* for
the incoming material - auto WB, auto exposure, log or already-processed. They are
asked per intake, not once per project: a new day can come off a different camera or
a different mode, and the answers decide whether these clips get a white balance at
all.

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
S9   → group "S9"   → pre-clip: camera match ┘   node 2: Film Look Creator
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
- **Node enabled state cannot be read back.** `SetNodeEnabled` is write-only -
  there is no `GetNodeEnabled` - and `GetToolsInNode` lists a node's tools
  identically whether the node is active or bypassed. So a graph readback proves
  a node *exists*, never that it is *doing anything*. Do not infer double-applied
  effects, wasted render time, or a "wrong" graph from presence alone; ask the
  user, or toggle the node and measure the image.
- **`SetCDL` is write-only too - there is no `GetCDL`.** A clip's balance cannot
  be read back at all, and `SetCDL` replaces the whole correction, so a second CDL
  pass on the same node erases the first one invisibly. Journal every per-clip
  pass to a plan JSON and recompose from it.
- **Scratch is not disposable once the project references it.** Derived audio
  beds, baked LUTs and normalised stems get written to a scratch dir and then
  become live project media. Deleting that dir as "temp" takes the timeline
  offline silently - the render still had picture, and days 3-5 audio was simply
  gone. Before removing any scratch folder, walk the timeline's media paths and
  refuse to delete anything referenced; better still, write project-referenced
  derivatives next to the other project media, not into `renders/`. Keep the
  builder scripts - deterministic builders made this fully recoverable.
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
- **Render job metadata reports `IsExportVideo` / `IsExportAudio`**, not the
  `ExportVideo` / `ExportAudio` keys you passed to `SetRenderSettings`. Asserting
  on the setter's names returns `None` and looks exactly like a misconfigured job
  when the job is fine. Always gate a long render on the `Is*` names - days 3-5
  once shipped silent through five masters because nothing checked.
- **`DeleteAllRenderJobs()` returns `True` without clearing a finished queue, and
  `AddRenderJob()` then refuses** - sometimes returning an empty string for a job
  it *did* create, so both the success and the failure lie. Bounce the page
  (`OpenPage('edit')` then `OpenPage('deliver')`), which genuinely empties the
  queue, then read `GetRenderJobList()` back and assert on the job's
  `TimelineName` and `OutputFilename` before starting it. A stale queue entry will
  otherwise re-render the previous job and report Complete.
- **H.264 refuses odd render dimensions.** `AddRenderJob` fails silently on a
  height like 267; keep QC proxy sizes even.
- **A script that renders usually segfaults on teardown.** `StartRendering` ->
  poll -> exit dies with SIGSEGV *after* the render finished and printed its
  status. Chain the follow-up steps with `;` rather than `&&`, or the measurement
  after the render silently never runs and it looks like the render failed.
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
- **`create_timeline_from_clips` mixes TWO frame spaces in one dict, and the
  reader disagrees with the writer.** `startFrame`/`endFrame` are in the clip's
  **native** rate; `recordFrame` is in **timeline** frames. Feed 59.94 fps source
  into a 24 fps timeline with both in timeline frames and every clip lands ~40%
  short with a gap after it. Convert with `native = timeline * (src_fps/tl_fps)`
  (2.4975 for 59.94 -> 24). Then note Resolve **FLOORS** the conversion back, so a
  clip whose `native / 2.4975` has a small fractional part comes out one frame
  short and leaves a 1-frame gap - 7 of 15 did here. Add +2 native frames to those
  and re-check. `recordFrame` is REQUIRED; omitting it errors rather than
  appending. And `probe_timeline_structure` reports `source_start`/`source_end` in
  **timeline** frames, not the native frames the setter wants - do not round-trip
  one into the other. Always finish with `detect_gaps_overlaps`.
- **There is no `AddNode`.** A clip/group/timeline node graph exposes only
  `GetNumNodes`, `GetToolsInNode`, `SetLUT`/`GetLUT`, `SetNodeEnabled`,
  `SetNodeCacheMode`, `ApplyGradeFromDRX`, `ResetAllGrades`. Any fix needing a
  *new* node - a power window, a vignette, anything spatial - is hand work.
  `drx.generate` cannot author windows or OFX either, so there is no back door.
- **A spatial fix belongs on the colour GROUP's pre-clip graph**, not per clip:
  one node covers every shot, it runs before the clip CDLs and the look, and it
  costs nothing at render time. `group.GetPreClipNodeGraph()` starts with one
  empty node ready for it.
- **Do not script per-clip Fusion comps for a whole-timeline fix.** Tried on 66
  test clips: `AddTool`/`SetInput`/`ConnectInput` all succeed and read back
  correct on 66/66, but the render came out **~83% black frames, every clip
  partially black**, and ran ~5x slower. Disabling `perfAutoRenderCacheEnable` /
  `perfAutoRenderCacheFuEffect` did not help.
- **Fusion's Custom tool renders BLACK on `pow()` and on the `? :` ternary** in
  this build, and `AddTool('Gamut')` fails outright (`CineonLog`, `Merge`,
  `Background`, `Loader`, `BrightnessContrast` all add fine). Localise expression
  faults with a ladder test - one feature per rung - not by rewriting blind.
- **In DaVinci Intermediate a linear-light gain IS a constant offset**:
  `offset = log2(gain)/14`. So a spatial gain can be written with `+` and `*`
  only, no `pow`/`log` needed. The DI transfer function is
  `V <= 0.02740668 ? V/10.44426855 : 2^(V*14-7) - 0.0075`.
- **Never sample per-shot stats with `ffmpeg -ss <t> -i file`.** `-ss` before
  `-i` is a keyframe seek, so on a long-GOP master it lands early and mixes in
  the neighbouring shot - a sunlit forest path measured as mean luma 0.041. Do
  one sequential decode and slice by frame NUMBER against the shot manifest.
  Same trap as `-ss` on mp3.
- **Luma percentiles cannot see channel clipping, and this WILL ship a bad
  master.** The Jura v1 master passed every luma check (p999 max 0.977 against a
  0.985 limit, "0 shots over") while 106 of 263 shots had over 1% of pixels with
  a channel pegged. Scan R/G/B separately, every time, and treat
  *any-channel-pegged* as the number that matters.
- **A look `.cube` can be the source of the clipping.** Read its neutral axis
  before blaming the footage: `WRO_Look_MarvelOlive_final1` goes flat above input
  DI 0.5312 at output **R 0.500 / G 0.501 / B 0.499**, and G 0.501 is above
  display white (DI 0.5138) while B 0.499 is below - so its own flat top pegs
  green and not blue. Every blown highlight in that look is yellow-green by
  construction.
- **Derive the shoulder ceiling from the look, never from the 0.49 default.**
  On this look 0.49 crushed p99 from 0.936 to 0.617; 0.525 landed highlights at
  Rec.709 0.940/0.942/0.931 with zero pegging. Evaluate
  `look(ceiling) -> DI -> Rec.709` arithmetically first; it costs nothing and
  saves a 16-minute render.
- **A shoulder buys headroom to fix underexposure.** Once highlights cannot clip,
  exposure can be lifted freely - the shoulder absorbs the top. Fixing the blown
  highlights and the dark shots is therefore one change, not two competing ones.
- **Rebuilding a timeline DESTROYS the timeline-level OFX.** Delete-and-recreate
  (the normal way to re-cut) takes halation, grain and vignette with it, and OFX
  cannot be scripted back. After ANY re-cut, read `GetNumNodes()` on the timeline
  graph before rendering: `0` means the texture is gone and the master would ship
  bare. Either re-cut before the texture is added, or hand back for it to be
  re-added. Clip grades, group LUTs and shoulder LUTs all survive - only the
  timeline graph is lost.
- **`None` and `''` mean different things on a grade readback.** `GetLUT` returns
  `''` for "no LUT" and `None` when the call **failed**. `GetToolsInNode`
  likewise. Reading `None` from every clip *and* from a group LUT you know is set
  is not "the grade was lost" - it is the API being blocked. Check before
  panicking, and never re-apply a whole grade on the strength of a `None`.
- **`GetCurrentPage()` returning `null` means a modal dialog is up, and every
  grade read AND write silently fails while it is.** Run that self-test before
  trusting any readback and before every render. `OpenPage()` also returns `None`
  and does not move. Only a human dismissing the dialog on screen clears it.
- **Never kill a render process mid-flight.** Killing the controlling script
  leaves the render running, and the forced stop raises exactly the modal above -
  wedging the whole application. Call `StopRendering()`, poll
  `IsRenderingInProgress()` until it clears, then delete the job.
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
- **A fresh CLI interpreter is not always enough - the queue can stay wedged for
  every short-lived script while a long-lived MCP session still works.** Seen
  after a `SetLUT` pass followed by a `SetCDL` pass: newly spawned `python3`
  scripts got a handle whose *setters silently no-op* - `DeleteAllRenderJobs()`
  returned `True` while the jobs remained, `SetRenderSettings()` returned `True`,
  and `AddRenderJob()` returned `''` - with `get_page` reporting `deliver`, so no
  modal was up. The tell is a **lying setter**: delete the jobs, then re-read the
  job list from a different process; if they are still there, the handle is dead.
  Recovery: drive `delete_all_jobs` -> `set_format_and_codec` -> `set_settings`
  -> `add_job` -> `start` through the **MCP server's own process** instead of
  spawning another script. Do not keep retrying the CLI script - it cannot heal.
- **Highlight recovery is not measurable by the std of the top 3% of pixels** -
  compression lowers that std even when detail is fully restored. Verify with
  any-channel clip% (-> ~0), unchanged mean luma below the knee, and the eye.

## Source media safety

Never modify, transcode, or derive camera originals. Analysis output goes to
sidecars or scratch. Clip properties (`PAR`, `Input Color Space`) are Resolve
database changes, not media changes, and are safe.
