# MiniGPT Required-Term Pair Loss-Alias Focus

- Status: `pass`
- Decision: `required_term_pair_loss_alias_focus_support_full_hit`
- Focus decision: `loss_alias_focus_support_full_hit`
- Surface decision: `loss_alias_focus_support_full_hit`
- Metric decision: `loss_alias_focus_support_full_hit`
- Focus cases: `2`
- Stable focus full coverage: `True`
- Stable support full coverage: `True`
- Newline cleanup gains: `0`
- Normalization gains: `0`

## Focus Cases

| Case | Prompt | Missed seeds |
| --- | --- | --- |
| source-loss | loss: | [515] |
| heldout-beta-loss | beta: | [515] |

## Seed Rows

| Seed | Strict focus | Strict support | Newline focus | Newline support | NL gains | Normalized focus | Normalized support | Gains |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 527 | 2 | 4 | 2 | 4 | 0 | 2 | 4 | 0 |

## Boundary

- Model quality claim: `tiny_loss_alias_focused_support_full_signal`
- Reason: The focused corpus recovered every support loss alias case for every tested seed.
- Next action: add fixed aliases back and test pair coexistence
