# MiniGPT Required-Term Pair Loss-Alias Metric Contrast

- Status: `pass`
- Decision: `required_term_pair_loss_alias_focus_normalized_delta_observed`
- Contrast decision: `loss_alias_focus_introduced_normalized_full_signal`
- Normalization gain delta: `4`
- Source normalized full: `False`
- Focus normalized full: `True`

## Stages

| Stage | Strict decision | Metric decision | Strict full | Norm full | Gains | Source |
| --- | --- | --- | --- | --- | ---: | --- |
| seed stability source | loss_alias_stable_partial_hit | loss_alias_stable_partial_hit | False | False | 0 | e\519\解释\model-capability-required-term-pair-loss-alias-stability-metrics\model_capability_required_term_pair_loss_alias_stability.json |
| focused repair metrics | loss_alias_focus_no_repair | loss_alias_focus_strict_miss_normalized_support_full_signal | False | True | 4 | e\518\解释\model-capability-required-term-pair-loss-alias-focus-metrics\model_capability_required_term_pair_loss_alias_focus.json |

## Boundary

- Model quality claim: `tiny_loss_alias_focus_formatting_sensitive_signal`
- Reason: The stability source had no normalized full delta, while focus produced a normalized full signal.
- Next action: inspect decoding or tokenization shape before treating normalized full signal as strict recovery
