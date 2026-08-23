# 🎬 HyperFrames Unified

**All-in-one skill for HTML-based video production with HyperFrames**

**Author**: HyperFrames (HeyGen) | **Consolidated by**: Yingjie Bian | **Type**: VS Code GitHub Copilot Skill | **Version**: 1.1 | **Date**: June 2026

A consolidated skill that unifies all HyperFrames video production capabilities — composition authoring, animation adapters (GSAP, Anime.js, CSS, WAAPI, Lottie, Three.js, WebGPU), Tailwind CSS v4, CLI dev loop, media preprocessing, registry management, catalog contribution, website-to-video workflows, and skill discovery.

| | |
|---|---|
| 🎨 **Author** | HTML video compositions with GSAP timelines, scene transitions, and brand-aware design systems |
| 🔧 **Build** | Scaffold, lint, inspect, preview, and render videos via the HyperFrames CLI |
| 🎙️ **Produce** | Generate TTS narration, transcribe audio, remove backgrounds, and sync captions |
| 🌐 **Convert** | Capture websites and produce professional videos from them |
| 🖥️ **Simulate** | (Optional) Embed realistic Dynamics 365 and M365 Copilot UIs in demo videos |

> **Who it's for:** Video producers, content creators, developers, and marketers building HTML-based video compositions with HyperFrames.

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **Node.js >= 22** | HyperFrames CLI runtime | [Download](https://nodejs.org/) |
| **FFmpeg** | Video rendering | [Download](https://ffmpeg.org/) |

### Step 1: Get the Skill Files

**Option A — Agentic Skill Installer** (recommended):

1. Open the **Agentic Skill Installer** from the Activity Bar
2. Find **hyperframes-unified** in the Skills section
3. Click the download icon to install

**Option B — Copy the skill folder**:
```
<your-workspace>/
└── .github/
    └── skills/
        └── hyperframes-unified/
            ├── SKILL.md
            ├── README.md
            ├── references/
            ├── scripts/
            ├── templates/
            └── palettes/
```

### Step 2: Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Describe your task (e.g., "create a product launch video")
3. The skill activates and guides you through the workflow
> **Troubleshooting**: Skill not activating → verify `.github/skills/hyperframes-unified/SKILL.md` exists → reload VS Code.
---

## Skill Structure

```
hyperframes-unified/
├── SKILL.md                                  # Core hub — all domains
├── README.md                                 # This file
├── LICENSE.TXT                               # MIT License
├── artefact.yaml                             # Catalog metadata
├── house-style.md                            # Default motion, sizing, palettes
├── visual-styles.md                          # 8 named visual style presets
├── patterns.md                               # PiP, title cards, slide show
├── data-in-motion.md                         # Data/stats/infographic patterns
├── palettes/                                 # Color palette presets
├── templates/                                # Design picker HTML
├── scripts/                                  # Animation map, contrast, audio extraction
├── assets/                                   # SFX and media assets
└── references/
    ├── core/                                 # Composition authoring references
    │   ├── video-composition.md
    │   ├── motion-principles.md
    │   ├── typography.md
    │   ├── beat-direction.md
    │   ├── transitions.md (+ transitions/)
    │   ├── captions.md
    │   ├── audio-reactive.md
    │   ├── css-patterns.md
    │   ├── narration.md
    │   ├── techniques.md
    │   ├── dynamic-techniques.md
    │   ├── design-picker.md
    │   ├── prompt-expansion.md
    │   └── transcript-guide.md
    ├── adapters/
    │   └── gsap-effects.md                   # Drop-in GSAP effects
    ├── registry/
    │   ├── install-locations.md
    │   ├── wiring-blocks.md
    │   ├── wiring-components.md
    │   ├── discovery.md
    │   └── examples/
    ├── contribute-catalog/
    │   └── templates.md                      # Block/component starter templates
    └── website-to-hyperframes/
        ├── step-0-capture.md through step-6-validate.md
        ├── capabilities.md
        └── beat-builder-guide.md
    └── ui-skills/                            # Optional: Microsoft product UI compositions
        ├── dynamics/
        │   └── dynamics-form.html                # Complete D365 Opportunity form
        └── m365copilot/
            ├── copilot-chat-page.html            # M365 Copilot empty chat page
            └── copilot-response-page.html        # M365 Copilot response page
```

| File | Purpose | Edit directly? |
|------|---------|----------------|
| `SKILL.md` | Unified skill definition — all domains | No — syncs from central repo |
| `references/core/*` | Composition authoring deep-dives | No — loaded on demand |
| `references/adapters/*` | Animation adapter patterns | No — loaded on demand |
| `references/registry/*` | Block/component installation | No — loaded on demand |
| `references/website-to-hyperframes/*` | Website-to-video workflow steps | No — loaded on demand |

**Progressive loading**: Only SKILL.md loads at start. Reference files load on-demand to minimize context consumption.

---

## Workflow

### Video Composition

1. **Design** — Establish brand identity via design.md, visual presets, or design picker
2. **Plan** — Structure scenes, rhythm, timing, and techniques
3. **Layout** — Build end-state HTML+CSS (no animation yet)
4. **Animate** — Add GSAP timelines, transitions, entrances
5. **Validate** — Lint, inspect, contrast check, animation map
6. **Render** — Produce MP4/WebM via CLI

### Website to Video

1. **Capture** → 2. **Brand Identity** → 3. **Strategy** → 4. **Storyboard** → 5. **VO + Timing** → 6. **Build** → 7. **Validate & Deliver**

---

## What You Get

### Outputs

| Output | Description | When Available |
|--------|-------------|---------------|
| `*.mp4` / `*.webm` | Rendered video | After `npx hyperframes render` |
| `design.md` | Brand identity cheat sheet | After design system setup |
| `transcript.json` | Word-level timestamps | After transcription |
| `narration.wav` | TTS voiceover | After TTS generation |
| `transparent.webm` | Background-removed video | After `remove-background` |

---

## Preferences

No preferences available — the skill uses fixed defaults. Design choices are driven by `design.md` (per-project) and the visual style presets.

---

## Key Features

- **Unified knowledge** — All HyperFrames domains in one skill, no cross-skill confusion
- **7 animation adapters** — GSAP, Anime.js, CSS, WAAPI, Lottie, Three.js, WebGPU/TypeGPU
- **Full production pipeline** — From website capture to rendered MP4
- **UI Skills (optional)** — Pre-built Dynamics 365 and M365 Copilot sub-compositions for demo videos
- **Media preprocessing** — TTS (54 voices, 9 languages), transcription, background removal
- **Registry ecosystem** — Install and contribute reusable blocks and components
- **Progressive loading** — Hub SKILL.md + on-demand reference files for minimal context

---

## Portability

This skill is **fully self-contained**. To use in another workspace:

1. **Recommended**: Use the Agentic Skill Installer extension
2. **Manual**: Copy `hyperframes-unified/` → `.github/skills/hyperframes-unified/` in target workspace
3. Any Copilot agent will discover and invoke it automatically

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| WebGPU availability | Not all browsers/environments support WebGPU; guard with feature detection |
| Headless Chrome video textures | `copyExternalImageToTexture` may fail in headless; pre-extract frames as PNGs |
| Non-English TTS | Requires `espeak-ng` system-wide for non-English phonemization |
| Tailwind browser runtime | For offline/production renders, compile to CSS instead of using browser runtime |

---

## Usage Examples

```
"Create a 15-second social ad for my product"
"Add captions synced to narration.wav"
"Capture https://example.com and make a product demo video"
"Add a Three.js particle background to scene 2"
"Fix the timing on the title card transition"
"Install the grain-overlay component from the registry"
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-02 | Initial release — consolidated from 15 individual skills (animejs, contribute-catalog, css-animations, find-skills, gsap, hyperframes, hyperframes-cli, hyperframes-media, hyperframes-registry, lottie, tailwind, three, typegpu, waapi, website-to-hyperframes) |
| 1.1 | 2026-06-16 | Aligned with latest skill-creator standards (artefact.yaml updates, README template compliance) |

---

## License

Apache License 2.0 — see LICENSE.TXT.

---

*Built with VS Code, GitHub Copilot, and HyperFrames CLI.*
