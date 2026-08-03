---
name: safe-push
owner: dwojcik
stream: technical
description: >
  Safely push current branch changes to GitHub — rebase on latest main, resolve conflicts, and push.
  Use ONLY when explicitly invoked via /safe-push. NOT auto-triggered.
argument-hint: "No arguments needed — the skill detects branch, changes, and remote automatically"
disable-model-invocation: true
---

# Safe Push — Rebase & Push Workflow

Execute the following steps **sequentially**. Stop immediately if any step fails and report the error.

Track a `stash_count` variable (starts at 0) throughout the workflow. Increment it each time you stash, decrement when you pop. If the workflow fails or aborts, remind the user about any outstanding stashes (`git stash list`).

## Pre-flight checks

1. Run `git status` to check for uncommitted changes.
2. If there are uncommitted changes:
   - Show the list of changed files.
   - Ask: "You have uncommitted changes. Should I stage and commit them first? If yes, suggest a commit message."
   - Wait for the user's response before proceeding.
3. Run `git branch --show-current` to confirm which branch we're on.
4. **Branch selection**:
   - **If already on a non-main feature branch**: confirm briefly — "Pushing from `<current-branch>`. Continue, switch to another branch, or create new?"
   - **If on `main`**: warn "You can't push directly to main" and present branch options.
   - In both cases, show the choice list:
     - Run `git for-each-ref --sort=-committerdate --format='%(refname:short) (%(committerdate:relative))' refs/heads/ --count=10` to list local branches sorted by most recently used. Filter out `main`.
     - Propose a new branch name based on uncommitted/staged changes and conversation context, following naming conventions:
       - `feature/<short-description>` for new features or skills
       - `fix/<short-description>` for bug fixes
       - `docs/<short-description>` for documentation changes
     - Display like this (mark current branch with ▶ if on a feature branch):
       ```
       ▶ 1. docs/add-skills-catalog-workflow (current — 2 hours ago)
         2. fix/update-readme (3 days ago)
         ...
         N+1. ✨ Create new branch — suggested: `<auto-proposed-name>`
       Continue on current branch (Enter), pick a number, or type a different name.
       ```
   - Wait for the user's response.
   - **If switching branches with uncommitted changes**: run `git stash push -u -m "safe-push: carrying changes to <target-branch>"` (increment `stash_count`), switch with `git checkout <branch>` (or `git checkout -b <new-branch>`), then run `git stash pop` (decrement `stash_count`).
   - **If switching branches with no uncommitted changes**: just run `git checkout <branch>` (or `git checkout -b <new-branch>`).
   - **If staying on current branch**: continue to step 5.

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

4c. **Merged branch detection** — check if the current branch was already merged:
   - Run `gh pr list --head <branch-name> --state merged --json number,title --limit 1`.
   - If a **merged PR is found**:
     - Say: "Your previous PR (#<number>) was already merged. To continue with new changes, I need to:
       1. Sync your fork's main with upstream
       2. Create a new branch for your new work"
     - **Sync fork main**:
       - Run `git checkout main`
       - Run `git fetch upstream` (or `git fetch origin` if no upstream remote)
       - Run `git merge upstream/main` (or `git merge origin/main`)
       - Run `git push origin main` (update fork's main on GitHub)
     - **Stash uncommitted changes** if any: `git stash push -u -m "safe-push: carrying changes to new branch"` (increment `stash_count`).
     - **Create a new branch** from updated main:
       - Propose a branch name based on the uncommitted/staged changes.
       - Ask the user to confirm or provide a different name.
       - Run `git checkout -b <new-branch-name>`
     - **Pop stash** if stashed: `git stash pop` (decrement `stash_count`).
     - **Stage and commit** the new changes if they were uncommitted.
     - Continue to step 5 (Rebase) with the new branch.
   - If **no merged PR found**: the branch is fresh — continue normally.

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

## Summary

18. Run `git log --oneline -5` to show recent commits.
19. Report:
    - Branch name
    - Number of commits ahead of main
    - Whether push was a normal push or force-with-lease
    - PR status (created / already exists / skipped)
    - Link to the PR or branch on GitHub
