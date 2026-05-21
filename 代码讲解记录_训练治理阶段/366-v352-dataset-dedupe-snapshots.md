# 第一百四十六篇代码讲解：第352版 dataset dedupe snapshots

## 本版目标和边界

v352 回到数据治理主线，解决的是“准备语料时能不能跳过完全重复的源文件，并把这个动作留下可审计证据”。v351 已经把 benchmark-history regression 传到 maturity review；v352 不继续堆 maturity 报告，而是补训练入口前面的数据快照能力。

本版新增的是 opt-in exact-source dedupe。默认行为仍然是不去重，避免已有训练和测试因为语料拼接顺序变化而改变。只有显式传入 `--dedupe-exact-sources` 时，准备数据才会跳过内容完全一致的后续源文件。

本版不做语义去重、不做近似重复检测、不改数据授权判断，也不声称自动清洗后的语料适合生产训练。它只把“哪些源文件进入 corpus，哪些被跳过，为什么跳过”变成机器可读和浏览器可读的证据。

## 前置链路

这版接在已有数据治理能力之后：

- v13-v15 已有 dataset preparation 和 quality report。
- v36 已有 dataset version manifest。
- v37 以后 dataset card、manifest、registry、training portfolio 都能消费数据版本。
- v352 在 `dataset_version.json` 里新增 snapshot，让后续训练、数据卡和审查报告可以看见去重策略与跳过源文件。

链路变成：

```text
source txt files
  -> build_prepared_dataset(..., dedupe_exact_sources=True)
  -> corpus.txt + dataset_report.json + dataset_quality.json
  -> dataset_version.json snapshot
  -> dataset_version.html / dataset_card.json / dataset_card.html
```

## 关键文件

### `src/minigpt/data_prep.py`

这是本版核心。

`SourceFileSummary` 新增三个字段：

```python
included: bool
duplicate_of: str | None
skip_reason: str | None
```

字段语义如下：

- `included`：这个源文件的规范化文本是否被写入最终 `corpus.txt`。
- `duplicate_of`：如果它是重复源文件，记录它重复的是哪个较早源文件。
- `skip_reason`：如果没有进入 corpus，记录原因，例如 `duplicate_source` 或 `empty_after_normalization`。

`PreparedDataset` 新增：

```python
included_sources
included_source_count
skipped_source_count
```

这些字段不是重新扫描文件系统，而是根据 `sources` 里的 `included` 计算，保证和最终 corpus 使用同一份证据。

`build_prepared_dataset()` 新增参数：

```python
dedupe_exact_sources: bool = False
```

默认是 `False`。开启后，函数会按规范化后的文本 SHA-256 判断完全重复源文件。第一个出现的源文件进入 corpus，后续完全相同的源文件标记为：

```json
{
  "included": false,
  "duplicate_of": ".../a.txt",
  "skip_reason": "duplicate_source"
}
```

`build_dataset_snapshot()` 是本版新增的快照结构。它输出：

- `dedupe_policy`
- `source_order_digest`
- `included_source_count`
- `skipped_source_count`
- `skipped_sources`
- `sources`

其中 `source_order_digest` 把 source path、sha256 和 included 状态串起来再计算摘要，用来证明这次准备语料的源文件顺序和纳入状态没有被悄悄改掉。

`build_dataset_version_manifest()` 把 snapshot 写入 `dataset_version.json`，并把 included/skipped 计数写入 `stats`。这让数据版本本身成为最终证据，而不是只依赖命令输出。

`render_dataset_version_html()` 新增 Snapshot 面板，并在 Sources 表里显示：

- Included
- Duplicate Of
- Skip reason

所以 reviewer 不需要打开 JSON，也能看到去重策略和跳过原因。

### `scripts/prepare_dataset.py`

CLI 新增：

```powershell
--dedupe-exact-sources
```

开启后会把参数传给 `build_prepared_dataset()` 和 `write_prepared_dataset()`。

命令输出新增：

```text
included_sources=...
skipped_sources=...
```

这让 shell 日志可以直接证明去重是否发生。

### `src/minigpt/dataset_card.py`

