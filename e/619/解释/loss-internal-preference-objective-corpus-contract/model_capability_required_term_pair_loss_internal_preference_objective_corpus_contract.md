# MiniGPT Required-Term Pair Loss-Internal-Preference Corpus Contract

- Status: `pass`
- Decision: `loss_internal_preference_objective_corpus_modes_ready`
- New mode count: `3`
- Source prompts: `fixed= / loss=`

| Mode | Purpose |
| --- | --- |
| equals_surface_no_pair_id_loss_internal_preference_repair | Train hidden preference rows before decoding. |
| equals_surface_no_pair_id_loss_internal_first_token_repair | Train `l` as first-token preference after `loss=`. |
| equals_surface_no_pair_id_loss_internal_ranked_choice_repair | Mirror forced-choice ranking rows in training text. |

## Boundary

This is a corpus contract only. It does not claim model quality until v620-v622 train real checkpoints.