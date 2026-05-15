# 第一百零二版代码讲解：Dataset Card 接入 report_utils

## 本版目标

v102 的目标是把 `dataset_card.py` 接入 `report_utils`，让数据卡也使用公共报告基础工具。

它解决的问题是：v101 已经让 experiment card 复用公共 JSON 写出、UTC 时间、HTML 转义和 dict 归一化工具，但更上游的 dataset card 仍然保留自己的 `utc_now`、JSON 写出、HTML 转义和 `_dict`。v102 把数据说明层也接入公共基础设施。

本版明确不做：

- 不改变 dataset card 字段结构。
- 不改变 dataset identity、summary、provenance、quality、artifact、recommendation、warning 的生成策略。
- 不改变 dataset quality 的判断规则。
- 不改变 Markdown/HTML 布局。
- 不改 experiment card、model card、project audit、release bundle 或 release gate。
- 不把 dataset-card-specific 的展示规则塞进公共工具层。

## 路线来源

v102 延续 report-utils consolidation 路线。

相关治理链路是：

```text
prepared dataset evidence
 -> dataset card
 -> experiment card
 -> model card
 -> project audit
 -> release bundle
 -> release gate
```

v101 把 experiment card 接入公共工具。
v102 继续把 experiment card 的上游 dataset card 接入公共工具。

这样从数据说明、单 run 说明、模型说明、项目审计到发布总包，开始共享同一套基础写出和转义能力。

## 关键文件

- `src/minigpt/dataset_card.py`
  - 删除本地 `utc_now`。
  - 删除本地 `_dict`。
  - 删除本地 `_e`。
  - 删除 `datetime/timezone` 和 `html` 直接导入。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`。

- `tests/test_dataset_card.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖完整数据卡、质量 warning、输出产物、HTML escaping 和缺失输入 warning。

- `README.md`
  - 当前版本更新到 v102。
  - shared report infrastructure 更新到 dataset card migration。
  - 增加 v102 tag 和 `c/102` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `117-v102-dataset-card-report-utils.md` 索引。
  - 当前阶段基线更新到 v102。

- `c/102/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，dataset card 自己实现：

```python
utc_now()
write_dataset_card_json()
_dict()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    utc_now,
    write_json_payload,
)
```

`write_dataset_card_json()` 变成：

```python
def write_dataset_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)
```

这让 dataset card 的 JSON 输出行为和 experiment card、model card、project audit、release bundle 保持一致。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `_pick`
- `_list_of_dicts`
- `_string_list`
- `_md`
- `_path_exists`
- `_first_number`
- `_key_value_section`
- `_quality_section_html`
- `_artifact_section_html`
- `_list_section`
- `_markdown_table`
- `_stat`
- `_style`

这些函数表达的是 dataset card 自己的数据清洗和展示语义。

例如：

- `_string_list` 会过滤空字符串，适合 intended use、limitations、issue codes、warnings 这类数据卡列表。
- `_md` 把 `None` 显示为 `missing`，这是数据卡 Markdown 表格里的缺失值表达。
- `_list_of_dicts` 当前返回原始 dict item，用于保留 artifacts 和 issue rows 的字段。
- `_quality_section_html` 和 `_artifact_section_html` 是数据质量和数据产物的 HTML 展示规则。

如果把这些迁到 `report_utils`，公共层会开始承载 dataset-card-specific 业务规则，边界反而变差。

## 数据结构和字段语义

dataset card 的主要输出仍然包括：

- `dataset`
  - 数据集名称、版本、id、description。

- `summary`
  - readiness status、quality status、source count、char count、line count、unique char ratio、fingerprint、warning/issue count、输出文本路径和证据文件存在性。

- `intended_use`
  - 说明这份数据卡服务于 MiniGPT 学习、对比和可复现实验审查。

- `limitations`
  - 说明小语料、轻量质量检查、授权和安全边界。

- `provenance`
  - source roots、recursive、output name、output text 和 source-level hash/size 信息。

- `quality`
  - status、warning count、issue count、duplicate line count、issue codes、severity counts 和最多 24 条 issue 明细。

- `artifacts`
  - dataset_version、dataset_report、dataset_quality、corpus、dataset_card JSON/Markdown/HTML 等产物状态。

- `recommendations`
  - 根据 readiness、缺失 manifest、缺失 quality report、issue codes、corpus 路径和 warnings 生成建议。

- `warnings`
  - 记录缺失或无效输入文件。

v102 没有改变这些字段，只改变公共写出和转义工具。

## 运行流程

dataset card 的流程仍然是：

```text
prepared dataset directory
 -> dataset_version.json
 -> dataset_report.json
 -> dataset_quality.json
 -> build_dataset_card()
 -> dataset_card.json
 -> dataset_card.md
 -> dataset_card.html
```

v102 改变的是：

- `generated_at` 使用公共 `utc_now`。
- JSON 写出使用公共 `write_json_payload`。
- HTML 转义使用公共 `html_escape`。
- dict 归一化使用公共 `as_dict`。

## 测试覆盖

本版使用 `tests.test_dataset_card` 做行为回归。

关键断言包括：

- 完整 prepared dataset 能生成 `demo-zh@v1`、ready status、pass quality、fingerprint 和 provenance。
- 重复数据源会进入 review/warn，并保留 `duplicate_source`、`repeated_line` 等 issue codes。
- 输出函数仍然生成 JSON、Markdown、HTML 三类产物，并把 dataset card 自身 artifacts 标记为存在。
- HTML 标题和 description 仍然正确 escaping。
- 缺失输入目录仍然生成 warnings 和补证据建议。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v102 的证据放在 `c/102`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-dataset-card-complete-smoke.png` 证明完整 prepared dataset evidence 能生成 ready dataset-card 输出。
- `03-dataset-card-missing-inputs-smoke.png` 证明 sparse dataset directory 仍会保留 warnings/recommendations。
- `04-dataset-card-structure-check.png` 证明通用 helper 已迁移，dataset-card-specific helper 保留。
- `05-playwright-dataset-card-html.png` 证明 HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、讲解索引和 v102 讲解文件互相对齐。

## 一句话总结

v102 把 dataset card 接入公共报告基础设施，让数据说明、单 run 说明、模型说明、项目审计和发布总包这条治理链共享同一套基础工具，同时保留数据卡自己的质量、缺失值和展示语义。
