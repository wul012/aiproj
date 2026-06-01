# v652 required-term pair surface-first schedule forced-choice

## 本版目标和边界

v652 检查 v651 真实训练 checkpoint 的内部 forced-choice 行为。v651 已经显示自由生成没有 pair-full，本版回答一个更细的问题：模型内部是否仍知道 `loss=` 应该选 `loss`。

本版不训练新模型，只读取 v651 的 checkpoint 和 tokenizer，输出 forced-choice 诊断。

## 输入输出

输入：

- `e/651/解释/model-capability-required-term-pair-surface-first-schedule-seed-3535/`
- label：`surface-first-schedule`

输出：

- `model_capability_required_term_pair_refresh_forced_choice_diagnostic.json`
- CSV/Markdown/HTML 同步输出。
- Playwright 截图归档到 `e/652/图片/`。

## 核心结果

报告显示：

- `decision=refresh_forced_choice_partial_internal_match`
- `expected_best_prompt_count=1`
- `forced_choice_full_match_source_count=0`

prompt 级别：

- `fixed` prompt 的 expected candidate 是 best。
- `loss` prompt 的 best candidate 变成 `fixed`。

这意味着 v650 的 surface-first corpus 不但没保住 loss 自由生成，也没保住 loss 内部偏好。

## 链路意义

v649 计划需要两类证据：

- surface stage 保生成 pair-full。
- internal stage 保 forced-choice pair-full。

v651/v652 说明当前单语料近似两边都没有达成：它保了 `fixed`，但 `loss` 在生成和内部都被压掉了。

## 测试和截图

本版复用 forced-choice diagnostic 的现有测试与 CLI。截图显示：

- Status=`pass`
- Decision=`refresh_forced_choice_partial_internal_match`
- Expected-best=`1`
- Full match=`0`

## 一句话总结

v652 把 surface-first schedule 的失败定位为生成和内部双重 fixed 偏置，而不是单纯采样问题。
