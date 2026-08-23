# 🛠️ README Template for VS Code Copilot Skills

> **Instructions**: Replace all `<placeholder>` values with your skill's details. Remove sections that don't apply. Delete this instruction block when done.

---

# <Emoji> <Skill Name>

**<One-line tagline describing what the skill does>**

**Author**: <Name> | **Type**: VS Code GitHub Copilot Skill | **Version**: <X.Y> | **Date**: <Month Year>

<2-3 sentence description of the skill — what it does, who it's for, and why it's useful.>

| | |
|---|---|
| <Emoji> **<Verb>** | <What it does — first capability> |
| <Emoji> **<Verb>** | <What it does — second capability> |
| <Emoji> **<Verb>** | <What it does — third capability> |

> **Who it's for:** <Target audience description>

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **<MCP Server Name>** | <What data/APIs it provides> | [Link](<url>) |
| **<Other Requirement>** | <Purpose> | — |

### Step 1: Configure MCP Server

> Skip if already configured.

Add to your VS Code `settings.json` (`Ctrl+,` → search `mcp`):

```json
"mcp": {
  "servers": {
    "<server-name>": {
      "command": "npx",
      "args": ["-y", "<package-name>"]
    }
  }
}
```

### Step 2: Get the Skill Files

**Option A — Agentic Skill Installer** (recommended):

