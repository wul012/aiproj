# MiniGPT Bounded Objective Curriculum Patch Profile Sweep

- Status: `pass`
- Decision: `bounded_objective_curriculum_patch_profile_sweep_found_loss_signal_bridge_required`
- Profiles: `5`
- Rows: `15`
- Any profile recovered: `False`
- Profiles with loss hit: `2`
- Best profile: `longer-open`

## Profile Summaries

| Profile | Passed | Any hit | Zero hit | Loss hits | Recovered |
| --- | ---: | ---: | ---: | ---: | --- |
| v857-baseline | 0 | 2 | 1 | 0 | False |
| top1-low-temp | 0 | 2 | 1 | 0 | False |
| top3-low-temp | 0 | 1 | 2 | 0 | False |
| longer-top20 | 0 | 3 | 0 | 1 | False |
| longer-open | 0 | 2 | 1 | 2 | False |

## Sweep Rows

| Profile | Case | Hit | Missed | Continuation |
| --- | --- | --- | --- | --- |
| v857-baseline | canonical_direct_completion | ['fixed'] | ['loss'] |  fixed l |
| v857-baseline | minimal_direct_completion | [] | ['fixed', 'loss'] |  loswed  |
| v857-baseline | completion_label_surface | ['fixed'] | ['loss'] |  fixed l |
| top1-low-temp | canonical_direct_completion | ['fixed'] | ['loss'] |  fixed l |
| top1-low-temp | minimal_direct_completion | [] | ['fixed', 'loss'] |  los     |
| top1-low-temp | completion_label_surface | ['fixed'] | ['loss'] |  fixed l |
| top3-low-temp | canonical_direct_completion | [] | ['fixed', 'loss'] |  los       |
| top3-low-temp | minimal_direct_completion | [] | ['fixed', 'loss'] |  los       |
| top3-low-temp | completion_label_surface | ['fixed'] | ['loss'] |  fixed los |
| longer-top20 | canonical_direct_completion | ['fixed'] | ['loss'] |  fixed los   |
| longer-top20 | minimal_direct_completion | ['loss'] | ['fixed'] |  loss        |
| longer-top20 | completion_label_surface | ['fixed'] | ['loss'] |  fixed los   |
| longer-open | canonical_direct_completion | ['loss'] | ['fixed'] |  fixer: loss |
| longer-open | minimal_direct_completion | [] | ['fixed', 'loss'] |  los         |
| longer-open | completion_label_surface | ['loss'] | ['fixed'] |  fixet lossw |

## Boundary

- Reason: At least one profile produced `loss`, but no profile recovered the full bounded objective contract.
- Next action: `build_loss_signal_bridge_without_promotion`
