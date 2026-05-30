# MiniGPT Required-Term Pair Loss-Alias Focus

- Status: `pass`
- Decision: `required_term_pair_loss_alias_focus_repaired`
- Focus decision: `loss_alias_focus_missed_rows_repaired`
- Surface decision: `loss_alias_focus_missed_rows_repaired`
- Metric decision: `loss_alias_focus_missed_rows_repaired`
- Focus cases: `2`
- Stable focus full coverage: `True`
- Stable support full coverage: `False`
- Newline cleanup gains: `2`
- Normalization gains: `2`

## Focus Cases

| Case | Prompt | Missed seeds |
| --- | --- | --- |
| source-loss | loss: | [515] |
| heldout-beta-loss | beta: | [515] |

## Seed Rows

| Seed | Strict focus | Strict support | Newline focus | Newline support | NL gains | Normalized focus | Normalized support | Gains |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 527 | 2 | 4 | 2 | 4 | 0 | 2 | 4 | 0 |
| 528 | 2 | 2 | 2 | 4 | 2 | 2 | 4 | 2 |
| 529 | 2 | 4 | 2 | 4 | 0 | 2 | 4 | 0 |

## Boundary

- Model quality claim: `tiny_loss_alias_focused_repair_signal`
- Reason: The focused corpus repaired every previously missed loss alias row for every tested seed.
- Next action: repeat focused repair with another seed before pair recombination
