# MiniGPT Schedule Approximation Batch Closeout

- Status: `pass`
- Decision: `stop_single_corpus_schedule_approximations`
- Selected generation route: `loss-internal-joint-cycle`
- Internal anchor route: `joint-cycle-internal-repair`

## Closeout Items

| ID | Status | Detail |
| --- | --- | --- |
| surface_first_result | rejected | generation=['fixed'] internal=['fixed'] class=fixed_only_aligned_partial |
| loss_guarded_result | rejected | generation=[] internal=['fixed'] class=internal_partial_generation_none |
| aligned_pair_full | missing | aligned_pair_full_count=0 |
| selected_generation_route | kept | loss-internal-joint-cycle remains selected |
| internal_anchor_route | kept | joint-cycle-internal-repair remains selected |

## Boundary

- Reason: Surface-first and loss-guarded single-corpus approximations did not produce aligned pair-full evidence.
- Next action: stop this branch and preserve v630/v640 as separate evidence anchors
