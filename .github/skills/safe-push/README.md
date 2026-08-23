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

1. **Pre-flight checks** — Detects uncommitted changes and agrees a commit message, but holds the commit until the target branch is settled, so nothing lands on `main` by accident. Then runs a **branch state survey** that joins open/merged/closed PR state to your local branches, so a branch that was already merged is never offered as a push target. If the tree is clean and the branch has nothing unpushed, it stops there rather than walking through a no-op rebase into a pull request GitHub would reject
2. **Stale branch sweep** — Reports in one line how many of your own branches are merged and can be cleaned up. Expands only if you ask, and never deletes without explicit confirmation
3. **Fork detection** — Tests write access to the remote. If denied, automatically creates a fork via `gh repo fork` and configures remotes (`origin` = fork, `upstream` = original)
4. **New branch** — Whenever a new branch is called for — the previous one was merged, closed or deleted, you were on `main`, or you just asked for one — brings `main` up to date the right way for your remote layout, starts the branch from there, carries over uncommitted changes, and only then commits them
5. **Rebase on main** — Updates local main (using `upstream` for forks), switches back to feature branch, and runs `git rebase main`
6. **Handle conflicts** — If rebase conflicts occur, lists conflicted files and waits for the user to resolve. Supports both "continue" and "abort" paths
7. **Push** — Uses `--force-with-lease` for previously pushed branches (safe force-push) or `-u` for new branches
8. **Pull Request** — Checks for `gh` CLI, creates a new PR (with correct fork syntax if applicable) or shows existing PR URL. Falls back to a manual compare link if `gh` is unavailable
9. **Summary** — Reports branch name, commits ahead of main, push type, PR status, and link

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
- **Branch state aware** — Joins PR state to your local branches *before* offering any of them, so a merged, closed or deleted branch is never proposed as a live target; it names the PR that closed it instead
- **Squash-merge safe** — Merge state always comes from the PR, never from `git branch --merged`, which reports squash-merged branches as unmerged
- **Confirms before it pushes** — One targeted check on the branch you actually chose. This also catches a pull request somebody *else* opened from your branch, before a rebase and force-push could disrupt it
- **Stale branch sweep** — Surfaces your own merged branches for cleanup in one line, with the owning PR as evidence, and never deletes without explicit confirmation
- **Merged branch recovery** — When the previous branch was merged, brings `main` up to date the right way for your remote layout and starts a fresh branch for new work
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
3. Invoke it with `/safe-push` — this skill is manual-only and is never auto-triggered

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
| Cannot delete at merge time | The skill stops at PR creation, so it is not running when the PR is merged — a PR held for approval may be merged days later by someone else. Merged branches are reclaimed by the sweep on a later run, not immediately |
| Branch state needs `gh` | Without the GitHub CLI the survey falls back to local branch names only, and says so — merged branches may then still appear in the list |

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
| 1.3 | 2026-08-21 | Stops after the survey when there is nothing to push — a clean tree with no unpushed commits previously walked the whole workflow into a pull request GitHub rejects |
| 1.2 | 2026-08-21 | Branch state survey runs before selection so merged branches are no longer offered; targeted confirmation on the chosen branch, which also catches a PR somebody else opened from it; stale branch sweep for your own merged branches; merge state read from the PR rather than `git branch --merged`; merged-branch recovery no longer assumes a fork. Manifest version corrected — it still read 1.0 |
| 1.1 | 2026-04-10 | Changed to manual-only invocation (`/safe-push`) — no longer auto-triggers on phrases like "push my changes" |
| 1.0 | 2026-03-23 | Initial release — pre-flight, rebase, push, PR, stash tracking, abort support |

---

## License

MIT License — Copyright (c) 2026 Microsoft Corporation. See [LICENSE.TXT](LICENSE.TXT) for full text.

---

*Built with VS Code and GitHub Copilot.*
