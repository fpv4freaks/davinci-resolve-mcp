---
name: create-repo
description: "Create a new GitHub repository for the current workspace and push initial commit. Supports personal repos and org repos (e.g. mcaps-microsoft) with Internal visibility. Add collaborators (EMU accounts auto-resolved from names or aliases), protect main branch with rulesets, configure CODEOWNERS and access.yml for org repos, and integrate with safe-push for team workflows. Also manages existing repos — shows current setup, proposes changes to collaborators, protection, visibility, CODEOWNERS, and access.yml. On JIT-capable org repos (mcaps-microsoft and any repo with a .github/ISSUE_TEMPLATE/JitAccess.yml template), admin-only operations like protect-main, add-secret, change-visibility, or update-description auto-file a JIT Request issue, draft a Teams ping for an approver from access.yml, and resume the queued operation after a maintainer approves. ALWAYS use this skill when the user mentions creating a repo, pushing code to GitHub, setting up a GitHub remote, sharing a workspace, adding collaborators, managing repo access, CODEOWNERS, access.yml, branch protection, JIT access, requesting temporary admin, GIM JIT, or wants to create or admin a repo on an org like mcaps-microsoft."
argument-hint: "Optional: repo name, owner (personal or org like mcaps-microsoft), visibility (internal/private), collaborators (names or aliases), or 'resume' to re-run a pending JIT operation"
disable-model-invocation: true
owner: dwojcik
stream: technical
---

# Create Repo

Create a GitHub repo for the current workspace, push the code, add collaborators, and protect the main branch. All accounts are Microsoft EMU (`alias_microsoft`). Repos can be created under your personal account or under an org (e.g. `mcaps-microsoft`). Personal repos are private by default; org repos can be **Internal** (visible to anyone in the enterprise) or **Private** (only invited collaborators can see it).

## Step 1 — Detect current state

Run `git rev-parse --is-inside-work-tree 2>&1` and `git remote -v`.

| State | What to do |
|-------|-----------|
| **No git repo** | Go to Step 2 (gather inputs), then Step 3 Path A |
| **Git repo, no remote** | Go to Step 2 (gather inputs), then Step 3 Path B |
| **Git repo with remote** | Go to Step 4 (show setup, ask if changes needed) |

## Step 2 — Gather inputs (new repos only)

### Preflight checks (run first)

Run these **before** gathering inputs. The results feed into the owner picker.

1. **Git identity** — `git config user.name` / `git config user.email`. If empty, auto-set from `gh api user`.
2. **gh CLI** — `Get-Command gh` (PowerShell) or `which gh`. If missing: `winget install GitHub.cli`.
3. **gh authenticated** — `gh auth status`. If not: `gh auth login`.
4. **Detect account & orgs** — discover who the user is and where they can create repos:
   ```bash
   # Get username
   gh api user --jq '.login'
   # List orgs the user belongs to
   gh api user/orgs --jq '.[].login' 2>/dev/null
   # For each org, check if members can create repos
   gh api orgs/[ORG] --jq '{login, members_can_create_repositories, members_can_create_internal_repositories}'
   ```
   Store the results: `EMU_USER` (e.g. `dwojcik_microsoft`), `ORGS` with their creation permissions.

### Choose where to create the repo

Use `vscode_askQuestions` to present a **single choice** — where to create the repo. Build the options dynamically from preflight step 4.

For each org, check `members_can_create_repositories` and `members_can_create_internal_repositories`. If **both are false**, the org blocks CLI repo creation — mark it accordingly in the picker:

```
Where would you like to create this repo?

  1. 👤 dwojcik_microsoft (your personal account)
     → Private repo — only you and invited collaborators can see it.
     → You manage access by inviting specific people.

  2. 🏢 mcaps-microsoft (organization) — ⚠️ requires Start Right portal
     → Choose visibility: Internal or Private (see next step).
     → Repo must be created via the Start Right portal first, then I'll set up collaborators + protection.

  3. 🏢 another-org (organization)
     → Choose visibility: Internal or Private (see next step).
     → Can be created directly from here.

  (one option per org the user belongs to)
```

**After selecting an org**, immediately ask for visibility:

```
What visibility for this org repo?

  1. 🏢 Internal (recommended)
     → Anyone in the Microsoft enterprise can SEE and CLONE this repo.
     → Only collaborators with write/maintain/admin access can push code.
     → Access is managed via CODEOWNERS + access.yml (no invites needed for read access).
     → Best for: team projects, shared IP, internal tools.

  2. 🔒 Private
     → Only you and explicitly invited collaborators can see this repo.
     → Works the same as a private repo on your personal account — invite-based access.
     → Access is managed via collaborator invites (same as personal repos).
     → Best for: sensitive projects, pre-announcement work, restricted access.
```

Wait for the user's selection. This determines the entire flow:

| Selection | Can create via CLI? | Flow |
|-----------|-------------------|------|
| **Personal account** | ✅ Always | Gather inputs → Step 3 → Step 5 (invite collaborators + protect main) |
| **Org (Internal, CLI allowed)** | ✅ Yes | Gather inputs → Step 3 (with `--internal`) → check role → protect main (if admin) → Step 6 (CODEOWNERS + access.yml) |
| **Org (Private, CLI allowed)** | ✅ Yes | Gather inputs → Step 3 (with `--private`) → Step 5 (invite collaborators + protect main if admin) — same as personal |
| **Org (Internal, CLI blocked)** | ❌ No | Start Right portal (select Internal) → connect workspace → push → check role → protect main (if admin, otherwise skip with note) → Step 6 (CODEOWNERS + access.yml) |
| **Org (Private, CLI blocked)** | ❌ No | Start Right portal (select Private) → connect workspace → push → Step 5 (invite collaborators + protect main if admin) — same as personal |

> **⚠️ Org repo protection note:** On most org repos (e.g. `mcaps-microsoft`), users get `maintain` role — not `admin`. Rulesets **cannot** be created without `admin`, and the GitHub settings page (`/settings/rules`) is also inaccessible. The skill detects this after repo creation and skips the protection step with guidance. See the **Ruleset permission check** in Step 5b for details.

### Org with CLI blocked — Start Right portal flow

When the user selects an org where `members_can_create_repositories` is false:

1. Ask for the **repo name** only — this is needed so the skill can verify the repo and connect the workspace later. Description, collaborators, and visibility are all entered directly on the portal.
2. Open the portal: `Start-Process "https://web-ux.prod.startclean.microsoft.com/new/create/repository"`
3. **Immediately** show the user the **full step-by-step walkthrough** for the 4-page wizard (do NOT skip this — the instructions must always appear when the Start Right path is selected):

   > *"**mcaps-microsoft** doesn't allow repo creation via CLI — you need to use the Start Right portal. I've opened it in your browser.*
   >
   > *Follow these steps on each page of the wizard:*
   >
   > ---
   >
   > **Page 1 of 4 — Repository setup**
   > - You'll see two options: *Create new repository* or *Transfer existing repository*
   > - Select **Create new repository**
   > - Click **Next** (bottom-right)
   >
   > ---
   >
   > **Page 2 of 4 — Create a new repository**
   > - **Owner** *(dropdown at the top)*: select **`mcaps-microsoft`** — this is the Microsoft org where all project repos live
   > - **Repository name**: `[NAME]`
   >   - Use lowercase letters and hyphens only (e.g. `customer-alpha-fdd`, `ai-first-pilot`)
   >   - No spaces, no underscores, no uppercase — GitHub will reject them
   > - **Description**: write a clear, meaningful description
   >   - This is **required** by mcaps-microsoft policy — the portal won't let you proceed without it
   >   - ⚠️ **Important**: the description **cannot be changed** after creation without JIT admin access, so write a clear one now (e.g. *"D365 F&O implementation for Customer Alpha — FDDs, TDDs, and development artefacts"*)
   > - **Visibility**: select **`[Internal / Private]`** *(as chosen in the previous step)*
   >   - **Internal** = anyone in the Microsoft enterprise can see and clone it; you control who can push
   >   - **Private** = only you and explicitly invited people can see it at all
   > - Click **Next**
   >
   > ---
   >
   > **Page 3 of 4 — Classification and Ownership**
   > - **Production / Non-Production**: select **`Non-Production`** *(this is correct for consulting/delivery projects, pilots, experiments, and internal tools)*
   > - **Service assignment**: select **`Assign via direct ownership`** *(the simplest option — you own it directly)*
   > - **Direct Owners**: search for and add **yourself** + **at least one colleague** (the portal requires at least 2 owners)
   >   - Type their name or alias in the search box, select from the dropdown
   >   - Good practice: add the project lead or a close team member
   > - Click **Next**
   >
   > ---
   >
   > **Page 4 of 4 — Grant access permissions**
   > - You must add **at least 2 members with Maintain role** — this is **mandatory**, the portal will not let you submit without it
   > - In the members list:
   >   - Add **yourself** → set role to **Maintain**
   >   - Add **at least one colleague** → set role to **Maintain**
   >   - Optionally add more team members with Write or Maintain role
   > - Review the summary and click **Submit**
   > - ⏳ Wait for the confirmation screen — the repo is being created. This usually takes 10–30 seconds.
   >
   > ---
   >
   > *When the repo is created, come back here and tell me — I'll connect your workspace, push your files, and continue with branch protection and access setup.*
   >
   > 📖 *For more details, screenshots, and troubleshooting, see the [full Start Right portal guide](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#for-mcaps-microsoft-repos--start-right-portal) in the main README.*
   >
   > ⚠️ **If you get a 403 error** after the repo is created (when pushing or cloning), your Git credential likely needs SSO authorization for `mcaps-microsoft`. Run `gh auth refresh -s repo` and authorize the org when prompted. See [Troubleshooting: 403 error on push or clone](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/README.md#troubleshooting-403-error-on-push-or-clone) for step-by-step fix."*

4. **Wait for the user** to confirm the repo was created.
5. When the user confirms:
   ```bash
   # Verify the repo exists
   gh repo view [ORG]/[NAME] --json name,visibility,html_url
   ```
6. If confirmed, connect the local workspace:
   ```bash
   git init  # if not already a git repo
   git remote add origin https://github.com/[ORG]/[NAME].git
   git add -A
   git commit -m "Initial commit"
   git push -u origin main
   ```
7. **Confirm success** — tell the user the workspace is now connected and the code is pushed:
   > ✅ **Connected!** Your workspace is now linked to `[ORG]/[NAME]` and the initial commit has been pushed.
   >
   > 🔗 https://github.com/[ORG]/[NAME]
8. **Go to Step 4** (existing repo flow) — show the current setup (Step 4a) and then present the "Would you like to change anything?" menu (Step 4b). This lets the user configure collaborators, protection, CODEOWNERS, access.yml, or push changes — same as if they had run create-repo on an existing repo.

### Gather remaining inputs

After the owner is selected, use `vscode_askQuestions` to collect the inputs below. **For CLI-blocked orgs (e.g. mcaps-microsoft using Start Right portal):** only ask for **Repo name** — description and collaborators are entered on the portal manually, so skip those fields entirely.

| Input | Default | When to ask |
|-------|--------|-------------|
| **Repo name** | Current folder name | Always |
| **Description** | *(empty)* — **required** for org repos on `mcaps-microsoft` (enforced by Start Right policy) | CLI-allowed orgs and personal repos only |
| **Collaborators / Maintainers** | *(empty)* — comma-separated names, aliases, or GitHub usernames. **What this means depends on repo type** (see access model below). | CLI-allowed orgs and personal repos only |

> **Access model — by visibility:**
>
> | | **Org repo (Internal)** | **Org repo (Private)** | **Personal repo (Private)** |
> |---|---|---|---|
> | **Who can see the repo** | Everyone in the Microsoft enterprise (automatic) | Only you + explicitly invited collaborators | Only you + explicitly invited collaborators |
> | **Who can clone/pull** | Everyone in the enterprise | Only invited collaborators | Only invited collaborators |
> | **Who can push code** | Only users with `write`/`maintain`/`admin` access | Only invited collaborators with push permission | Only invited collaborators with push permission |
> | **Who can approve PRs** | Anyone with `write`+ access, or CODEOWNERS if enforced | Any collaborator, or CODEOWNERS if enforced | Any collaborator, or CODEOWNERS if enforced |
> | **Who can merge to main** | Depends on ruleset — typically CODEOWNERS or maintainers | Depends on ruleset — any collaborator or owner | Depends on ruleset — any collaborator or owner |
> | **How to manage access** | `access.yml` + CODEOWNERS (Step 6) — grant elevated roles to a few people | Collaborator invites (Step 5) — same as personal private | Collaborator invites (Step 5) — grant access to specific people |
> | **"Collaborators" means** | People who get **maintain/admin** roles (everyone else already has read) | People who get **invited** (without invite they have zero access) | People who get **invited** (without invite they have zero access) |

### Additional preflight checks

5. **Verify org access** (org repos only, CLI-allowed orgs) — confirm the user can create repos in the selected org:
   ```bash
   gh api orgs/[ORG] --jq .login 2>&1
   gh api orgs/[ORG]/memberships/$(gh api user --jq .login) --jq '.role' 2>&1
   ```
   This check is only needed for orgs where CLI creation is allowed. For CLI-blocked orgs (e.g. `mcaps-microsoft`), the Start Right portal flow (above) handles everything.

6. **No name collision** — `gh repo view [OWNER]/[NAME]`. If exists, offer to pick a new name or use existing repo (→ Step 4).

### Sensitive file check

Before staging, scan for files that should NOT be pushed: `.env`, `*.pem`, `*.key`, `*.pfx`, `node_modules/`, `__pycache__/`, files >10MB. Warn and suggest `.gitignore` entries.

## Step 3 — Create and push

### .gitignore setup

If the workspace has no `.gitignore`, ask the user if they want one. If yes, fetch a template:

```bash
# List available templates
gh api gitignore/templates --jq '.[].name'
# Fetch a specific template (e.g. Python, Node, Java)
gh api gitignore/templates/[LANGUAGE] --jq .source > .gitignore
```

If the API call fails, generate a minimal `.gitignore` with common entries for the detected language.

### Path A — Fresh workspace (no git)

```
git init
git add -A
git commit -m "Initial commit"
gh repo create [OWNER]/[NAME] --[VISIBILITY] --source=. --push --description "[DESC]"
```

- For **personal** repos: `--private` (default)
- For **org** repos (CLI-allowed, Internal): `--internal`
- For **org** repos (CLI-allowed, Private): `--private`
- For **org repos where CLI is blocked**: skip this step entirely — use the Start Right portal flow from Step 2 instead.

### Path B — Git repo, no remote

1. `git status --short` — if uncommitted changes, ask to commit (suggest a message based on changes).
2. If clean, skip commit.
3. `gh repo create [OWNER]/[NAME] --[VISIBILITY] --source=. --push --description "[DESC]"`
   - Use `--private` for personal repos and org repos with Private visibility
   - Use `--internal` for org repos with Internal visibility
   - For CLI-blocked orgs: this path is never reached — use Start Right portal flow from Step 2

**After push:**
- **All repo types:** Go to **Step 4** (existing repo flow) — show the current setup (Step 4a) and present the "Would you like to change anything?" menu (Step 4b). The menu routes "Add collaborators" to the right mechanism automatically (access.yml for org repos, invites for personal repos).

## Step 4 — Repo already exists (show setup, propose changes)

This is the main interaction when someone runs create-repo on a workspace that already has a remote.

### 4a — Show current setup

Fetch and display:

```bash
gh api repos/[OWNER]/[NAME] --jq '{name, full_name, private, visibility, description, default_branch, html_url}'
gh api repos/[OWNER]/[NAME]/collaborators --jq '.[] | {login, role_name}'
gh api repos/[OWNER]/[NAME]/collaborators/$(gh api user --jq .login)/permission --jq '.role_name'
gh api repos/[OWNER]/[NAME]/rulesets --jq '.[] | {name, enforcement}' 2>/dev/null
```

Present as:

```
📋 [OWNER]/[NAME]
  URL:          https://github.com/[OWNER]/[NAME]
  Visibility:   internal (anyone in the enterprise can see this, collaborators can commit)
                or: private (only you and collaborators can see this)
  Description:  [DESC]
  Branch:       main
  Your role:    maintain (or: admin, write, read)

👥 Collaborators:
  • you (maintain)
  • dandreje_microsoft (write)

🔒 Protection:
  • Ruleset "Protect main" — PRs required, 1 approval
  (or: ⚠ No protection — anyone can push directly to main)
  (if maintain role on org repo: ℹ️ Rulesets require admin role — ask an org admin to configure)
```

### 4b — Propose changes

Use `vscode_askQuestions` with `multiSelect: true`:

> "Would you like to change anything?"

First, check the user's role on the repo:
```bash
gh api repos/[OWNER]/[NAME]/collaborators/$(gh api user --jq .login)/permission --jq '.role_name'
```

Build the options list **dynamically** based on the user's role and the repo type. Admin-only options (Protect/Remove protection, Change visibility, Update description on `mcaps-microsoft`) are still shown to non-admins on **JIT-capable org repos**, but tagged `⏳ requires JIT` so the user knows the skill will file a JIT Request issue before executing them (see Step 7).

| Option | Description | Shown when |
|--------|-------------|------------|
| **Add collaborators** | Add people to the repo. | Always |
| **Remove collaborators** | Remove someone from the repo. | Always (if collaborators exist) |
| **Protect main branch** | Everyone must work on a separate branch and submit changes for review (pull request) before they go into main. You as the owner can still push directly. | `admin` role → run directly. `maintain` on a JIT-capable org repo → shown as `⏳ requires JIT` (Step 7). Otherwise hidden. |
| **Remove main protection** | Let anyone push directly to main (no review required). | Same rules as Protect — `⏳ requires JIT` for non-admin on JIT-capable repos. Only shown if a ruleset already exists. |
| **Change visibility** | Switch between internal/private. (Public is blocked by MCAPS policy.) Internal means anyone in the enterprise can see the code. | Same rules as Protect — `⏳ requires JIT` for non-admin on JIT-capable repos. |
| **Update description** | Change the repo description. On `mcaps-microsoft` the description is admin-only and **immutable** without admin role — so on that org it is tagged `⏳ requires JIT` for non-admins. | Always. Tagged `⏳ requires JIT` on `mcaps-microsoft` for non-admins. |
| **Manage Actions secrets / variables** | Add, update or remove repo-level secrets or variables used by GitHub Actions workflows. Secret values are entered in the terminal, never in chat or in the JIT issue body. | `admin` role → run directly. `maintain` on a JIT-capable org repo → `⏳ requires JIT` (Step 7). |
| **Manage webhooks** | Add, edit or remove a repo webhook. The webhook URL secret is entered in the terminal. | Same rules as secrets — `⏳ requires JIT` for non-admin on JIT-capable repos. |
| **Configure CODEOWNERS** | Set up or update `.github/CODEOWNERS` — defines who must review PRs that touch specific files. | Always (file-based, no admin needed) |
| **Request JIT access (no specific op)** | File a 1–24h JIT Request issue without queuing a specific operation. Useful when you want to do something interactively in the GitHub UI yourself after approval. | JIT-capable org repos only (any role) |
| **Resume pending JIT operation** | Re-run the operation that was queued before you filed your last JIT issue (saved in `.tmp/jit-pending-op.json`). | When `.tmp/jit-pending-op.json` exists |
| **Push changes** | Push your current work to the repo. | Always |
| **Nothing — all good** | Exit. | Always |

> **"Add/Remove collaborators" routes automatically based on repo type:**
> - **Org repos (e.g. mcaps-microsoft):** → edits `.github/access.yml` (Step 6b). Users are added with a role (admin/maintain/write/read). No invites needed for Internal repos — everyone already has read access.
> - **Private/personal repos (`_microsoft` accounts):** → sends GitHub collaborator invites (Step 5a). Users must accept the invite to get access.
>
> The user doesn't need to know the difference — the menu just says "Add collaborators" and the skill picks the right mechanism.

If the user has `maintain` (or lower) on an **org repo**, detect whether the repo is **JIT-capable** (see Step 7 — `is_jit_capable` check). Show the appropriate menu header:

- **JIT-capable** (e.g. `mcaps-microsoft/ISDAIFirstAiBS` — has `.github/ISSUE_TEMPLATE/JitAccess.yml` and `.github/acl/access.yml`):
  > ℹ️ You have **`[ROLE]`** access on this org repo. Admin-only operations below are tagged `⏳ requires JIT` — selecting one will file a **JIT Request** issue and (after a maintainer approves) you'll get 2–24 hours of admin to run it. See Step 7 for how the JIT round-trip works.

- **Not JIT-capable** (org repo without the JIT template):
  > ℹ️ You have **`[ROLE]`** access on this org repo. Branch protection, visibility, and other admin-only operations require **admin** — ask an org admin (this repo does not have a JIT request template configured).

Execute selected options in order. After each, confirm the result.

**Add collaborators — routing:**
- **Org repos:** resolve EMU accounts (see Step 5a), then go to Step 6b (access.yml) — ask for role (admin/maintain/write/read) and update the file.
- **Private/personal repos:** resolve EMU accounts (see Step 5a), invite with push permission via GitHub API.

**Remove collaborators — routing:**
- **Org repos:** show current access.yml entries, ask which to remove, update the file, commit and push.
- **Private/personal repos:** `gh api "repos/[OWNER]/[NAME]/collaborators/[USER]" -X DELETE`

**Protect main branch** (only shown if user has `admin` role) — ask PR-only, 1 approval (Maintain/Admin bypass), Standard, or Strict:

| Level | What it means |
|-------|---------------|
| **PR-only** (recommended) | PRs required but 0 approvals needed — anyone can merge their own PR. Force-push blocked. Owner can push directly. Good for small teams that want branch hygiene without review overhead. |
| **1 approval (Maintain/Admin bypass)** | PRs are always required. Write users need 1 approval from any eligible reviewer, including another Write user. Maintain and Admin users can merge their own PR without approval, but cannot push directly to main. |
| **Standard** | PRs required, 1 approval needed. Owner can push directly. |
| **Strict** | Same as Standard + old approvals cancelled on new changes + force-push blocked. |

Apply using rulesets (see Step 5b).

**Remove main protection:**
```bash
gh api repos/[OWNER]/[NAME]/rulesets --jq '.[].id' | while read id; do
  gh api repos/[OWNER]/[NAME]/rulesets/$id -X DELETE
done
```

### 4c — Push changes

First check if the **safe-push** skill exists in this workspace:

```powershell
Test-Path ".github/skills/safe-push/SKILL.md"
```

**If safe-push is available — run it directly, no questions asked:**

> "Running **safe-push** — it will rebase on latest main, push safely, and create a PR."
> 📖 [safe-push documentation](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/.github/skills/safe-push/SKILL.md)

Read `.github/skills/safe-push/SKILL.md` and execute the safe-push workflow inline (follow all its steps: pre-flight, rebase, push, PR creation). Do NOT ask the user whether to use safe-push or push directly — just use safe-push.

**If safe-push is NOT available:**

> ⚠️ **The safe-push skill is not installed — strongly recommended for team repos.** It rebases your branch on latest main, resolves conflicts interactively, pushes safely with `--force-with-lease`, and creates a pull request automatically. Direct push skips all of that.
>
> 📖 [safe-push documentation (source)](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/.github/skills/safe-push/SKILL.md)

Offer via `vscode_askQuestions` (safe-push options listed first):
- **Install safe-push and use it (recommended)** — download, then tell user to invoke it
- **Install safe-push for later** — download, then do a simple push now
- **Just push directly** — ⚠️ Skips rebase, conflict detection, and PR creation. Run `git push -u origin HEAD`

**Installing safe-push:**

```powershell
New-Item -ItemType Directory -Path ".github/skills/safe-push" -Force
$content = gh api repos/mcaps-microsoft/ISDAIFirstAiBS/contents/.github/skills/safe-push/SKILL.md --jq .content
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($content)) | Set-Content -Path ".github/skills/safe-push/SKILL.md" -Encoding UTF8
```

Confirm: "safe-push installed. Type **safe push** in Copilot Chat to use it. 📖 [Documentation](https://github.com/mcaps-microsoft/ISDAIFirstAiBS/blob/main/.github/skills/safe-push/SKILL.md)"

## Step 5 — Add collaborators and protect main (private repos only)

Runs after Step 3 for **private/personal repos** when collaborators were provided. Also used by Step 4b when adding collaborators to an existing private repo.

> **Not for org/internal repos.** For org repos, everyone already has read access — skip the invite flow entirely. Go straight to protecting main (Step 5b options below) and then Step 6 (CODEOWNERS + access.yml) for elevated permissions.

**Important:** adding collaborators and protecting main are **two separate decisions**. Adding a collaborator does NOT automatically enable branch protection — always ask the user explicitly in Step 5b (including a "Skip protection" option). Never apply a protection preset silently.

### 5a — Resolve EMU accounts

All accounts follow the `alias_microsoft` pattern. Resolution order:

1. **Already has `_microsoft` suffix** (e.g. `dwojcik_microsoft`) → verify: `gh api users/[INPUT]`
2. **Microsoft alias** (e.g. "dwojcik") → try `[INPUT]_microsoft`
3. **Full name** (e.g. "Ints Burvis") → try `iburvis_microsoft`, `intsi_microsoft`, `ints_microsoft`
4. **Search** (fallback) → `gh api "search/users?q=[NAME]+in:name+type:user"` — prefer `_microsoft` results
5. **Not found** → ask for the exact GitHub username

**Confirm before inviting:**

| Input | Resolved | Profile |
|-------|----------|---------|
| Ints Burvis | `iburvis_microsoft` | https://github.com/iburvis_microsoft |
| dwojcik | `dwojcik_microsoft` | https://github.com/dwojcik_microsoft |

**Invite with push permission:**
```bash
gh api "repos/[OWNER]/[NAME]/collaborators/[USER]" -X PUT -f permission=push
```

After collaborators are invited, ask the user **explicitly** whether to protect main. Use `vscode_askQuestions` with these options (PR-only recommended). Show the full description next to each option so the user knows exactly what they're choosing:

| Option | What it means | Who can push to main |
|--------|---------------|---------------------|
| **PR-only** (recommended) | Everyone works on feature branches and opens a pull request to merge into main. No approval is required — you can merge your own PR. Force-pushes and history rewrites are blocked. Good for small teams that want branch hygiene without review overhead. | Owner (direct) + anyone via self-approved PR |
| **1 approval (Maintain/Admin bypass)** | Everyone must open a PR. A **Write** user needs **1 approval from any eligible reviewer**, including another Write user. Users with **Maintain** or **Admin** can bypass the approval and merge their own PR. Their bypass applies only through a PR, so they still cannot push directly to main. | Maintain/Admin via self-merge PR + Write users via approved PR |
| **Standard** | Same as PR-only, but **1 approval from another collaborator** is required before merging. Force-pushes are allowed. Good for teams that want peer review. | Owner (direct) + anyone via approved PR |
| **Strict** | Same as Standard, plus: approvals are **dismissed automatically** when new commits are pushed to the PR, and force-pushes are blocked. Best for regulated or high-risk repos where every change must be re-approved. | Owner (direct) + anyone via freshly-approved PR |
| **Skip protection** | No ruleset applied. Anyone with write access can push directly to main, force-push, or rewrite history. Fastest for solo work or trusted 2-person teams; risky for larger groups. | Anyone with write access |

Only apply a ruleset if the user picks PR-only, 1 approval (Maintain/Admin bypass), Standard, or Strict. If they pick **Skip**, do nothing and confirm: *"Main left unprotected — you can enable it later by running create-repo again."*

Use rulesets to require pull requests on main. Read `references/rulesets.md` for the full JSON payloads for each protection level (PR-only, 1 approval (Maintain/Admin bypass), Standard, Strict). The key differences:

| Level | `required_approving_review_count` | `require_code_owner_review` | `dismiss_stale_reviews_on_push` | `non_fast_forward` rule | Maintain bypass |
|-------|----------------------------------|-----------------------------|--------------------------------|------------------------|-----------------|
| **PR-only** | 0 | false | false | yes | — |
| **1 approval (Maintain/Admin bypass)** | 1 | false | false | yes | Maintain + Admin (`pull_request`) |
| **Standard** | 1 | false | false | no | — |
| **Strict** | 1 | false | true | yes | — |

Most presets use `actor_id: 5` (Admin) with their documented bypass mode. For **1 approval (Maintain/Admin bypass)**, both `actor_id: 5` (Admin) and `actor_id: 2` (Maintain) use `bypass_mode: pull_request`. GitHub maps `actor_id: 4` to **Write**, which is deliberately excluded from bypass.

### Ruleset permission check (run before attempting to create rulesets)

Creating rulesets requires **admin** role on the repo. Before calling the rulesets API, check the user's role:

```bash
gh api repos/[OWNER]/[NAME]/collaborators/$(gh api user --jq .login)/permission --jq '.role_name'
```

| Role | Can create rulesets? | Action |
|------|---------------------|--------|
| **admin** | ✅ Yes | Proceed with ruleset creation normally |
| **maintain** | ❌ No | Skip API call — show org admin guidance (below) |
| **write** / **read** | ❌ No | Skip API call — show org admin guidance (below) |

**If the user does NOT have admin role (or the API call fails):**

First run the **JIT capability detection** (Step 7 — `is_jit_capable` check). The flow then branches:

- **JIT-capable org repo** (e.g. `mcaps-microsoft/ISDAIFirstAiBS`) → **DO NOT silently skip**. Tell the user the operation needs admin, explain that you can file a JIT Request issue on their behalf, and offer the choice:

  > ⏳ **Branch protection requires admin** — you have `[ROLE]` role on `[OWNER]/[NAME]`. Microsoft policy doesn't allow permanent admin on this repo, but you can get **2–24 hours of temporary admin** through the JIT process:
  >
  > 1. I'll ask how long you need (2–24h, default 2h), auto-justify the request, and file a **JIT Request** issue on the repo.
  > 2. A maintainer from `.github/acl/access.yml` reviews and approves it.
  > 3. You get admin for the chosen duration.
  > 4. You run `/create-repo` again (or `/create-repo resume`) and the saved ruleset op is applied.
  >
  > What would you like to do?
  >
  > - **File JIT and queue this op** *(recommended)* — save the ruleset payload to `.tmp/jit-pending-op.json`, file the issue, open it in your browser, and exit cleanly.
  > - **Skip protection for now** — leave main unprotected. You can run `/create-repo` later.

  If the user picks **File JIT**, follow Step 7 with `operation_kind = "protect-main"` and the chosen ruleset level. After the issue is filed, **stop the skill** (do not block waiting for approval) — the resume happens in a separate invocation.

- **Org repo without JIT template** → no self-service option. Show the legacy guidance:

  > ⚠️ **Branch protection** — could not create ruleset (you have `[ROLE]` role, rulesets require `admin`). This repo does not have a JIT request template, so there is no self-service path. Ask an **org admin** to create a ruleset for `[OWNER]/[NAME]` on the `main` branch.
  >
  > Recommended: **PR-only** — requires pull requests, 0 approvals, force-push blocked.

- **Personal repo** → this should not happen (you are always admin on your own repos). If it does, try: `https://github.com/[OWNER]/[NAME]/settings/rules`.

Do NOT provide a link to `/settings/rules` for org repos — the user cannot access that page without admin role.

### 5c — Confirm

```bash
gh api repos/[OWNER]/[NAME]/collaborators --jq '.[].login'
gh api repos/[OWNER]/[NAME]/rulesets --jq '.[].name'
```

Report:
- Collaborators invited (pending acceptance) — *private repos only*
- Ruleset active on main
- How it works: everyone creates a branch → pushes to their branch → opens a pull request → gets approval → merges

**After Step 5 for org repos:** Go to Step 6 — CODEOWNERS + access.yml.

## Step 6 — Configure CODEOWNERS and access.yml (org repos)

Runs after creating/pushing an org repo, or when selected from Step 4b. Both files live in `.github/` and should be committed + pushed.

For **org/internal repos**, everyone already has read access. This step defines **who gets elevated permissions**:
- **CODEOWNERS** — who must approve PRs
- **access.yml** — who can push code, maintain the repo, or administer settings

> For **private/personal repos**, CODEOWNERS can still be used (from Step 4b menu), but access.yml is not relevant — use collaborator invites from Step 5 instead.

### 6a — CODEOWNERS

The `CODEOWNERS` file defines who must review PRs that touch specific files. It lives at `.github/CODEOWNERS`.

**Check if it already exists:**
```bash
gh api repos/[OWNER]/[NAME]/contents/.github/CODEOWNERS --jq '.content' 2>/dev/null
```

**If it exists**, decode and show the current contents. Ask if the user wants to update it.

**If it doesn't exist (or user wants to update)**, use `vscode_askQuestions` to collect:

| Input | Description |
|-------|-------------|
| **Default owner(s)** | Who should review everything by default? (e.g. `@dwojcik_microsoft`) |
| **Path-specific owners** | Optional — map specific paths to specific reviewers (e.g. `.github/skills/** @dwojcik_microsoft @iburvis_microsoft`) |

Resolve all usernames using the EMU resolution from Step 5a (add `@` prefix for CODEOWNERS format).

**Generate the file:**

```
# CODEOWNERS — auto-generated by create-repo skill
# https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

# Default owners for everything in the repo
*       @[DEFAULT_OWNER]

# Path-specific owners (last matching pattern wins)
[PATH]  @[OWNER1] @[OWNER2]

# Protect the CODEOWNERS file itself
/.github/CODEOWNERS @[DEFAULT_OWNER]
```

**Show the generated file to the user for confirmation** before writing it.

**Write and push:**
```powershell
# Create .github/ if needed
New-Item -ItemType Directory -Path ".github" -Force
Set-Content -Path ".github/CODEOWNERS" -Value $codeownersContent -Encoding UTF8
git add .github/CODEOWNERS
git commit -m "chore: add CODEOWNERS"
git push origin HEAD
```

**Optionally enable CODEOWNERS enforcement** — if a ruleset already exists, update it to require code owner review:
```bash
# Get existing ruleset ID
RULESET_ID=$(gh api repos/[OWNER]/[NAME]/rulesets --jq '.[0].id')
# Update the pull_request rule to require code owner review
gh api repos/[OWNER]/[NAME]/rulesets/$RULESET_ID -X PUT --input - <<'EOF'
{
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": true,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
    }}
  ]
}
EOF
```

Ask before enabling enforcement: *"Should PRs require approval from a CODEOWNER before merging? (This updates the existing ruleset.)"*

### 6b — access.yml (org repos only)

The `access.yml` file defines **elevated permissions** for org repos. It lives at `.github/access.yml` and is processed by the org's access management automation.

For **Internal** repos, everyone in the enterprise can already read/clone. This file controls who gets **write, maintain, or admin** access — the people who can push code, approve PRs, merge to main, and manage settings.

> **Not for private/personal repos.** For private repos on a personal EMU account, use collaborator invites from Step 5a instead — they control all access (read + write).

**Check if it already exists:**
```bash
gh api repos/[OWNER]/[NAME]/contents/.github/access.yml --jq '.content' 2>/dev/null
```

**If it exists**, decode and show the current contents. Ask if the user wants to update it.

**If it doesn't exist (or user wants to update)**, explain the permission levels first:

> **Permission levels for org repos:**
>
> | Level | What they can do |
> |-------|------------------|
> | **admin** | Full control — manage settings, rulesets, delete repo, manage access. Usually just the repo creator. |
> | **maintain** | Push code, approve & merge PRs, manage issues/PRs. Cannot change repo settings or access. Good for tech leads. |
> | **write** (push) | Push code to branches, create PRs. Can approve PRs if not restricted by CODEOWNERS. The default for active contributors. |
> | **read** (pull) | Clone and view code. **Everyone in the enterprise already has this for Internal repos** — no need to grant explicitly. |

Then use `vscode_askQuestions` to collect:

| Input | Description | When to ask |
|-------|-------------|-------------|
| **Admin users** | Full control (usually just you). Default: current user. | Always |
| **Maintainers** | Can push, approve PRs, merge to main. Tech leads or senior contributors. | Always |
| **Writers** | Can push code and create PRs. Active contributors. | Always |
| **Readers** | Clone and view code. For Internal repos everyone already has read — only needed for **Private** org repos where read access must be explicitly granted. | Private org repos only |
| **Teams** | Optional — org teams to grant access (e.g. `mcaps-microsoft/my-team`). Specify team + permission level. | Always |

Resolve all usernames using EMU resolution from Step 5a.

**Generate the file:**

```yaml
# access.yml — elevated access for org repo
# Everyone in the enterprise can already read this Internal repo.
# This file grants write/maintain/admin to specific people and teams.
# Processed by the org's access automation — changes sync automatically.

access:
  # Full control (repo settings, rulesets, access management)
  admins:
    users:
      - [ADMIN_USER]  # e.g. dwojcik_microsoft

  # Can push, approve PRs, merge, manage issues (no settings access)
  maintainers:
    users:
      - [MAINTAINER1]  # e.g. iburvis_microsoft
    teams:
      - [ORG]/[TEAM_NAME]  # e.g. mcaps-microsoft/ai-first-delivery

  # Can push code and create PRs
  writers:
    users:
      - [WRITER1]
      - [WRITER2]

  # Read access — not needed for Internal repos (everyone has it)
  # For Private org repos, uncomment and add users/teams who need read access:
  # readers:
  #   users:
  #     - [READER1]
  #   teams:
  #     - [ORG]/[TEAM_NAME]
```

> **For Private org repos:** uncomment the `readers` section and add users/teams. For Internal repos, leave it commented out — everyone in the enterprise already has read access.

**Show the generated file to the user for confirmation** before writing it.

**Write and push:**
```powershell
New-Item -ItemType Directory -Path ".github" -Force
Set-Content -Path ".github/access.yml" -Value $accessYmlContent -Encoding UTF8
git add .github/access.yml
git commit -m "chore: add access.yml"
git push origin HEAD
```

### 6c — Confirm

After creating/updating either file, verify by fetching from the repo:
```bash
gh api repos/[OWNER]/[NAME]/contents/.github/CODEOWNERS --jq '.name' 2>/dev/null
gh api repos/[OWNER]/[NAME]/contents/.github/access.yml --jq '.name' 2>/dev/null
```

Report:
- CODEOWNERS: created/updated (list default owner + path rules)
- access.yml: created/updated (list admins, writers, teams)
- CODEOWNER enforcement: enabled/disabled on ruleset
- Remind: *"Changes to access.yml are synced by the org's automation — allow a few minutes for permissions to update."*

## Step 7 — JIT (Just-in-Time) admin access on org repos

Microsoft security policy **forbids permanent admin** on `mcaps-microsoft` and most other corporate org repos. Instead, those repos ship a `.github/ISSUE_TEMPLATE/JitAccess.yml` form: anyone with at least Maintain role can file a **JIT Request** issue, get it approved by a fellow maintainer, and receive **2 to 24 hours of admin role** (default 2h).

This step is invoked whenever an admin-only operation is needed but the user only has `maintain` (or lower). It is referenced from:
- Step 4b — the menu shows admin ops tagged `⏳ requires JIT` for non-admins on JIT-capable repos, plus the standalone *Request JIT access* and *Resume pending JIT operation* options.
- Step 5b — the Ruleset permission check offers "File JIT and queue this op" when the user lacks admin.
- Any future admin-only sub-step (secrets, webhooks, visibility, description on `mcaps-microsoft`).

> 🚀 **Preferred implementation — canonical script.** Steps 7b–7e are implemented end-to-end by `jit-request.ps1`. It works for every nature of JIT request:
>
> ```powershell
> # 1) Default: PR-only ruleset on the current repo's default branch
> pwsh .github/skills/create-repo/scripts/jit-request.ps1
>
> # 2) Known operation + structured params (templated justification)
> pwsh .github/skills/create-repo/scripts/jit-request.ps1 -Level Standard -DurationHours 4
> pwsh .github/skills/create-repo/scripts/jit-request.ps1 -OperationKind secret -Params @{ name = 'NPM_TOKEN' }
>
> # 3) Known operation + free-text justification override
> pwsh .github/skills/create-repo/scripts/jit-request.ps1 -OperationKind webhook `
>      -Justification "Rotate hooks.example.com webhook secret per IR-123."
>
> # 4) Ad-hoc / jit-only -- 'just give me 2h, I'll do it manually in the UI'
> pwsh .github/skills/create-repo/scripts/jit-request.ps1 -OperationKind jit-only `
>      -Justification "Need 2h admin to clean up orphan webhooks in the GitHub UI."
> ```
>
> All modes auto-detect owner/repo/default-branch via `gh repo view`, read approvers live from `.github/acl/access.yml` (Admin + Maintain roles, excluding the requester), file the JIT issue, and open a Teams group chat (desktop deep link + https + web fallback + clipboard).
>
> **Pending-op behaviour:** modes (1)–(3) write `.tmp/jit-pending-op.json` so `/create-repo resume` can finish the operation after approval. Mode (4) — `OperationKind jit-only` — skips the pending-op file (nothing to resume; the user does the action by hand).
>
> **Never hard-code approvers, owner, repo, branch, justification, or duration.** Pass `-Justification` for any free-text request; pass `-Params @{ ... }` for structured operation context (never put secret values in `-Params`).

### 7a — JIT capability detection (`is_jit_capable`)

Before offering the JIT path, check that the repo actually uses this pattern:

```bash
# Both files must exist for the JIT round-trip to work
gh api repos/[OWNER]/[NAME]/contents/.github/ISSUE_TEMPLATE/JitAccess.yml --jq '.name' 2>/dev/null
gh api repos/[OWNER]/[NAME]/contents/.github/acl/access.yml --jq '.name' 2>/dev/null
```

If both exist → the repo is JIT-capable. Otherwise → fall back to the "ask an org admin" guidance.

### 7b — Build operation payload & persist it

The goal of persisting is: after JIT is approved (hours later, in a fresh chat session), the skill can resume the **exact same operation** without re-prompting the user.

Write `.tmp/jit-pending-op.json` in the workspace root. Make sure `.tmp/` is in `.gitignore` (add it if missing — never commit pending-op files).

```json
{
  "created_at": "<ISO timestamp>",
  "owner": "mcaps-microsoft",
  "repo": "<repo>",
  "actor": "<your EMU username>",
  "role_at_request_time": "maintain",
  "operation_kind": "protect-main | secret | variable | description | visibility | features | webhook | jit-only",
  "params": {
    "...": "...   (operation-specific — e.g. ruleset_level=PR-only, secret_name=FOO_TOKEN, etc.)"
  },
  "jit_issue_url": "https://github.com/mcaps-microsoft/<repo>/issues/<n>",
  "jit_duration_hours": 2
}
```

**Never store secret values, webhook URLs with tokens, or any sensitive payload** in this file — store only the operation shape. The actual sensitive value is re-prompted in the terminal at resume time.

### 7c — Auto-generate justification

The JIT issue's `justification` field (required by `JitAccess.yml`) is filled by the skill. Use the operation kind to produce a short, honest sentence — no secrets, no PII:

| Operation | Justification template |
|---|---|
| `protect-main` | `Create a branch ruleset on main ([LEVEL]) for [OWNER]/[REPO].` |
| `secret` | `Add/update a repo-level Actions secret ([NAME]) for [OWNER]/[REPO].` |
| `variable` | `Add/update a repo-level Actions variable ([NAME]) for [OWNER]/[REPO].` |
| `description` | `Update the repository description / topics for [OWNER]/[REPO].` |
| `visibility` | `Change repository visibility (Internal ↔ Private) for [OWNER]/[REPO].` |
| `features` | `Toggle repo features (issues / wiki / discussions / projects / merge type) for [OWNER]/[REPO].` |
| `webhook` | `Add / edit / remove a repository webhook for [OWNER]/[REPO].` |
| `jit-only` | Ask the user — they're going to do something manually in the GitHub UI. |

### 7d — Ask duration, then file the JIT Request issue

The issue template lives at `.github/ISSUE_TEMPLATE/JitAccess.yml`. It has `title: "JIT Request"`, `labels: ["jit"]`, `assignees: [gimsvc_microsoft]`, and two form fields: `justification` (required textarea) and `duration` (dropdown — `2`–`24` hours, default `2`).

> ⚠️ **`gh issue create` cannot fill issue-form fields from the CLI.** The `--template` flag only pre-fills the editor in interactive mode; in non-interactive mode it's silently ignored. `-F` is `--body-file` (Go's `os.Open`) — passing `-F duration=2` gives `open duration=2: The system cannot find the file specified`. The canonical helper `jit-request.ps1` works around this by posting a plain `--body` markdown payload (the approver bot parses `Duration: N hours` from the body and triggers on the `jit` label). **Always invoke `jit-request.ps1`; never call `gh issue create --template` directly.**

**Step 1 — Always ask the user how long they need admin for.** Do NOT silently default. Use `vscode_askQuestions` with a single question, options for common values (2, 4, 8, 12, 24), `2 hours` marked as recommended, and `allowFreeformInput: true` so the user can type any integer in `2..24`:

> ⏳ **How long do you need admin access for?**
> Pick a duration between **2 and 24 hours** (default **2h**). The clock starts when the JIT is approved and admin auto-expires at the end.
>
> - **2 hours** *(recommended)*
> - 4 hours
> - 8 hours
> - 12 hours
> - 24 hours
> - *(or type any integer between 2 and 24)*

Validate the answer is an integer in `[2, 24]`. If the user types something invalid (1, 0, 25, "two", empty), re-ask with the same options. Do not fall back silently to 2 — make the user pick. (1-hour was removed — approvers said it's too short to be useful for any real admin task.)

**Step 2 — File the issue immediately with the chosen duration.** No extra confirmation step — invoke `jit-request.ps1` with the chosen duration and operation kind:

```powershell
pwsh .github/skills/create-repo/scripts/jit-request.ps1 `
  -OperationKind protect-main `
  -Level PR-only `
  -DurationHours [CHOSEN_HOURS]
```

The script auto-detects owner/repo, builds the justification, posts the issue via `gh issue create --body ... --label jit --assignee gimsvc_microsoft --title 'JIT Request'`, writes `.tmp/jit-pending-op.json`, and launches Teams.

> **Implementation note for `jit-request.ps1`:** the canonical script takes `-DurationHours <N>` (validated to `2..24`). The skill asks the user first via `vscode_askQuestions`, then invokes the script with `-DurationHours <chosen>` — the script itself does NOT re-prompt. Never bypass the script with a direct `gh issue create --template` call — it will fail (see warning box above).

After creation:
1. Capture the issue URL and write it into `.tmp/jit-pending-op.json` (`jit_issue_url`).
2. Open the issue in the browser so the user can see it: `Start-Process "<issue_url>"`.

### 7e — Open a Teams group chat with all maintainers

Approvers come from the repo's `.github/acl/access.yml` — anyone with role **Admin** or **Maintain**, excluding the requester. Read it live; never hardcode:

```powershell
gh api repos/[OWNER]/[NAME]/contents/.github/acl/access.yml --jq '.content' |
  ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

From the YAML, list every member with role `Admin` or `Maintain` and remove the current user. **Rank by recent collaboration** (last 60 days of git log in the workspace) so the most-likely-responsive person is shown first in the candidate list — but the Teams chat itself includes **all** maintainers, not just the top pick:

```bash
git log --since="60 days ago" --format='%an' | Sort-Object | Get-Unique -AsString | Group-Object | Sort-Object Count -Descending
```

Map git author names to EMU aliases by approximate match against the access.yml list.

Then show the candidate list and the message that will be prefilled in the group chat:

> 👥 **Maintainers on `[OWNER]/[NAME]`** (ranked by recent collaboration with you — all of them will be added to the Teams group chat):
> 1. **[Alias 1]** — `@[alias1]_microsoft` *(top pick)*
> 2. **[Alias 2]** — `@[alias2]_microsoft`
> 3. **[Alias 3]** — `@[alias3]_microsoft`
> *…and the rest of the Maintain/Admin list from access.yml*
>
> **Draft message** (will be prefilled in the Teams group chat — review before hitting Send). The JIT issue link MUST be a **bare URL on its own line, surrounded by whitespace** — Teams compose does NOT process Markdown from deep-link `message=` params (confirmed 2026-05-22 — `[#NNN](url)` renders as literal text in the sent message). Bare URLs surrounded by whitespace ARE auto-linkified by Teams on Send:
>
> > Hi all — I'm requesting JIT admin on `[OWNER]/[NAME]` for **[CHOSEN_HOURS]h** to [GENERATED_JUSTIFICATION_SHORT]. Could one of you approve it?
> >
> > JIT issue — please click to approve:
> > https://github.com/[OWNER]/[NAME]/issues/NNN
> >
> > Thanks!

#### Auto-open the Teams group chat with the message prefilled

After showing the list, **automatically open a Teams group chat that includes every maintainer** using the Teams deep-link `chat/0/0` endpoint with a comma-separated `users=` parameter. The message body is prefilled in the compose box; **the user still has to click Send** — the skill never sends on the user's behalf.

Resolve each maintainer's email by combining their EMU alias from `access.yml` with the Microsoft tenant domain (`@microsoft.com`). Drop any alias you cannot map cleanly and report the drops. If fewer than two emails survive, the deep-link still works but Teams may open a 1:1 instead of a group chat — that is acceptable.

```powershell
# Build the maintainer email list (all of them, comma-joined, current user excluded)
$maintainerEmails = $maintainerAliases | ForEach-Object { "$_@microsoft.com" }
$usersParam       = ($maintainerEmails -join ",")

# IMPORTANT: pass the JIT issue URL as a BARE URL on its own line, surrounded
# by whitespace. Teams compose does NOT process Markdown from the deep-link
# `message=` parameter (confirmed 2026-05-22 -- `[#NNN](url)` was sent as
# literal text). Bare URLs surrounded by whitespace ARE auto-linkified by
# Teams when the user clicks Send.
$draftMessage = @"
Hi all -- I'm requesting JIT admin on $owner/$repo for ${durationHours}h to $justShort. Could one of you approve it?

JIT issue -- please click to approve:
$jitIssueUrl

Thanks!
"@

$encodedMsg = [uri]::EscapeDataString($draftMessage)
$teamsUrl   = "https://teams.microsoft.com/l/chat/0/0?users=$usersParam&message=$encodedMsg"

# Open in the Teams desktop client (falls back to web if desktop isn't installed)
Start-Process $teamsUrl
```

Notes & guardrails:
- Use the **`https://teams.microsoft.com/l/chat/0/0`** deep link (the documented "start chat" endpoint). When `users=` contains multiple comma-separated emails, Teams opens a **group chat** with all of them; the `message=` value is prefilled in the compose box. It does **not** auto-send.
- **All maintainers by default** — group chat is the intended behaviour so any one of them can approve the JIT issue and you don't depend on a single person being online. The user can override and request a 1:1 with the top pick if they want.
- **Group chat size limit**: Teams `chat/0/0` accepts up to ~20 users. If `access.yml` has more than 19 maintainers (excluding the requester), fall back to the top 19 by collaboration rank and tell the user *"X additional maintainers were not added to the chat — see access.yml."*
- **Always reference the JIT issue as a bare URL on its own line, surrounded by whitespace** — NOT a Markdown `[text](url)` link. Teams compose **does not process Markdown** from the deep-link `message=` parameter (proven 2026-05-22: `[#NNN](url)` was sent and rendered as literal text). A bare URL with whitespace on both sides IS auto-linkified by Teams on Send.
- **Privacy**: never include secret values, the full JIT issue body, or anything sensitive in the prefilled message. Just the short justification + issue URL.
- **Fallback**: if `Start-Process` returns an error (no browser, no Teams installed, headless box), keep the copy-paste block visible and tell the user *"Couldn't launch Teams automatically — copy the message above and paste it manually."*
- **User opt-out**: if the user has previously said *"don't auto-open Teams"* in this session, skip the `Start-Process` call and show the copy-paste block only.

After launching, append a one-liner to the summary so the user knows what happened:
> 💬 Opened a Teams group chat with **N maintainers** ([Alias 1], [Alias 2], …) — review the prefilled message and hit **Send** when ready.

### 7f — Exit cleanly

After the issue is filed and the Teams draft is shown, **stop the skill**. Do NOT loop polling for approval — JIT can take minutes to hours and the user shouldn't have an idle session burning context.

Show a final summary:
> ✅ **JIT Request filed.** Operation `[KIND]` saved to `.tmp/jit-pending-op.json`. When the JIT is approved (you'll get a GitHub notification), run **`/create-repo`** again and pick *"Resume pending JIT operation"* from the menu — or just type `/create-repo resume`.

### 7g — Resume after JIT approval

When the user comes back and selects **Resume pending JIT operation** (or invokes `/create-repo resume`):

1. **Read** `.tmp/jit-pending-op.json`. If missing → tell the user there is nothing to resume and exit.
2. **Re-check the user's role** with `gh api repos/<owner>/<repo>/collaborators/<actor>/permission`. 
   - If still not admin → the JIT was not yet approved (or has already expired). Show the issue URL, ask whether to file a new JIT or wait, and exit.
   - If now admin → continue.
3. **Execute** the saved operation. For sensitive ops (secret, webhook with token), re-prompt the user for the secret value in the terminal:
   ```powershell
   $value = Read-Host "Enter secret value for [SECRET_NAME]" -AsSecureString
   # convert and pipe to: gh secret set [SECRET_NAME] --repo [OWNER]/[NAME] --body -
   ```
4. **Verify** with the matching read-back call (e.g. `gh api repos/.../rulesets` after `protect-main`, `gh secret list` after `secret`).
5. **Comment on the JIT issue** with the operation outcome so the audit trail is closed:
   ```bash
   gh issue comment [N] --repo [OWNER]/[NAME] --body "Operation `[KIND]` completed successfully at [ISO]. Closing."
   gh issue close [N] --repo [OWNER]/[NAME]
   ```
6. **Cleanup** — delete `.tmp/jit-pending-op.json`.
7. Report success.

### 7h — What JIT will NOT cover

- ❌ **Making a repo Public** — MCAPS policy blocks this regardless of role. Refuse even if asked.
- ❌ **Bypassing JIT approval** — every admin operation goes through the issue + maintainer approval. The skill makes it fast, not optional.
- ❌ **Storing secret values in chat or in the issue body** — secret values are entered directly in the terminal at resume time.
- ❌ **Maintainer-level ops** — inviting collaborators, editing `access.yml` / CODEOWNERS, archiving, managing labels/milestones don't need admin. Use the regular menu (Step 4b) — no JIT needed.

## Maintenance notes (for skill editors)

Reference notes for anyone editing `scripts/jit-request.ps1`, `JitAccess.yml`, or this SKILL.md. These are hard-won lessons from prior debugging sessions — re-introducing any of them will silently break the JIT flow.

### gh CLI — `gh issue create` flags

- **`-F` is `--body-file`, NOT a form-field setter.** Passing `-F duration=2` produces `open duration=2: The system cannot find the file specified` because gh tries to open `duration=2` as a file. There is no `gh issue create` flag that fills issue-form fields.
- **`--template` only pre-fills the interactive editor.** In non-interactive mode (any CI / scripted invocation) the template is silently ignored. Issue Forms cannot be filled programmatically.
- **Workaround used by `jit-request.ps1`:** post a plain `--body` markdown payload that the JIT approver bot (`gimsvc_microsoft`) can parse for `Duration: N hours`, with `--label jit` and `--assignee gimsvc_microsoft` replicating what the form would have set. Never replace this with a `gh issue create --template` call.
- **`gh api` flag conventions are the opposite of `gh issue create`:** `gh api -f key=value` = string field, `gh api -F key=value` = typed field (number/bool auto-coerced). Don't mix the two conventions up.

### `JitAccess.yml` — Issue Forms quirks

- **`default:` on a dropdown is zero-indexed into `options:`.** `default: 0` resolves to the **first** option in the list, `default: 1` to the second, etc. — NOT to a literal value. The template currently sets `default: 0` so the dropdown opens on "2 hours". Bumping to `default: 1` opens on "3 hours". Verified 2026-05-21. There is an inline comment in `JitAccess.yml` to remind future editors.
- **Title/labels/assignees in the YAML are NOT applied when `gh issue create` posts a plain `--body`.** The script replicates them explicitly via `--title 'JIT Request' --label 'jit' --assignee 'gimsvc_microsoft'`. If you change the YAML's `title:` / `labels:` / `assignees:`, mirror the change in `jit-request.ps1`'s `gh issue create` call.

### Teams deep-link compose

- **Markdown is NOT processed in the `message=` parameter of `https://teams.microsoft.com/l/chat/0/0`.** Proven 2026-05-22: `[#330](https://github.com/...)` was sent and displayed as the literal 6 characters `[#330]` followed by the literal URL in parens — no clickable hyperlink. **Always use bare URLs on their own line, surrounded by whitespace** — Teams auto-linkifies them on Send. `jit-request.ps1` builds the chat body this way; do not "improve" it to Markdown links.
- Same rule applies to `mailto:` bodies and most other chat-compose deep links. Adaptive cards and Teams message extensions DO process Markdown, but the `chat/0/0` deep-link prefill path does not.

### PowerShell editing pitfalls

- **`create_file` writes UTF-8 without BOM. PowerShell 5.1 reads `.ps1` files as Windows-1252 (ANSI) unless a UTF-8 BOM is present.** Result: emojis (`🔄 ⏰ ✅ →`) get mojibaked at parse time (`🔄` → `ðŸ"„`, `→` → `â†'`) and the script fails with `ParseException`. If you (re)create `jit-request.ps1` from scratch via `create_file`, immediately prepend a UTF-8 BOM:
  ```powershell
  $p='.github/skills/create-repo/scripts/jit-request.ps1'
  $bom=[byte[]](0xEF,0xBB,0xBF)
  [IO.File]::WriteAllBytes($p, $bom + [IO.File]::ReadAllBytes($p))
  ```
  Alternatively, run the script with `pwsh.exe` (PowerShell 7+), which defaults to UTF-8. For pure text-substitution edits on this SKILL.md, prefer `multi_replace_string_in_file` over scripted PowerShell — no encoding traps.
- **`Out-File -NoNewline` destroys multi-line content.** PowerShell splits native command output (e.g. `gh issue view --json body`) into an array of strings; `-NoNewline` concatenates them WITHOUT separators. Use plain `Out-File` or `Set-Content` with the raw string.
- **VS Code persistent terminal can stop echoing output mid-session.** Symptom: `Write-Host "hello"` produces no output but the same command works in a fresh terminal. Usually triggered by a prior `ParseException` or a backgrounded process. Workaround: route results through `Set-Content` + `Get-Content`, or open a fresh terminal. The script itself doesn't rely on echo for correctness (it writes `.tmp/jit-pending-op.json` and the JIT issue URL is recoverable via `gh issue list --label jit`).
