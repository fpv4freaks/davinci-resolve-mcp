---
name: safe-push
owner: dwojcik
stream: technical
description: >
  Safely push current branch changes to GitHub — survey branch state so merged branches are never
  offered, rebase on latest main, resolve conflicts, push, and sweep stale merged branches.
  Use ONLY when explicitly invoked via /safe-push. NOT auto-triggered.
argument-hint: "No arguments needed — the skill detects branch, changes, and remote automatically"
disable-model-invocation: true
---

# Safe Push — Rebase & Push Workflow

Execute the following steps **sequentially**. Stop immediately if any step fails and report the error.

Track a `stash_count` variable (starts at 0) throughout the workflow. Increment it each time you stash, decrement when you pop. If the workflow fails or aborts, remind the user about any outstanding stashes (`git stash list`).

## Rules that never bend

- **Never infer merge state from `git branch --merged`.** A squash merge rewrites history, so the merged commits are not ancestors of `main` and that check reports a merged branch as unmerged. Merge state comes from the PR, via `gh`.
- **Always `git fetch origin --prune` before trusting `%(upstream:track)`.** Without a prune, `[gone]` is stale.
- **Never delete a branch without a confirmed merged PR**, and never as a side effect of pushing.
- **Never read, enumerate, or act on branches belonging to anyone else.** Broad pull-request queries are scoped with `--author "@me"`. The **only** permitted lookup outside your own pull requests is a single query about the one branch you are about to push to, asking whether a pull request exists on it. It exists solely because a rebase plus force-push would destroy a pull request somebody else opened from your branch, and `--force-with-lease` does not protect them. Never loop it over multiple branches, and never run it on a branch you are not about to push to. **Never enumerate the remote**: `git ls-remote --heads origin` and `git for-each-ref refs/remotes/origin/` without a branch name both list everybody's work. Neither is ever necessary — every branch you act on comes from a list you already own, so you always have a name to ask about.
- **Detect repository settings, never assume them.** `deleteBranchOnMerge` and `allow_auto_merge` differ per repository.
- **Run each command as a single line.** Multi-line shell blocks are mangled by some Windows PowerShell terminals and silently half-execute; chain with `;` rather than newlines.

## Pre-flight checks

1. Run `git status` to check for uncommitted changes.
2. If there are uncommitted changes:
   - Show the list of changed files.
   - Ask: "You have uncommitted changes. Should I stage and commit them first? If yes, suggest a commit message."
   - Wait for the user's response before proceeding.
   - **Agree the message here, but do not commit yet.** The branch this work belongs on has not been chosen. Step 4 may move you off the current one, and if you are on `main` it certainly will. Committing now lands the commit wherever you happen to be standing — on `main` that leaves local `main` sitting ahead of the remote holding a commit that belongs on a feature branch. Carry the approved message forward to step 4d.
3. **Branch state survey** — build this *before* offering any branch, so a merged or deleted branch is never presented as a live target.

   Run these three commands:
   ```
   git fetch origin --prune
   gh pr list --state all --author "@me" --json headRefName,number,state,mergedAt,url --limit 100
   git for-each-ref --sort=-committerdate --format='%(refname:short)|%(upstream:track)|%(committerdate:relative)' refs/heads/
   ```
   `--author "@me"` is **required**: only your own pull requests are ever read, and only your own local branches are ever classified.

   Join the PR list to the local branches **by name in one pass** — one API call, never one call per branch — and classify each branch:

   | State | Evidence | Offer as a push target? |
   |-------|----------|-------------------------|
   | `active` | no PR, or its PR is open | yes |
   | `merged` | its PR has a non-null `mergedAt` | no |
   | `closed` | its PR was closed without merging | no |
   | `gone` | `%(upstream:track)` is `[gone]` | no |
   | `local-only` | no upstream set, never pushed | yes |

   If `gh` is unavailable, fall back to the local branch list alone and say plainly that merge state could not be checked, so any branch shown may already be merged.

   Because this query is scoped to your own pull requests, a branch you pushed but which somebody else opened the PR for would show here as `active`. Step 4 closes that with a single targeted check before the branch is actually used.

