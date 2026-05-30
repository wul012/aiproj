# v520 required-term pair loss-alias metric contrast 代码讲解

## 本版目标与边界

v520 的目标是把 v519 stability metrics 和 v518 focus metrics 合并成一个只读对比报告。v519 已经确认原始 stability 源头没有 normalized full；v518 则显示 focus 后出现 normalized full。本版把这两个事实放到同一个报告里，避免后续误读。

本版不训练模型、不重跑 generation、不改已有 checkpoint，也不把 normalized hit 宣称为 strict success。它只是读取已归档 JSON，输出阶段对比证据。

## 前置链路

前置版本：

- v518：focus 报告显示 strict support `0/4`，normalized support `4/4`，gain `4`。
- v519：stability 报告显示 strict 与 normalized 都是 stable partial，gain `0`。

v520 的工作是说明这两个结果之间的差异来自阶段变化，而不是同一报告的度量口径冲突。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_metric_contrast.py`
  - 新增只读 builder，读取 stability 与 focus summary。
  - 输出两个 stage rows：`stability-source` 与 `focused-repair`。
  - 计算 `normalization_gain_delta` 和 `metric_contrast_decision`。
- `src/minigpt/model_capability_required_term_pair_loss_alias_metric_contrast_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 表格展示 strict decision、metric decision、strict full、normalized full 和 gains。
- `scripts/run_model_capability_required_term_pair_loss_alias_metric_contrast.py`
  - CLI 接受两个输入路径或目录，自动定位对应 JSON。
- `tests/test_model_capability_required_term_pair_loss_alias_metric_contrast.py`
  - 覆盖 focus normalized delta、产物输出和 source report failure。

## 核心数据结构

stage row 字段：

- `stage`
- `strict_decision`
- `metric_decision`
- `strict_full_seed_count`
- `normalized_full_seed_count`
- `stable_strict_full`
- `stable_normalized_full`
- `normalization_gain_count`
- `source_path`

summary 字段：

- `metric_contrast_decision`
- `source_metric_decision`
- `focus_metric_decision`
- `source_normalization_gain_count`
- `focus_normalization_gain_count`
- `normalization_gain_delta`
- `source_stable_normalized_full`
- `focus_stable_normalized_full`
- `focus_stable_strict_full`

这些字段把 v518/v519 的核心差异压缩成一张表和一个 decision。

## 核心流程

1. CLI 定位 stability JSON 和 focus JSON。
2. Builder 校验两个 source report 都是 `status=pass`。
3. `_stage_rows()` 分别抽取 source/focus 的 strict 与 normalized 指标。
4. `_summary()` 计算 gain delta 与阶段状态差异。
5. artifact writer 输出可审计的 JSON/CSV/text/Markdown/HTML。

整个流程只读，不会修改上游报告，也不会重建训练产物。

## 真实结果解释

v520 真实运行结果：

```text
source_normalization_gain_count=0
focus_normalization_gain_count=4
normalization_gain_delta=4
source_stable_normalized_full=False
focus_stable_normalized_full=True
focus_stable_strict_full=False
```

这说明 focus 阶段引入了格式敏感的 normalized full signal，但 strict full 仍然没有成立。下一步不应该盲目加数据或扩大模型，而应该检查 decoding/tokenization 形态，弄清楚为什么模型输出 `loss` 字符序列时会被分隔。

## 测试覆盖

测试覆盖：

- source 无 normalized gain、focus 有 normalized full gain 时，decision 进入 `required_term_pair_loss_alias_focus_normalized_delta_observed`。
- artifact writer 输出五类文件。
- source report fail 时，`--require-pass` 会返回失败。

这些测试保护 v520 的边界：报告只解释已存在证据，不伪造模型能力提升。

## 运行证据

运行证据归档在：

```text
e/520/解释/model-capability-required-term-pair-loss-alias-metric-contrast/
e/520/图片/
```

截图：

```text
e/520/图片/01-model-capability-required-term-pair-loss-alias-metric-contrast.png
```

## 一句话总结

v520 把 loss-alias 的 source/focus 双指标关系收束清楚：focus 带来了 normalized formatting signal，但 strict 模型能力仍未真正修复。
