---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
metadata:
  owner: dwojcik
  stream: platform
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any (if there are some, you can either use as is or modify if you feel something needs to change about them). Then explain them to the user (or if they already existed, explain the ones that already exist)
  - Use the `eval-viewer/generate_review.py` script to show the user the results for them to look at, and also let them look at the quantitative metrics
- Rewrite the skill based on feedback from the user's evaluation of the results (and also if there are any glaring flaws that become apparent from the quantitative benchmarks)
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages. So for instance, maybe they're like "I want to make a skill for X". You can help narrow down what they mean, write a draft, write the test cases, figure out how they want to evaluate, run all the prompts, and repeat.

On the other hand, maybe they already have a draft of the skill. In this case you can go straight to the eval/iterate part of the loop.

Of course, you should always be flexible and if the user is like "I don't need to run a bunch of evaluations, just vibe with me", you can do that instead.

Then after the skill is done (but again, the order is flexible), you can also run the skill description improver, which we have a whole separate script for, to optimize the triggering of the skill.

Cool? Cool.

## Communicating with the user

The skill creator is liable to be used by people across a wide range of familiarity with coding jargon. If you haven't heard (and how could you, it's only very recently that it started), there's a trend now where the power of Claude is inspiring plumbers to open up their terminals, parents and grandparents to google "how to install npm". On the other hand, the bulk of users are probably fairly computer-literate.

So please pay attention to context cues to understand how to phrase your communication! In the default case, just to give you some idea:

- "evaluation" and "benchmark" are borderline, but OK
- for "JSON" and "assertion" you want to see serious cues from the user that they know what those things are before using them without explaining them

It's OK to briefly explain terms if you're in doubt, and feel free to clarify terms with a short definition if you're unsure if the user will get it.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until you've got this part ironed out.

Check available MCPs - if useful for research (searching docs, finding similar skills, looking up best practices), research in parallel via subagents if available, otherwise inline. Come prepared with context to reduce burden on the user.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

### Skill Writing Guide

#### Anatomy of a Skill

```text
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
├── README.md (required)
│   └── Human-readable documentation (generated from template)
├── LICENSE.TXT (required)
│   └── MIT License (generated from references/license-template.txt)
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

These word counts are approximate and you can feel free to go longer if needed.

**Key patterns:**

- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```text
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

#### Write it portable

A skill gets copied. It gets installed under a different root, into a repository that does not
contain the one it was written in, and sometimes driven by an orchestrator rather than a person.
Each of these habits costs nothing while drafting and is expensive to retrofit.

- **Resolve paths from the skill folder, not the repository root.** A path written as
  `.github/skills/<name>/...` resolves to nothing anywhere else, and it fails quietly — a
  reference simply does not load. Write `python scripts/thing.py` and tell the reader to run it
  from the skill folder; in code, resolve from the script's own location.
