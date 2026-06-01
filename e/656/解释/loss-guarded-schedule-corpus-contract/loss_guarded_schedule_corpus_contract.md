# MiniGPT Loss-Guarded Schedule Corpus Contract

- Status: `pass`
- Decision: `loss_guarded_schedule_corpus_contract_ready`
- Corpus mode: `equals_surface_no_pair_id_loss_internal_loss_guarded_schedule_repair`
- Boundary: `not_checkpoint_resume`

## Checks

| ID | Status | Detail |
| --- | --- | --- |
| mode_registered | pass | mode is accepted by the loss-internal objective corpus registry |
| loss_guard_rows_present | pass | loss guard rows directly counter fixed-only collapse |
| loss_weight_exceeds_fixed_weight | pass | loss generation rows outnumber fixed generation rows |
| internal_rank_rows_present | pass | both internal rank targets remain visible |
| resume_boundary_present | pass | corpus states this is not checkpoint resume |
| no_teacher_forced_loss_row | pass | mode avoids the heavy teacher-forced loss row |
| no_pair_id | pass | mode remains pair-id free |

## Sample Lines

- `MiniGPT fixed/loss pair coexistence refresh corpus.`
- `The prompt before the colon selects the exact continuation term.`
- `loss guard surface loss=loss fixed=fixed`
- `loss guard surface fixed=fixed loss=loss`
- `generation loss= loss`
- `generation loss= loss`
- `generation loss= loss`
- `generation fixed= fixed`
- `generation fixed= fixed`
- `loss=l loss=lo loss=los loss=loss`
- `fixed=f fixed=fi fixed=fix fixed=fixed`
- `prompt loss= answer loss`
- `prompt loss= answer loss`
- `prompt fixed= answer fixed`
