# MiniGPT Required-Term Pair Loss-Branch Ten-Version Closeout

- Status: `pass`
- Decision: `close_loss_branch_batch_and_start_fixed_retention_objective`
- Version range: `v589-v598`
- Single-seed pair-full count: `0`
- Stability pair-full seed count: `0`
- First-token gap count: `3`
- Readiness ready: `True`

## Evidence

| Version | Label | Status | Decision | Key result |
| --- | --- | --- | --- | --- |
| v589 | v589-corpus-contract | pass | loss_branch_objective_corpus_modes_ready | modes=3; pair_id_removed=True |
| v590 | v590-targeted-seed | pass | required_term_pair_coexistence_refresh_no_pair_full | pair_full=False; training=pass |
| v591 | v591-dual-anchor-seed | pass | required_term_pair_coexistence_refresh_no_pair_full | pair_full=False; training=pass |
| v592 | v592-micro-span-seed | pass | required_term_pair_coexistence_refresh_no_pair_full | pair_full=False; training=pass |
| v593 | v593-objective-comparison | pass | loss_branch_objectives_confirm_loss_only_tradeoff | pair_full=0; loss_only=3; terms=loss |
| v594 | v594-route-decision | pass | select_targeted_loss_branch_for_seed_stability_not_promotion | selected=v590-targeted; fixed_required=True |
| v595 | v595-targeted-stability | pass | required_term_pair_colon_immediate_not_stable | pair_full_seeds=0/3; stable=False |
| v596 | v596-missed-seed-diagnostic | pass | required_term_pair_colon_immediate_first_token_gap | missed=3; first_token_gaps=3 |
| v597 | v597-fixed-retention-readiness | pass | design_fixed_retention_objective_before_more_loss_branch_training | ready=True; requirements=3 |

## Boundary

- Model quality claim: `batch_closeout_only`
- Reason: Three loss-branch objectives and three targeted seeds improved loss visibility but never reached pair-full.
- Next action: build and train a fixed-retention objective with balanced first-token rows