- **Keep runtime content inside the package.** If you lean on host tooling, guard it ("if the
  repository provides X, run it") so the skill still works without it.
- **Declare sibling skills you depend on** instead of assuming the folder is there.
- **Discover project structure rather than assuming it** — read a setting, fall back to
  discovery, ask once. A fixed folder shape works in exactly one repository.
- **Document modes, inputs, and outputs, and the non-interactive path.** An orchestrator cannot
  improvise around an undocumented contract.
- **Put an approval point before external writes** so effects stay bounded under composition.

The `rapid-distribution-reviewer` skill owns these definitions and verifies them against the
files; following them here is what makes that review pass.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

### Write the README.md (mandatory)

Every skill must have a `README.md` alongside its `SKILL.md`. The README is human-facing documentation — it tells users what the skill does, how to install it, what it outputs, and how to configure preferences. While SKILL.md is instructions *for* Copilot, README.md is documentation *for people*.

Generate the README using the template in `references/readme-template.md`. Read the template, then fill in every `<placeholder>` with the skill's actual details. Remove sections that don't apply (e.g., if the skill has no MCP dependency, drop the MCP config step; if there are no preferences, replace the Preferences section with "No preferences available — the skill uses fixed defaults.").

The README must be:

- **Created** when a new skill is created — it's a mandatory deliverable alongside SKILL.md
- **Updated** when the skill is modified — if capabilities, outputs, prerequisites, or workflow change, the README must reflect that
- **Validated** when an existing skill is reviewed — check that README.md exists and is up-to-date with the current SKILL.md

If you're improving an existing skill that's missing a README, generate one as part of the improvement. If the skill already has a README, review it against the template and update any sections that are stale or missing.

### Write the LICENSE.TXT (mandatory)

Every skill must include a `LICENSE.TXT` file alongside its `SKILL.md` and `README.md`. The license ensures proper intellectual property coverage for every skill distributed from this repository.

Generate the LICENSE.TXT by copying the template from `references/license-template.txt`. The template is an MIT License with `Copyright (c) 2026 Microsoft Corporation` — use it as-is without modifications.

The LICENSE.TXT must be:

- **Created** when a new skill is created — it's a mandatory deliverable alongside SKILL.md and README.md
- **Validated** when an existing skill is reviewed — check that LICENSE.TXT exists in the skill folder. If it's missing, create it from the template

### Evaluate Preferences Need (mandatory checkpoint)

After drafting the SKILL.md and before moving to test cases, assess whether the skill would benefit from a **user preferences system** (Copilot Memory). This is a mandatory checkpoint — every new skill must go through this evaluation, even if the answer is "no preferences needed."

#### Why this matters

Skills that have configurable behaviors (menus, output paths, search presets, format options, toggles) create a problem when users customize them: edits to shared files leak into git commits, get overwritten on `git pull`, and cause merge conflicts. The Copilot Memory system (`/memories/`) solves this by giving each user their own persistent config that never touches the repo.

Full documentation: [`CONTRIBUTING.md` — Step 2b: Design User Preferences with Memory`](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/CONTRIBUTING.md#step-2b-design-user-preferences-with-memory-for-parameterizable-skills)

Reference implementation: [`.github/skills/meeting-scribe/SKILL.md`](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/tree/main/.github/skills/meeting-scribe) — demonstrates mandatory rules, type-dependent save timing, full list overrides, and preference management.

#### How to evaluate

Run through this checklist against the drafted skill. For each "yes", note the specific area:

| # | Question | If yes → preference candidate |
|---|----------|-------------------------------|
| 1 | Does the skill have configurable lists (menus, presets, folder paths)? | Store custom lists in user memory |
| 2 | Does the skill have settings users might want to change (format, verbosity, sections, themes)? | Store key-value overrides in user memory |
| 3 | Could users accidentally push personal config to the shared repo? | Move all user-facing config to memory |
| 4 | Does the skill show the same menu/options every session? | Load from memory first, fall back to defaults |
| 5 | Do different users need different defaults (e.g., different project paths, team names, environments)? | Memory gives each user their own config |
| 6 | Does the skill accept free-form input that the user might want to reuse (search terms, folder paths, recipient lists)? | Offer to save custom inputs as preferences |
| 7 | Does the skill have output formatting options (HTML vs markdown, detailed vs summary, color themes)? | Store format preferences in memory |

#### Determine Memory Scope for each preference

For every preference candidate identified above, determine the correct **memory scope**. This is critical — storing preferences in the wrong scope causes frustrating UX (preferences vanish when switching workspaces, or workspace-specific values leak to other projects).

**Three scopes available:**

| Scope | Path | Persists across workspaces? | Persists across conversations? | Best for |
|---|---|---|---|---|
| **User memory** | `/memories/` | ✅ Yes | ✅ Yes | Personal preferences that follow the user everywhere |
| **Repo memory** | `/memories/repo/` | ❌ No — per workspace | ✅ Yes | Project/workspace-specific settings |
| **Session memory** | `/memories/session/` | ❌ No | ❌ No | Temporary working state, in-progress context |

**Intent recognition — how to classify each preference:**

| Signal in the preference | → Scope | Why |
|---|---|---|
| Personal style/format choices (verbosity, themes, language) | **User** | Follows the person, not the project |
| Output folder paths, default recipients, personal API keys | **User** | Specific to the person's machine/identity |
| Custom quick-action menus, saved search presets | **User** | User curates these once, expects them everywhere |
| Project-specific paths (repo URLs, environment names, team names) | **Repo** | Different per workspace — wrong in other projects |
| Connection strings, Dataverse environments, ADO project/org | **Repo** | Tied to a specific project, not the user globally |
| Build commands, test configurations, deployment targets | **Repo** | Vary by codebase |
| In-progress FDD/TDD context, partial results, working state | **Session** | Disposable — only relevant to current conversation |
| Intermediate computation results, draft outputs | **Session** | Temporary scaffolding, not worth persisting |

**Decision tree (apply per preference candidate):**

```text
Is this preference the same regardless of which workspace the user opens?
  ├─ YES → User memory (/memories/)
  │         Examples: format preferences, personal menus, output style
  └─ NO → Would it still be useful in the next conversation about the same project?
           ├─ YES → Repo memory (/memories/repo/)
           │         Examples: project paths, environment names, team config
           └─ NO → Session memory (/memories/session/)
                     Examples: in-progress work, temporary state, draft data
```

**Present scope recommendations to the user** alongside the preference candidates:

> | Preference | Recommended Scope | Reasoning |
> |---|---|---|
> | Output format (markdown/HTML) | **User** `/memories/` | Personal style — same preference in all workspaces |
> | D365 environment URL | **Repo** `/memories/repo/` | Different per project — wrong value in other workspaces |
> | Current FDD draft state | **Session** `/memories/session/` | Temporary — only needed in this conversation |

Use `vscode_askQuestions` to confirm the scope for each preference with the user:

- **Header**: "MemoryScopes"
- **Question**: "I've recommended memory scopes for each preference. Do these look right, or should any be different?"
- **Options**:
  - `Looks good — proceed` (recommended)
  - `I want to change some scopes` — let user override, then update the design
- `allowFreeformInput: true`

**Important:** If the skill has preferences in **multiple scopes**, the SKILL.md must instruct Copilot to check each scope at conversation start. Example:

```markdown
## Preferences

At conversation start, load preferences from all applicable scopes:
1. `/memories/<skill-name>-preferences.md` — user-level preferences (format, style, menus)
2. `/memories/repo/<skill-name>-project.md` — workspace-level settings (environment, paths, team)

User-level preferences apply globally. Repo-level preferences override user-level for workspace-specific values.
```

#### Present the assessment to the user

After evaluating, present the findings clearly. The format depends on the result:

**If NO preference candidates found** (all "no" answers):

> **Preferences check:** I evaluated your skill against the preferences checklist and it doesn't need a user preferences system right now. The skill uses fixed behaviors with no user-configurable options — keeping it simple.
>
> If you later add configurable menus, output paths, or user-facing settings, consider adding preferences at that point. See [CONTRIBUTING.md — Preferences](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/CONTRIBUTING.md#step-2b-design-user-preferences-with-memory-for-parameterizable-skills) for guidance.

**If preference candidates ARE found** (one or more "yes" answers):

> **Preferences check:** Your skill has areas that would benefit from user preferences (Copilot Memory). Here's what I found:
>
> | Area | What it enables | Recommended Scope | Example |
> |------|----------------|-------------------|---------|
> | [area from checklist] | [what the preference stores] | [User/Repo/Session] | [concrete example for this skill] |
> | ... | ... | ... | ... |
>
> **What are preferences?** They let each user customize the skill's behavior (menus, paths, formats, defaults) without editing shared files. Preferences are stored in Copilot Memory — they persist across conversations, never get committed to git, and survive `git pull`. Each user gets their own config automatically.
>
> **Memory scopes:** User (`/memories/`) = follows you everywhere. Repo (`/memories/repo/`) = workspace-specific. Session (`/memories/session/`) = current conversation only.
>
> Full docs: [CONTRIBUTING.md — Preferences](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/CONTRIBUTING.md#step-2b-design-user-preferences-with-memory-for-parameterizable-skills)
> Reference implementation: [meeting-scribe](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/tree/main/.github/skills/meeting-scribe)
>
> **What would you like to do?**

Then use `ask_questions` to let the user decide:

- **Header**: "PreferencesDecision"
- **Question**: "Should this skill support user preferences?"
- **Options**:
  - `Yes — add preferences now` (recommended if 2+ areas found)
  - `Yes — but add later` — skip for now, add as a future improvement
  - `No — keep it simple` — no preferences needed
- `allowFreeformInput: true`

#### If the user chooses "Yes — add preferences now"

Follow the implementation pattern from [CONTRIBUTING.md Step 2b](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/CONTRIBUTING.md#step-2b-design-user-preferences-with-memory-for-parameterizable-skills):

1. **Define defaults in reference files** — create a `references/defaults.md` (or similar) with shared default values
2. **Add MANDATORY RULES** at the top of SKILL.md — load preferences at conversation start, save prompts with "Why" rationale, never-save-silently rule
3. **Add a Preferences section** to SKILL.md — instruct the skill to check `/memories/<skill-name>-preferences.md` and apply overrides
4. **Implement save prompts** — when users provide custom values, ask immediately (before processing) if they want to save for next time
5. **Support preference management** — show/add/remove/reset via natural language
6. **Update README.md** — document the preferences architecture and available settings

Use `ask_questions` to walk the user through which specific areas to make configurable, what the default values should be, and the save-prompt timing for each value type.

#### If the user chooses "Yes — but add later"

Add a `<!-- TODO: Preferences -->` comment in SKILL.md listing the identified areas, so the user has a reminder when they come back to it:

```markdown
<!-- TODO: Preferences — the following areas were identified as preference candidates:
- [area 1]: [description]
- [area 2]: [description]
See CONTRIBUTING.md Step 2b for implementation guidance.
-->
```

Key sections to fill in carefully:

- **Author** — fetch the current user's name by running `git config user.name` in the terminal. Use this value for the `<Name>` placeholder in the Author line. If git config returns empty, ask the user for their name.
- **Skill Structure** — list actual files in the skill folder, not placeholders
- **Workflow** — describe the real user-facing workflow steps
- **Outputs** — what the skill produces (files, reports, etc.)
- **Prerequisites** — actual MCP servers, tools, or dependencies needed
- **Preferences** — if the skill supports user preferences, document the architecture; if not, say so
- **Changelog** — add an entry for the current version

Place the generated `README.md` directly inside the skill folder (sibling to `SKILL.md`).

### Generate artefact.yaml (mandatory)

Every skill must include an `artefact.yaml` file — this is the structured metadata that powers the skill catalog, the Agentic Skill Installer extension, methodology-based discovery, and explicit opt-in distribution to RAPID projects.

Read the template from `references/artefact-template.yaml` and the valid enum values from `references/mappings-reference.md`. Fill in every field based on the skill's actual capabilities.

The artefact.yaml must be:

- **Created** when a new skill is created — it's a mandatory deliverable alongside SKILL.md, README.md, and LICENSE.TXT
- **Updated** when the skill is modified — if capabilities, prerequisites, methodology mappings, or ownership change, the artefact.yaml must reflect that
- **Validated** when an existing skill is reviewed — check that artefact.yaml exists and is up-to-date. If missing, generate it from the template

#### How to fill it in

1. **Read the template** from `references/artefact-template.yaml` — it has all fields with inline comments explaining each one
2. **Read the mappings reference** from `references/mappings-reference.md` — it has the valid values for local enum fields and explains how canonical RAPID task mappings are resolved
3. **Fill in identity** — `name` (must match the skill folder name), `description` (from SKILL.md frontmatter)
4. **Fill in ownership** — `author` (use `git config user.name` or ask), `maintainers` (Microsoft aliases), `support` email
5. **Fill in lifecycle** — `version`, `created`/`updated` dates, `status`
6. **Fill in classification** — `type` (usually `skill`), `category` (functional domain), `installer-group` (one of: presales, methodology-manager, governance, delivery, productivity — used by the Agentic Skill Installer UI), `roles` (who uses this), `phases` (when)
7. **Fill in methodology mapping** — `methodologies`, then the per-methodology block:
   - `surestep365.phases` + `surestep365.activities` for SureStep365 (use `{code, name}` objects so activity names survive JSON aggregation)
8. **Evaluate RAPID module distribution** — this is an explicit, conservative opt-in:
  - Every manifest must include the full `distribution.rapid-module` assessment block. For a nonmember, keep `enabled: false`, omit `mapping`, and retain the conservative defaults. Do not omit the assessment block.
  - Keep every per-skill RAPID attribute in `distribution.rapid-module`. Do not add `RAPID` to `methodologies` and do not create a top-level `rapid:` block.
  - A skill belongs to the RAPID module when `distribution.rapid-module.mapping` is present. `enabled` is a separate distribution approval flag: a mapped skill may remain disabled until portability and owner approval are complete.
  - Ground `mapping.phases`, `mapping.streams`, and `mapping.tasks` in `references/rapid-registry.generated.json`, which records the exact source commit from `mcaps-microsoft/RAPID`. Use the pinned cache by default and verify it with `python <skill-creator-folder>/scripts/sync_rapid_registry.py --check`. Run the command without `--check` only when intentionally advancing the approved RAPID source commit; never fill gaps from memory.
  - Use canonical phase folder slugs and stream folder slugs. `phases` must contain at least one value; `streams: []` is valid for unstreamed scope.
  - Add a canonical task slug only when the skill materially performs, produces, or validates that task. Compare task name, purpose, inputs, outputs, owner, and source path; output semantics are stronger evidence than keywords. Present ambiguous candidates for confirmation instead of guessing. `tasks: []` is valid when the skill belongs at phase/stream level but claims no exact task.
  - Task groups (`context`, `outcomes`, `eval`, `refinement`), owners, I/O, and predecessor sequencing are read from RAPID task files and displayed by the atlas. Never copy them into skill metadata.
  - Never recreate artificial AiBS activities such as `project-setup`, `foundation-strategy`, `authored`, `solutioned`, `designed`, `built`, `tested`, or `loop-complete` in RAPID metadata. Runtime ADO tags may remain in skill contracts, but they do not define methodology placement.
  - Leave `distribution.rapid-module.enabled: false` unless the skill owner explicitly approves redistribution through RAPID.
  - A skill may be enabled only when its status is `beta` or `production`, its licence permits redistribution, and both `namespace-safe` and `self-contained` are true.
  - **Namespace-safe** means the skill works from `.github/skills/AIBS/<name>/`. Search the whole package for hard-coded root paths such as `.github/skills/<name>/` and replace them upstream with paths resolved from the skill folder before setting this true.
  - **Self-contained** means every runtime file is inside the skill folder or another AiBS skill named in `required-skills`. Repository-level `docs/`, scripts, templates, or sibling skills that are not declared make this false.
  - Both are claims about files, not about intent. Do not set them true because the [portability rules](#write-it-portable) were followed while drafting — leave them false and let `rapid-distribution-reviewer` derive them from a scan of the finished package.
  - Set `mode` to `standalone` when the skill is independent of RAPID behavior, `supporting` when it complements RAPID, or `substitute` only when it intentionally replaces one or more canonical tasks. A substitute requires non-empty `mapping.tasks` and explicit owner confirmation.
  - Record dependency closure in `required-skills`, known coexistence problems in `conflicts-with`, and direct RAPID plane access in `plane-access`. `raw` is immutable and may never appear under `writes`.
  - Do not infer readiness. If any condition is unverified, keep `enabled: false` and report what must change before opt-in.
  - **When updating an existing skill, do not regenerate an existing `distribution.rapid-module` block.** Preserve it as written: `namespace-safe`, `self-contained`, `enabled`, and `mapping` may already carry values a review derived from evidence you cannot reproduce here, and regenerating them silently discards that work. If your change affects them, say so and route to `rapid-distribution-reviewer`.
9. **Fill in prerequisites** — 6 categories:
   - `mcp_servers` — MCP servers the skill talks to (with `name`, `purpose`, `required`, `install`)
   - `cli_tools` — command-line tools invoked (with `name`, `purpose`, `required`, `install`, `verify`)
   - `python_packages` — Python packages needed (with `name`, `purpose`, `required`, `install`)
   - `npm_packages` — Node.js / npm packages needed (with `name`, `purpose`, `required`, `install`, optional `verify`)
   - `extensions` — VS Code extensions required (with `name`, `purpose`, `required`)
   - `environment` — runtime environments / IDEs / platforms that are provisioned, not one-command-installed (with `name`, `purpose`, `required`, optional `setup`)
10. **Fill in documentation** — `documentation` URL, `repo`, `project`
11. **Fill in technologies and tags** — technology stack and free-form search tags

#### Important rules for SureStep365 activities

Activities must use `{code, name}` objects — **not plain strings**. Plain strings lose their names when aggregated to JSON because YAML comments are stripped.

**Correct:**
```yaml
activities:
  - code: "05-04"
    name: "Configuration & Development activity set"
```

**Wrong** (name lost in JSON):
```yaml
activities:
  - "05-04"    # Configuration & Development activity set
```

RAPID module mappings do not use activity objects. They reference canonical phases, streams, and optional tasks under `distribution.rapid-module.mapping`.

#### After generating

Show the generated artefact.yaml to the user for confirmation before writing it. Highlight any fields where you made assumptions (e.g., methodology mappings, activity selections). Never enable RAPID distribution based on an assumption.

After writing or changing any AiBS skill file, regenerate the catalog from the repository root:

```bash
python scripts/aggregate-artefacts.py
python scripts/aggregate-artefacts.py --check
```

The aggregation command is also the package conformance gate. It rejects missing companion files, incomplete manifest fields, invalid enums, malformed prerequisites, inconsistent product mappings, stale template placeholders, invalid RAPID references, and an out-of-date catalog. Commit the resulting `.github/skills/master-artefacts.json` in the same change. The catalog fingerprints the complete skill folder, so a change to `SKILL.md`, `README.md`, references, scripts, assets, or `artefact.yaml` can all make it stale. If the aggregation script is not present because skill-creator was copied into another repository, state that catalog regeneration is not applicable there.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through. Do NOT use `/skill-test` or any other testing skill.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Within the workspace, organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.). Don't create all of this upfront — just create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. This is important: don't spawn the with-skill runs first and then come back for baselines later. Launch everything at once so it all finishes around the same time.

**With-skill run:**

```text
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">
```

**Baseline run** (same prompt, but the baseline depends on context):

- **Creating a new skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving an existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing — not just "eval-0". Use this name for the directory too. If this iteration uses new or modified eval prompts, create these files for each new eval directory — don't assume they carry over from previous iterations.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait for the runs to finish — you can use this time productively. Draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review them and explain what they check.

Good assertions are objectively verifiable and have descriptive names — they should read clearly in the benchmark viewer so someone glancing at the results immediately understands what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with the assertions once drafted. Also explain to the user what they'll see in the viewer — both the qualitative outputs and the quantitative benchmark.

### Step 3: As runs complete, capture timing data

When each subagent task completes, you receive a notification containing `total_tokens` and `duration_ms`. Save this data immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — it comes through the task notification and isn't persisted elsewhere. Process each notification as it arrives rather than trying to batch them.

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader subagent (or grade inline) that reads `agents/grader.md` and evaluates each assertion against the outputs. Save results to `grading.json` in each run directory. The grading.json expectations array must use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants) — the viewer depends on these exact field names. For assertions that can be checked programmatically, write and run a script rather than eyeballing it — scripts are faster, more reliable, and can be reused across iterations.

2. **Aggregate into benchmark** — run the aggregation script from the skill-creator directory:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta. If generating benchmark.json manually, see `references/schemas.md` for the exact schema the viewer expects.
Put each with_skill version before its baseline counterpart.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. See `agents/analyzer.md` (the "Analyzing Benchmark Results" section) for what to look for — things like assertions that always pass regardless of skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs.

4. **Launch the viewer** with both qualitative outputs and quantitative data:
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

   **Cowork / headless environments:** If `webbrowser.open()` is not available or the environment has no display, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Feedback will be downloaded as a `feedback.json` file when the user clicks "Submit All Reviews". After download, copy `feedback.json` into the workspace directory for the next iteration to pick up.

Note: please use generate_review.py to create the viewer; there's no need to write custom HTML.

5. **Tell the user** something like: "I've opened the results in your browser. There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

### What the user sees in the viewer

The "Outputs" tab shows one test case at a time:

- **Prompt**: the task that was given
- **Output**: the files the skill produced, rendered inline where possible
- **Previous Output** (iteration 2+): collapsed section showing last iteration's output
- **Formal Grades** (if grading was run): collapsed section showing assertion pass/fail
- **Feedback**: a textbox that auto-saves as they type
- **Previous Feedback** (iteration 2+): their comments from last time, shown below the textbox

The "Benchmark" tab shows the stats summary: pass rates, timing, and token usage for each configuration, with per-eval breakdowns and analyst observations.

Navigation is via prev/next buttons or arrow keys. When done, they click "Submit All Reviews" which saves all feedback to `feedback.json`.

### Step 5: Read the feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus your improvements on the test cases where the user had specific complaints.

Kill the viewer server when you're done with it:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the skill

This is the heart of the loop. You've run the test cases, the user has reviewed the results, and now you need to make the skill better based on their feedback.

### How to think about improvements

1. **Generalize from the feedback.** The big picture thing that's happening here is that we're trying to create skills that can be used a million times (maybe literally, maybe even more who knows) across many different prompts. Here you and the user are iterating on only a few examples over and over again because it helps move faster. The user knows these examples in and out and it's quick for them to assess new outputs. But if the skill you and the user are codeveloping works only for those examples, it's useless. Rather than put in fiddly overfitty changes, or oppressively constrictive MUSTs, if there's some stubborn issue, you might try branching out and using different metaphors, or recommending different patterns of working. It's relatively cheap to try and maybe you'll land on something great.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Make sure to read the transcripts, not just the final outputs — if it looks like the skill is making the model waste a bunch of time doing things that are unproductive, you can try getting rid of the parts of the skill that are making it do that and seeing what happens.

3. **Explain the why.** Try hard to explain the **why** behind everything you're asking the model to do. Today's LLMs are *smart*. They have good theory of mind and when given a good harness can go beyond rote instructions and really make things happen. Even if the feedback from the user is terse or frustrated, try to actually understand the task and why the user is writing what they wrote, and what they actually wrote, and then transmit this understanding into the instructions. If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag — if possible, reframe and explain the reasoning so that the model understands why the thing you're asking for is important. That's a more humane, powerful, and effective approach.

4. **Look for repeated work across test cases.** Read the transcripts from the test runs and notice if the subagents all independently wrote similar helper scripts or took the same multi-step approach to something. If all 3 test cases resulted in the subagent writing a `create_docx.py` or a `build_chart.py`, that's a strong signal the skill should bundle that script. Write it once, put it in `scripts/`, and tell the skill to use it. This saves every future invocation from reinventing the wheel.

This task is pretty important (we are trying to create billions a year in economic value here!) and your thinking time is not the blocker; take your time and really mull things over. I'd suggest writing a draft revision and then looking at it anew and making improvements. Really do your best to get into the head of the user and understand what they want and need.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Update the README.md to reflect any changes to workflow, outputs, prerequisites, or features (read `references/readme-template.md` if unsure about structure)
3. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs. If you're creating a new skill, the baseline is always `without_skill` (no skill) — that stays the same across iterations. If you're improving an existing skill, use your judgment on what makes sense as the baseline: the original version the user came in with, or the previous iteration.
4. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
5. Wait for the user to review and tell you they're done
6. Read the new feedback, improve again, repeat

Keep going until:

- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. Read `agents/comparator.md` and `agents/analyzer.md` for the details. The basic idea is: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

This is optional, requires subagents, and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

The queries must be realistic and something a Claude Code or Claude.ai user would actually type. Not abstract requests, but requests that are concrete and specific and have a good amount of detail. For instance, file paths, personal context about the user's job or situation, column names and values, company names, URLs. A little bit of backstory. Some might be in lowercase or contain abbreviations or typos or casual speech. Use a mix of different lengths, and focus on edge cases rather than making them clear-cut (the user will get a chance to sign off on them).

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

For the **should-trigger** queries (8-10), think about coverage. You want different phrasings of the same intent — some formal, some casual. Include cases where the user doesn't explicitly name the skill or file type but clearly needs it. Throw in some uncommon use cases and cases where this skill competes with another but should win.

For the **should-not-trigger** queries (8-10), the most valuable ones are the near-misses — queries that share keywords or concepts with the skill but actually need something different. Think adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, and cases where the query touches on something the skill does but in a context where another tool is more appropriate.

The key thing to avoid: don't make should-not-trigger queries obviously irrelevant. "Write a fibonacci function" as a negative test for a PDF skill is too easy — it doesn't test anything. The negative cases should be genuinely tricky.

### Step 2: Review with user

Present the eval set to the user for review using the HTML template:

1. Read the template from `assets/eval_review.html`
2. Replace the placeholders:
   - `__EVAL_DATA_PLACEHOLDER__` → the JSON array of eval items (no quotes around it — it's a JS variable assignment)
   - `__SKILL_NAME_PLACEHOLDER__` → the skill's name
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` → the skill's current description
3. Write to a temp file (e.g., `/tmp/eval_review_<skill-name>.html`) and open it: `open /tmp/eval_review_<skill-name>.html`
4. The user can edit queries, toggle should-trigger, add/remove entries, then click "Export Eval Set"
5. The file downloads to `~/Downloads/eval_set.json` — check the Downloads folder for the most recent version in case there are multiple (e.g., `eval_set (1).json`)

This step matters — bad eval queries lead to bad descriptions.

### Step 3: Run the optimization loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run in the background:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

This handles the full optimization loop automatically. It splits the eval set into 60% train and 40% held-out test, evaluates the current description (running each query 3 times to get a reliable trigger rate), then calls Claude to propose improvements based on what failed. It re-evaluates each new description on both train and test, iterating up to 5 times. When it's done, it opens an HTML report in the browser showing the results per iteration and returns JSON with `best_description` — selected by test score rather than train score to avoid overfitting.

### How skill triggering works

Understanding the triggering mechanism helps design better eval queries. Skills appear in Claude's `available_skills` list with their name + description, and Claude decides whether to consult a skill based on that description. The important thing to know is that Claude only consults skills for tasks it can't easily handle on its own — simple, one-step queries like "read this PDF" may not trigger a skill even if the description matches perfectly, because Claude can handle them directly with basic tools. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means your eval queries should be substantive enough that Claude would actually benefit from consulting a skill. Simple queries like "read file X" are poor test cases — they won't trigger skills regardless of description quality.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

---

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Claude.ai-specific instructions

In Claude.ai, the core workflow is the same (draft → test → review → improve → repeat), but because Claude.ai doesn't have subagents, some mechanics change. Here's what to adapt:

**Running test cases**: No subagents means no parallel execution. For each test case, read the skill's SKILL.md, then follow its instructions to accomplish the test prompt yourself. Do them one at a time. This is less rigorous than independent subagents (you wrote the skill and you're also running it, so you have full context), but it's a useful sanity check — and the human review step compensates. Skip the baseline runs — just use the skill to complete the task as requested.

**Reviewing results**: If you can't open a browser (e.g., Claude.ai's VM has no display, or you're on a remote server), skip the browser reviewer entirely. Instead, present results directly in the conversation. For each test case, show the prompt and the output. If the output is a file the user needs to see (like a .docx or .xlsx), save it to the filesystem and tell them where it is so they can download and inspect it. Ask for feedback inline: "How does this look? Anything you'd change?"

**Benchmarking**: Skip the quantitative benchmarking — it relies on baseline comparisons which aren't meaningful without subagents. Focus on qualitative feedback from the user.

**The iteration loop**: Same as before — improve the skill, rerun the test cases, ask for feedback — just without the browser reviewer in the middle. You can still organize results into iteration directories on the filesystem if you have one.

**Description optimization**: This section requires the `claude` CLI tool (specifically `claude -p`) which is only available in Claude Code. Skip it if you're on Claude.ai.

**Blind comparison**: Requires subagents. Skip it.

**Packaging**: The `package_skill.py` script works anywhere with Python and a filesystem. On Claude.ai, you can run it and the user can download the resulting `.skill` file.

**Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. In this case:

- **Preserve the original name.** Note the skill's directory name and `name` frontmatter field -- use them unchanged. E.g., if the installed skill is `research-helper`, output `research-helper.skill` (not `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the output directory -- direct writes may fail due to permissions.

---

## Cowork-Specific Instructions

If you're in Cowork, the main things to know are:

- You have subagents, so the main workflow (spawn test cases in parallel, run baselines, grade, etc.) all works. (However, if you run into severe problems with timeouts, it's OK to run the test prompts in series rather than parallel.)
- You don't have a browser or display, so when generating the eval viewer, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Then proffer a link that the user can click to open the HTML in their browser.
- For whatever reason, the Cowork setup seems to disincline Claude from generating the eval viewer after running the tests, so just to reiterate: whether you're in Cowork or in Claude Code, after running tests, you should always generate the eval viewer for the human to look at examples before revising the skill yourself and trying to make corrections, using `generate_review.py` (not writing your own boutique html code). Sorry in advance but I'm gonna go all caps here: GENERATE THE EVAL VIEWER *BEFORE* evaluating inputs yourself. You want to get them in front of the human ASAP!
- Feedback works differently: since there's no running server, the viewer's "Submit All Reviews" button will download `feedback.json` as a file. You can then read it from there (you may have to request access first).
- Packaging works — `package_skill.py` just needs Python and a filesystem.
- Description optimization (`run_loop.py` / `run_eval.py`) should work in Cowork just fine since it uses `claude -p` via subprocess, not a browser, but please save it until you've fully finished making the skill and the user agrees it's in good shape.
- **Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. Follow the update guidance in the claude.ai section above.

---

## Reference files

The agents/ directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory has additional documentation:

- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.
- `references/readme-template.md` — Template for generating the mandatory README.md for every skill. Read this template when creating or updating a skill's README.
- `references/license-template.txt` — MIT License template for the mandatory LICENSE.TXT in every skill. Copy as-is into the skill folder.
- `references/artefact-template.yaml` — Template for generating the mandatory artefact.yaml for every skill. Read this template when creating or updating a skill's catalog metadata.
- `references/mappings-reference.md` — Valid local enum values plus the canonical RAPID task-mapping and registry-freshness contract. Read this when filling in artefact.yaml.

---

Repeating one more time the core loop here for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Generate or update the README.md from `references/readme-template.md` — this is mandatory, every skill ships with a README
- Ensure LICENSE.TXT exists in the skill folder — if missing, create it from `references/license-template.txt`. This is mandatory, every skill ships with a license
- Run claude-with-access-to-the-skill on test prompts
- With the user, evaluate the outputs:
  - Create benchmark.json and run `eval-viewer/generate_review.py` to help the user review them
  - Run quantitative evals
- Repeat until you and the user are satisfied
- Final check: ensure README.md is up-to-date with the final version of the skill
- Final check: ensure LICENSE.TXT exists in the skill folder (create from `references/license-template.txt` if missing)
- Final check: ensure artefact.yaml exists and is up-to-date (create from `references/artefact-template.yaml` using values from `references/mappings-reference.md` if missing)
- Package the final skill and return it to the user.

Please add steps to your TodoList, if you have such a thing, to make sure you don't forget. If you're in Cowork, please specifically put "Create evals JSON and run `eval-viewer/generate_review.py` so human can review test cases" in your TodoList to make sure it happens.

Good luck!

