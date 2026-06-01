# v661 required-term pair v630 internal-repair resume forced-choice

## 本版目标和边界

v661 检查 v660 的续训 checkpoint 内部评分。v660 自由生成退成 loss-only，本版判断内部 forced-choice 是否至少有所改善。

本版不训练，只读取 v660 checkpoint。

## 结果

- `decision=refresh_forced_choice_partial_internal_match`
- `expected_best_prompt_count=1`
- `forced_choice_full_match_source_count=0`

prompt 级别：

- `fixed` prompt：best candidate 是 `fixed`。
- `loss` prompt：best candidate 仍是 `fixed`。

## 链路意义

v660/v661 组合说明 naive internal-repair continuation 没有达成目标：

- 生成侧没有 pair-full。
- 内部侧也没有 pair-full。

它不应进入 promotion 或 seed stability，只能作为负向 continuation 证据。

## 一句话总结

v661 把 v660 的失败定位为生成与内部未对齐，而不是单纯采样问题。
