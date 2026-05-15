# 第一百零七版代码讲解：Release Readiness Comparison 接入 report_utils

## 本版目标

v107 的目标是把 `release_readiness_comparison.py` 接入 `report_utils`，让跨版本发布就绪对比报告也使用公共报告基础工具。

它解决的问题是：v106 已经把单份 release readiness dashboard 接入公共 JSON 写出、UTC 时间、HTML 转义和 dict/list 归一化工具，但读取多份 `release_readiness.json` 做对比的 `release_readiness_comparison.py` 仍然保留自己的 `utc_now()`、JSON 写出、HTML 转义、dict/list helper 和一部分 CSV cell 处理。v107 把这些通用部分迁到公共层。

本版明确不做：

- 不改变 baseline override 规则。
- 不改变 `blocked`、`incomplete`、`review`、`ready` 的 status score 顺序。
- 不改变 `improved`、`regressed`、`panel-changed`、`same` 的 delta 判断。
- 不改变 panel change 的 `key:before->after` 格式。
- 不改变 audit score、missing artifact、fail panel、warn panel delta 计算。
- 不改变 recommendations 的优先级。
- 不改变 CSV、delta CSV、Markdown、HTML 输出结构。
- 不改变 release readiness dashboard 本身的生成逻辑。

## 路线来源

v107 延续 v106 的发布就绪治理链路。

相关链路是：

```text
release readiness dashboard
 -> release readiness comparison
 -> registry release readiness tracking
 -> maturity release readiness trend context
```

v106 迁移的是单份 dashboard。v107 迁移的是多份 dashboard 之间的比较层。

这样以后 release readiness dashboard 和 release readiness comparison 在报告写出、HTML 转义、UTC 时间、dict/list normalization 上共用同一套基础设施，而跨版本比较规则继续留在 comparison 模块内。

## 关键文件

- `src/minigpt/release_readiness_comparison.py`
  - 删除本地 `datetime/timezone` 和 `html` 依赖。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`、`csv_cell`。
  - `write_release_readiness_comparison_json()` 改为调用公共 JSON 写出。
  - 删除本地 `_dict()`、`_list_of_dicts()` 和 `_e()`。
  - `_csv_value()` 对普通标量复用公共 `csv_cell()`，但保留 list -> semicolon 的 comparison-specific 输出规则。

- `tests/test_release_readiness_comparison.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖 improvement、regression、baseline override、CSV/delta CSV/Markdown/HTML 输出和 HTML escape。

- `README.md`
  - 当前版本更新到 v107。
  - shared report infrastructure 更新到 v83-v107。
  - 增加 v107 tag 和 `c/107` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `122-v107-release-readiness-comparison-report-utils.md` 索引。
  - 当前阶段基线更新到 v107。

- `c/107/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，release readiness comparison 自己实现：

```python
utc_now()
write_release_readiness_comparison_json()
_dict()
_list_of_dicts()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)
```

JSON 写出变成：

```python
def write_release_readiness_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)
```

CSV 标量处理变成：

```python
def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(_string_list(value))
    return str(csv_cell(value))
```

这里刻意保留 list -> semicolon，因为 delta CSV 的 `changed_panels` 是给人扫读的列表字段；公共 `csv_cell()` 对 list 会输出 JSON 字符串，语义不完全相同。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `_row_from_report`
- `_delta_from_baseline`
- `_delta_status`
- `_delta_explanation`
- `status_delta_label`
- `_summary`
- `_recommendations`
- `_read_required_json`
- `_number_delta`
- `_html_row`
- `_html_delta`
- `_list_section`
- `_stat`
- `_style`
- `_markdown_table`
- `_string_list`
- `_csv_value`
- `_fmt`
- `_md`

这些函数表达的是 release readiness comparison 自己的业务语义。

例如：

- `_row_from_report` 把单份 readiness dashboard 压成可比较行。
- `_delta_from_baseline` 定义和 baseline 的状态、panel、audit、artifact、fail/warn 差异。
- `_delta_status` 定义 improved/regressed/panel-changed/same。
- `_delta_explanation` 把 delta 转成人能读懂的解释。
- `_recommendations` 根据 regression、improvement、blocked 和 panel change 选择建议。
- `_csv_value` 保留 `changed_panels` 的 semicolon 展示。

如果把这些迁到 `report_utils`，公共层会开始承载 release-readiness-comparison-specific 对比规则，边界会变差。

## 数据结构和字段语义

release readiness comparison 的主要输出仍然包括：

- `schema_version`
  - comparison report schema 版本。

- `title`
  - HTML/Markdown 报告标题。

- `generated_at`
  - 生成时间。v107 起来自公共 `utc_now()`。

- `baseline_path`
  - 当前比较使用的基线 `release_readiness.json`。

- `readiness_paths`
  - 所有参与比较的 readiness 报告路径。

- `summary`
  - 总览计数，包括 readiness 数量、baseline status、ready/review/blocked/incomplete 数量、improved/regressed 数量和 panel delta 数量。

- `rows`
  - 每份 readiness dashboard 的压缩行。
  - 包含 release name、readiness status、decision、gate/audit/request/maturity status、ready runs、missing artifacts、panel counts 和 `panel_statuses`。

- `deltas`
  - 非 baseline 报告相对 baseline 的变化。
  - 包含 status delta、delta status、audit score delta、missing artifact delta、fail/warn panel delta、changed panels 和 explanation。

- `recommendations`
  - 对 regression、improvement、blocked、panel-changed 或 stable 的行动建议。

v107 不改变这些字段，只改变公共写出、转义和归一化工具来源。

## 运行流程

release readiness comparison 的流程仍然是：

```text
release_readiness.json list
 -> optional baseline override
 -> read required JSON dashboards
 -> compress each dashboard into rows
 -> compute deltas from baseline
 -> summarize readiness and delta counts
 -> generate recommendations
 -> write JSON/CSV/delta CSV/Markdown/HTML outputs
```

v107 改变的是：

- `generated_at` 使用公共 `utc_now`。
- comparison JSON 使用公共 `write_json_payload`。
- HTML 文本转义使用公共 `html_escape`。
- dict/list normalization 使用公共 `as_dict` 和 `list_of_dicts`。
- CSV 标量 cell 使用公共 `csv_cell`。

## 测试覆盖

本版使用 `tests.test_release_readiness_comparison` 做行为回归。

关键断言包括：

- blocked -> ready 仍然得到 `delta_status=improved`。
- baseline override 后 ready -> blocked 仍然得到 `delta_status=regressed`。
- panel change 仍然记录为 `release_gate:fail->pass` 等格式。
- `write_release_readiness_comparison_outputs()` 仍然写出 JSON、CSV、delta CSV、Markdown、HTML 五类产物。
- HTML 渲染仍然转义 `<Comparison>` 和 `<baseline>`。
- Markdown 仍然保留原始 `<baseline>` 文本，符合原来的文本报告语义。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v107 的证据放在 `c/107`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-readiness-comparison-improved-smoke.png` 证明 blocked-to-ready 输入仍然生成 improved delta。
- `03-readiness-comparison-regressed-smoke.png` 证明 baseline override 后仍然生成 regressed delta。
- `04-readiness-comparison-structure-check.png` 证明通用 helper 已迁移，comparison-specific helper 保留。
- `05-playwright-readiness-comparison-html.png` 证明 comparison HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、阶段讲解索引和 v107 讲解互相对齐。

## 一句话总结

v107 把 release readiness comparison 接入公共报告基础设施，让发布就绪总览和跨版本发布质量对比共享同一套基础工具，同时保留 baseline、delta、recommendation 和输出布局的本地业务语义。