Use the **Agentic Skill Installer** VS Code extension to browse and install skills directly into your workspace. See [Install the Agentic Skill Installer](https://github.com/mcaps-microsoft/ISDAIFirstAiBS#7-install-the-agentic-skill-installer) in the main setup guide for installation instructions.

1. Open the **Agentic Skill Installer** from the Activity Bar (left sidebar)
2. Find **<SkillName>** in the Skills section
3. Click the download icon (⬇) to install it into your workspace

**Option B — Clone the repo**:
```
git clone <repo-url>
```
Open the folder in VS Code.

**Option C — Copy only the skill folder** into an existing workspace:
```
<your-workspace>/
└── .github/
    └── skills/
        └── <SkillName>/
            ├── SKILL.md
          ├── README.md
          ├── LICENSE.TXT
          ├── artefact.yaml
            └── references/
                └── <reference-files>.md
```

### Step 3: Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Type `/<SkillName> hi` or describe your task
3. The skill activates and guides you through the workflow

> **Troubleshooting**: Skill not activating → verify `.github/skills/<SkillName>/SKILL.md` exists → reload VS Code. MCP errors → check config in `settings.json`.

---

## Skill Structure

```
<SkillName>/
├── SKILL.md              # Core workflow & configuration
├── README.md             # This file
├── LICENSE.TXT           # Package license
├── artefact.yaml         # Catalog metadata and distribution assessment
└── references/
    ├── <file1>.md        # <Purpose>
    ├── <file2>.md        # <Purpose>
    └── <file3>.md        # <Purpose>
```

| File | Purpose | Edit directly? |
|------|---------|----------------|
| `SKILL.md` | Skill definition — workflow, config, user preferences system | No — syncs from central repo |
| `README.md` | User-facing setup, workflow, outputs, and changelog | No — syncs from central repo |
| `LICENSE.TXT` | Package license | No |
| `artefact.yaml` | Catalog metadata, prerequisites, mappings, and distribution assessment | No — validate with the catalog aggregator |
| `references/<file1>.md` | <Description> — default settings | No — customize via preferences |
| `references/<file2>.md` | <Description> | No — syncs from central repo |

> **Important**: None of the skill files should be edited by hand. They're shared via the central repo and updated through `git pull`. All user customizations go through the **User Preferences** system (see below).

**Progressive loading**: Only core files load at start. Reference files load on-demand to minimize context consumption.

---

## Workflow

> Describe the step-by-step workflow the user experiences.

1. **<Step Name>** — <What happens>
2. **<Step Name>** — <What happens>
3. **<Step Name>** — <What happens>
4. **<Step Name>** — <What happens>

---

## What You Get

### Outputs

| Output | Description | When Available |
|--------|-------------|---------------|
| `<filename pattern>` | <Description> | <Condition> |
| `<filename pattern>` | <Description> | <Condition> |
| `<filename pattern>` | <Description> | <Condition> |

### File Naming Convention

```
<Naming pattern with placeholders>
```

---

## Preferences

> **If your skill has no configurable options, replace this entire section with:** "No preferences available — the skill uses fixed defaults."
>
> **If your skill has configurable options**, use the patterns below. See [meeting-scribe README](../.github/skills/meeting-scribe/README.md) for a full reference implementation.
>
> **If your skill has both shared config (repo files) AND user-level preferences (memory)**, include both `### User Preferences` and `### Shared Preferences`. If only user-level, include just `### User Preferences`.

### User Preferences

#### Architecture: Skill Files vs. User Preferences

<Skill Name> separates **shared behavior** from **user preferences**:

```
┌─────────────────────────────┐     ┌────────────────────────────────────────────┐
│   Skill Files (Git repo)    │     │  User Profile Memory (VS Code internal)   │
│                             │     │                                            │
│  SKILL.md                   │     │  /memories/                                │
│  references/<defaults>.md   │     │    <skill-name>-preferences.md             │
│                             │     │                                            │
│  ✅ Updated via git pull     │     │  ✅ Your custom options & overrides         │
│  ✅ Shared with all users    │     │  ✅ Follows you across ALL workspaces      │
│  ❌ Don't edit by hand       │     │  ✅ Auto-loaded every conversation          │
│                             │     │  ✅ Never committed to git                  │
└─────────────────────────────┘     └────────────────────────────────────────────┘
```

Skill files define **defaults and behavior**. User profile memory stores **your personal overrides**. When both exist, your preferences win.

#### Where Are User Preferences Stored?

User preferences live in **VS Code's user profile memory** (`/memories/`), not in your workspace files:
- **Not a file on disk** — managed by the Copilot memory system
- **Not committed** to git — never appears in `git status`
- **Follows you everywhere** — same preferences in every workspace and conversation
- **Auto-loaded** into context at the start of every conversation
- **Only editable through Copilot** — ask the skill to show/change/reset preferences

#### Memory Scopes

| Scope | Path | Persists across workspaces? | Persists across conversations? | Auto-loaded? |
|---|---|---|---|---|
| **User memory** | `/memories/` | ✅ Yes | ✅ Yes | ✅ Yes (first 200 lines) |
| **Repo memory** | `/memories/repo/` | ❌ No — per workspace | ✅ Yes | ✅ Yes |
| **Session memory** | `/memories/session/` | ❌ No | ❌ No | Listed only |

<Skill Name> uses **user memory** so user preferences follow you across all workspaces.

> **When to use repo memory instead**: If preferences are workspace-specific (different project = different settings), use `/memories/repo/<skill-name>-preferences.md`. The trade-off is that users must re-configure in each new workspace.

#### What Can Be Customized

> List all configurable aspects and their source files:

| Category | Examples | Source file (defaults) |
|----------|----------|------------------------|
| **<Category 1>** | <Add/remove/reorder entries, change defaults> | `references/<file>.md` |
| **<Category 2>** | <Toggle sections, change format> | `references/<file>.md` |
| **<Category 3>** | <Change paths, styling, behavior> | `SKILL.md` |

#### How to Change Preferences

Customize through **natural language** during any conversation. Every change requires confirmation before saving.

**During normal use (implicit):**
```
You: "<custom value that differs from default>"
Skill: ✅ Applied for this session.
       Want me to save this for future conversations?
       > Yes — save it
       > No — one-time use only
```

**Direct management (explicit):**

| What you want | What to say |
|---|---|
| See all preferences | *"Show my <skill-name> preferences"* |
| Add an item | *"Add 'X' to my <list name>"* |
| Remove an item | *"Remove 'X' from my <list name>"* |
| Reorder items | *"Reorder my <list> — put 'X' first"* |
| Reset to defaults | *"Reset my <skill-name> preferences"* |
| Reset one setting | *"Reset <setting> to default"* |

> **Tip**: You don't need to use exact wording. Copilot understands natural language — *"what are my settings?"* or *"show me my config"* work just as well.

**Confirmation rule**: Every write to memory shows the proposed change and requires Yes/No confirmation. No silent saves.

#### First-Time Setup

On first use (no preferences file yet), the skill runs with defaults from reference files. During your session, if you express non-default choices, the skill offers to save each one. You build up preferences organically.

#### New Workspace Behavior

Since preferences are in **user memory**, they follow you everywhere. A new workspace automatically picks up your existing preferences — no re-configuration needed.

Changes take effect on the next conversation — no restart needed.

---

## Key Features

- **<Feature>** — <Description>
- **<Feature>** — <Description>
- **<Feature>** — <Description>
- **<Feature>** — <Description>

---

## Portability

<State the skill's actual position rather than assuming it is self-contained: what ships in the
package, what it optionally depends on, and what degrades if that dependency is absent. If it is
genuinely self-contained with no external runtime dependencies, say so.>

To use in another workspace:

1. **Recommended**: Use the [Agentic Skill Installer](https://github.com/mcaps-microsoft/ISDAIFirstAiBS#7-install-the-agentic-skill-installer) extension — find the skill and click download
2. **Manual**: Copy `<SkillName>/` → `.github/skills/<SkillName>/` in target workspace
3. Ensure required MCP server(s) are configured
3. Any Copilot agent will discover and invoke it automatically
4. Your preferences follow you automatically via user profile memory — no re-configuration needed

> **Note**: User preferences are stored in user profile memory (`/memories/`), which follows you across all workspaces.

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| <Limitation> | <Details> |
| <Limitation> | <Details> |
| <Limitation> | <Details> |

---

## Usage Examples

```
/<SkillName> hi                    # Full guided workflow
/<SkillName> <example query 1>    # <Description>
/<SkillName> <example query 2>    # <Description>
/<SkillName> <example query 3>    # <Description>
```

---

## Changelog

| Version | Date | Changes |
|---------|------|----------|
| <X.Y> | <YYYY-MM-DD> | <Description of changes> |

---

## License

Internal use — Microsoft ISD EMEA.

---

*Built with VS Code, GitHub Copilot, and <MCP Server Name>.*
