# 第一百零五版代码讲解：Data Quality 接入 report_utils

## 本版目标

v105 的目标是把 `data_quality.py` 接入 `report_utils`，让数据质量证据也使用公共报告基础工具。

它解决的问题是：v104 已经让 data preparation 复用公共 JSON 写出、UTC 时间、HTML 转义和 dict 归一化工具，但 `dataset_quality.json` 和 `dataset_quality.svg` 仍然由 `data_quality.py` 自己处理 JSON 写出和 HTML/SVG 转义。v105 把这层也接入公共基础设施。

本版明确不做：

- 不改变数据质量判断规则。
- 不改变 `DatasetQualityIssue` 字段结构。
- 不改变 `status`、`warning_count`、`issue_count`、`duplicate_line_count` 的计算方式。
- 不改变 duplicate source 检测。
- 不改变 repeated line 检测。
- 不改变 fingerprint 计算。
- 不改变 dataset quality SVG 布局。
- 不改 data preparation、run manifest、dataset card、experiment card、model card、project audit、release bundle 或 release gate。

## 路线来源

v105 延续 report-utils consolidation 路线。

相关治理链路是：

```text
prepared dataset
 -> data quality report
 -> data preparation outputs
 -> run manifest
 -> dataset card
 -> experiment card
 -> model card
 -> project audit
 -> release bundle
 -> release gate
```

v104 把 data preparation 接入公共工具。
v105 继续把 data preparation 调用的 data quality 证据层接入公共工具。

这样 dataset quality、prepared corpus、训练复现清单、数据说明、单 run 说明、模型说明、项目审计和发布总包开始共享同一套基础写出和转义能力。

## 关键文件

- `src/minigpt/data_quality.py`
  - 删除 `html` 和 `json` 直接导入。
  - 引入 `report_utils.write_json_payload` 和 `report_utils.html_escape`。
  - `write_dataset_quality_json()` 改为调用公共 JSON 写出。
  - 删除本地 `_e`。
  - SVG 文本转义继续通过 `_e` 别名完成，但实现来自公共 `html_escape`。

- `tests/test_data_quality.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖 SHA-256、重复源、重复行、pass/warn 状态和 JSON/SVG 输出。

- `README.md`
  - 当前版本更新到 v105。
  - shared report infrastructure 更新到 data quality migration。
  - 增加 v105 tag 和 `c/105` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `120-v105-data-quality-report-utils.md` 索引。
  - 当前阶段基线更新到 v105。

- `c/105/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，data quality 自己实现：

```python
write_dataset_quality_json()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import html_escape as _e, write_json_payload
```

`write_dataset_quality_json()` 变成：

```python
def write_dataset_quality_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)
```

这让 dataset quality 的 JSON 输出行为和 data preparation、run manifest、dataset card、experiment card、model card、project audit、release bundle 保持一致。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `DatasetQualityIssue`
- `build_dataset_quality_report`
- `write_dataset_quality_svg`
- `sha256_text`
- `_find_duplicate_lines`
- `_clip`

这些函数表达的是 data quality 自己的质量检查语义。

例如：

- `DatasetQualityIssue` 是数据质量报告的 issue schema。
- `build_dataset_quality_report` 包含小数据集、低 unique ratio、空 source、tiny source、重复 source 和重复 line 的判断。
- `_find_duplicate_lines` 规定重复行最小长度和排序规则。
- `sha256_text` 是 dataset fingerprint 的稳定来源。
- `_clip` 是 SVG 文本截断规则。

如果把这些迁到 `report_utils`，公共层会开始承载 data-quality-specific 业务规则，边界反而变差。

## 数据结构和字段语义

data quality 的主要输出仍然包括：

- `schema_version`
  - 数据质量报告 schema 版本。

- `status`
  - 如果存在 warning 则为 `warn`，否则为 `pass`。

- `fingerprint` / `short_fingerprint`
  - 基于 prepared dataset 文本计算的 SHA-256。

- `char_count`、`line_count`、`unique_char_count`、`unique_char_ratio`
  - 语料规模和字符多样性信息。

- `source_count`
  - source file 数量。

- `issue_count`、`warning_count`、`duplicate_line_count`
  - issue 和 warning 汇总。

- `sources`
  - source path、char count、line count、sha256、duplicate_of。

- `issues`
  - severity、code、message、path、details。

v105 没有改变这些字段，只改变公共写出和转义工具。

## 运行流程

data quality 的流程仍然是：

```text
PreparedDataset
 -> build_dataset_quality_report()
 -> detect size / uniqueness / duplicate source / repeated line issues
 -> dataset_quality.json
 -> dataset_quality.svg
```

v105 改变的是：

- dataset quality JSON 使用公共 `write_json_payload`。
- dataset quality SVG 文本转义使用公共 `html_escape`。

## 测试覆盖

本版使用 `tests.test_data_quality` 做行为回归。

关键断言包括：

- `sha256_text("abc")` 仍然稳定。
- 重复 source 和重复 line 仍然触发 `duplicate_source` 和 `repeated_line`。
- 合理小语料在放宽阈值后仍然可以 `pass`。
- `write_dataset_quality_json()` 和 `write_dataset_quality_svg()` 仍然写出 JSON/SVG 两类产物。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v105 的证据放在 `c/105`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-data-quality-pass-smoke.png` 证明合理 corpus 仍然生成 pass status 和 JSON/SVG 输出。
- `03-data-quality-warn-smoke.png` 证明重复 source 和 repeated line warning 仍然可见。
- `04-data-quality-structure-check.png` 证明通用 helper 已迁移，data-quality-specific helper 保留。
- `05-playwright-data-quality-svg.png` 证明 dataset quality SVG 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、讲解索引和 v105 讲解文件互相对齐。

## 一句话总结

v105 把 data quality 接入公共报告基础设施，让数据质量证据、prepared corpus、训练复现清单、数据说明、单 run 说明、模型说明、项目审计和发布总包这条治理链共享同一套基础工具，同时保留质量检查自己的 issue schema、阈值和重复检测语义。
