# MiniGPT Required-Term Pair Dual-Objective Boundary Plan

- Status: `pass`
- Decision: `explicit_dual_objective_boundary_plan_ready`
- Proposed corpus mode: `equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair`
- Fixed miss class: `prefix_fragment_without_full_term`

## Constraints

| ID | Source | Required | Detail |
| --- | --- | --- | --- |
| preserve_generation_anchor | loss-internal-joint-cycle | True | Keep the generation pair-full surface route visible before adding new internal rows. |
| preserve_internal_anchor | joint-cycle-internal-repair | True | Keep the internal forced-choice pair match visible as anchor evidence. |
| repair_fixed_after_constrained_decode | prefix_fragment_without_full_term | True | Add explicit fixed retention rows because constrained decode still misses fixed. |
| retain_loss_after_constrained_decode | loss_constrained_hit | True | Do not erase the loss-side hit recovered by constrained decoding. |
| avoid_naive_resume | constrained_decode_or_explicit_dual_objective_boundary | True | Do not continue lower-rate or light-merge checkpoint continuation variants. |

## Boundary

- Model quality claim: `plan_only`
- Reason: The evidence points to fixed-side repair while preserving loss and the existing split anchors.
- Next action: add corpus mode equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair
