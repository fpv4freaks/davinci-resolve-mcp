# Ruleset JSON Payloads

Reference file for Step 5b — apply the appropriate JSON based on the user's protection level choice.

## Standard

PRs required, 1 approval needed. Force-pushes allowed. Owner can push directly.

```bash
gh api repos/[OWNER]/[NAME]/rulesets -X POST --input - <<'EOF'
{
  "name": "Protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
    }}
  ],
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }
  ]
}
EOF
```

## Strict

PRs required, 1 approval needed, stale approvals dismissed, force-push blocked. Owner can push directly.

```bash
gh api repos/[OWNER]/[NAME]/rulesets -X POST --input - <<'EOF'
{
  "name": "Protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
    }},
    { "type": "non_fast_forward" }
  ],
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }
  ]
}
EOF
```

## 1 approval (Maintain/Admin bypass)

PRs are always required. Write users need 1 approval from any eligible reviewer, including another Write user. Maintain and Admin users can bypass the approval and merge their own PR, but they still cannot push directly to main.

```bash
gh api repos/[OWNER]/[NAME]/rulesets -X POST --input - <<'EOF'
{
  "name": "Protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
    }},
    { "type": "non_fast_forward" }
  ],
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request" },
    { "actor_id": 2, "actor_type": "RepositoryRole", "bypass_mode": "pull_request" }
  ]
}
EOF
```

## PR-only

PRs required, 0 approvals needed (self-merge OK), force-push blocked. Owner can push directly.

```bash
gh api repos/[OWNER]/[NAME]/rulesets -X POST --input - <<'EOF'
{
  "name": "Protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
    }},
    { "type": "non_fast_forward" }
  ],
  "bypass_actors": [
    { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" }
  ]
}
EOF
```

## Notes

- `actor_id: 5` = the built-in **Admin** repository role. For **1 approval (Maintain/Admin bypass)** it uses `bypass_mode: pull_request`, so admins can bypass approval only through a PR and cannot push directly to main. Other presets retain their documented Admin bypass behavior.
- `actor_id: 2` = the built-in **Maintain** repository role. With `bypass_mode: pull_request`, maintainers can bypass approval only through a PR and cannot push directly to main.
- `actor_id: 4` = the built-in **Write** repository role. It is not a bypass actor: Write users need one approval from any eligible reviewer, including another Write user, before merging.
- CODEOWNER enforcement is optional; enable it separately with `"require_code_owner_review": true` in the `pull_request` parameters (see Step 6a).
