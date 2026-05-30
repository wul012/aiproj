# MiniGPT Required-Term Pair Loss-Alias Focus

- Status: `pass`
- Decision: `required_term_pair_loss_alias_focus_no_repair`
- Focus decision: `loss_alias_focus_no_repair`
- Focus cases: `2`
- Stable focus full coverage: `False`
- Stable support full coverage: `False`

## Focus Cases

| Case | Prompt | Missed seeds |
| --- | --- | --- |
| source-loss | loss: | [515] |
| heldout-beta-loss | beta: | [515] |

## Seed Rows

| Seed | Focus hits | Support hits | Focus full | Support full |
| ---: | ---: | ---: | --- | --- |
| 515 | 0 | 0 | False | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The focused corpus completed but did not repair the missed loss alias rows.
- Next action: inspect focused corpus ordering and generation previews before adding capacity
