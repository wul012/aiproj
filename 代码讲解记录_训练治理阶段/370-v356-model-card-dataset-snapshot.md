# 第一百五十篇代码讲解：第356版 model card dataset snapshot carryover

## 本版目标和边界

v356 的目标是把 v355 进入 registry 的 dataset snapshot 证据，继续带到 model card。model card 是项目级说明，如果它只总结 run count、best run、实验卡覆盖、eval 和 generation quality，却不展示数据版本边界，那么 reviewer 在项目级材料中仍然看不到“数据变了吗”。

本版解决的问题是：model card 的 top runs 和 all runs 也能展示 dataset version、dedupe policy、source order、included/skipped source count 和 corpus char count。

本版不新增独立报告，不训练模型，不改变 ready/review 判定，不把 loss 改善解释成模型能力提升。

## 前置链路

本版承接 v352-v355：

```text
v352 dataset_version.json
  -> snapshot/stats/preparation
v353 dataset version comparison
  -> 多数据版本对比
v354 run comparison
  -> loss delta 旁边展示数据边界 delta
v355 registry
  -> 多 run 入口展示数据快照
v356 model card
  -> 项目级模型说明继承数据快照
```

它的核心价值不是“又多一个字段”，而是让数据治理信号穿过 registry 进入 model card，成为项目交付说明的一部分。

## 关键文件

### `src/minigpt/model_card.py`

`_build_run_summaries()` 从 registry run row 复制 dataset snapshot 字段：

```python
dataset_version
dataset_fingerprint
dataset_dedupe_policy
dataset_source_order_digest
dataset_included_source_count
dataset_skipped_source_count
dataset_char_count
```

`build_model_card()` 顶层新增：

- `dataset_versions`
- `dataset_dedupe_policy_counts`
- `dataset_snapshot_summary`

这些字段来自 registry，不重新扫描 run 目录。这样 model card 的输入仍然保持为 registry + experiment cards，职责边界不变。

`_build_summary()` 和 `_build_coverage()` 新增：

- `dataset_snapshot_runs`
- `dataset_skipped_source_runs`
- `dataset_version_count`
- `dataset_snapshot_coverage`

这些字段让 model card 能说明：有多少 run 带有数据快照、有多少 run 使用了不同 dataset version、是否存在 skipped source。

`_build_recommendations()` 新增两条判断：

- 如果不是每个 run 都有 dataset snapshot，建议从 dataset-versioned runs 重新生成 registry。
- 如果存在 skipped source，提醒先 review skipped dataset sources，再把 loss delta 当作模型变化证据。

### `src/minigpt/model_card_artifacts.py`

Markdown/HTML 的 run table 新增 `Data Snapshot` 列。每行格式类似：

```text
demo-v356@deduped; dedupe=exact-source-content; included=2; skipped=1; chars=90; order=order-deduped
```

HTML 顶部 stat card 新增：

- `Datasets`
- `Snapshots`
- `Skipped sources`

HTML/Markdown 还新增 `Dataset Snapshot Summary` section，HTML 额外显示 `Dataset Dedupe Policies`。这些都是只读证据，不是新决策模块。

### `scripts/build_model_card.py`

stdout 新增：

```text
dataset_snapshot_runs=...
dataset_snapshot_coverage=...
dataset_snapshot_summary=...
```

这样 shell-only 或 CI 日志也能看到 model card 是否继承了 registry 的数据快照，以及覆盖比例是否完整。

## 测试覆盖

`tests/test_model_card.py` 的 registry fixture 增加：

- `dataset_versions`
- `dataset_dedupe_policy_counts`
- `dataset_snapshot_summary`
- 每个 run 的 dataset snapshot 字段

测试断言覆盖：

- card JSON 的 coverage 与 summary。
- top run 是否携带 `dataset_dedupe_policy`。
- recommendations 是否提示 skipped dataset sources。
- Markdown 是否包含 `Dataset Snapshot Summary` 和 dedupe label。
- HTML 是否包含同样的 snapshot section 与 run row label。

## 运行证据

运行证据放在：

```text
d/356/图片/01-model-card-dataset-snapshot.png
d/356/解释/说明.md
```

截图可以看到：

- 顶部 `Datasets / Snapshots / Skipped sources` stat cards。
- Top Runs 和 All Runs 的 `Data Snapshot` 列。
- `Dataset Dedupe Policies` 与 `Dataset Snapshot Summary` sections。
- Recommendations 中的 skipped-source 审阅提醒。

## 一句话总结

v356 把 dataset snapshot 从 registry 继续传到 model card，让项目级模型说明也能明确区分模型变化和数据边界变化。