数据卡新增 `snapshot` section，读取 `dataset_version.json` 中的 `snapshot`。如果旧数据版本没有这个字段，也会根据 `preparation.dedupe_exact_sources` 给出兼容默认值。

`summary` 也新增：

- `included_source_count`
- `skipped_source_count`

推荐项新增两类判断：

- 未开启去重且没有跳过源文件时，建议较大语料可考虑 `--dedupe-exact-sources`。
- 已存在 skipped sources 时，建议 review `skipped_sources` 后再把数据集当作 clean training corpus。

### `src/minigpt/dataset_card_artifacts.py`

Markdown 和 HTML 输出新增 Snapshot。

Markdown 会展示：

- dedupe policy
- source order digest
- included/skipped source counts
- skipped source rows

HTML 会在顶部 stats 显示 Included/Skipped，并在 Snapshot 表中展示 dedupe policy、source order digest 和 skipped sources。

## 输入输出

典型输入：

```powershell
python scripts/prepare_dataset.py `
  --dataset-name demo-zh `
  --dataset-version v352 `
  --dataset-description "v352 dedupe snapshot smoke" `
  --dedupe-exact-sources `
  --out-dir runs/v352-data-governance-smoke/prepared `
  runs/v352-data-governance-smoke/inputs
```

关键输出：

- `corpus.txt`：只包含 included source 的文本。
- `dataset_report.json`：记录 source_count、included_source_count、skipped_source_count。
- `dataset_quality.json`：仍记录重复源 warning，保留质量审查边界。
- `dataset_version.json`：最终数据版本证据，新增 snapshot。
- `dataset_version.html`：浏览器可读的数据版本快照。
- `dataset_card.json/md/html`：人类可读的数据卡，也携带 snapshot。

这里有一个刻意设计：即使 exact duplicate 被跳过，quality report 仍能看到 duplicate_source warning，因为质量报告扫描的是 source summary，不是只扫描 included source。这样不会因为“自动跳过”而抹掉数据质量风险。

## 测试覆盖

新增和更新的测试集中在两块。

`tests/test_data_prep.py` 覆盖：

- 默认准备数据仍会合并所有源文件。
- `dedupe_exact_sources=True` 时，只保留第一份完全重复源。
- 跳过源文件会记录 `included=False`、`duplicate_of` 和 `skip_reason=duplicate_source`。
- dataset report 和 dataset version manifest 写入 included/skipped source counts。
- dataset version manifest 写入 `snapshot.dedupe_policy`。

`tests/test_dataset_card.py` 覆盖：

- dataset card summary 能读取 included/skipped counts。
- dataset card snapshot 能读取 `dedupe_policy`。
- 开启 dedupe 后，card 能展示 skipped sources。
- 有 skipped sources 时，recommendations 会提示 reviewer 先检查 snapshot。

完整验证还跑了：

```text
python -m unittest discover -s tests
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v352
python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-v352
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-v352 --fail-under 80
```

全量测试为 634 个，通过；覆盖率门禁为 90.40%，通过。

## 运行截图

运行证据保存在 `d/352`：

- `01-dataset-version-dedupe-snapshot.png`：证明 dataset version HTML 显示 dedupe policy、included/skipped source counts、source_order_digest 和 duplicate_source skip reason。
- `02-dataset-card-dedupe-snapshot.png`：证明 dataset card HTML 也消费了 snapshot，并把 skipped source review 变成推荐项。

## 链路角色

v352 的价值不在“自动清洗很聪明”，而在“清洗动作可审计”。后续如果把语料扩大到真实中文 corpus，项目需要知道：

- 哪些文件进入训练。
- 哪些文件被跳过。
- 跳过依据是不是 exact-source-content。
- 这次源文件顺序和 included 状态是否能复现。

这些信息现在都进入了 dataset version 和 dataset card，因此训练 run、registry、maturity narrative 再消费数据版本时，有了更可靠的数据边界。

## 一句话总结

v352 把 MiniGPT 的数据准备从“合并文本并报告质量”推进到“可选去重、可复现快照、可审计 skipped source 证据”的数据治理层。
