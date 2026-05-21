# 第一百四十七篇代码讲解：第353版 dataset version comparison

## 本版目标和边界

v353 接在 v352 的 dataset snapshot 之后，解决的是“多个 prepared dataset 版本之间到底差了什么”。v352 已经能在 `dataset_version.json` 中记录 dedupe policy、source order digest、included/skipped sources 和 skip reason；但如果后续训练拿 raw、deduped 或更大 corpus 做比较，只看单个版本还不够。

所以本版新增 dataset version comparison，把多个 `dataset_version.json` 放到同一个报告里，以 baseline 视角比较：

- dataset identity 是否变化
- fingerprint 是否变化
- dedupe policy 是否变化
- source order digest 是否变化
- source count / included / skipped 是否变化
- char count、warning count、issue count 是否变化

本版不训练模型、不跑 benchmark、不声明模型能力提升。它的角色是数据治理前置检查：先确认数据变化，再解释训练或评估变化。

## 前置链路

本版依赖前面的数据治理能力：

```text
source txt files
  -> prepare_dataset.py
  -> dataset_report.json / dataset_quality.json
  -> dataset_version.json snapshot
  -> compare_dataset_versions.py
  -> dataset_version_comparison.{json,csv,md,html}
```

这条链路的关键点是：比较报告不是重新扫描源文件，而是消费已经生成的 dataset version manifest。这样比较结果和后续训练使用的数据版本证据保持一致。

## 关键文件

### `src/minigpt/dataset_version_comparison.py`

这是本版核心模块。

`DatasetVersionSummary` 是对单个 `dataset_version.json` 的归一化摘要：

```python
@dataclass(frozen=True)
class DatasetVersionSummary:
    name: str
    path: str
    dataset_id: str | None
    fingerprint: str | None
    short_fingerprint: str | None
    source_count: int
    included_source_count: int
    skipped_source_count: int
    char_count: int
    quality_status: str | None
    dedupe_policy: str
    source_order_digest: str | None
```

它把 `dataset`、`stats`、`quality`、`preparation`、`snapshot` 五块信息合并成一行可比较数据。这里的 `dedupe_policy` 优先读取 `snapshot.dedupe_policy`，旧 manifest 缺 snapshot 时才回退到 `preparation.dedupe_exact_sources`。

`summarize_dataset_version()` 支持两种输入：

- prepared dataset 目录，例如 `datasets/demo/v1`
- 直接传入 `dataset_version.json`

目录输入会自动解析到 `dataset_version.json`，便于 CLI 使用。

`build_dataset_version_comparison()` 是总入口。它会：

1. 读取所有版本。
2. 根据 `--baseline` 或第一个版本选择 baseline。
3. 生成每个版本相对 baseline 的 delta。
4. 汇总 fingerprint count、dedupe policy count、changed source-order count 等审计指标。
5. 给出 recommendations。

delta 的核心字段包括：

```json
{
  "fingerprint_changed": true,
  "dedupe_policy_changed": true,
  "source_order_changed": true,
  "included_source_count_delta": -1,
  "skipped_source_count_delta": 1,
  "char_count_delta": -50
}
```

这些字段能直接回答“数据变了没有、怎么变的、是否和去重策略有关”。

同一模块还包含 JSON、CSV、Markdown、HTML 四种输出。JSON 是机器读证据，CSV 适合表格审计，Markdown 适合提交说明，HTML 适合浏览器查看和截图归档。

### `scripts/compare_dataset_versions.py`

这是命令行入口。

示例：

```powershell
python -B scripts/compare_dataset_versions.py `
  datasets/demo-v353/raw `
  datasets/demo-v353/deduped `
  --name raw --name deduped `
  --baseline raw `
  --out-dir runs/dataset-version-comparison
```

它会打印：

- `version_count`
- baseline JSON 摘要
- summary JSON 摘要
- outputs 路径

这些 shell 输出让 CI 或人工运行时不用打开 HTML，也能快速确认比较结果。

### `src/minigpt/__init__.py`

本版把 dataset version comparison 的主要函数加入 facade 导出：

- `DatasetVersionSummary`
- `build_dataset_version_comparison`
- `render_dataset_version_comparison_html`
- `render_dataset_version_comparison_markdown`
- `write_dataset_version_comparison_outputs`

这样后续 project audit、maturity narrative 或 training portfolio 如果要消费 dataset comparison，不需要绕过包边界直接 import 文件。

### `tests/test_dataset_version_comparison.py`

测试覆盖四类风险：

- 单版本摘要是否能读出 snapshot 字段。
- baseline delta 是否能识别 fingerprint、dedupe policy、source order 和 char count 变化。
- 输出文件是否完整生成。
- HTML 是否正确 escape 用户可控的 dataset name / version name。
- facade export 是否指向同一实现。

这些测试保护的是数据治理契约，而不是 UI 外观。

## 运行证据

本版 smoke 构造了两个真实 prepared dataset：

- raw：3 个源文件全部进入 corpus。
- deduped：开启 exact-source dedupe，3 个源文件中 1 个重复源被跳过。

新 CLI 生成的比较摘要显示：

```text
version_count=2
fingerprint_count=2
dedupe_policy_count=2
changed_fingerprint_count=1
changed_dedupe_policy_count=1
changed_source_order_count=1
```

归档截图在 `d/353`：

- `d/353/图片/01-dataset-version-comparison.png`
- `d/353/图片/02-deduped-dataset-version-snapshot.png`
- `d/353/解释/说明.md`

第一张图证明横向比较报告可读；第二张图证明 deduped 单版本 snapshot 里确实存在 included/skipped/dedupe 证据。

## 一句话总结

v353 把 MiniGPT 的数据治理从“单个 dataset version 可追溯”推进到“多个 dataset version 可比较”，为后续真实训练和 benchmark 变化解释提供了数据边界证据。
