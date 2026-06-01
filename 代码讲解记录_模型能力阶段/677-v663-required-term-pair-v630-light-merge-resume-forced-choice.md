# v663 required-term pair v630 light-merge resume forced-choice

## 本版目标和边界

v663 检查 v662 的 lower-rate light-merge continuation 是否在内部 forced-choice 上保留了信号。

## 结果

- `decision=refresh_forced_choice_not_recovered`
- `expected_best_prompt_count=0`
- `forced_choice_full_match_source_count=0`

这说明 light-merge continuation 不仅生成侧退化，内部侧也没有保住任一 expected-best prompt。

## 一句话总结

v663 把 v662 light-merge continuation 定性为生成与内部双失败路线。
