# MiniGPT tiny scorecard decision smoke

- Generated: `2026-05-26T04:02:50Z`
- Decision: `blocked`
- Action: `keep_baseline_or_fix_candidate`
- Baseline: `tiny-baseline`
- Selected run: `None`
- Selected rubric: `None`
- Selected gen flags delta: `missing`
- Candidates: `0`
- Clean candidates: `0`
- Review candidates: `0`
- Blocked candidates: `1`
- Non comparison-ready candidates: `0`
- Non design-ready candidates: `0`
- Dominant blocker category: `threshold`
- Dominant review category: `None`
- Remediation plan count: `1`
- Remediation blocker count: `1`
- Remediation review count: `0`
- Dominant remediation kind: `blocker`
- Dominant remediation category: `threshold`
- Dominant remediation action: `Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change.`
- Threshold-blocked candidates: `1`
- Threshold blocked names: `tiny-candidate`
- Threshold closest: `tiny-candidate` / `-23.33`
- Threshold largest gap: `tiny-candidate` / `-23.33`

## Candidate Evaluations

| Run | Relation | Rubric | Eval Compare | Design Compare | Overall Delta | Flag Delta | Case Regressions | Blockers | Blocker Categories | Review Items | Review Categories |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| tiny-baseline | baseline | 36.67 | pass | pass | +0 | +0 | 0 | baseline run is not a promotion candidate; rubric_avg_score below 60.0 | baseline_candidate; threshold |  |  |
| tiny-candidate | blocked | 36.67 | pass | pass | +0 | +0 | 0 | rubric_avg_score below 60.0 | threshold |  |  |

## Recommendations

- Keep the baseline or fix candidate scorecard regressions before promotion.
- Blocked candidates should stay in the comparison as evidence for why they were not promoted.
- Top remediation: threshold -> Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change.

## Remediation Plan

| Kind | Category | Count | Priority | Severity | Owner | Action Code | Target Artifacts | Action |
| --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| blocker | threshold | 1 | 60 | blocker | model-eval | raise_candidate_rubric_or_change_policy | benchmark_scorecard_decision, benchmark_scorecard | Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change. |
