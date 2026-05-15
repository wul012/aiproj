# 第一百零四版代码讲解：Data Preparation 接入 report_utils

## 本版目标

v104 的目标是把 `data_prep.py` 接入 `report_utils`，让数据准备链路也使用公共报告基础工具。

它解决的问题是：v103 已经让 run manifest 复用公共 JSON 写出、UTC 时间和 HTML 转义工具，但更上游的数据准备层仍然保留自己的 `_utc_now`、JSON 写出、HTML 转义和 `_dict`。v104 把 prepared corpus、dataset report、dataset version 这层也接入公共基础设施。

本版明确不做：

- 不改变 source discovery 规则。
- 不改变文本归一化规则。
- 不改变 prepared corpus 内容生成规则。
- 不改变 dataset report 字段结构。
- 不改变 dataset version manifest 字段结构。
- 不改变 dataset quality 的调用和交接方式。
- 不改变 dataset report SVG 或 dataset version HTML 布局。
- 不改 run manifest、dataset card、experiment card、model card、project audit、release bundle 或 release gate。

## 路线来源

v104 延续 report-utils consolidation 路线。

相关治理链路是：

```text
raw text sources
 -> prepared corpus
 -> dataset report / dataset quality / dataset version
 -> run manifest
 -> dataset card
 -> experiment card
 -> model card
 -> project audit
 -> release bundle
 -> release gate
```

v103 把 run manifest 接入公共工具。
v104 继续把 run manifest 的上游 data preparation 接入公共工具。

这样从原始文本准备、训练复现清单、数据说明、单 run 说明、模型说明、项目审计和发布总包，开始共享同一套基础写出和转义能力。

## 关键文件

- `src/minigpt/data_prep.py`
  - 删除 `datetime/timezone` 和 `html` 直接导入。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`。
  - `write_dataset_report_json()` 改为调用公共 JSON 写出。
  - `write_dataset_version_json()` 改为调用公共 JSON 写出。
  - dataset report SVG 的文件名转义改为公共 `html_escape`。
  - `_utc_now()` 保留为本模块兼容入口，但内部委托给公共 `utc_now()`。
  - 删除本地 `_dict` 和 `_e`。

- `tests/test_data_prep.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖文本归一化、文件发现、prepared dataset、dataset report、dataset version 和完整输出。

- `README.md`
  - 当前版本更新到 v104。
  - shared report infrastructure 更新到 data preparation migration。
  - 增加 v104 tag 和 `c/104` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `119-v104-data-prep-report-utils.md` 索引。
  - 当前阶段基线更新到 v104。

- `c/104/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，data preparation 自己实现：

```python
_utc_now()
write_dataset_report_json()
write_dataset_version_json()
_dict()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import as_dict as _dict, html_escape as _e, utc_now, write_json_payload
```

`write_dataset_report_json()` 和 `write_dataset_version_json()` 变成公共 JSON 写出：

```python
def write_dataset_report_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)

def write_dataset_version_json(manifest: dict[str, Any], path: str | Path) -> None:
    write_json_payload(manifest, path)
```

`_utc_now()` 仍然留在本模块，但只作为兼容包装：

```python
def _utc_now() -> str:
    return utc_now()
```

这样外部语义不变，公共时间格式和 JSON 写出格式与 run manifest、dataset card、experiment card 保持一致。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `SourceFileSummary`
- `PreparedDataset`
- `discover_text_files`
- `normalize_text`
- `build_prepared_dataset`
- `build_dataset_report`
- `build_dataset_version_manifest`
- `write_prepared_dataset`
- `write_dataset_report_svg`
- `render_dataset_version_html`
- `write_dataset_version_html`
- `_summarize_source`
- `_clip`
- `_sha256_text`
- `_stat`
- `_html_style`

这些函数表达的是 data preparation 自己的语料准备和展示语义。

例如：

- `discover_text_files` 决定目录是否递归、只读 `.txt` 文件、如何去重排序。
- `normalize_text` 决定换行和行尾空白如何清理。
- `build_prepared_dataset` 决定多源文本之间用空行分隔，并在末尾保留换行。
- `_sha256_text` 决定 source summary 和 corpus fingerprint。
- `write_dataset_report_svg` 是 source char count 可视化。
- `render_dataset_version_html` 是 dataset version 给浏览器查看的证据页面。

如果把这些迁到 `report_utils`，公共层会开始承载 data-prep-specific 业务规则，边界反而变差。

## 数据结构和字段语义

data preparation 的主要输出仍然包括：

- `corpus.txt`
  - 合并后的训练文本，是后续训练和 run manifest 的真实数据输入。

- `dataset_report.json`
  - `source_count`、`char_count`、`line_count`、`unique_char_count`、`token_count_char_estimate`、`fingerprint`、`output_text`、`sources`、`most_common_chars`。

- `dataset_report.svg`
  - source-level 字符数可视化，作为人工检查数据来源规模的浏览器证据。

- `dataset_quality.json`
  - 来自 `data_quality` 模块，记录 warning、issue、duplicate source、repeated line 等质量信息。

- `dataset_quality.svg`
  - 数据质量可视化。

- `dataset_version.json`
  - 数据集 name/version/id、created_at、preparation、stats、quality、outputs、sources。

- `dataset_version.html`
  - dataset version 的浏览器页面，展示 identity、fingerprint、quality、outputs 和 sources。

v104 没有改变这些字段，只改变公共写出和转义工具。

## 运行流程

data preparation 的流程仍然是：

```text
source files/directories
 -> discover_text_files()
 -> normalize_text()
 -> build_prepared_dataset()
 -> write_prepared_dataset()
 -> corpus.txt
 -> dataset_report.json/svg
 -> dataset_quality.json/svg
 -> dataset_version.json/html
```

v104 改变的是：

- dataset version 的 `created_at` 间接使用公共 `utc_now`。
- dataset report JSON 使用公共 `write_json_payload`。
- dataset version JSON 使用公共 `write_json_payload`。
- SVG/HTML 文本转义使用公共 `html_escape`。
- dict 归一化使用公共 `as_dict`。

## 测试覆盖

本版使用 `tests.test_data_prep` 做行为回归。

关键断言包括：

- `normalize_text()` 仍然清理 CRLF、行尾空白和多余结尾换行。
- `discover_text_files()` 仍然递归发现 `.txt` 并忽略非 txt。
- `build_prepared_dataset()` 仍然合并多文件文本并生成 source summary 和 fingerprint。
- `build_dataset_report()` 仍然输出 common chars、fingerprint 和 output_text。
- `build_dataset_version_manifest()` 仍然记录 dataset id、short fingerprint、quality status 和 outputs。
- `write_prepared_dataset()` 仍然写出 corpus、report JSON/SVG、quality JSON/SVG、dataset version JSON/HTML。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v104 的证据放在 `c/104`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-data-prep-complete-smoke.png` 证明完整数据准备能生成 corpus、report、quality、version JSON/HTML。
- `03-data-prep-nonrecursive-smoke.png` 证明 non-recursive source discovery 仍然排除 nested `.txt` 文件。
- `04-data-prep-structure-check.png` 证明通用 helper 已迁移，data-prep-specific helper 保留。
- `05-playwright-dataset-version-html.png` 证明 dataset version HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、讲解索引和 v104 讲解文件互相对齐。

## 一句话总结

v104 把 data preparation 接入公共报告基础设施，让 prepared corpus、训练复现清单、数据说明、单 run 说明、模型说明、项目审计和发布总包这条治理链共享同一套基础工具，同时保留数据准备自己的 source discovery、文本归一化、fingerprint 和展示语义。
