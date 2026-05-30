# MiniGPT Required-Term Pair Loss-Alias Focus

- Status: `pass`
- Decision: `required_term_pair_loss_alias_focus_newline_cleanup_support_signal`
- Focus decision: `loss_alias_focus_no_repair`
- Surface decision: `loss_alias_focus_strict_miss_newline_cleanup_support_full_signal`
- Metric decision: `loss_alias_focus_strict_miss_normalized_support_full_signal`
- Focus cases: `2`
- Stable focus full coverage: `False`
- Stable support full coverage: `False`
- Newline cleanup gains: `4`
- Normalization gains: `4`

## Focus Cases

| Case | Prompt | Missed seeds |
| --- | --- | --- |
| source-loss | loss: | [515] |
| heldout-beta-loss | beta: | [515] |

## Seed Rows

| Seed | Strict focus | Strict support | Newline focus | Newline support | NL gains | Normalized focus | Normalized support | Gains |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 515 | 0 | 0 | 2 | 4 | 4 | 2 | 4 | 4 |

## Boundary

- Model quality claim: `tiny_loss_alias_focused_newline_cleanup_support_signal`
- Reason: Strict hits still failed, but every support loss alias appears after removing only newline separators.
- Next action: treat line-broken required-term output as a decode-surface issue before changing training again
