# 第一百四十九篇代码讲解：第355版 registry dataset snapshot carryover

## 本版目标和边界

v355 的目标是把 v354 已经进入 run comparison 的 dataset snapshot 信号，继续带到 run registry。registry 是多 run 的第一入口，如果它只显示 `dataset_fingerprint`，reviewer 仍然需要进入每个 run 的 `dataset_version.json` 或 comparison 报告，才能判断数据边界是否变化。

本版解决的问题是：多 run 扫描时，直接看到 dataset version、dedupe policy、source order、included/skipped source count 和 corpus char count。

本版不新增独立报告，不改 best-val-loss 排名，不训练模型，也不把 registry 中的 loss 改善解释成模型能力提升。

## 前置链路

前置能力来自 v352-v354：

```text
v352 dataset_version.json
  -> stats / snapshot / preparation
v353 compare_dataset_versions.py
  -> 多 dataset version 对比
v354 compare_runs.py
  -> run comparison 展示数据变化 delta
v355 registry
  -> 多 run 入口直接展示 dataset snapshot
```

本版承接的是同一条数据治理路线：先让数据快照可复现，再让对比报告识别变化，最后让 registry 入口也能显示这些变化。

## 关键文件

### `src/minigpt/registry_data.py`

`RegisteredRun` 新增字段：

```python
dataset_version: str | None
dataset_dedupe_policy: str | None
dataset_source_order_digest: str | None
dataset_included_source_count: int | None
dataset_skipped_source_count: int | None
dataset_char_count: int | None
```

`summarize_registered_run()` 新增读取 `dataset_version.json`：

```text
dataset_version.json
  -> dataset.id
  -> stats.short_fingerprint
  -> stats.included_source_count
  -> stats.skipped_source_count
  -> stats.char_count
  -> snapshot.dedupe_policy
  -> snapshot.source_order_digest
```

这里的 fingerprint 读取顺序也更完整：优先使用 run manifest 的 dataset version fingerprint，其次使用 dataset version stats，再退回 dataset quality。这样旧 run 仍然兼容，新 run 能展示更丰富的数据边界。

`build_run_registry()` 新增：

- `dataset_versions`
- `dataset_dedupe_policy_counts`
- `dataset_snapshot_summary`

`dataset_snapshot_summary` 统计：

- 有 snapshot 的 run 数
- 缺 snapshot 的 run 数
- dataset version / fingerprint / dedupe policy / source order 的不同数量
- 有 skipped source 的 run 数
- included/skipped source 总数
- char count 总量

这些字段是 registry 的机器可读入口，后续 model card、maturity 或 release review 如果需要消费，也可以直接读取。

### `src/minigpt/registry_artifacts.py`

CSV 新增 dataset snapshot 字段：

```text
dataset_version
dataset_dedupe_policy
dataset_source_order_digest
dataset_included_source_count
dataset_skipped_source_count
dataset_char_count
```

SVG 也显示一行压缩后的 snapshot label：

```text
dedupe=exact-source-content; included=2; skipped=1; chars=90; order=...
```

这保证非 HTML 消费者也能看到关键数据边界。

### `src/minigpt/registry_render.py`

HTML 顶部 stat card 新增：

- `Dataset snapshots`
- `Dedupe policies`

run table 的 `Data` 列从单纯 fingerprint 扩展为：

```text
data source kind
dataset version
dataset fingerprint
dataset snapshot label
```

页面底部新增 `Dataset Snapshot Summary`，以 JSON 形式保留完整聚合字段。这个 section 是只读证据，不是新的决策模块。

### `scripts/register_runs.py`

stdout 新增：

```text
dataset_versions=...
dataset_dedupe_policy_counts=...
dataset_snapshot_summary=...
```

这样 CI 或 shell-only reviewer 不打开 HTML，也能看到本版新增的数据边界摘要。

## 测试覆盖

`tests/test_registry.py` 的 fixture run 现在写入真实 `dataset_version.json`，并覆盖：

- `summarize_registered_run()` 是否读出 dataset version 和 snapshot 字段。
- `build_run_registry()` 是否聚合 dataset versions、dedupe policy counts 和 snapshot summary。
- CSV 是否包含新增列。
- HTML 是否包含 Dataset snapshots / Dedupe policies / Dataset Snapshot Summary。
- SVG 是否包含 snapshot label。

同时运行 `tests.test_registry_split`、`tests.test_registry_assets`、`tests.test_registry_rankings`，确认 registry 拆分边界、浏览器交互资产和 leaderboard 没有因为新增数据字段回归。

## 运行证据

运行证据放在：

```text
d/355/图片/01-registry-dataset-snapshot.png
d/355/解释/说明.md
```

截图中可以看到：

- stat card 显示 `Dataset snapshots` 和 `Dedupe policies`。
- `deduped` run 显示 `dedupe=exact-source-content; included=2; skipped=1; chars=90`。
- `raw` run 显示 `dedupe=none; included=3; skipped=0; chars=140`。
- 底部 `Dataset Snapshot Summary` 保留机器可读聚合字段。

## 一句话总结

v355 把 dataset snapshot 从单个 run 和 run comparison 扩展到 registry 入口，让多 run 审计一开始就能区分模型变化和数据边界变化。
