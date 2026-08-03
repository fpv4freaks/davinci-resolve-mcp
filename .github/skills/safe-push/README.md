# 🚀 Safe Push

**Rebase on main and push your branch to GitHub — safely, every time.**

**Author**: Daniel Wojcik | **Type**: VS Code GitHub Copilot Skill | **Version**: 1.0 | **Date**: March 2026

Automates the full push workflow: checks for uncommitted changes, rebases your feature branch on latest main, handles conflicts gracefully, pushes with `--force-with-lease`, and optionally creates a Pull Request — all in one command.

| | |
|---|---|
| 🔍 **Pre-flight** | Detects uncommitted changes, offers to commit, and lets you pick or create a branch |
| 🔄 **Rebase** | Updates local main and replays your commits on top — with conflict handling and abort support |
| 📤 **Push & PR** | Pushes safely with `--force-with-lease` and creates a Pull Request via `gh` CLI |

> **Who it's for:** All developers working in Git-based repos who want a safe, repeatable push workflow without memorizing the exact sequence of git commands.

---

## Installation & Setup

> **Recommended:** The easiest way to install this skill is via the **[Agentic Skill Installer](https://github.com/mcaps-microsoft/ISDAIFirstAiBS#7-install-the-agentic-skill-installer)** — a VS Code extension that lets you browse, install, and update skills with one click. No Git commands or manual file copying needed.

### Prerequisites

| Tool | Purpose | Link |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **Git** | Version control | [Download](https://git-scm.com/) |
| **GitHub CLI (`gh`)** | PR creation (optional) | [Download](https://cli.github.com/) |

### Step 1: Get the Skill Files

**Option A — Clone the repo** (recommended):
```
git clone https://github.com/mcaps-microsoft/ISDAIFirstAiBS.git
```
Open the folder in VS Code.

**Option B — Copy only the skill folder** into an existing workspace:
```
<your-workspace>/
└── .github/
    └── skills/
        └── safe-push/
            ├── SKILL.md
            └── README.md
```

### Step 2: Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Type `/safe-push`
3. The skill activates and guides you through the workflow

> **Troubleshooting**: Skill not activating → verify `.github/skills/safe-push/SKILL.md` exists → reload VS Code. Git errors → ensure you're inside a Git repository with a remote configured.

---

## Skill Structure

```
safe-push/
├── SKILL.md              # Core workflow & step-by-step instructions
├── README.md             # This file
└── LICENSE.TXT            # MIT License
```

| File | Purpose | Edit directly? |
|------|---------|----------------|
| `SKILL.md` | Skill definition — full push workflow with branch selection, rebase, push, and PR steps | No — syncs from central repo |
| `README.md` | Documentation and usage guide | No — syncs from central repo |
| `LICENSE.TXT` | MIT License — Copyright (c) 2026 Microsoft Corporation | No — syncs from central repo |

---

## Workflow

1. **Pre-flight checks** — Detects uncommitted changes (offers to stage & commit), confirms current branch, and presents branch selection (continue on current, switch to existing, or create new with auto-proposed name)
2. **Fork detection** — Tests write access to the remote. If denied, automatically creates a fork via `gh repo fork` and configures remotes (`origin` = fork, `upstream` = original)
3. **Merged branch detection** — Checks if the current branch was already merged (common after squash-merge). If so, syncs fork's main with upstream, creates a new branch, and carries over uncommitted changes
4. **Rebase on main** — Updates local main (using `upstream` for forks), switches back to feature branch, and runs `git rebase main`
5. **Handle conflicts** — If rebase conflicts occur, lists conflicted files and waits for the user to resolve. Supports both "continue" and "abort" paths
6. **Push** — Uses `--force-with-lease` for previously pushed branches (safe force-push) or `-u` for new branches
7. **Pull Request** — Checks for `gh` CLI, creates a new PR (with correct fork syntax if applicable) or shows existing PR URL. Falls back to a manual compare link if `gh` is unavailable
8. **Summary** — Reports branch name, commits ahead of main, push type, PR status, and link

---

## What You Get

### Outputs

| Output | Description | When Available |
|--------|-------------|---------------|
| Rebased branch | Feature branch replayed on top of latest main | After successful rebase |
| Pushed branch | Branch pushed to `origin` with `--force-with-lease` or `-u` | After push step |
| Pull Request | New PR created via `gh` CLI with auto-generated title and description | When `gh` is available and user confirms |
| Manual PR link | GitHub compare URL for manual PR creation | When `gh` CLI is not installed |
| Summary report | Branch name, commits ahead, push type, PR status, and link | End of every run |

---

## Key Features

- **Safe by default** — Uses `--force-with-lease` instead of `--force`, preventing overwrites of others' work
- **Rebase-first** — Always rebases on latest main before pushing, keeping history clean
- **Fork-aware** — Detects when you don't have write access, auto-creates a fork, configures remotes, and creates cross-fork PRs with the correct syntax
- **Merged branch recovery** — Detects when your branch was already squash-merged, syncs your fork's main with upstream, and creates a fresh branch for new work
- **Branch-aware** — Blocks direct pushes to `main`, proposes branch names following `feature/` / `fix/` / `docs/` conventions
- **Conflict recovery** — Supports both "continue after resolving" and "abort rebase" paths with stash tracking
- **Stash tracking** — Tracks all stash operations throughout the workflow and reminds about outstanding stashes on failure
- **PR automation** — Creates Pull Requests via `gh` CLI with auto-generated titles and descriptions from commit history
- **Graceful fallbacks** — Works without `gh` CLI by providing a manual PR comparison URL

---

## Portability

This skill is **fully self-contained**. To use in another workspace:

1. Copy `safe-push/` → `.github/skills/safe-push/` in target workspace
2. Ensure Git and a remote repository are configured
3. Any Copilot agent will discover and invoke it automatically

---

## Preferences

No preferences available — the skill uses fixed defaults. The target branch (`main`), remote (`origin`), and push strategy (`--force-with-lease`) are defined in `SKILL.md`.

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| Main branch hardcoded | Always rebases on `main` — repos using `master` or other default branches need to edit the skill |
| GitHub CLI recommended | Fork detection, auto-fork, and PR creation all require `gh` CLI; without it, only manual push + link is provided |
| No merge workflow | Only supports rebase strategy — if your team uses merge commits, this skill isn't the right fit |

---

## Usage Examples

This skill is **manual-only** (`disable-model-invocation: true`). It will never auto-trigger. Invoke it by typing:

```
/safe-push
```

The skill handles everything from there — uncommitted changes, branch selection, rebase, push, and PR creation.

---

## Changelog

| Version | Date | Changes |
|---------|------|----------|
| 1.1 | 2026-04-10 | Changed to manual-only invocation (`/safe-push`) — no longer auto-triggers on phrases like "push my changes" |
| 1.0 | 2026-03-23 | Initial release — pre-flight, rebase, push, PR, stash tracking, abort support |

---

## License

MIT License — Copyright (c) 2026 Microsoft Corporation. See [LICENSE.TXT](LICENSE.TXT) for full text.

---

*Built with VS Code and GitHub Copilot.*
