# Skill Creator

**Author**: www.anthropic.com 

A **Copilot skill** for creating new skills, iteratively improving existing ones, and measuring skill performance through structured evaluation loops. Handles the full skill lifecycle — from intent capture and drafting, through test case execution with baseline comparison, to quantitative benchmarking and description optimization for triggering accuracy.

## Prerequisites

The skill works standalone for basic skill drafting. For full functionality, configure these:

| Requirement | Purpose | Required for |
|-------------|---------|-------------|
| **Subagents** (Claude Code / Cowork) | Parallel test case execution, blind comparison, grading | Run evals, Benchmark, Blind comparison |
| **Python 3.x** | Aggregation scripts, eval viewer, description optimization | Benchmark, Eval viewer, Description optimization |
| **Git + PyYAML** | Refresh the canonical RAPID task registry | RAPID metadata assignment |
| **`claude` CLI** | Description optimization loop (`claude -p`) | Description optimization |
| **Browser / Display** | Interactive eval viewer for human review | Eval viewer (use `--static` fallback in headless environments) |

Without subagents (e.g., Claude.ai), the skill still works for manual skill creation — test cases run sequentially and review happens inline in the conversation.

## Installation

Copy the `skill-creator/` folder into your VS Code workspace's skills directory (e.g., `.github/skills/`, `skills/`, or wherever you keep skills):

```
your-project/
├── <skills-directory>/
│   └── skill-creator/    ← This is the entire skill
└── (your skill workspaces go here as siblings)
```

Combines with other skills — just place them alongside in your skills directory.

## Usage

Open Copilot Chat and ask naturally:

| You say... | What happens |
|------------|-------------|
| "I want to create a skill for X" | Interactive interview to capture intent, then drafts SKILL.md |
| "turn this into a skill" | Extracts workflow from conversation history into a skill |
| "run the test cases" | Spawns parallel with-skill and baseline runs, grades results |
| "improve the skill based on feedback" | Reads feedback.json, generalizes fixes, reruns evals |
| "optimize the description" | Generates trigger eval queries, runs optimization loop |
| "package the skill" | Bundles into a distributable `.skill` file |

The core workflow loop is: **Draft → Test → Review → Improve → Repeat** until the user is satisfied.

## What's Inside

```
skill-creator/
├── SKILL.md                          # Core knowledge & behaviors
├── README.md                         # This file
├── LICENSE.txt                       # License
├── artefact.yaml                     # Catalog and distribution metadata
├── agents/
│   ├── grader.md                     # How to evaluate assertions against outputs
│   ├── comparator.md                 # Blind A/B comparison between two outputs
│   └── analyzer.md                   # Analyze why one version beat another
├── assets/
│   └── eval_review.html              # HTML template for trigger eval review
├── eval-viewer/
│   ├── generate_review.py            # Generates interactive eval viewer
│   └── viewer.html                   # Viewer HTML template
├── references/
│   ├── artefact-template.yaml        # Canonical skill catalog metadata template
│   ├── mappings-reference.md         # Valid metadata values and distribution contract
│   ├── rapid-registry.generated.json # RAPID task cache with source commit provenance
│   └── schemas.md                    # JSON schemas for evals, grading, benchmarks
└── scripts/
    ├── aggregate_benchmark.py        # Aggregates grading results into benchmark stats
    ├── generate_report.py            # Generates benchmark reports
    ├── improve_description.py        # Proposes improved skill descriptions
    ├── package_skill.py              # Packages skill into .skill file
    ├── quick_validate.py             # Quick validation checks
    ├── run_eval.py                   # Runs trigger eval queries
    ├── run_loop.py                   # Full description optimization loop
    ├── sync_rapid_registry.py        # Verifies or intentionally refreshes the pinned RAPID task cache
    └── utils.py                      # Shared utilities
```

## Core Workflow

### 1. Capture Intent
The skill interviews the user to understand what the skill should do, when it should trigger, expected output format, and whether test cases are appropriate.

### 2. Draft the Skill
Writes SKILL.md, README.md, LICENSE.TXT, and artefact.yaml following progressive disclosure. All per-skill RAPID metadata lives under `distribution.rapid-module`: canonical phase/stream references plus optional exact task slugs from a commit-pinned registry. Task groups, owners, I/O, and sequencing stay owned by RAPID and are derived rather than copied. Distribution remains disabled unless every portability condition is verified and the owner opts in.

### 3. Run Test Cases
Spawns parallel subagent runs — one with the skill, one baseline (no skill or old version). Saves outputs to `<skill-name>-workspace/iteration-<N>/` with timing data.

### 4. Evaluate Results
Launches an interactive eval viewer (`generate_review.py`) with two tabs:
- **Outputs** — side-by-side review with feedback textboxes
- **Benchmark** — quantitative pass rates, timing, and token usage

### 5. Iterate
Reads user feedback, generalizes improvements (avoiding overfitting to test cases), reruns evals into a new iteration directory, and repeats until satisfied.

### 6. Optimize Description
Generates trigger eval queries (should-trigger and should-not-trigger), runs an automated optimization loop, and applies the best-performing description.

## Environment-Specific Notes

| Environment | Subagents | Eval Viewer | Description Optimization |
|-------------|-----------|-------------|--------------------------|
| **Claude Code** | Full parallel execution | Browser-based | Full support via `claude -p` |
| **Cowork** | Supported (may need serial fallback) | Use `--static` for HTML file | Supported |
| **Claude.ai** | Not available — run tests sequentially | Present results inline | Not available |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.4 | 2026-08-21 | Added portability authoring rules to the Skill Writing Guide; derived distribution booleans must come from a scan, not from intent; existing `distribution.rapid-module` blocks are preserved on update; README template no longer pre-claims self-containment. |
| 1.3 | 2026-08-20 | Unified RAPID membership, canonical phase/stream/task references, and distribution eligibility under `distribution.rapid-module`; removed separate top-level RAPID mappings. |
| 1.2 | 2026-08-20 | Replaced copied RAPID activity and execution-step enums with commit-pinned canonical task mappings, registry synchronization, and derived placement metadata. |
| 1.1 | 2026-08-20 | Added explicit RAPID module distribution assessment to artefact.yaml generation, conservative opt-in defaults, namespace/self-containment checks, and mandatory master catalog regeneration guidance. |
| 1.0 | 2026-03-17 | Initial release — full skill lifecycle: capture intent, draft, run evals with baselines, benchmark with variance analysis, eval viewer, description optimization, blind comparison, packaging. Multi-environment support (Claude Code, Cowork, Claude.ai). |