3b. **Stop if there is nothing to push.** If step 1 found a clean working tree *and* the current branch has no commits the remote is missing — `git log <current-branch> --not --remotes` prints nothing — then the rest of this workflow has no work to act on. Every remaining step degrades to a no-op and the last one fails outright: the rebase replays nothing, the push sends nothing, and `gh pr create` is rejected with "No commits between main and `<branch>`".

   Report what the survey found about the current branch — including its PR and merge state, since a freshly merged branch is the usual way to arrive here — then stop. Offer the stale branch sweep, which is normally the useful thing to do at that point, and do not create a branch, rebase, push, or open a pull request.

4. **Branch selection** — driven by the survey, never by branch names alone.
   - **If on `main`**: say "You can't push directly to main" and go straight to the list.
   - **If the current branch is `merged`, `closed` or `gone`**: do not offer to continue on it. Name the PR that closed it — "`<branch>` was merged in #<number>" — and make *create new branch* the default.
   - **If the current branch is `active`**: confirm briefly — "Pushing from `<current-branch>`. Continue, switch, or create new?"
   - Propose a new branch name from the staged/uncommitted changes and conversation context: `feature/` for new capability, `fix/` for bug fixes, `docs/` for documentation.
   - Show at most 10 branches, most recent first, each with its state. Ineligible branches are listed but not selectable, and always carry the reason:
     ```
       1. fix/meeting-visual-context-manifest — merged in #566, not available
       2. docs/update-readme (3 days ago)
     ▶ 3. ✨ Create new branch — suggested: `<auto-proposed-name>`   (default)
     Pick a number, press Enter for the default, or type a different name.
     ```
   - Wait for the user's response.
   - **Confirm the chosen branch before using it.** The survey above only sees your own pull requests, so run one targeted check on the branch you are about to push to — by exact name, for a branch you already have locally. Once, for the selected branch only; never for the whole list:
     ```
     gh pr list --head <branch> --state all --limit 1 --json number,state,mergedAt,author
     ```
     - Returns a **merged or closed** PR the survey missed — the branch is dead. Say which PR, and go back to the choice.
     - Returns an **open PR opened by somebody else** — stop before pushing and say who owns it. `--force-with-lease` will **not** protect their pull request: it guards against refs you have not fetched, not against a rebase that rewrites history their PR depends on. Continue only once the user has seen this.
     - Returns nothing — the branch is genuinely fresh.
   - **If switching to an existing branch with uncommitted changes**: run `git stash push -u -m "safe-push: carrying changes to <target-branch>"` (increment `stash_count`), switch with `git checkout <branch>`, then run `git stash pop` (decrement `stash_count`).
   - **If switching to an existing branch with no uncommitted changes**: just run `git checkout <branch>`.
   - **If creating a new branch**: do not create it here. Step 4c creates it, because a new branch has to start from an up-to-date `main` and nothing has refreshed `main` yet at this point.
   - **If staying on current branch**: continue to step 4b.

### Stale branch sweep

The skill stops at PR creation, so it is never running at merge time and cannot delete a branch then. Instead it sweeps what earlier rounds left behind.

- Identify the current user once: `gh api user --jq .login`.
- The step 3 survey is **not sufficient here**. It is capped at the most recent PRs, which covers your local branches but not the full history of merged ones. Run one targeted query instead:
  ```
  gh pr list --state merged --author "@me" --json headRefName,number,url --limit 500
  ```
  Do not lower that limit or reuse the step 3 result: on a repo with 154 remote branches, the capped survey found 11 candidates where this query found all 48.
