# MiniGPT Pair-Readiness Objective-Structure Plan

- Status: `pass`
- Decision: `pair_readiness_objective_structure_plan_ready`
- Proposed next artifact: `pair_readiness_objective_structure_contract`

## Objective Strategy

- separate fixed and loss as explicit task-id objectives before the answer token
- add paired block rows that ask both branches in one sample without reusing heldout prompts
- keep direct fixed= and loss= probes held out for promotion checks
- avoid another capacity increase until the objective contract is materialized and replayed

## Contract Requirements

- training rows must not contain the exact heldout direct or pair probes
- fixed and loss row families must be balanced by count and template role
- paired rows must include both terms in deterministic order and reversed order
- contract output must expose row family counts and leakage checks

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| route_comparison_passed | pass | pass | source five-route comparison must pass |
| route_comparison_decision | pass | pair_readiness_capacity_probe_no_improvement_fixed_only | objective-structure planning follows only a closed capacity-probe no-improvement result |
| no_pair_full_route | pass | False | no compared route should already be pair-full |
| five_routes_present | pass | 5 | comparison should include baseline, repairs, and capacity probe |
| capacity_probe_no_improvement | pass | True | capacity probe must be measured as no improvement |
| capacity_probe_no_delta | pass | 0 | capacity probe should not improve default hit count |
| capacity_probe_still_misses_loss | pass | ['loss'] | loss must remain missed before changing objective structure |
| capacity_probe_row_present | pass | True | capacity-probe route row must be present for auditability |
