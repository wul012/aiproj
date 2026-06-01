# MiniGPT Generation/Internal Alignment Route Decision

- Status: `pass`
- Decision: `repair_internal_preference_preserve_generation_pair_full`
- Selected generation route: `loss-internal-joint-cycle`
- Internal anchor route: `loss-internal-first-token`
- Direct promotion ready: `False`

## Constraints

| ID | Status | Source | Detail |
| --- | --- | --- | --- |
| preserve_generation_pair_full | required | loss-internal-joint-cycle | Do not lose fixed/loss generation pair-full while repairing internal preference. |
| repair_loss_internal_preference | required | loss-internal-first-token | Recover the loss-side forced-choice preference without regressing fixed. |
| avoid_pair_id_shortcut | required |  | Keep explicit pair-id leakage out of the next corpus objective. |

## Boundary

- Model quality claim: `route_decision_only`
- Reason: The best generation route is not internally aligned yet.
- Next action: use the selected generation route as the base and repair internal preference
