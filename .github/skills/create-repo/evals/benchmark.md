# create-repo — Eval Benchmark (Iteration 2)

**Date:** 2026-04-10 | **Skill version:** 1.1 | **Assertions:** 38/38 passed (100%)

## Changes from Iteration 1

Iteration 1 found 1 assertion failure and 9 issues. The SKILL.md was updated, then a PR review found 13 additional remarks (5 blocking, 8 warnings). All blocking issues were addressed:

| Remark | Issue | Fix Applied |
|--------|-------|-------------|
| 1 (blocking) | ask-questions tool undocumented | Specified `vscode_askQuestions` with inline fallback |
| 2 (blocking) | OWNER never resolved | Added Owner input + check 5 (resolve owner) |
| 3 (blocking) | Stale eval artifacts | Full eval rewrite (this iteration) |
| 4 (blocking) | Evals used free-form prompts | All prompts now use `/create-repo` trigger |
| 5 (blocking) | Eval-3 results contradicted SKILL.md | Deleted stale evals, re-ran all 7 |
| 6 (warning) | Bare `git push` fragile | Changed to `git push -u origin HEAD` |
| 7 (warning) | No git identity check | Added check 2 (git config user.name/email) |
| 8 (warning) | No secrets warning | Added sensitive file scan before staging |
| 9 (warning) | Linux docs incomplete | Added Linux install, cross-platform code blocks |
| 10 (warning) | Eval set too narrow | Expanded from 3 to 7 evals including error paths |
| 11 (warning) | .gitignore uses non-existent gh subcommand | Changed to `gh api gitignore/templates/[LANGUAGE]` |
| 12 (warning) | No Path C or error-path evals | Added evals 5, 6, 7 |
| 13 (warning) | PowerShell-only code blocks | Added bash/zsh blocks alongside PowerShell |

Additionally: added halt rule, collision handling with retry loop, reordered checks (repo state first), Path C skips unnecessary inputs.

---

## Summary

| # | Eval | Scenario | Assertions | Pass Rate |
|---|------|----------|------------|-----------|
| 1 | path-a-happy-path | Fresh workspace, defaults | 9/9 | 100% |
| 2 | path-a-all-inputs-provided | All inputs in prompt | 5/5 | 100% |
| 3 | path-b-existing-repo-with-changes | Existing repo, unstaged files | 6/6 | 100% |
| 4 | path-b-clean-tree | Existing repo, clean tree | 4/4 | 100% |
| 5 | path-c-existing-remote | Repo with remote already | 4/4 | 100% |
| 6 | error-gh-not-installed | gh CLI missing | 4/4 | 100% |
| 7 | error-name-collision | Repo name already taken | 4/4 | 100% |
| | **Total** | | **38/38** | **100%** |

---

## Coverage

| Category | Covered | Not Yet Covered |
|----------|---------|-----------------|
| **Green paths** | Path A (fresh), Path B (changes), Path B (clean), Path C (remote) | — |
| **Error paths** | gh CLI missing, name collision | gh auth failure, git identity missing, org resolution failure |
| **Trigger** | All evals use `/create-repo` | — |
| **Cross-platform** | SKILL.md has PowerShell + bash/zsh blocks | — |

---

## Remaining Gaps (non-blocking)

1. No eval for `gh auth status` failure (unauthenticated user)
2. No eval for missing git identity (fresh machine)
3. No eval for org owner provided but org doesn't exist / no access
4. Path C skips inputs but the skip-logic relies on model interpretation of "skip to Path C directly"
