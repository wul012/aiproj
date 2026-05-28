# MiniGPT Baseline-Candidate Eval Loop

- Status: `pass`
- Decision: `reject_candidate`
- Source mode: `rerun_smoke`
- Gate mode: `exploratory`
- Expected exit code: `0`
- Suite: `standard-zh`
- Controlled variable: `max_iters`
- Min overall score delta: `0.0`
- Overall score delta: `0.0`
- Best val loss delta: `-0.0031`
- Final val loss delta: `None`
- Generation flags delta: `0.0`
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

## Capability Metrics

| Metric | Baseline | Candidate | Delta | Direction |
| --- | ---: | ---: | ---: | --- |
| Overall score | 81.67 | 81.67 | 0.0 | higher is better |
| Best val loss | 5.345132350921631 | 5.3419880867004395 | -0.0031 | lower is better |
| Final val loss | None | None | None | lower is better |
| Generation flags | 0 | 0 | 0.0 | lower is better |

## Control Checks

- none

## Acceptance Criteria

- scorecard_decision_promote expected promote, got blocked
- selected_candidate expected tiny-candidate, got None
