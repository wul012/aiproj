# MiniGPT Surface-First Failure Analysis

- Status: `pass`
- Decision: `surface_first_schedule_fixed_collapse_confirmed`
- Fixed collapse: `True`
- Next objective: `loss_guarded_surface_schedule_repair`

## Evidence Rows

| ID | Status | Value | Detail |
| --- | --- | --- | --- |
| generation_replay | observed | ['fixed'] | Surface-first generation replay hit terms. |
| forced_choice | observed | ['fixed'] | Surface-first expected-best forced-choice terms. |
| alignment_class | fixed_only_aligned_partial | fixed_only_aligned_partial | How the full comparison classifies the surface-first route. |
| route_selection | not_selected | loss-internal-joint-cycle | The route decision selected a different generation route when surface-first was added. |

## Recommendations

| ID | Action |
| --- | --- |
| stop_surface_first_repeat | do not repeat the same surface-first schedule without a loss guard |
| keep_generation_baseline | keep loss-internal-joint-cycle as the generation baseline |
| try_loss_guard | add loss-guarded rows before running the next tiny training seed |

## Boundary

- Model quality claim: `negative_route_diagnosis`
- Reason: Surface-first schedule collapsed to fixed-only generation and fixed-only internal preference.
- Next action: try a loss-guarded schedule approximation or stop this branch
