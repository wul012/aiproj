# MiniGPT Bounded Objective Seed Revision Partial-Hit Diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready`
- Partial-hit cases: `2`
- Zero-hit cases: `1`
- Hit terms: `['fixed']`
- Missed terms: `['fixed', 'loss']`
- Claim: `partial_required_term_signal_diagnosed`

## Case Diagnostics

| Case | Partial | Zero | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | True | False | ['fixed'] | ['loss'] |  fixed t |
| minimal_direct_completion | True | False | ['fixed'] | ['loss'] |  fixed t |
| completion_label_surface | False | True | [] | ['fixed', 'loss'] |  ler: lo |

## Root Causes

| Cause | Severity | Detail | Evidence |
| --- | --- | --- | --- |
| first_term_only_uptake | high | 2 cases hit a required term but still missed another term. | ['canonical_direct_completion', 'minimal_direct_completion'] |
| loss_term_not_stabilized | high | `fixed` appears in replay continuations, but `loss` remains missed even though it exists in the revised corpus. | ['canonical_direct_completion', 'minimal_direct_completion', 'completion_label_surface'] |
| prompt_surface_still_zero_hit | medium | At least one contract prompt surface still has no required-term hit. | ['completion_label_surface'] |
| corpus_contains_missed_terms | medium | The missed terms are present in the seed corpus, so this is an uptake/generation issue rather than missing raw data. | ['fixed', 'loss'] |
| no_case_passed_contract | high | No replay case satisfied all required terms, so promotion remains blocked. | [] |
| unassisted_path_confirmed | low | The checkpoint came from the no-anchor revised seed path; partial uptake is unassisted evidence. | [] |

## Boundary

- Reason: The revised no-anchor checkpoint partially learned the objective surface, but the dominant diagnostic is `first_term_only_uptake`.
- Next action: `build_bounded_objective_unassisted_repair_seed_revision_curriculum_patch`
