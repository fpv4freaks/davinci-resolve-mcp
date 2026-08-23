<#
.SYNOPSIS
  File a JIT admin-access request on any GitHub repo, optionally queue an
  operation for later resume, and ping approvers via Teams.

.DESCRIPTION
  Canonical implementation of the create-repo skill's Step 7 (JIT flow).
  Generic across repos AND across reasons. Supports three natures of request:

    1. KNOWN OPERATION + STRUCTURED PARAMS  (e.g. -OperationKind protect-main -Level Standard)
       -> Generates a templated justification, writes .tmp/jit-pending-op.json
          so /create-repo resume can finish the work after approval.

    2. KNOWN OPERATION + FREE-TEXT OVERRIDE (e.g. -OperationKind secret -Justification "...")
       -> Uses your justification verbatim. Still writes pending-op so resume works.

    3. AD-HOC / JIT-ONLY                    (e.g. -OperationKind jit-only -Justification "Need 2h to fix a webhook in the UI")
       -> Uses your justification verbatim. Does NOT write pending-op (nothing to resume;
          you'll do it manually in the GitHub UI).

  In every mode the script:
    * auto-detects owner/repo/default branch via `gh repo view`,
    * reads approvers live from .github/acl/access.yml,
    * files the JIT issue using .github/ISSUE_TEMPLATE/JitAccess.yml,
    * opens a Teams group chat (desktop + https + web fallbacks),
    * copies the message to clipboard as a final fallback.

  Hard-codes nothing about owner, repo, branch, or maintainer list.

.PARAMETER OperationKind
  What the JIT will be used for. Drives default justification and whether a
  pending-op file is written. Values:
    protect-main | secret | variable | description | visibility | features | webhook | jit-only
  Default: protect-main.

.PARAMETER Justification
  Free-text justification that goes verbatim into the JIT issue's required
  `justification` field. If omitted, a templated message is generated from
  OperationKind. Always required for OperationKind = jit-only.

.PARAMETER Level
  Ruleset level for OperationKind=protect-main: PR-only | Standard | Strict.
  Ignored for other operation kinds.

.PARAMETER Params
  Hashtable of operation-specific parameters serialized into pending-op.json.
  Examples:
    -OperationKind secret    -Params @{ name = 'NPM_TOKEN' }
    -OperationKind webhook   -Params @{ action = 'add'; url_host = 'hooks.example.com' }
  Never put secret VALUES here -- only the shape of the operation.

.PARAMETER Owner / Repo / Branch
  Auto-detected via `gh repo view` if omitted.

.PARAMETER DurationHours
  JIT admin duration in hours. Must be an integer in [2, 24]. Default 2.
  The skill (create-repo SKILL.md Step 7d) ALWAYS asks the user to pick a
  value 2-24 before invoking this script -- the script itself does not prompt.
  (1-hour was removed -- approvers said it's too short to be useful for any
  real admin task and just creates churn.)

.PARAMETER AccessYmlPath
  Path to access.yml. Default .github/acl/access.yml.

.PARAMETER ApproverRoles
  Roles in access.yml whose members are considered approvers. Default Admin + Maintain.

.PARAMETER EmailDomain
  Domain appended to each approver alias for the Teams chat. Default microsoft.com.

.PARAMETER JitTemplate
  Issue template filename. Default JitAccess.yml.

.PARAMETER SkipTeams
  Skip the Teams launch (issue is still filed and, where applicable, queued).

.PARAMETER SkipPendingOp
  Skip writing .tmp/jit-pending-op.json even for resumable operations
  (forces the request into ad-hoc mode).

.EXAMPLE
  # Default: PR-only ruleset on the current repo's default branch
  pwsh .github/skills/create-repo/scripts/jit-request.ps1

.EXAMPLE
  # Stricter ruleset, 4h, skip Teams (e.g. CI)
  pwsh .github/skills/create-repo/scripts/jit-request.ps1 -Level Strict -DurationHours 4 -SkipTeams

.EXAMPLE
  # Free-text ad-hoc request -- "just give me 2h admin to do something manually"
  pwsh .github/skills/create-repo/scripts/jit-request.ps1 -OperationKind jit-only `
       -Justification "Need 2h admin to clean up orphan webhooks in the GitHub UI."

.EXAMPLE
  # Known operation kind with a custom justification
  pwsh .github/skills/create-repo/scripts/jit-request.ps1 -OperationKind secret `
       -Params @{ name = 'NPM_TOKEN' } `
       -Justification "Rotate NPM_TOKEN for the publish workflow (value will be pasted on resume)."
#>
[CmdletBinding()]
param(
  [ValidateSet('protect-main', 'secret', 'variable', 'description', 'visibility', 'features', 'webhook', 'jit-only')]
  [string]    $OperationKind = 'protect-main',
  [string]    $Justification,
  [ValidateSet('PR-only', 'Standard', 'Strict')]
  [string]    $Level         = 'PR-only',
  [hashtable] $Params,
  [string]    $Owner,
  [string]    $Repo,
  [string]    $Branch,
  [ValidateRange(2, 24)]
  [int]       $DurationHours = 2,
  [string]    $AccessYmlPath = '.github/acl/access.yml',
  [string[]]  $ApproverRoles = @('Admin', 'Maintain'),
  [string]    $EmailDomain   = 'microsoft.com',
  [string]    $JitTemplate   = 'JitAccess.yml',
  [switch]    $SkipTeams,
  [switch]    $SkipPendingOp
)

$ErrorActionPreference = 'Stop'

# ----- Helper: auto-detect owner / repo / default branch via gh -----
function Get-RepoContext {
  param([string]$OwnerHint, [string]$RepoHint)
  $json = gh repo view --json owner,name,defaultBranchRef 2>$null | ConvertFrom-Json
  if (-not $json) { throw "Could not detect repo context. Run inside a git repo with `gh` authenticated, or pass -Owner / -Repo." }
  [pscustomobject]@{
    Owner         = if ($OwnerHint) { $OwnerHint } else { $json.owner.login }
    Repo          = if ($RepoHint)  { $RepoHint }  else { $json.name }
    DefaultBranch = $json.defaultBranchRef.name
  }
}

# ----- Helper: minimal YAML parser for access.yml (manageAccess list) -----
function Get-AccessApprovers {
  param([string]$Path, [string[]]$Roles)
  if (-not (Test-Path $Path)) {
    Write-Host "WARN: $Path not found -- no approvers to ping"
    return @()
  }
  $lines    = Get-Content $Path -Encoding UTF8
  $inBlock  = $false
  $member   = $null
  $approvers = @()
  foreach ($l in $lines) {
    if ($l -match '^\s*manageAccess\s*:') { $inBlock = $true; continue }
    if (-not $inBlock) { continue }
    if ($l -match '^\S' -and $l -notmatch '^\s*-') { $inBlock = $false; continue }
    if ($l -match '^\s*-\s*member\s*:\s*([\w\-\.]+)') { $member = $Matches[1]; continue }
    if ($l -match '^\s*role\s*:\s*([\w]+)') {
      $role = $Matches[1]
      if ($member -and ($Roles -contains $role)) { $approvers += $member }
      $member = $null
    }
  }
  $approvers | Sort-Object -Unique
}

# ----- Helper: build a default justification from OperationKind -----
function New-DefaultJustification {
  param([string]$Kind, [string]$Slug, [string]$Branch, [string]$Level, [hashtable]$Params)
  $name = if ($Params -and $Params.ContainsKey('name')) { " (``$($Params.name)``)" } else { '' }
  switch ($Kind) {
    'protect-main' { "Create a branch ruleset on ``$Branch`` (level: $Level) for ``$Slug``. ``maintain`` cannot manage rulesets; need admin to apply protection." }
    'secret'       { "Add/update a repo-level Actions secret$name for ``$Slug``." }
    'variable'     { "Add/update a repo-level Actions variable$name for ``$Slug``." }
    'description'  { "Update the repository description / topics for ``$Slug``." }
    'visibility'   { "Change repository visibility for ``$Slug``." }
    'features'     { "Toggle repo features (issues / wiki / discussions / projects / merge type) for ``$Slug``." }
    'webhook'      { "Add / edit / remove a repository webhook for ``$Slug``." }
    'jit-only'     { $null }  # require explicit -Justification
    default        { "Admin action on ``$Slug``." }
  }
}

# ===== Step 0: detect context =====
$ctx = Get-RepoContext -OwnerHint $Owner -RepoHint $Repo
$Owner  = $ctx.Owner
$Repo   = $ctx.Repo
if (-not $Branch) { $Branch = $ctx.DefaultBranch }
$slug   = "$Owner/$Repo"
$requester = try { (gh api user --jq .login) 2>$null } catch { $env:USERNAME }
if (-not $requester) { $requester = $env:USERNAME }

# Resolve justification
if (-not $Justification) {
  $Justification = New-DefaultJustification -Kind $OperationKind -Slug $slug -Branch $Branch -Level $Level -Params $Params
}
if (-not $Justification) {
  throw "OperationKind = '$OperationKind' has no default justification. Pass -Justification ""<reason>""."
}

Write-Host "=== JIT request ==="
Write-Host "Repo:           $slug"
Write-Host "Operation:      $OperationKind"
if ($OperationKind -eq 'protect-main') {
  Write-Host "Branch:         $Branch"
  Write-Host "Level:          $Level"
}
Write-Host "Duration:       $DurationHours h"
Write-Host "Requester:      $requester"
Write-Host "Template:       $JitTemplate"
Write-Host "Justification:  $Justification"
Write-Host ""

# Decide whether to queue
$shouldQueue = ($OperationKind -ne 'jit-only') -and -not $SkipPendingOp

# ===== Step 1: .tmp/ in .gitignore (only if we'll queue) =====
if ($shouldQueue) {
  $gitignorePath = '.gitignore'
  $needsAppend = $true
  if (Test-Path $gitignorePath) {
    if ((Get-Content $gitignorePath -Raw -Encoding UTF8) -match '(?m)^\.tmp/?\s*$') { $needsAppend = $false }
  } else {
    Set-Content -Path $gitignorePath -Value '' -Encoding UTF8 -NoNewline
  }
  if ($needsAppend) {
    $existing = if (Test-Path $gitignorePath) { Get-Content $gitignorePath -Raw -Encoding UTF8 } else { '' }
    $sep = if ($existing -and -not $existing.EndsWith("`n")) { "`n" } else { '' }
    $append = "${sep}# create-repo skill -- JIT pending-op queue (no secrets stored)`n.tmp/`n"
    [System.IO.File]::AppendAllText((Resolve-Path $gitignorePath), $append, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "OK: appended .tmp/ to .gitignore"
  } else {
    Write-Host "OK: .tmp/ already in .gitignore"
  }
}

# ===== Step 2: file JIT issue =====
# NOTE: `gh issue create` does NOT support filling issue-form fields from CLI
# flags. The --template flag only pre-fills the editor in interactive mode; in
# non-interactive mode you must pass a plain --body. The JIT approver bot
# (gimsvc_microsoft) parses the body for "Duration: N hours" and uses the
# `jit` label as its trigger, so we replicate the template's title/label/
# assignee here.
$jitBodyLines = @(
  "Auto-filed by create-repo skill v4.5.",
  "",
  "**Justification:** $Justification",
  "",
  "**Duration:** $DurationHours hours",
  ""
)
if ($shouldQueue) {
  $jitBodyLines += "Pending op queued in workspace at ``.tmp/jit-pending-op.json`` -- ``/create-repo`` will resume once admin role is granted."
} else {
  $jitBodyLines += "Ad-hoc / jit-only request (no queued operation -- requester will perform the action manually in the GitHub UI)."
}
$jitBody = $jitBodyLines -join "`n"

Write-Host "---"
Write-Host "Filing JIT issue against $slug..."
$ghOutput = gh issue create `
  --repo $slug `
  --title 'JIT Request' `
  --label 'jit' `
  --assignee 'gimsvc_microsoft' `
  --body $jitBody 2>&1
Write-Host ($ghOutput -join "`n")

# ===== Step 3: extract URL =====
$jitUrl = ($ghOutput | Select-String -Pattern 'https://github.com/[^\s]+/issues/\d+' -AllMatches |
           ForEach-Object { $_.Matches.Value } | Select-Object -First 1)
if (-not $jitUrl) {
  Write-Host "ERROR: could not parse JIT issue URL from gh output. Aborting before queue."
  exit 1
}
Write-Host "OK: JIT URL = $jitUrl"

# ===== Step 4: queue pending-op (if applicable) =====
if ($shouldQueue) {
  New-Item -ItemType Directory -Path '.tmp' -Force | Out-Null

  $opParams = @{}
  if ($Params) { foreach ($k in $Params.Keys) { $opParams[$k] = $Params[$k] } }
  if ($OperationKind -eq 'protect-main') {
    if (-not $opParams.ContainsKey('level'))  { $opParams['level']  = $Level }
    if (-not $opParams.ContainsKey('branch')) { $opParams['branch'] = $Branch }
  }

  $payload = [ordered]@{
    operation_kind = $OperationKind
    owner          = $Owner
    repo           = $Repo
    params         = $opParams
    justification  = $Justification
    filed_at       = (Get-Date).ToString('o')
    duration_hours = $DurationHours
    jit_issue_url  = $jitUrl
    created_by     = $requester
    skill_version  = '4.5'
  }
  $payload | ConvertTo-Json -Depth 4 | Set-Content -Path '.tmp/jit-pending-op.json' -Encoding UTF8
  Write-Host "OK: wrote .tmp/jit-pending-op.json (operation_kind=$OperationKind)"
} else {
  Write-Host "OK: no pending-op written (ad-hoc / jit-only request -- nothing to resume)"
}

# ===== Step 5: Teams notify =====
if ($SkipTeams) {
  Write-Host "---"
  Write-Host "SkipTeams = true. Done. Open the issue manually to ping reviewers: $jitUrl"
  return
}

$approvers = Get-AccessApprovers -Path $AccessYmlPath -Roles $ApproverRoles |
             Where-Object { $_ -ne $requester -and $_ -ne ($requester -replace '_microsoft$','') }

if (-not $approvers) {
  Write-Host "WARN: no approvers found in $AccessYmlPath under roles [$($ApproverRoles -join ', ')]"
  Write-Host "Open the issue manually and @-mention an admin: $jitUrl"
  return
}

$emails = $approvers | ForEach-Object { "$_@$EmailDomain" }
$usersJoined = ($emails -join ',')

# Short summary line for the chat body
$summaryLine = switch ($OperationKind) {
  'protect-main' { "Create branch ruleset on '$Branch' (level: $Level)" }
  'jit-only'     { "Ad-hoc admin task (manual in UI)" }
  default        { "$OperationKind on $slug" }
}

$msgLines = @(
  "Hi all -- requesting JIT admin approval.",
  "",
  "Repo:       $slug",
  "Action:     $summaryLine",
  "Why:        $Justification",
  "Duration:   $DurationHours hours (auto-expires)",
  "Requester:  $requester",
  "",
  # Bare URL on its own line, surrounded by whitespace. Teams compose does
  # NOT process Markdown from the deep-link message= parameter (confirmed
  # 2026-05-22 -- [#NNN](url) renders as literal text in the sent message).
  # Bare URLs surrounded by whitespace ARE auto-linkified by Teams on Send.
  "JIT issue -- please click to approve:",
  $jitUrl,
  "",
  "Please approve in the issue when you have a moment. Thanks!"
)
$msg = $msgLines -join "`n"

Add-Type -AssemblyName System.Web
$msgEnc      = [System.Web.HttpUtility]::UrlEncode($msg)
$usersEnc    = [System.Web.HttpUtility]::UrlEncode($usersJoined)
$teamsUrl    = "https://teams.microsoft.com/l/chat/0/0?users=$usersEnc&message=$msgEnc"
$teamsWebUrl = "https://teams.microsoft.com/_#/conversations/0?users=$usersEnc&message=$msgEnc"
$msteamsUrl  = "msteams:/l/chat/0/0?users=$usersEnc&message=$msgEnc"

Write-Host "---"
Write-Host "Approvers ($($approvers.Count)):"
$emails | ForEach-Object { Write-Host "  - $_" }
Write-Host "---"
Write-Host "Message body:"
$msgLines | ForEach-Object { Write-Host "  $_" }
Write-Host "---"

try { Set-Clipboard -Value $msg; Write-Host "OK: message copied to clipboard (fallback)" } catch {}

# Ensure Teams desktop is running
if (-not (Get-Process -Name 'ms-teams','Teams' -ErrorAction SilentlyContinue)) {
  try { Start-Process 'ms-teams:' -ErrorAction Stop; Start-Sleep -Seconds 2 } catch {}
}

# Triple-launch (desktop protocol, https deep link, web fallback) for reliability
foreach ($u in @($msteamsUrl, $teamsUrl, $teamsWebUrl)) {
  try { Start-Process $u -ErrorAction Stop; Write-Host "OK: launched $($u.Substring(0,[Math]::Min(60,$u.Length)))..." } catch {
    Write-Host "WARN: $($u.Substring(0,40))... failed: $_"
  }
  Start-Sleep -Milliseconds 700
}

# Also open the JIT issue itself
try { Start-Process $jitUrl -ErrorAction Stop; Write-Host "OK: opened JIT issue in browser" } catch {}

Write-Host "---"
Write-Host "Done. If the Teams chat didn't surface, paste from clipboard into a new chat with the approvers above."
