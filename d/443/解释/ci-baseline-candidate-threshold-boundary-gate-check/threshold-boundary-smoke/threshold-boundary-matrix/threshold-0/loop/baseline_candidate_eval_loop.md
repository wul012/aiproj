# MiniGPT Baseline-Candidate Eval Loop

- Status: `pass`
- Decision: `reject_candidate`
- Source mode: `reuse_summary`
- Gate mode: `strict`
- Expected exit code: `2`
- Suite: `standard-zh`
- Controlled variable: `max_iters`
- Min overall score delta: `0.0`
- Overall score delta: `0.0`
- Control status: `pass`
- Acceptance status: `fail`
- Promotion status: `blocked`
- Candidate accepted: `False`
- Next action: `keep_baseline_and_fix_candidate`

## Rejected Reasons

- rubric_avg_score below 60.0
- Keep the baseline or fix candidate scorecard regressions before promotion.
- scorecard_decision_promote expected promote, got blocked
- selected_candidate expected tiny-candidate, got None

## Control Checks

- none

## Acceptance Criteria

- scorecard_decision_promote expected promote, got blocked
- selected_candidate expected tiny-candidate, got None
