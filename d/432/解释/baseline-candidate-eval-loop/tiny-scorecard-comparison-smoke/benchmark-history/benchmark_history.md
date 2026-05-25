# MiniGPT tiny scorecard smoke benchmark history

- Generated: `2026-05-25T15:28:41Z`
- Entries: `1`
- Promote decisions: `1`
- Review decisions: `0`
- Blocked decisions: `0`
- Model quality claim: `not_claimed`
- Best candidate: `tiny-candidate`
- Suite design not-ready entries: `0`
- Readiness requirement: `fail`
- Readiness decision: `stop`
- Readiness exit code: `1`
- Readiness failed reasons: `not_real_benchmark_evidence`

## Ledger

| Name | Baseline | Candidate | Decision | Readiness | Eval Compare | Design Compare | Rubric Delta | Case Regressions | Gen Flag Delta | Boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tiny-scorecard-smoke | tiny-baseline | tiny-candidate | promote | ready | pass | pass | 0.0 | 0 | 0 | tiny-smoke-plumbing-evidence |

## Recommendations

- Use ready benchmark entries as candidates for repeated standard-suite checkpoint evaluation.
- Tiny-smoke history is plumbing evidence; run real benchmark candidates before claiming model quality.
