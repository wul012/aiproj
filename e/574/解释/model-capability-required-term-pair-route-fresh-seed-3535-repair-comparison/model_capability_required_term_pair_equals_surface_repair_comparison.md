# MiniGPT Required-Term Pair Equals-Surface Repair Comparison

- Status: `pass`
- Decision: `required_term_pair_equals_surface_repair_comparison_recorded`
- Compared reports: `2`
- Branch competition seeds: `0`
- Pair-full profile seeds: `0`
- Union hit terms: `fixed`

## Source Reports

| Label | Status | Corpus mode | Pair-full seeds | Source |
| --- | --- | --- | ---: | --- |
| v571-loss-balanced-fresh3535 | pass | equals_surface_no_pair_id_loss_balanced_repair | 0/1 | e\571\解释\model-capability-required-term-pair-route-fresh-seed-3535\model_capability_required_term_pair_colon_immediate_stability.json |
| v573-first-token-fresh3535 | pass | equals_surface_no_pair_id_loss_balanced_first_token_repair | 0/1 | e\573\解释\model-capability-required-term-pair-route-fresh-seed-3535-first-token-repair\model_capability_required_term_pair_colon_immediate_stability.json |

## Branch Rows

| Seed | Competition | Fixed hit reports | Loss hit reports | Pair-full reports | Next action |
| --- | --- | --- | --- | --- | --- |
| 3535 | False | v571-loss-balanced-fresh3535 |  |  | collect another comparable equals-surface repair report before changing the objective |

## Term Evidence

| Report | Seed | Profile | Term | Hit | Prompt | Preview |
| --- | --- | --- | --- | --- | --- | --- |
| v571-loss-balanced-fresh3535 | 3535 | default | fixed | True | fixed= | fixed= fixed |
| v571-loss-balanced-fresh3535 | 3535 | suppress_newline_tokens | fixed | True | fixed= | fixed los=fi |
| v571-loss-balanced-fresh3535 | 3535 | default | loss | False | loss= |  fixed= fixe |
| v571-loss-balanced-fresh3535 | 3535 | suppress_newline_tokens | loss | False | loss= |  fixed= fixe |
| v573-first-token-fresh3535 | 3535 | default | fixed | False | fixed= | fixt los=ixe |
| v573-first-token-fresh3535 | 3535 | suppress_newline_tokens | fixed | False | fixed= | fixt los=ixe |
| v573-first-token-fresh3535 | 3535 | default | loss | False | loss= | fixed\nixefix |
| v573-first-token-fresh3535 | 3535 | suppress_newline_tokens | loss | False | loss= | fixed fiixef |

## Boundary

- Model quality claim: `comparison_only`
- Reason: The compared reports do not yet show complementary fixed/loss evidence.
- Next action: add one stronger targeted repair or reduce the comparison scope
