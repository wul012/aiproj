# 第一百四十八篇代码讲解：第354版 run comparison dataset snapshot carryover

## 本版目标和边界

v354 的目标是把 v353 的 dataset version comparison 信号接入已有 run comparison。此前 `compare_runs.py` 已经能看到 `dataset_version_changed`，但这只回答“数据版本名不同”，不能回答“数据到底怎么变了”。

本版补充的是数据边界解释能力：

- dataset fingerprint 是否相对 baseline 改变
- dedupe policy 是否改变
- source order digest 是否改变
- included/skipped source count 相对 baseline 的 delta
- dataset char count 相对 baseline 的 delta

本版不新增独立报告，不训练模型，不改 benchmark，不把 loss 改善解释成模型能力提升。它只是让模型比较报告在展示 loss、eval、perplexity 之前，把数据变化证据摆出来。

## 前置链路

v352 已经把 dataset snapshot 写入 `dataset_version.json`：

```text
dataset_version.json
  -> stats.included_source_count
  -> stats.skipped_source_count
  -> stats.char_count
  -> snapshot.dedupe_policy
  -> snapshot.source_order_digest
```

v353 能单独比较多个 dataset version。v354 则把同样的数据边界接进 run comparison：

```text
run directory
  -> dataset_version.json
  -> summarize_run()
  -> build_comparison_report()
  -> comparison.json/csv/md/html
```

这样，当两个 run 的 best_val_loss 不同，但 dataset snapshot 也不同，报告会直接提示 reviewer 先检查数据变化。

## 关键文件

### `src/minigpt/comparison.py`

`RunComparison` 新增字段：

```python
dataset_dedupe_policy: str | None
dataset_source_order_digest: str | None
dataset_included_source_count: int | None
dataset_skipped_source_count: int | None
dataset_char_count: int | None
```

这些字段都来自 run 目录下的 `dataset_version.json`。其中：

- `dataset_dedupe_policy` 优先读 `snapshot.dedupe_policy`。
- `dataset_source_order_digest` 读 `snapshot.source_order_digest`。
- source count 与 char count 读 `stats`。

`_baseline_delta()` 新增数据变化字段：

```json
{
  "dataset_fingerprint_changed": true,
  "dataset_dedupe_policy_changed": true,
  "dataset_source_order_changed": true,
  "dataset_included_source_count_delta": -1,
  "dataset_skipped_source_count_delta": 1,
  "dataset_char_count_delta": -50
}
```

这些字段让 run comparison 不再只靠 `dataset_version_changed`，而是能说明差异来自内容 fingerprint、准备策略、源文件纳入状态还是语料规模。

`_comparison_summary()` 新增聚合字段：

- `dataset_fingerprint_count`
- `dataset_dedupe_policy_count`
- `dataset_fingerprint_changed_count`
- `dataset_dedupe_policy_changed_count`
- `dataset_source_order_changed_count`

`_comparison_recommendations()` 也新增两类提醒：

- fingerprint 改变时，不要把 loss delta 当成纯模型变化。
- dedupe policy 改变时，要先检查 included/skipped source delta。

### `src/minigpt/comparison_artifacts.py`

本版没有新增独立 artifact 模块，而是扩展既有 run comparison 输出：

- CSV 新增 dataset snapshot 和 delta 列。
- Markdown 表格新增 `Data Snapshot` 列。
- HTML 的 Dataset 单元格新增 dedupe、included/skipped、chars 和 changed 标签。
- 顶部 stat card 新增 `Data fingerprint changes` 和 `Dedupe changes`。

核心格式化函数是 `_dataset_snapshot_label()`，它把多个字段压成一段紧凑说明：

```text
dedupe=exact-source-content;
included=2 (-1);
skipped=1 (+1);
chars=90 (-50);
changed=fingerprint,dedupe,source-order
```

这段文本被 Markdown 和 HTML 共同使用，避免两个 renderer 各自拼接一套含义。

### `tests/test_comparison.py`

测试新增两层保护：

- `summarize_run()` 能从 `dataset_version.json` 读出 dedupe policy 和 included source count。
- `build_comparison_report()` 能生成 dataset fingerprint、dedupe policy、source order 和 source/char delta。

这保护的是比较契约，不是某个截图样式。

### `tests/test_comparison_artifacts.py`

artifact 测试确保：

- CSV 包含 `dataset_dedupe_policy_changed`。
- HTML 包含 `dedupe=exact-source-content`。

这样以后如果 renderer 被重构，dataset snapshot 证据不会悄悄丢失。

## 运行证据

本版 smoke 使用两个 run：

- `raw`：3 个源文件全部纳入，dedupe policy 为 `none`。
- `deduped`：2 个源文件纳入，1 个源文件跳过，dedupe policy 为 `exact-source-content`。

命令输出中 summary 显示：

```text
dataset_fingerprint_changed_count=1
dataset_dedupe_policy_changed_count=1
dataset_source_order_changed_count=1
```

运行截图归档在：

- `d/354/图片/01-run-comparison-dataset-snapshot.png`
- `d/354/解释/说明.md`

截图证明 HTML 报告中已经能直接看到 dataset snapshot delta。

## 一句话总结

v354 让 MiniGPT 的 run comparison 从“只比较训练结果”推进到“训练结果和数据变化边界一起比较”，更适合后续真实 benchmark 和模型晋升审计。
