---
name: hyperframes-unified
description: >
  Unified HyperFrames video production skill — covers composition authoring, animation adapters (GSAP, Anime.js, CSS, WAAPI, Lottie, Three.js, WebGPU/TypeGPU), Tailwind CSS v4, CLI dev loop (init, lint, inspect, preview, render), media preprocessing (TTS, transcription, background removal), registry blocks/components, contributing to the catalog, website-to-video workflows, UI skills (Dynamics 365 and M365 Copilot sub-compositions for demo videos), and skill discovery. Use this skill whenever the user mentions HyperFrames, HTML video, video compositions, animation timelines, scene transitions, captions, voiceover, TTS, transcription, background removal, hyperframes CLI, hyperframes add, registry blocks, website capture to video, Tailwind in compositions, GSAP timelines, Anime.js, Lottie, Three.js, WebGPU, WGSL shaders, Web Animations API, deterministic rendering, Dynamics 365 video, Copilot chat video, D365 demo video, M365 Copilot demo, simulate Dynamics UI, simulate Copilot UI, or any HTML-based video production task. Even for partial mentions like "render a video", "add captions", "create a title card", or just pasting a URL and asking for a video — this is the skill to use.
---

# HyperFrames Unified

HTML is the source of truth for video. A composition is an HTML file with `data-*` attributes for timing, a GSAP timeline for animation, and CSS for appearance. The framework handles clip visibility, media playback, and timeline sync.

This skill consolidates all HyperFrames knowledge into one place. Sections below cover each domain; detailed reference files are loaded on demand.

**Domains:** 1. Core Composition · 2. GSAP · 3. Animation Adapters · 4. Tailwind · 5. CLI · 6. Media · 7. Registry · 8. Catalog Contribution · 9. Website-to-Video · 10. Skill Discovery · 11. UI Skills (optional)

---

## 1. Core Composition Authoring

The primary workflow for creating HyperFrames video compositions.

### Approach

**Exploratory requests** ("make me a product launch video"): understand audience, platform, priority, and variations before picking colors.

**Specific requests** ("add a title card", "fix timing"): skip discovery, go to rules.

### Design System

1. If `design.md` or `DESIGN.md` exists, read it first — it's the source of truth for brand colors, fonts, and constraints.
2. If no design exists, offer: named style presets ([visual-styles.md](visual-styles.md)), visual design picker ([references/core/design-picker.md](references/core/design-picker.md)), or quick setup from [house-style.md](house-style.md).

### Layout Before Animation

Position every element at its **most visible moment** as static HTML+CSS first. No GSAP yet. Then:
1. Add entrances with `gsap.from()` — animate FROM offscreen TO the CSS position
2. Add exits with `gsap.to()` — only on the **final scene**

### Data Attributes

| Attribute | Required | Values |
|-----------|----------|--------|
| `id` | Yes | Unique identifier |
| `data-start` | Yes | Seconds or clip ID reference |
| `data-duration` | Required for img/div/compositions | Seconds |
| `data-track-index` | Yes | Integer (layering via CSS z-index) |
| `data-composition-id` | Yes (compositions) | Unique composition ID |
| `data-composition-src` | No | Path to external HTML file |
| `data-width`/`data-height` | Yes (compositions) | Pixel dimensions |

### Timeline Contract

- All timelines: `gsap.timeline({ paused: true })`
- Register: `window.__timelines["<composition-id>"] = tl`
- Duration from `data-duration`, not GSAP timeline length
- Synchronous construction only — never inside async/setTimeout/Promises

### Rules (Non-Negotiable)

1. **Deterministic** — no `Math.random()`, `Date.now()`, or time-based logic
2. **GSAP** — only animate visual properties (opacity, x, y, scale, rotation, color, transforms)
3. **No `repeat: -1`** — calculate finite repeat count from duration
4. **No exit animations** except final scene — transitions handle exits
5. **Entrance animations on every element** — nothing appears fully formed
6. **Always use transitions between scenes** — no jump cuts
7. **Video must be `muted playsinline`** — audio via separate `<audio>` element
8. **No `<br>` in content text** — use `max-width` for wrapping
9. **60px+ headlines, 20px+ body, 16px+ labels** for rendered video

