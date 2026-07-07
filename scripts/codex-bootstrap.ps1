# Codex session bootstrap - run at session start: .\scripts\codex-bootstrap.ps1
# Prints orientation in one command instead of re-deriving repo state by hand.
$ErrorActionPreference = 'SilentlyContinue'

Write-Output '=== git: last 3 commits / status ==='
git log --oneline -3
git status -sb | Select-Object -First 8
Write-Output '=== latest tag ==='
git tag --sort=-creatordate | Select-Object -First 1
Write-Output '=== CI: last 3 runs (do not block-watch intermediates) ==='
gh run list --limit 3
Write-Output '=== pointers ==='
Write-Output 'Active program : cross-project AGENTS.md -> Current Active Program (see repository AGENTS.md)'
Write-Output 'Active brief   : docs\production-excellence-aiproj-brief.md (A-track)'
Write-Output 'Two lanes      : engineering lane only; do NOT touch science-lane experiments/verdicts.'
