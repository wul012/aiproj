# MiniGPT Required-Term Pair Loss-Alias Focus

- Status: `pass`
- Decision: `required_term_pair_loss_alias_focus_normalized_support_signal`
- Focus decision: `loss_alias_focus_no_repair`
- Metric decision: `loss_alias_focus_strict_miss_normalized_support_full_signal`
- Focus cases: `2`
- Stable focus full coverage: `False`
- Stable support full coverage: `False`
- Normalization gains: `4`

## Focus Cases

| Case | Prompt | Missed seeds |
| --- | --- | --- |
| source-loss | loss: | [515] |
| heldout-beta-loss | beta: | [515] |

## Seed Rows

| Seed | Strict focus | Strict support | Normalized focus | Normalized support | Gains |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 515 | 0 | 0 | 2 | 4 | 4 |

## Boundary

- Model quality claim: `tiny_loss_alias_focused_normalized_support_signal`
- Reason: Strict hits still failed, but every support loss alias contains the required term after normalization.
- Next action: carry strict and normalized hit metrics together before another training change
