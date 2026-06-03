# MiniGPT Objective-Level Contrast Acceptance Review

- Status: `pass`
- Decision: `pair_readiness_objective_level_contrast_acceptance_review_accepted`
- Promotion allowed: `True`
- Accepted route: `objective_level_contrast`
- Boundary: `tiny_required_term_pair_probe_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| rollup_passed | pass | pass | seed stability rollup must pass |
| rollup_decision_ready | pass | pair_readiness_objective_level_contrast_seed_stability_ready_for_acceptance_review | acceptance review follows only a ready seed-stability rollup |
| rollup_acceptance_review_ready | pass | True | rollup must explicitly be ready for acceptance review |
| rollup_not_preapproved | pass | False | rollup should not have already allowed promotion before this review |
| observed_expected_seed_count | pass | {'expected': 3, 'observed': 3, 'rows': 3} | all expected seeds must be represented by replay rows |
| all_seed_replays_ready | pass | {'ready': 3, 'rows': 3} | each seed replay must be ready |
| minimum_pair_full_strength | pass | {'minimum': 2, 'observed_min': 2} | each accepted seed should keep enough pair-full surfaces |
| uniform_strength_when_required | pass | {'min': 2, 'max': 3, 'required': False} | uniform pair-full strength is optional unless explicitly required |
| rollup_checks_clean | pass | 0 | source rollup should have no failed checks |