### References (loaded on demand)

| File | When to read |
|------|-------------|
| [references/core/video-composition.md](references/core/video-composition.md) | **Always** — video-medium rules override web instincts |
| [references/core/motion-principles.md](references/core/motion-principles.md) | **Always** — every composition has motion |
| [references/core/typography.md](references/core/typography.md) | **Always** — every composition has text |
| [references/core/beat-direction.md](references/core/beat-direction.md) | Multi-scene compositions — rhythm planning |
| [references/core/transitions.md](references/core/transitions.md) | Multi-scene — scene transitions |
| [references/core/captions.md](references/core/captions.md) | Text synced to audio timing |
| [references/core/audio-reactive.md](references/core/audio-reactive.md) | Visuals responding to music/sound |
| [references/core/css-patterns.md](references/core/css-patterns.md) | Text highlighting (marker, circle, burst) |
| [references/core/narration.md](references/core/narration.md) | Voiceover or TTS scripts |
| [references/core/techniques.md](references/core/techniques.md) | SVG drawing, Canvas 2D, CSS 3D, kinetic type, etc. |
| [references/core/dynamic-techniques.md](references/core/dynamic-techniques.md) | Dynamic caption animation (karaoke, slam, scatter) |
| [references/core/design-picker.md](references/core/design-picker.md) | Creating design.md via visual picker |
| [references/core/prompt-expansion.md](references/core/prompt-expansion.md) | Grounding user intent for compositions |
| [references/core/transcript-guide.md](references/core/transcript-guide.md) | Transcript handling, cleaning, quality checks |
| [visual-styles.md](visual-styles.md) | Named visual style presets |
| [house-style.md](house-style.md) | Default motion, sizing, color palettes |
| [patterns.md](patterns.md) | PiP, title cards, slide show patterns |
| [data-in-motion.md](data-in-motion.md) | Data, stats, infographic patterns |

---

## 2. GSAP Animation

GSAP is the primary animation engine. Create a paused timeline synchronously, register on `window.__timelines`, and let HyperFrames seek it.

### Core Methods

- `gsap.to(targets, vars)` — animate to `vars` (most common)
- `gsap.from(targets, vars)` — animate from `vars` (entrances)
- `gsap.fromTo(targets, fromVars, toVars)` — explicit start/end
- `gsap.set(targets, vars)` — apply immediately (duration 0)

### Key Rules

- camelCase properties (`backgroundColor`, not `background-color`)
- Transform aliases: `x`, `y`, `scale`, `rotation` (not raw transform strings)
- `autoAlpha` over `opacity` for visibility toggling
- Position parameter for timeline sequencing: absolute (`1`), relative (`"+=0.5"`), label (`"intro"`), alignment (`"<"`, `"<0.2"`)
- Never `repeat: -1` — always finite
- `gsap.matchMedia()` for responsive + accessibility

### References

- **[references/adapters/gsap-effects.md](references/adapters/gsap-effects.md)** — Drop-in effects: typewriter text, audio visualizer

---

## 3. Animation Adapters

HyperFrames supports multiple animation engines via runtime adapters. Each adapter follows the same contract: create animations synchronously, register on a global, let HyperFrames seek.

### Anime.js

Register on `window.__hfAnime`. Set `autoplay: false`. Adapter seeks with `instance.seek(timeMs)`.

```js
const anim = anime({ targets: ".mark", translateX: 280, duration: 1200, autoplay: false });
window.__hfAnime = window.__hfAnime || [];
window.__hfAnime.push(anim);
```

Use GSAP for complex sequencing unless the user specifically asks for Anime.js.

