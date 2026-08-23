# 🚀 Create Repo

> ☁️ **From "folder on my hard drive" to a shared, protected team project in one command.** One conversation pushes your workspace to GitHub, invites the right colleagues, and locks down `main` with the push rules you choose — backup, collaboration, and governance in a single flow.

> 🎯 **Creating a repo on a customer tenant?** By default the skill proposes to create the repo on the **`mcaps-microsoft`** org (or your personal account). To target a **customer's GitHub tenant** instead, just paste the customer repo or org URL after the command:
>
> ```
> /create-repo on https://github.com/<customer-org>
> /create-repo on https://github.com/<customer-org>/<existing-repo>
> ```
>
> The skill detects the host/org, checks your access on that tenant (running `gh auth login --hostname …` if needed), and runs the full creation/management flow against the customer tenant instead of `mcaps-microsoft`. See [Targeting a repo by URL](#targeting-a-repo-by-url-eg-a-customer-tenant-repo) for the full list of variants.
>
> ⚠️ <ins>**Advanced operations on `mcaps-microsoft` repos require `admin` rights.**</ins> On `mcaps-microsoft` your standing role is `maintain`, which is enough for day-to-day work but **not** enough for *Protect main*, *Remove protection*, *Change visibility*, *Update description*, *Manage Actions secrets/variables*, or *Manage webhooks*. <ins>**This skill fully supports the [JIT (Just-in-Time) admin process](#jit-just-in-time-admin-on-mcaps-microsoft-repos) — it files the JIT Request issue for you, pings an approver in Teams, waits for approval, and then resumes the queued operation automatically.**</ins> You never need to leave the conversation, and no admin role is held longer than the 1–2 hour window you request. See [JIT (Just-in-Time) admin](#jit-just-in-time-admin-on-mcaps-microsoft-repos) below for the full round-trip.

**Initialize a Git repo, create a GitHub remote, push, add collaborators, protect your branch, configure CODEOWNERS and access.yml — or manage all of these on an existing repo.**

**Author**: Daniel Wojcik | **Type**: VS Code GitHub Copilot Skill | **Version**: 4.4 | **Date**: May 2026

For new workspaces that need a Git repo and GitHub remote, or existing repos that need collaborator and protection management. Supports personal repos (private) and org repos like `mcaps-microsoft` (internal or private). Handles preflight checks, edge cases (existing repo, missing CLI, Start Right portal fallback), `.gitignore` setup, EMU account resolution, CODEOWNERS, access.yml, and safe-push integration.

| | |
|---|---|
| 🔍 **Checks** | Existing repo, gh CLI, auth, name collisions, account & org detection |
| 🏢 **Org support** | Create repos on `mcaps-microsoft` or other orgs with Internal or Private visibility |
| 🏗️ **Creates** | Git repo + GitHub remote in one flow |
| 📤 **Pushes** | All workspace files committed and pushed (auto-uses safe-push when installed) |
| ☁️ **Protects** | Online backup of your workspace on GitHub |
| 🔒 **Access** | Add/remove collaborators with PR-only, Standard, or Strict branch protection |
| 📄 **CODEOWNERS** | Define who must approve PRs for specific files or the whole repo |
| 📋 **access.yml** | Declarative access management for org repos (admins, maintainers, writers, teams) |
| ⚙️ **Manages** | View and change repo settings (visibility, description, protection, collaborators, CODEOWNERS, access.yml) |
| ⏳ **JIT admin** | On `mcaps-microsoft` (and any repo with a JIT template), auto-file a **JIT Request** issue for admin-only ops, **auto-open a Teams group chat with every maintainer from `access.yml`** (message prefilled with the JIT issue link, you press Send), then resume the queued op once any of them approves |

> **Who it's for:** Anyone starting a new VS Code workspace who wants it in GitHub quickly, or managing an existing repo's collaborators and branch protection. Especially useful for **small teams (2–6 people)** — tiger teams, pilots, skill-building sprints — who want proper collaboration hygiene without the overhead of a full DevOps setup.

### Why use it?

Your local VS Code workspace is only as safe as the device it lives on. A hardware failure, lost laptop, or accidental deletion could wipe out hours — or weeks — of work. And if you want to bring colleagues into that workspace to collaborate, there's no easy way to share it, control who can change what, or track who did what. By running `/create-repo`, a personal folder on your disk becomes a ready-to-go team project:

- **☁️ Survives device failure** — your code, configs, and notes are safe on GitHub even if your machine is lost or damaged.
- **💻 Recovery on any device** — clone the repo on a new machine and pick up right where you left off.
- **🕘 Version history** — every commit is a snapshot you can roll back to if something goes wrong locally.
- **👥 Team setup in one go** — invite colleagues as collaborators (resolved from names/aliases into Microsoft EMU accounts) with write access to the repo.
- **🔒 Push controls for others** — protect `main` so collaborators can't push directly; they work on feature branches and submit pull requests for review, while you as the owner can still push when needed.
- **🧭 Pull request workflow** — everyone sees what's changing and why, with history and discussion attached.
- **🔁 Sync point** — access your workspace from multiple devices or share it with teammates.
- **⏳ JIT admin without the friction** — on `mcaps-microsoft` (and any repo that has `.github/ISSUE_TEMPLATE/JitAccess.yml`), admin-only operations like *Protect main*, *Add Actions secret*, *Update description*, or *Toggle visibility* are tagged `⏳ requires JIT` in the menu. Selecting one auto-files a **JIT Request** issue with a sensible justification, **auto-opens a Teams group chat with every maintainer from `.github/acl/access.yml`** (message prefilled and pointing at the JIT issue — you click Send), saves the operation to `.tmp/jit-pending-op.json`, and exits cleanly. When any maintainer approves, `/create-repo resume` re-runs the exact saved op against your now-admin role — no context-switching tax, no secret values in chat history.

Think of it as a **one-command project kickoff**: a few clicks take you from "folder on my hard drive" to a private, shared, protected repo with the right people invited, sensible push limits in place, and everyone ready to start pushing changes through pull requests. Tuned for smaller groups but still a real productivity boost — no more zipping folders, emailing files, or wondering who has the latest version.

---

## Installation & Setup

### Prerequisites

| Tool | Purpose | Install |
|------|---------|------|
| **VS Code** | IDE and skill host | [Download](https://code.visualstudio.com/) |
| **GitHub Copilot + Chat** | AI assistant | [Marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) |
| **GitHub CLI (gh)** | Repo creation and push | `winget install GitHub.cli` (Windows), `brew install gh` (macOS), or [Linux instructions](https://cli.github.com/) |
| **Git** | Version control | [Download](https://git-scm.com/) — also set `git config --global user.name` and `user.email` |

### Get the Skill

Copy `create-repo/` into `.github/skills/create-repo/` in your workspace, or use the Agentic Skill Installer.

### Verify

1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Type `/create-repo`
3. Follow the prompts

---

## Skill Structure

```
create-repo/
├── SKILL.md         # Workflow and procedure
├── README.md        # This file
├── LICENSE.TXT      # MIT License
├── artefact.yaml    # Skill catalog metadata
├── references/      # Extracted reference docs
│   └── rulesets.md  # Ruleset JSON payloads for branch protection
└── evals/           # Test cases and benchmarks
    ├── evals.json
    ├── benchmark.json
    ├── benchmark.md
    └── eval-*/      # Individual eval scenarios
```

---

## Workflow

**Starting point:** you need a VS Code workspace (a folder open in VS Code) that isn't yet pushed to GitHub. You have two ways to get there:

- **Existing local folder** — you already have a workspace on your hard drive that isn't synchronized to any remote repo (no `git remote` configured, or not even a Git repo yet). Open it in VS Code and run `/create-repo`.
- **Brand-new workspace** — create it right now following the same convention as the main [AI-First Delivery setup guide](https://github.com/mcaps-microsoft/ISDAIFirstAiBS#6-create-your-first-workspace):
  1. Open **Windows Explorer** and navigate to your user profile (`C:\Users\YourName\`).
  2. If you don't have a `repos` folder yet, create one: `C:\Users\YourName\repos\`. This is your **one-time, local-only** home for every VS Code workspace you'll ever have. ⚠️ Do **not** put `repos` inside OneDrive — OneDrive's sync breaks Git internals. Keep it on local disk only.
  3. Inside `repos`, create a **new folder for this project** — e.g. `my-new-project`. Full path: `C:\Users\YourName\repos\my-new-project`.
  4. In VS Code: `File → Open Folder…` → select your new project folder. When prompted *"Do you trust the authors of the files in this folder?"* → click **Yes, I trust the authors**.
  5. The folder **intentionally starts empty**. Over time it grows organically as you install skills, add deliverables, and configure MCP servers. A typical repos layout ends up looking like:

     ```
     C:\Users\YourName\repos\
     ├── customer-alpha\          ← Project A workspace
     ├── customer-beta\           ← Project B workspace
     ├── my-new-project\          ← ← you just created this one
     └── ISDAIFirstAiBS\          ← Team skills repo (if cloned)
     ```

     One folder = one VS Code workspace = one GitHub repo. Keep projects isolated so AI context stays focused.
  6. Drop in any files you want to start with (or leave it empty) and run `/create-repo`. The skill handles everything from there — even an empty workspace is a valid starting point.

Either way, the skill detects the workspace state and follows the appropriate path:

### New repo (no git or no remote)

1. **Preflight checks** — Git identity, gh CLI, authentication, account & org detection
2. **Choose where to create the repo** — the skill detects your EMU account and org memberships, then presents a picker:
   - 👤 **Your personal account** (`alias_microsoft`) → Private repo — only you and invited collaborators can see it
   - 🏢 **Organization** (e.g. `mcaps-microsoft`) → Choose visibility:
     - **Internal** — anyone in the Microsoft enterprise can see and clone it; you control who can push/approve via access.yml
     - **Private** — only you and explicitly invited collaborators can see it
3. **Gather remaining inputs** — Repo name, description, collaborators/maintainers. For CLI-blocked orgs (e.g. `mcaps-microsoft`), only the repo name is asked — description and collaborators are entered on the Start Right portal directly.
4. **Sensitive file scan** — Warns about `.env`, secrets, keys, large files before staging
5. **Create and push** — Two paths:
   - **Path A** (fresh workspace): `git init` → `git add` → `git commit` → `gh repo create --push`
   - **Path B** (existing repo, no remote): optional commit → `gh repo create --push`
   - For CLI-blocked orgs: falls back to the [Start Right portal](https://web-ux.prod.startclean.microsoft.com/new/create/repository) with a guided 4-page walkthrough
6. **Show setup & offer changes** — After the initial push, the skill shows a setup dashboard and presents a change menu (the same one used for existing repos). From this menu you can add/remove collaborators, protect main, configure CODEOWNERS, set up access.yml, or push changes. The menu automatically routes collaborator management to the right mechanism:
   - **Org repos** → edits `.github/access.yml` (admin/maintain/write/read roles) + `.github/CODEOWNERS` (PR reviewers)
   - **Personal/private repos** → sends GitHub collaborator invites

### Existing repo (has remote)

1. **Show current setup** — Repo info, collaborators, protection status, and CODEOWNERS/access.yml status displayed in a dashboard view
2. **Propose changes** — Multi-select menu:
   - Add/remove collaborators
   - Protect or unprotect the default branch
   - Change visibility (internal/private/public)
   - Update description
   - Configure CODEOWNERS
   - Configure access.yml (org repos)
   - Push changes
3. **Push changes** — If **safe-push** is installed, runs it automatically (rebase, conflict resolution, force-with-lease push, PR creation). If not installed, offers to install it or push directly with a warning.

### Branch protection levels

Adding collaborators and protecting the default branch are **two separate decisions**. After inviting collaborators, the skill asks you explicitly whether to protect main and shows a description for each option:

| Level | PRs required | Approvals | Stale approvals dismissed | Force-push blocked | What it means | Best for |
|-------|-------------|-----------|---------------------------|--------------------|---------------|----------|
| **PR-only** (recommended) | Yes | 0 | — | Yes | Everyone works on branches and opens a PR; you can self-approve and merge. History rewrites blocked. | Small teams wanting branch hygiene without review overhead |
| **1 approval (Maintain/Admin bypass)** | Yes | 1 for Write; Maintain/Admin bypass | No | Yes | Write users need approval from any eligible reviewer, including another Write user. Maintain and Admin users can merge their own PR without approval. Nobody can bypass the PR itself. | Teams wanting review for contributors with a fast lane for leads |
| **Standard** | Yes | 1 | No | No | 1 reviewer must approve before merge. Force-pushes allowed. | Teams needing peer code review |
| **Strict** | Yes | 1 | Yes | Yes | 1 reviewer must approve; approvals dismissed on new commits; force-push blocked. | Regulated or high-risk repos |
| **Skip protection** | — | — | — | — | No ruleset applied — anyone with write access pushes directly to main. | Solo work or trusted 2-person teams |

The **1 approval (Maintain/Admin bypass)** preset uses GitHub's built-in repository-role IDs: Maintain = `2` and Admin = `5`, both with PR-only bypass; Write = `4`, with no bypass. Therefore everyone must open a PR, Write needs one approval from any eligible reviewer, and Maintain/Admin can self-merge their PR without approval. Protection is never applied silently — you always confirm the level (or skip) before a ruleset is created.

### safe-push integration

`create-repo` is the **one-time kickoff**; [`safe-push`](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/.github/skills/safe-push/SKILL.md) is the **ongoing daily driver** for every push after that. The two skills are designed to work together:

```
/create-repo     ← one-time: initialize repo, invite collaborators, protect main, first push
/safe-push       ← ongoing: rebase on main, handle conflicts, push safely, open PR
```

**When does `safe-push` kick in?**

- **During the initial push** — when creating a new repo, `create-repo` uses `gh repo create --push` for the very first push. From that point on, all subsequent pushes should go through `safe-push`.
- **When pushing changes to an existing repo** — when you select "Push changes" from the change menu, `create-repo` checks whether `safe-push` is installed in `.github/skills/safe-push/`:
  - **Installed** → runs `safe-push` automatically: rebases your branch on the latest `main`, resolves conflicts interactively, pushes with `--force-with-lease`, and opens a pull request. No prompt — it just uses the safer path.
  - **Not installed** → warns that direct `git push` skips rebase, conflict detection, and PR creation, then offers three options: install `safe-push` and use it (recommended), install it for later, or push directly this one time.

**Why this pairing matters for small teams:** once `main` is protected (PR-only, Standard, or Strict), collaborators can't push directly. `safe-push` automates the PR-based workflow so no one has to remember the right sequence of `git fetch` / `rebase` / `push` / `gh pr create` commands — they just type `/safe-push` and it does the right thing. That's how this skill pair keeps a small team productive without losing branch hygiene.

Install both via the [Agentic Skill Installer](https://github.com/mcaps-microsoft/ISDAIFirstAiBS#7-install-the-agentic-skill-installer) in one go.

### .gitignore templates

If no `.gitignore` exists, the skill fetches a template from GitHub's API (`gh api gitignore/templates/[LANGUAGE]`). Supported languages include Python, Node, Java, Go, and [many more](https://github.com/github/gitignore). If the API is unavailable, a minimal template is generated for the detected language.

---

## Invocation

This skill is **manual-only** (`disable-model-invocation: true`). It will never auto-trigger. Invoke it by typing:

```
/create-repo
```

You can also pass context directly after the slash command to skip or pre-fill prompts. The skill parses your intent and jumps straight to the relevant step.

### Example Prompts

#### Creating a new repo

| Prompt | What it does |
|--------|-------------|
| `/create-repo` | Full guided flow — detects workspace state, asks all questions interactively |
| `/create-repo my-project-name` | Pre-fills the repo name, asks where to create it and other details |
| `/create-repo on mcaps-microsoft as internal` | Creates an Internal org repo (opens Start Right portal if CLI-blocked) |
| `/create-repo private repo called customer-alpha-fdd` | Creates a private repo with the given name |
| `/create-repo with collaborators Ints Burvis, Daniel Wojcik` | Creates the repo and invites the listed people (EMU accounts auto-resolved) |

#### Managing collaborators and roles

| Prompt | What it does |
|--------|-------------|
| `/create-repo add maintain role to Ints Burvis, Dan Andreje` | Adds the listed people as maintainers (via access.yml for org repos, invites for personal repos) |
| `/create-repo add write access for iburvis, dandreje` | Grants write (push) access to the listed aliases |
| `/create-repo add admin role to dwojcik_microsoft` | Grants admin access in access.yml (org repos only) |
| `/create-repo remove dandreje from collaborators` | Removes a collaborator from the repo |
| `/create-repo show who has access` | Displays current collaborators, their roles, and access setup |

#### Branch protection

| Prompt | What it does |
|--------|-------------|
| `/create-repo protect main` | Asks which protection level (PR-only, Standard, Strict) and applies it |
| `/create-repo protect main with PR-only` | Applies PR-only ruleset directly — PRs required, 0 approvals, force-push blocked |
| `/create-repo remove protection from main` | Removes all rulesets from the default branch |

#### CODEOWNERS and access.yml

| Prompt | What it does |
|--------|-------------|
| `/create-repo set up CODEOWNERS` | Creates or updates `.github/CODEOWNERS` — defines who must approve PRs |
| `/create-repo set up CODEOWNERS with dwojcik and iburvis as default reviewers` | Creates CODEOWNERS with the specified default owners |
| `/create-repo update access.yml` | Creates or updates `.github/access.yml` with elevated permissions for org repos |
| `/create-repo configure access.yml with maintainers: Ints Burvis, writers: Dan Andreje` | Pre-fills access.yml roles from the prompt |

#### Managing an existing repo

| Prompt | What it does |
|--------|-------------|
| `/create-repo show current setup` | Displays repo info, collaborators, protection, CODEOWNERS, and access.yml status |
| `/create-repo change visibility to internal` | Switches the repo from private to internal (admin role required) |
| `/create-repo update description to "D365 FnO implementation for Customer Alpha"` | Updates the repo description on GitHub |
| `/create-repo push changes` | Pushes current work (auto-uses safe-push if installed) |

#### Targeting a repo by URL (e.g. a customer tenant repo)

If you want to inspect or manage a repo that **isn't** the one open in your workspace — for example a customer-tenant repo you've just been invited to, or any repo on another org — just paste its URL after the slash command:

```
/create-repo on https://github.com/customer-org/their-repo
```

The skill will:

1. **Target that repo directly** instead of your current workspace.
2. **Check your access** — verifies you're authenticated to the right host/tenant (`gh auth status`), confirms the repo is reachable, and reports your role on it (read / triage / write / maintain / admin).
3. **Show the current setup** — visibility, default branch, collaborators, branch protection, CODEOWNERS, and `access.yml` status — exactly like the existing-repo flow.
4. **Offer options** scoped to what your role allows — e.g. add collaborators, update CODEOWNERS, protect `main`, change visibility, or clone the repo locally. Actions you don't have permission for are flagged with what role is required.

Useful variants:

| Prompt | What it does |
|--------|-------------|
| `/create-repo on https://github.com/customer-org/their-repo` | Targets the customer repo, checks your access, shows the dashboard |
| `/create-repo on https://github.com/customer-org/their-repo show who has access` | Lists collaborators and roles on the customer repo |
| `/create-repo on https://github.com/customer-org/their-repo add write access for iburvis` | Grants write access (requires `admin` on that repo) |
| `/create-repo on https://github.com/customer-org/their-repo protect main with PR-only` | Applies PR-only ruleset on the customer repo's `main` (requires `admin`) |
| `/create-repo on customer-org/their-repo` | Short form — `owner/name` works the same as a full URL |

> **Multi-tenant note:** If the customer repo lives on a different GitHub host or EMU tenant than your default `gh` login, the skill will detect the auth mismatch and walk you through `gh auth login --hostname …` before continuing. No changes are made until you have access.

> **Tip:** You can combine multiple intents in one prompt — e.g. `/create-repo add maintain role to Ints Burvis and protect main with PR-only`. The skill processes each action in sequence.

---

## JIT (Just-in-Time) admin on `mcaps-microsoft` repos

<ins>**Managing advanced elements of `mcaps-microsoft` repos requires `admin` rights — and admin is granted via the JIT (Just-in-Time) process, which this skill fully automates.**</ins> Your standing role on `mcaps-microsoft` is `maintain`. That is enough for normal contribution work (push branches, open/merge PRs, edit CODEOWNERS and access.yml, manage issues), but it is **not** enough for the operations listed below — they require admin.

### Operations that require admin (and therefore JIT)

| Operation | Why it needs admin |
|---|---|
| **Protect main** / **Remove protection** | Creating, updating, or deleting GitHub Rulesets is admin-only. The settings UI `/settings/rules` is also blocked for non-admins. |
| **Change visibility** (Internal ↔ Private) | Visibility changes are admin-only repo settings. |
| **Update description** | On `mcaps-microsoft` the description field is policy-locked and admin-only — it cannot be edited from the regular repo UI. |
| **Manage Actions secrets / variables** | Adding, updating, or removing repo-level Actions secrets/variables requires admin. |
| **Manage webhooks** | Webhook creation, edit, and deletion are admin-only. |

Maintainer-level work (collaborator changes via `access.yml`, CODEOWNERS edits, branches, PRs, issues, labels, milestones) does **not** need JIT — the skill runs it directly under your standing `maintain` role.

### How the skill drives the JIT round-trip

When you select any of the operations above and your role is below `admin`, the skill:

1. **Saves the operation payload** to `.tmp/jit-pending-op.json` (e.g. the exact ruleset JSON for *Protect main*, or the visibility target).
2. **Files a JIT Request issue** on the repo using the `JitAccess.yml` issue template — auto-justified, default duration 2h, mentions a maintainer from `.github/acl/access.yml` as approver.
3. **Opens a Teams group chat** with every maintainer from `access.yml`, prefilled with a message pointing at the JIT issue. You just press Send.
4. **Exits cleanly** — it does *not* poll or block. You go do other work.
5. **A maintainer approves the issue** — this triggers the GIM (GitHub Identity Management) automation to grant you `admin` for the requested duration.
6. **You re-run** `/create-repo` (or `/create-repo resume`) — the skill detects the pending op, confirms your role is now `admin`, replays the saved payload against the repo, deletes `.tmp/jit-pending-op.json`, and closes issue.

The admin grant auto-expires at the end of the window (1h or 2h), so no elevated access lingers. Secret values for the *Manage secrets* operation are entered in the terminal at resume time — never stored in the issue body or chat history.

### Requirements for JIT-capable repos

A repo is JIT-capable when it has both:

- `.github/ISSUE_TEMPLATE/JitAccess.yml` — the JIT issue template the skill files against
- `.github/acl/access.yml` — defines who can approve (maintainers + admins)

All `mcaps-microsoft` repos that follow the AI-First Delivery convention have both. On org repos without these files, the skill falls back to legacy guidance ("ask an org admin").

---

## Preferences

No preferences — all inputs are gathered at invocation time.

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| GitHub only | Does not support Azure DevOps, GitLab, or Bitbucket |
| gh CLI required | Cannot create remote repos without it |
| Cross-platform | Skill provides both PowerShell and bash/zsh code blocks — works on Windows, macOS, and Linux |
| Git identity required | `git config user.name` and `user.email` must be set — the skill auto-resolves from your GitHub profile if missing |
| Branch protection | Uses GitHub Rulesets (works on all plans including Free for private repos). **Requires `admin` role** — on org repos like `mcaps-microsoft` where you typically have `maintain`, rulesets cannot be created via CLI or the settings page. <ins>**On JIT-capable repos the skill handles this for you via the [JIT admin process](#jit-just-in-time-admin-on-mcaps-microsoft-repos)** — files the request, pings an approver, queues the ruleset payload, and resumes the operation once approved.</ins> On org repos without a JIT template, the skill falls back to asking an org admin manually. |
| EMU accounts only | Collaborator resolution assumes Microsoft EMU naming convention (`alias_microsoft`). Non-EMU accounts must be provided as exact GitHub usernames |
| Enterprise scope detection | Querying enterprise details requires `read:enterprise` token scope — the skill detects EMU accounts by username suffix instead |
| Org repo creation | Some orgs (e.g. `mcaps-microsoft`) may require repo creation through the [Start Right portal](https://web-ux.prod.startclean.microsoft.com/new/create/repository) — the skill detects this and falls back gracefully |
| access.yml | Relevant for org repos (Internal and Private) — skipped for personal repos. For Internal repos, controls write/maintain/admin access (everyone already has read). For Private org repos, also controls read access. |
---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 4.0 | April 2026 | Org repo support: owner picker (personal vs org), Internal and Private visibility for orgs, Start Right portal fallback, CODEOWNERS configuration, access.yml for elevated permissions, permission levels table (admin/maintain/write/read). Rulesets extracted to references/rulesets.md. Pushy trigger description. Post-push flow unified — all repo types now route to the setup dashboard + change menu after initial push. |
| 3.0 | April 2026 | Major rewrite: simplified from 560 to ~300 lines. EMU-first account resolution. Owner/org resolution in preflight. .gitignore template fetching restored. Cleaner step structure (detect → gather → create → manage → collaborate). |
| 2.0 | April 2026 | Existing repo management (Step 4): dashboard view, multi-select change menu. Three protection levels (Standard, Strict, PR-only). Auto-runs safe-push when installed. Account & plan detection. Evals and artefact.yaml added. |
| 1.2 | April 2026 | GitHub EMU account resolution from names/aliases; collaborators step made optional |
| 1.1 | April 2026 | Added collaborator management and branch protection for private repos |
| 1.0 | April 2026 | Initial release |
