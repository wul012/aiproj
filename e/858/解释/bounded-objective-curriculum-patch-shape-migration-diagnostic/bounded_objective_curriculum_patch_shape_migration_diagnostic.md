# MiniGPT Bounded Objective Curriculum Patch Shape Migration Diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnosed_profile_sweep_required`
- Improved cases: `1`
- Regressed cases: `1`
- Stable partial cases: `1`
- Any-hit delta: `0`
- Zero-hit delta: `0`
- Claim: `partial_signal_shape_migration_without_contract_recovery`

## Case Migration

| Case | Migration | Pre hit | Post hit | Pre missed | Post missed |
| --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | stable_partial | ['fixed'] | ['fixed'] | ['loss'] | ['loss'] |
| minimal_direct_completion | regressed_to_zero | ['fixed'] | [] | ['loss'] | ['fixed', 'loss'] |
| completion_label_surface | improved_to_partial | [] | ['fixed'] | ['fixed', 'loss'] | ['loss'] |

## Root Causes

| Cause | Severity | Detail | Evidence |
| --- | --- | --- | --- |
| summary_masked_case_migration | high | Aggregate any-hit counts stayed flat while case-level surfaces moved in opposite directions. | ['completion_label_surface', 'minimal_direct_completion'] |
| completion_surface_fixed_only_improved | medium | At least one post-patch surface gained the `fixed` term but still missed `loss`. | ['completion_label_surface'] |
| minimal_surface_regressed_to_zero_hit | high | At least one previously partial-hit surface became zero-hit after the curriculum patch. | ['minimal_direct_completion'] |
| loss_term_still_missing_after_patch | high | `loss` remains absent from post-patch replay continuations. | ['canonical_direct_completion', 'minimal_direct_completion', 'completion_label_surface'] |
| contract_not_recovered | high | No case-level migration is enough to recover the bounded objective contract. | [] |

## Boundary

- Reason: The curriculum patch changed which prompt surfaces show partial signal, but it did not recover `fixed loss`.
- Next action: `run_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_profile_sweep_before_more_training`
