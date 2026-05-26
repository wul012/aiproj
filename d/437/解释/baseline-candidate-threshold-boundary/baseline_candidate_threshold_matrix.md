# MiniGPT Baseline-Candidate Threshold Matrix

- Status: `pass`
- Decision: `threshold_matrix_ready`
- Accept count: `1`
- Reject count: `2`
- Threshold boundary: `accept_reject_boundary_observed`
- Strictest accepting threshold: `0.0`
- First rejecting threshold: `0.5`

| Threshold | Loop decision | Handoff ready | Next source | Exit | Check |
| --- | --- | --- | --- | --- | --- |
| 0.0 | accept_candidate | True | candidate | 0 | pass |
| 0.5 | reject_candidate | False | current_baseline | 2 | pass |
| 1.0 | reject_candidate | False | current_baseline | 2 | pass |
