# MiniGPT Objective-Level Contrast Promotion Manifest

- Status: `pass`
- Decision: `pair_readiness_objective_level_contrast_promotion_manifest_ready`
- Route: `objective_level_contrast`
- Route status: `promoted`
- Scope: `tiny_required_term_pair_probe_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| acceptance_review_passed | pass | pass | acceptance review must pass |
| acceptance_decision | pass | pair_readiness_objective_level_contrast_acceptance_review_accepted | promotion manifest follows only an accepted objective-level contrast review |
| promotion_allowed | pass | True | acceptance review must allow promotion inside its declared boundary |
| route_id_matches | pass | objective_level_contrast | accepted route must match manifest route id |
| boundary_scoped | pass | tiny_required_term_pair_probe_only | promotion manifest must preserve the tiny pair-probe boundary |
| claim_scoped | pass | seed_stable_pair_probe_route_accepted | accepted claim must remain route/probe scoped |
| seed_rows_present | pass | {'seed_count': 3, 'ready': 3} | manifest should carry ready seed evidence |
| source_rollup_was_review_ready | pass | True | manifest must trace back to a review-ready seed-stability rollup |
