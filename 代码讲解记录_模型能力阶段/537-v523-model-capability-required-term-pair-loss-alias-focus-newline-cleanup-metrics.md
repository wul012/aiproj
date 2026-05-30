# v523 required-term pair loss-alias focus newline cleanup metrics 代码讲解

## 本版目标与边界

v523 的目标是把 v522 发现的 bounded newline cleanup 结论并入主线 `loss_alias_focus` 报告。它解决的问题是：v518/v521/v522 已经证明 `loss` 字符常被换行拆开，但主线 focus 报告仍只有 strict 与 normalized 两档，读者必须跳到旁路审计才能知道 normalized gain 是否只是换行导致。

本版不改训练数据、不扩大模型、不重跑多 seed 稳定性，也不把 newline cleanup 命中算作 strict success。它只在主线报告中新增一层更窄的 surface metric。

## 前置链路

前置版本：

- v518：主线 focus 报告开始同时携带 strict 和 normalized hit。
- v521：segment audit 确认 normalization gains 来自 newline split。
- v522：decode cleanup audit 确认只移除 newline 就能恢复 4/4 hidden loss hit。

v523 顺着 v522 的结论，把旁路 cleanup 证据折回主报告。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_metrics.py`
  - 新增 `remove_newline_separators()`。
  - `required_term_hit_metrics()` 增加 `newline_cleanup_hit`、`newline_cleanup_gain`、`newline_cleanup_continuation`。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus_components.py`
  - 新增 `focus_surface_decision()`。
  - strict 没修复时，优先区分 newline cleanup support/focus/partial signal。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus.py`
  - generation rows、seed summary、top-level summary 都携带 newline cleanup 字段。
  - 顶层 `decision` 和 `model_quality_claim` 在 normalized 之前先判断 newline cleanup signal。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus_artifacts.py`
  - text/CSV/Markdown/HTML 输出新增 newline cleanup counts、gains 和 surface decision。
- `tests/test_model_capability_required_term_pair_loss_alias_focus.py`
  - 覆盖 strict success、no repair、split-loss newline signal 三类情况。

## 核心数据结构

generation row 新增字段：

- `newline_cleanup_hit`
- `newline_cleanup_gain`
- `newline_cleanup_continuation_preview`

seed summary 新增字段：

- `support_newline_cleanup_hit_case_count`
- `focus_newline_cleanup_hit_case_count`
- `support_newline_cleanup_full_coverage`
- `focus_newline_cleanup_full_coverage`
- `newline_cleanup_gain_count`

top-level summary 新增字段：

- `loss_alias_focus_surface_decision`
- `support_newline_cleanup_full_seed_count`
- `focus_newline_cleanup_full_seed_count`
- `stable_support_newline_cleanup_full_coverage`
- `stable_focus_newline_cleanup_full_coverage`
- `newline_cleanup_gain_count`

这些字段的位置有意放在 strict 与 normalized 之间：newline cleanup 只删除 `\r`/`\n`，比 alnum normalization 更窄，也更适合解释 line-broken required-term 输出。

## 核心流程

1. Focus builder 读取 v515 stability report，选择 support cases 和 seed 515 missed focus cases。
2. 训练与生成流程保持不变。
3. `_generation_rows()` 对每条 continuation 调用 `required_term_hit_metrics()`。
4. `_seed_summary()` 汇总 strict、newline cleanup、normalized 三层命中。
5. `summarize_loss_alias_focus()` 生成 strict decision、surface decision 和 metric decision。
6. artifact writer 输出 JSON/CSV/text/Markdown/HTML，HTML 顶部同时展示 Decision、Surface、Metric。

## 真实结果解释

v523 真实运行结果：

```text
decision=required_term_pair_loss_alias_focus_newline_cleanup_support_signal
loss_alias_focus_decision=loss_alias_focus_no_repair
loss_alias_focus_surface_decision=loss_alias_focus_strict_miss_newline_cleanup_support_full_signal
loss_alias_focus_metric_decision=loss_alias_focus_strict_miss_normalized_support_full_signal
support_full_seed_count=0
support_newline_cleanup_full_seed_count=1
newline_cleanup_gain_count=4
support_normalized_full_seed_count=1
normalization_gain_count=4
```

这说明 v523 没有把原始 strict failure 美化成成功：`support_full_seed_count=0` 仍然保留。新增信息是：只去掉换行后，support loss alias 全覆盖，说明当前失败更像 decode surface 问题，而不是完全没有生成目标字符。

## 测试覆盖

测试覆盖：

- 正常 `loss` continuation 下，strict、newline cleanup、normalized 都 full，且 gain 为 0。
- 空 continuation 下，strict、newline cleanup、normalized 都不构成修复。
- `lo\ns\ns` continuation 下，strict no repair，但 surface decision 变成 newline cleanup full signal，同时 normalized metric 仍保留。

这些断言保护了本版的边界：newline cleanup 是独立的 bounded surface metric，不会覆盖 strict hit，也不会替代 normalized metric。

## 运行证据

运行证据归档在：

```text
e/523/解释/model-capability-required-term-pair-loss-alias-focus-newline-cleanup-metrics/
e/523/图片/
```

截图：

```text
e/523/图片/01-model-capability-required-term-pair-loss-alias-focus-newline-cleanup-metrics.png
```

## 一句话总结

v523 把 loss-alias 的 newline surface 边界接入主线 focus 报告，让后续能力判断能同时看到 strict failure、bounded cleanup signal 和 normalized signal。
