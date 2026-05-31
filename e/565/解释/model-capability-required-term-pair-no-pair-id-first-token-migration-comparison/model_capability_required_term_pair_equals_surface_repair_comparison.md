# MiniGPT Required-Term Pair Equals-Surface Repair Comparison

- Status: `pass`
- Decision: `required_term_pair_equals_surface_pair_full_found`
- Compared reports: `2`
- Branch competition seeds: `0`
- Pair-full profile seeds: `1`
- Union hit terms: `fixed,loss`

## Source Reports

| Label | Status | Corpus mode | Pair-full seeds | Source |
| --- | --- | --- | ---: | --- |
| v562-loss-balanced | pass | equals_surface_no_pair_id_loss_balanced_repair | 1/3 | e\562\解释\model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability\model_capability_required_term_pair_colon_immediate_stability.json |
| v564-first-token | pass | equals_surface_no_pair_id_loss_balanced_first_token_repair | 1/3 | e\564\解释\model-capability-required-term-pair-no-pair-id-loss-balanced-first-token-stability\model_capability_required_term_pair_colon_immediate_stability.json |

## Branch Rows

| Seed | Competition | Fixed hit reports | Loss hit reports | Pair-full reports | Next action |
| --- | --- | --- | --- | --- | --- |
| 1535 | False | v562-loss-balanced,v564-first-token | v562-loss-balanced,v564-first-token | v562-loss-balanced,v564-first-token | promote the pair-full repair report and test fresh held-out prompts |
| 2535 | False |  | v562-loss-balanced |  | collect another comparable equals-surface repair report before changing the objective |
| 535 | False | v564-first-token |  |  | collect another comparable equals-surface repair report before changing the objective |

## Term Evidence

| Report | Seed | Profile | Term | Hit | Prompt | Preview |
| --- | --- | --- | --- | --- | --- | --- |
| v562-loss-balanced | 535 | default | fixed | False | fixed= | los\nlxessslo |
| v562-loss-balanced | 535 | suppress_newline_tokens | fixed | False | fixed= | los= fixeslo |
| v562-loss-balanced | 535 | default | loss | False | loss= | oosososs=  l |
| v562-loss-balanced | 535 | suppress_newline_tokens | loss | False | loss= | oosososs=  l |
| v562-loss-balanced | 1535 | default | fixed | True | fixed= | fixed\nlos= f |
| v562-loss-balanced | 1535 | suppress_newline_tokens | fixed | True | fixed= | fixed=fixed= |
| v562-loss-balanced | 1535 | default | loss | True | loss= |  fixed=loss= |
| v562-loss-balanced | 1535 | suppress_newline_tokens | loss | True | loss= |  fixed=loss= |
| v562-loss-balanced | 2535 | default | fixed | False | fixed= | loss=ixed=ix |
| v562-loss-balanced | 2535 | suppress_newline_tokens | fixed | False | fixed= | loss=ixed fi |
| v562-loss-balanced | 2535 | default | loss | True | loss= | loss=fixed=l |
| v562-loss-balanced | 2535 | suppress_newline_tokens | loss | True | loss= | loss=fixed=l |
| v564-first-token | 535 | default | fixed | True | fixed= |  loked=fixed |
| v564-first-token | 535 | suppress_newline_tokens | fixed | True | fixed= |  loked=fixed |
| v564-first-token | 535 | default | loss | False | loss= | los= fixed=i |
| v564-first-token | 535 | suppress_newline_tokens | loss | False | loss= | los= fixed l |
| v564-first-token | 1535 | default | fixed | True | fixed= | fixed\nlos=fi |
| v564-first-token | 1535 | suppress_newline_tokens | fixed | True | fixed= | fixed=los=lo |
| v564-first-token | 1535 | default | loss | True | loss= | loss=fixed=l |
| v564-first-token | 1535 | suppress_newline_tokens | loss | True | loss= | loss=fixed l |
| v564-first-token | 2535 | default | fixed | False | fixed= |  lo los=los= |
| v564-first-token | 2535 | suppress_newline_tokens | fixed | False | fixed= |  lo los=los= |
| v564-first-token | 2535 | default | loss | False | loss= | lo=  fixed=  |
| v564-first-token | 2535 | suppress_newline_tokens | loss | False | loss= | lo=  fixed=  |

## Boundary

- Model quality claim: `targeted_equals_surface_pair_full_signal`
- Reason: At least one compared repair report produced a pair-full profile.
- Next action: promote that repair candidate into held-out replay before changing the corpus again
