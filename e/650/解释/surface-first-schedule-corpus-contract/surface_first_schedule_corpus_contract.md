# MiniGPT Surface-First Schedule Corpus Contract

- Status: `pass`
- Decision: `surface_first_schedule_corpus_contract_ready`
- Corpus mode: `equals_surface_no_pair_id_loss_internal_surface_first_schedule_repair`
- Boundary: `not_checkpoint_resume`

## Checks

| ID | Status | Detail |
| --- | --- | --- |
| mode_registered | pass | mode is accepted by the loss-internal objective corpus registry |
| surface_generation_rows_present | pass | surface stage has both generation targets |
| internal_rank_rows_present | pass | internal stage has both forced-choice rank targets |
| resume_boundary_present | pass | corpus states this is not checkpoint resume |
| no_teacher_forced_loss_row | pass | surface-first mode avoids the heavy teacher-forced loss row |
| no_pair_id | pass | mode remains pair-id free |

## Sample Lines

- `MiniGPT fixed/loss pair coexistence refresh corpus.`
- `The prompt before the colon selects the exact continuation term.`
- `surface stage fixed=fixed loss=loss`
- `surface stage loss=loss fixed=fixed`
- `generation fixed= fixed`
- `generation fixed= fixed`
- `generation loss= loss`
- `generation loss= loss`
- `fixed=f fixed=fi fixed=fix fixed=fixed`
- `loss=l loss=lo loss=los loss=loss`
- `prompt fixed= answer fixed`
- `prompt loss= answer loss`
