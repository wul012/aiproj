# MiniGPT Generation/Internal Batch Closeout

- Status: `pass`
- Decision: `close_batch_and_design_two_stage_surface_internal_schedule`
- Batch versions: `10`
- Selected generation route: `loss-internal-joint-cycle`
- Internal anchor route: `joint-cycle-internal-repair`
- Aligned pair-full count: `0`

## Closeout Items

| ID | Status | Detail |
| --- | --- | --- |
| joint_cycle_generation_pair_full | confirmed | v630 joint-cycle is the only generation pair-full route in this batch. |
| internal_alignment_not_ready | confirmed | No route has both generation pair-full and internal pair-full. |
| balanced_anchor_rejected | confirmed | v634/v635 balanced-anchor remains fixed-only in generation and internal scoring. |
| next_route_selected | confirmed | Preserve joint-cycle generation pair-full while repairing loss-side internal preference. |
| light_merge_rejected | confirmed | v645/v646 light-merge remains a partial tradeoff, not an aligned route. |

## Boundary

- Model quality claim: `targeted_generation_signal_only`
- Reason: The batch found a generation pair-full route but no aligned generation/internal route.
- Next action: design a two-stage surface/internal schedule instead of another single-corpus merge