- That query is the **only** source of branch names for the sweep. Work down it; never go looking for names on the remote. Deciding which of them still exist is a **local** test, one name at a time — step 3 already ran `git fetch origin --prune`, so the remote-tracking refs are accurate:
  ```
  git show-ref --verify --quiet refs/remotes/origin/<branch>
  ```
  Exit code 0 means the branch is still on the remote. This costs no network call, so running it across a few hundred names you already own is cheap, and it reveals nothing about anyone else. Listing the remote to answer the same question is faster to type and is the thing this skill exists to prevent.
- A branch is a **sweep candidate** only when all of these hold:
  - its PR is merged, and **that PR was authored by the current user**
  - it still exists on the remote, by the local test above
  - it is not `main` and not the branch currently checked out
  - it has no open PR
  - if it exists locally, it has no unpushed commits — check with `git log <branch> --not --remotes`
- Report the count in **one line** and stop there: "12 of your branches are merged and can be cleaned up. Want the list?" Expand only if the user asks. A push request must not turn into a cleanup session.
- If the user asks to clean up, show the full list with each branch's PR number, then require explicit confirmation before deleting anything.
  - Local: `git branch -d <branch>`. If it refuses with "not fully merged", that is the squash-merge case — use `git branch -D <branch>` **only** because the merged PR is confirmed, and say so.
  - Immediately before each *remote* deletion, re-confirm that one branch against the live remote. The local refs are only as fresh as the last fetch, and deletion cannot be undone: `git ls-remote --heads origin <branch>`. Always with an explicit branch name — the bare form lists everybody else's work.
  - Remote: `git push origin --delete <branch>` is a **separate** step needing its own confirmation. Check `deleteBranchOnMerge` first (`gh repo view --json deleteBranchOnMerge`); when it is enabled there is usually nothing to sweep, and when it is disabled mention that enabling it prevents the backlog from rebuilding.
- Never propose branches belonging to other people, and never delete without confirmation.

## Rebase on latest main

### Fork detection and sync

4b. Before rebasing, check if the user is working with a fork:
   - Run `git remote -v` to list remotes.
   - **If only `origin` exists** (pointing to the upstream repo, e.g., `mcaps-microsoft/...`):
     - Run `git push --dry-run origin HEAD` to test write access.
     - If push is **rejected with permission denied**: the user has no write access.
       - Say: "You don't have write access to the upstream repo. I'll create a fork for you."
       - Run `gh repo fork --remote=true` — this creates a fork on GitHub and adds it as `origin`, renaming the original to `upstream`.
       - Verify with `git remote -v` — confirm `origin` = fork, `upstream` = original.
   - **If both `origin` (fork) and `upstream` (original) exist**: this is already a fork setup. Continue.

4c. **Start the new branch from up-to-date main** — run this whenever step 4 chose *create new*, whatever the reason: the current branch was `merged`, `closed` or `gone`; you were on `main`, which can never be pushed to and so always forces a new branch; or the user simply asked for a fresh one. Steps 3 and 4 already established which of those applies; do not re-query per branch.
   - **Stash uncommitted changes** if any: `git stash push -u -m "safe-push: carrying changes to new branch"` (increment `stash_count`).
   - **Bring main up to date** — the commands depend on the remote layout, so check it rather than assuming a fork:
     - **If an `upstream` remote exists** (fork setup): `git checkout main`, `git fetch upstream`, `git merge upstream/main`, then `git push origin main` to update the fork.
     - **Otherwise** (direct write access): `git checkout main`, then `git pull --ff-only`.
   - **Create the new branch**: `git checkout -b <new-branch-name>`, using the name confirmed in step 4.
   - **Pop stash** if stashed: `git stash pop` (decrement `stash_count`).
   - Continue to step 4d.

4d. **Commit, now that the branch is settled.** If step 2 agreed a commit message and the changes are still uncommitted, stage and commit them here, on whichever branch steps 4 and 4c arrived at. Every path reaches this step — new branch, switched branch, or stayed put — and it is the first point in the workflow where the target branch is known to be the right one.

