# MiniGPT Required-Term Pair Seed Config Held-Out Gap Diagnostic

- Status: `pass`
- Decision: `required_term_pair_seed_config_heldout_gap_fixed_term_surface`
- Gap rows: `1/9`
- Gap classes: `fixed_term_surface_gap:1`

## Gap Rows

| Spec | Seed | Config | Gap class | Missed terms | Best profile | Prompts |
| --- | ---: | --- | --- | --- | --- | --- |
| equals | 1535 | v546-loss-calibrated-topk2-t080 | fixed_term_surface_gap | fixed | suppress_newline_tokens | fixed= / loss= |

## Profile Evidence

| Spec | Profile | Hit terms | Missed terms | Continuation previews |
| --- | --- | --- | --- | --- |
| equals | default | loss | fixed | fixed=losss\nlossss; loss=fixel-lossss |
| equals | suppress_newline_tokens | loss | fixed | fixed=los:lompromp; loss=fixel-lossss |

## Boundary

- Model quality claim: `diagnostic_only`
- Reason: The held-out replay gaps are now localized by prompt surface, seed, config, and missed term.
- Next action: repair the dominant missed-term surface before adding broader benchmarks