### CSS Animations

Use `data-start` for clip timing. Finite `animation-duration` and `animation-iteration-count`. Prefer `animation-fill-mode: both`. Use CSS custom properties for stagger. Good for decorative loops, shimmer, glow, masks.

### Web Animations API (WAAPI)

Create with `element.animate(...)`, finite `duration` and `iterations`, `fill: "both"`. Pause after creation. Adapter calls `document.getAnimations()` and sets `currentTime`. Good for lightweight DOM motion without GSAP dependency.

### Lottie / dotLottie

Register on `window.__hfLottie`. Set `autoplay: false`, `loop: false`. Load assets from local `assets/` directory. Adapter seeks lottie-web with `goToAndStop(timeMs, false)`.

### Three.js / WebGL

Listen for `hf-seek` event, render at `event.detail.time`. Create scene synchronously. Set `renderer.setSize(1920, 1080, false)` and `renderer.setPixelRatio(1)`. No `requestAnimationFrame` for render-critical motion. For AnimationMixer: `mixer.setTime(time)`.

### TypeGPU / WebGPU

Initialize WebGPU async, but register GSAP tweens **synchronously** before any `await`. Listen for `hf-seek` event. Call `await device.queue.onSubmittedWorkDone()` after GPU work for frame capture. Guard against unavailable WebGPU. For video-backed effects, wait for metadata before creating texture.

---

## 4. Tailwind CSS v4

For compositions created with `hyperframes init --tailwind`. Pinned to `@tailwindcss/browser@4.2.4` (v4, not v3).

### Key Rules

- Use `@theme` and `@utility` in `<style type="text/tailwindcss">` blocks
- No v3 `@tailwind` directives, no `tailwind.config.js`
- Keep Tailwind for layout/style, GSAP for motion
- Use complete class names in HTML (no dynamic class generation at seek time)
- Wait for `window.__tailwindReady` before capture
- Prefer transforms/opacity for animations
- Avoid hover, focus, scroll, viewport variants

---

## 5. CLI Dev Loop

Everything runs through `npx hyperframes`. Requires Node.js >= 22 and FFmpeg.

### Workflow

1. `npx hyperframes init my-video` — scaffold (templates: blank, warm-grain, play-mode, swiss-grid, vignelli, decision-tree, kinetic-type, product-promo, nyt-graph)
2. Author HTML composition
3. `npx hyperframes lint` — catch structural errors
4. `npx hyperframes inspect` — visual layout audit (text overflow, container escape)
5. `npx hyperframes preview` — hot-reload dev server
6. `npx hyperframes render` — produce MP4/WebM

### Rendering Flags

| Flag | Options | Default | Notes |
|------|---------|---------|-------|
| `--quality` | draft, standard, high | standard | draft for iterating |
| `--fps` | 24, 30, 60 | 30 | 60fps doubles render time |
| `--format` | mp4, webm | mp4 | WebM supports transparency |
| `--variables` | JSON object | — | Override composition variables |
| `--strict` | flag | off | Fail on lint errors |

### Troubleshooting

```bash
npx hyperframes doctor    # check environment
npx hyperframes browser   # manage Chrome
npx hyperframes info      # version details
npx hyperframes upgrade   # check for updates
```

When handing a project back, use the Studio project URL: `http://localhost:<port>/#project/<project-name>`

---

## 6. Media Preprocessing

Three CLI commands for asset production. Each downloads its model on first run.

### Text-to-Speech (`tts`)

```bash
npx hyperframes tts "Text" --voice af_nova --output narration.wav
npx hyperframes tts --list    # 54 voices
```

Voice IDs encode language: `a`=American, `b`=British, `e`=Spanish, `f`=French, `h`=Hindi, `i`=Italian, `j`=Japanese, `p`=Portuguese, `z`=Mandarin.

### Transcription (`transcribe`)

```bash
npx hyperframes transcribe audio.mp3 --model small
```

