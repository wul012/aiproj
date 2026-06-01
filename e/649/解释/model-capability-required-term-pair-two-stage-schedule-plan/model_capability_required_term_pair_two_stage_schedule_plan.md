# MiniGPT Two-Stage Schedule Plan

- Status: `pass`
- Decision: `two_stage_surface_internal_schedule_ready`
- Boundary: `not_checkpoint_resume`
- Failed count: `0`

## Stage Rows

| Stage | Source | Gate | Hits | Class |
| --- | --- | --- | --- | --- |
| surface_generation_stage | loss-internal-joint-cycle | generation_pair_full=True | ['fixed', 'loss'] | generation_pair_full_internal_partial |
| internal_repair_stage | joint-cycle-internal-repair | internal_pair_full=True | [] | internal_pair_full_generation_none |

## Guardrails

| ID | Status | Detail |
| --- | --- | --- |
| not_checkpoint_resume | active | The plan does not claim checkpoint continuation; it only schedules a runnable corpus approximation. |
| no_aligned_route_claim | pass | Aligned generation/internal pair-full must remain unclaimed unless comparison proves it. |
| surface_generation_pair_full_required | pass | The first stage must start from the route that already releases both required terms. |
| internal_pair_full_required | pass | The second stage must be backed by forced-choice internal pair-full evidence. |

## Boundary

- Model quality claim: `schedule_plan_only`
- Reason: Surface generation pair-full and internal forced-choice pair-full exist in separate routes.
- Next action: run a surface-first single-corpus approximation while keeping the no-resume boundary visible
