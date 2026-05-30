# v525 required-term pair loss-alias newline suppression repeat 代码讲解

## 本版目标与边界

v525 的目标是验证 v524 的 newline suppression 严格恢复是否可重复。v524 只证明 v523 checkpoint 在屏蔽 newline token 后能从 strict `0/4` 恢复到 `4/4`；v525 把同一套 probe 应用于 v518 和 v523 两个 focus checkpoints，判断这是不是稳定的 decode-surface 信号。

本版不重新训练、不改默认生成策略，也不把 repeat 结果扩大解释为通用模型能力提升。它只验证两个归档 focus checkpoints 上的 newline suppression recovery 是否一致。

## 前置链路

前置版本：

- v518：首次把 strict 与 normalized metrics 接入 focus report。
- v523：把 bounded newline cleanup metrics 接入主线 focus report。
- v524：证明 v523 checkpoint 在 newline-token suppression 下 strict hit 从 `0/4` 恢复到 `4/4`。

v525 用 v524 的 probe builder 作为内部能力，不复制生成逻辑。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_newline_suppression_repeat.py`
  - 新增 repeat builder。
  - 接收多个 focus report 路径。
  - 对每个 source 调用 v524 probe builder。
  - 汇总 source-level baseline/suppressed strict full coverage。
- `src/minigpt/model_capability_required_term_pair_loss_alias_newline_suppression_repeat_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 展示每个 source 的 baseline strict、suppressed strict、suppressed full 和 gains。
- `scripts/run_model_capability_required_term_pair_loss_alias_newline_suppression_repeat.py`
  - CLI 接收多个 focus JSON 或目录。
- `tests/test_model_capability_required_term_pair_loss_alias_newline_suppression_repeat.py`
  - 覆盖多 source stable recovery、artifact 输出和缺失 source 失败。

## 核心数据结构

source row 字段：

- `source_id`
- `source_loss_alias_focus`
- `status`
- `decision`
- `case_count`
- `baseline_strict_hit_count`
- `baseline_strict_full_coverage`
- `suppressed_strict_hit_count`
- `suppressed_strict_full_coverage`
- `suppressed_focus_strict_hit_count`
- `suppressed_focus_strict_full_coverage`
- `suppressed_strict_gain_count`

summary 字段：

- `newline_suppression_repeat_decision`
- `source_count`
- `pass_source_count`
- `baseline_strict_full_source_count`
- `suppressed_strict_full_source_count`
- `suppressed_strict_gain_count`
- `stable_suppressed_strict_full_coverage`
- `case_count_total`

这些字段让报告能回答一个更工程化的问题：newline suppression 是一次性修复，还是跨 archived focus checkpoints 稳定成立。

## 核心流程

1. CLI 接收多个 focus report 或输出目录。
2. `locate_loss_alias_newline_suppression_source()` 解析每个 source 的 JSON。
3. Repeat builder 对每个 source 调用 v524 `build_model_capability_required_term_pair_loss_alias_newline_suppression_probe()`。
4. `_source_rows()` 提取每个 source 的 baseline/suppressed 结果。
5. `_summary()` 计算 stable full coverage 和总 strict gains。
6. artifact writer 输出多 source 对比报告。

## 真实结果解释

v525 真实运行结果：

```text
source_count=2
baseline_strict_full_source_count=0
suppressed_strict_full_source_count=2
suppressed_strict_gain_count=8
stable_suppressed_strict_full_coverage=True
```

这说明 v518 与 v523 都不是 baseline strict full，但都能通过 newline suppression 达到 strict full。这个结果支持把 newline-suppressed decoding 作为实验评估 profile，而不是立即改训练数据或默认 decoding。

## 测试覆盖

测试覆盖：

- 两个 fake focus sources 都从 baseline miss 变为 suppression full recovery。
- artifact writer 输出五类文件。
- source 缺失时结构失败，`--require-pass` 返回非零。

这些断言保护 repeat 层的职责：它只组合多个 v524 probe 结果，不改变单 source probe 的判定规则。

## 运行证据

运行证据归档在：

```text
e/525/解释/model-capability-required-term-pair-loss-alias-newline-suppression-repeat/
e/525/图片/
```

截图：

```text
e/525/图片/01-model-capability-required-term-pair-loss-alias-newline-suppression-repeat.png
```

## 一句话总结

v525 把 newline-suppressed decoding recovery 从单次 probe 推进为跨 v518/v523 两个 focus checkpoints 的稳定 strict recovery 证据。