**Non-Negotiable:** Never use `.en` models unless audio is confirmed English. `.en` models **translate** non-English into English. Default model: `small` (not `small.en`).

| Model | Size | When |
|-------|------|------|
| `tiny` | 75 MB | Quick previews |
| `small` | 466 MB | **Default** — most content |
| `medium` | 1.5 GB | Noisy audio, music |
| `large-v3` | 3.1 GB | Production quality |

### Background Removal (`remove-background`)

```bash
npx hyperframes remove-background subject.mp4 -o transparent.webm
npx hyperframes remove-background subject.mp4 -o subject.webm --background-output plate.webm
```

Produces transparent VP9 WebM by default. Use `--background-output` for hole-cut plate (text-behind-subject). Quality presets: fast (CRF 30), balanced (CRF 18), best (CRF 12).

### TTS → Transcribe → Captions Chain

```bash
npx hyperframes tts script.txt --voice af_heart --output narration.wav
npx hyperframes transcribe narration.wav   # → transcript.json
```

---

## 7. Registry (Blocks & Components)

Install reusable items via `hyperframes add <name>`.

- **Blocks** — standalone sub-compositions (own dimensions/duration). Wire via `data-composition-src`.
- **Components** — effect snippets. Paste HTML/CSS/JS into host composition.

```bash
hyperframes add data-chart        # install block
hyperframes add grain-overlay     # install component
```

Blocks install to `compositions/<name>.html`. Components to `compositions/components/<name>.html`. Configurable in `hyperframes.json`.

### References

| File | Purpose |
|------|---------|
| [references/registry/install-locations.md](references/registry/install-locations.md) | Install paths and config |
| [references/registry/wiring-blocks.md](references/registry/wiring-blocks.md) | How to wire blocks into host |
| [references/registry/wiring-components.md](references/registry/wiring-components.md) | How to wire component snippets |
| [references/registry/discovery.md](references/registry/discovery.md) | Browse available registry items |

---

## 8. Contributing to the Catalog

For authoring **new** registry blocks or components and shipping as an upstream PR.

### Workflow

1. **Clarify** — block vs component, description, visual reference
2. **Scaffold** — create `registry/{blocks|components}/{name}/` with HTML + `registry-item.json`
3. **Build** — follow templates in [references/contribute-catalog/templates.md](references/contribute-catalog/templates.md)
4. **Validate** — `hyperframes lint` (0 errors), `hyperframes validate --no-contrast` (0 console errors)
5. **Preview** — `hyperframes render -o preview.mp4`, `hyperframes snapshot`
6. **Ship** — branch, format, update registry.json, generate catalog pages, commit, PR

### Caption Block Rules

- Font: 96px minimum (proportional), 64-72px (monospace)
- Readability: `-webkit-text-stroke: 2-3px` or multi-layer `text-shadow`
- Overflow: call `window.__hyperframes.fitTextFontSize()` on every group
- All IDs prefixed with 2-3 letter abbreviation to avoid collisions
- Never `tl.from(el, { opacity: 0 })` at same position as `tl.set(el, { opacity: 1 })`

---

## 9. Website to HyperFrames

Capture a website and produce a professional video from it. Triggers when a user provides a URL and wants a video.

### 7-Step Workflow

| Step | Action | Reference |
|------|--------|-----------|
| 0 | Capture & understand the brand | [references/website-to-hyperframes/step-0-capture.md](references/website-to-hyperframes/step-0-capture.md) |
| 1 | Write DESIGN.md brand identity | [references/website-to-hyperframes/step-1-design.md](references/website-to-hyperframes/step-1-design.md) |
| 2 | Strategy & messaging alignment | [references/website-to-hyperframes/step-2-brief.md](references/website-to-hyperframes/step-2-brief.md) |
| 3 | Storyboard + script (💬 user gate) | [references/website-to-hyperframes/step-3-storyboard.md](references/website-to-hyperframes/step-3-storyboard.md) |
| 4 | VO, timing + captions (💬 user gate) | [references/website-to-hyperframes/step-4-vo.md](references/website-to-hyperframes/step-4-vo.md) |
| 5 | Build compositions | [references/website-to-hyperframes/step-5-build.md](references/website-to-hyperframes/step-5-build.md) |
| 6 | Validate & deliver | [references/website-to-hyperframes/step-6-validate.md](references/website-to-hyperframes/step-6-validate.md) |

Also read: [references/website-to-hyperframes/capabilities.md](references/website-to-hyperframes/capabilities.md) (HyperFrames capability inventory)

### Video Types

| Type | Duration | Narration |
|------|----------|-----------|
| Social ad | 10-15s | Optional |
| Product demo | 30-60s | Full |
| Feature announcement | 15-30s | Full |
| Brand reel | 20-45s | Optional, music focus |
| Launch teaser | 10-20s | Minimal |

Formats: 1920x1080 (landscape), 1080x1920 (portrait), 1080x1080 (square).

---

## 10. Skill Discovery

Find and install agent skills from the open ecosystem.

```bash
npx skills find [query]         # search for skills
npx skills add <package> -g -y  # install globally
npx skills check                # check for updates
```

Browse at [skills.sh](https://skills.sh/). Verify quality before recommending: prefer 1K+ installs, official sources, repos with 100+ GitHub stars.

---

## 11. UI Skills (Optional)

Pre-built HTML sub-compositions that replicate Microsoft product UIs for demo videos, product tours, and promotional content. **This section is optional** — skip it unless the user needs realistic D365 or M365 Copilot UI in their video.

### Available UI Kits

#### Dynamics 365

Faithful reproduction of D365 model-driven app UI. A complete assembled Opportunity form is provided at `references/ui-skills/dynamics/dynamics-form.html`.

Components included: TopNav, Sidebar, CommandBar, RecordHeader, BusinessProcessFlow, TabBar, SectionCard, FormFields, TimelineCard, ScoreCard, SubgridCard — all assembled into one full form composition.

**Design tokens:** Brand `#0F6CBD` | Nav `#1B1B3A` | Background `#FAFAFA` | Font: Segoe UI | Card radius: 8px

#### M365 Copilot

Faithful reproduction of M365 Copilot chat UI. Two full-page compositions:
- `references/ui-skills/m365copilot/copilot-chat-page.html` — empty chat with sidebar, header, greeting, input, suggestion pills
- `references/ui-skills/m365copilot/copilot-response-page.html` — full response page with conversation, citations, follow-ups

**Design tokens:** Brand `#464feb` | Background `#fafafa` | Font: Segoe UI | Input radius: 32px

### Usage

Embed as sub-compositions in a HyperFrames project:

```html
<div id="el-d365"
     data-composition-id="dynamics-form"
     data-composition-src="compositions/dynamics/dynamics-form.html"
     data-start="0" data-duration="8" data-track-index="1"
     data-variable-values='{"recordTitle":"Contoso Deal","ownerName":"Jane Smith"}'>
</div>
```

Customize via `data-variable-values` per-instance or `--variables` at render time. Copy the HTML files from `references/ui-skills/` into your project's `compositions/` folder before use.

### Animation Patterns

All UI compositions use entrance-only animations (per HyperFrames rules): `gsap.from()` with staggered opacity + transforms. No exit animations. Timelines registered on `window.__timelines`, start `{ paused: true }`.

---

## Quality Checklist

- [ ] `npx hyperframes lint` — 0 errors
- [ ] `npx hyperframes validate` — 0 errors, contrast warnings addressed
- [ ] `npx hyperframes inspect` — no unintentional overflow
- [ ] Design adherence verified against design.md (if exists)
- [ ] Animation map reviewed for choreography (new/major compositions)
- [ ] Studio project URL provided to user