5. Run `git checkout main` — switch to main.
6. Run `git pull --ff-only` — fast-forward main to match remote. Using `--ff-only` avoids accidental merge commits on local main.
   - **If working with a fork** (upstream remote exists): run `git fetch upstream && git merge upstream/main` instead, then `git push origin main` to keep the fork in sync.
   - If `git pull --ff-only` **fails** due to untracked files conflicting with incoming changes: run `git stash push -u -m "safe-push: stash before pull"` (increment `stash_count`), then retry `git pull --ff-only`, then run `git stash pop` (decrement `stash_count`).
   - If `--ff-only` fails because main has diverged: report the error and suggest `git pull --rebase` on main as an alternative, but do not run it automatically.
7. Run `git checkout <original-branch>` — switch back to the feature branch (use the branch name from step 4).
8. Run `git rebase main` — replay commits on top of updated main.

## Handle rebase result

9. If rebase **succeeds** — continue to Push.
10. If rebase **fails with conflicts**:
    - Run `git diff --name-only --diff-filter=U` to list conflicted files.
    - Show the list and say: "Rebase paused — these files have conflicts. Resolve them manually, then tell me to continue. If you want to abort the rebase entirely, say 'abort'."
    - STOP here — do not proceed until the user says to continue.
    - If the user says **abort**: run `git rebase --abort`, report that the branch is back to its original state, and stop the workflow. Remind about any outstanding stashes if `stash_count > 0`.
    - When the user says **continue**: run `git add -u` then `git rebase --continue`. If new conflicts appear, repeat this step.

## Push

11. Check if the branch exists on the remote: `git ls-remote --heads origin <branch-name>`.
12. If branch **already exists** on remote (was previously pushed):
    - Run `git push --force-with-lease origin <branch-name>`.
    - This is safe — it only force-pushes if no one else has pushed to this branch since the last fetch.
13. If branch is **new** (not yet on remote):
    - Run `git push -u origin <branch-name>`.

## Pull Request

14. Check if `gh` CLI is available: run `gh --version`.
    - If `gh` is **not installed**, derive the repo URL with `git remote get-url origin`, convert SSH URLs to HTTPS format, and skip to Summary with: "GitHub CLI (`gh`) not installed — create the PR manually at `<repo-url>/compare/main...<branch-name>`".
15. Check if a PR already exists for this branch: `gh pr list --head <branch-name> --state open`.
    - **If working with a fork**: use `gh pr list --head <fork-owner>:<branch-name> --state open --repo <upstream-owner>/<upstream-repo>` to check PRs on the upstream repo.
16. If **no open PR exists**, ask: "Would you like me to create a Pull Request against main? (yes/no)"
    - If yes and **working with a fork**: run `gh pr create --repo <upstream-owner>/<upstream-repo> --base main --head <fork-owner>:<branch-name> --title "<title>" --body "<body>"`.
    - If yes and **not a fork**: run `gh pr create --base main --head <branch-name> --title "<generate a clear title from the commit messages>" --body "<generate a summary of changes from git log>"`.
    - Show the PR URL from the output.
17. If a **PR already exists**, show its URL and say: "PR already exists — your latest push is included automatically."

> **On merging and branch deletion.** This skill stops at PR creation and does not merge, so it cannot delete the branch at merge time — a PR waiting on approval may be merged days later, possibly by someone else, when nothing is running here. The stale branch sweep in pre-flight is what recovers those. If asked to merge from this skill, pass `--delete-branch`; and check `allow_auto_merge` (`gh api repos/<owner>/<repo> -q .allow_auto_merge`) before using `--auto`, because it fails outright where auto-merge is disabled.

## Summary

18. Run `git log --oneline -5` to show recent commits.
19. Report:
    - Branch name
    - Number of commits ahead of main
    - Whether push was a normal push or force-with-lease
    - PR status (created / already exists / skipped)
    - Link to the PR or branch on GitHub
