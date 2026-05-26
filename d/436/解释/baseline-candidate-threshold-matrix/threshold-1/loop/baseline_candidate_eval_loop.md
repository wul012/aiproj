# MiniGPT Baseline-Candidate Eval Loop

- Status: `pass`
- Decision: `reject_candidate`
- Source mode: `reuse_summary`
- Gate mode: `strict`
- Expected exit code: `2`
- Suite: `standard-zh`
- Controlled variable: `max_iters`
- Min overall score delta: `1.0`
- Overall score delta: `0.0`
- Control status: `pass`
- Acceptance status: `fail`
- Promotion status: `promote`
- Candidate accepted: `False`
- Next action: `keep_baseline_and_fix_candidate`

## Rejected Reasons

- min_overall_score_delta expected >= 1.0, got 0.0

## Control Checks

- none

## Acceptance Criteria

- min_overall_score_delta expected >= 1.0, got 0.0
