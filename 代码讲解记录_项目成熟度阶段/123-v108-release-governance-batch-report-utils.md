# 第一百零八版代码讲解：Release Governance 批量接入 report_utils

## 本版目标

v108 的目标是把三个位于同一条发布治理链上的模块合并迁移到 `report_utils`：

- `release_gate.py`
- `release_gate_comparison.py`
- `request_history_summary.py`

它解决的问题是：v83-v107 已经逐模块验证了 `report_utils` 的边界和稳定性。继续“一个小 helper 迁移发一版”会让版本节奏偏碎，所以 v108 改成同类低风险迁移合并发布。

本版明确不做：

- 不改变 release gate 的 policy profile、threshold、warning/fail 判断。
- 不改变 strict/review/standard/legacy profile 的语义。
- 不改变 release gate profile comparison 的 baseline profile、decision delta、check delta 和 recommendation。
- 不改变 request history summary 的 status 统计、endpoint/checkpoint 统计、最近请求列表和 recommendation。
- 不改变 Markdown/HTML 的布局结构。
- 不迁移大模块 `server.py`、`registry.py`、`playground.py`。
- 不把发布治理业务规则放进 `report_utils`。

## 路线来源

v108 延续 report-utils consolidation 路线，但节奏发生变化：

```text
v83-v107: one-module migration, proving the abstraction
v108: batched related migration, reducing version fragmentation
```

本版选择的三个模块都属于发布治理链：

```text
request history summary
 -> project audit / release bundle
 -> release gate
 -> release gate profile comparison
 -> release readiness dashboard
 -> release readiness comparison
```

`request_history_summary.py` 是 release gate 的上游证据之一；`release_gate.py` 是发布准入判断；`release_gate_comparison.py` 比较同一 bundle 在不同 gate profile 下的结果。这三者迁移类型一致，测试覆盖也比较明确，所以适合作为合并批次。

## 关键文件

- `src/minigpt/release_gate.py`
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`。
  - 删除本地 `utc_now()`、`_dict()`、`_list_of_dicts()`、`_e()`。
  - `write_release_gate_json()` 改为调用公共 JSON 写出。
  - 保留 release gate policy、check builder、recommendation、score label 和 display formatting。

- `src/minigpt/release_gate_comparison.py`
  - 引入 `report_utils.write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`、`csv_cell`。
  - 删除本地 `_dict()`、`_list_of_dicts()`、`_e()`。
  - JSON 写出改为公共 `write_json_payload`。
  - `_csv_value()` 对普通标量复用 `csv_cell()`，但继续保留 list -> semicolon 的 profile delta 展示规则。

- `src/minigpt/request_history_summary.py`
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`。
  - 删除本地 `utc_now()`、`_dict()`、`_list_of_dicts()`、`_e()`。
  - JSON 写出改为公共 `write_json_payload`。
  - 保留 request-history-specific CSV rate formatting 和 string list 语义。

- `tests/test_release_gate.py`
  - 原测试继续覆盖 policy profiles、strict/review/legacy、warning/fail、request-history audit check、输出文件和 HTML escape。

- `tests/test_release_gate_comparison.py`
  - 原测试继续覆盖 profile matrix、多 bundle、baseline profile、legacy profile、delta CSV、Markdown/HTML 和 HTML escape。

- `tests/test_request_history_summary.py`
  - 原测试继续覆盖状态统计、checkpoint 统计、invalid rows、输出文件、CSV、Markdown 和 HTML escape。

- `README.md`、`代码讲解记录_项目成熟度阶段/README.md`、`c/108/解释/说明.md`
  - 说明 v108 是合并批次，而不是单模块迁移。

## 核心迁移点

三个模块都复用了相同的公共工具模式：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)
```

`release_gate_comparison.py` 额外使用：

```python
from minigpt.report_utils import csv_cell
```

JSON 写出统一变成：

```python
def write_xxx_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)
```

HTML 转义统一走公共 `html_escape`，但 HTML 的页面结构、表格列、CSS 和业务文案仍由各模块自己维护。

## 为什么不全部迁走

本版保留了大量本地 helper，因为它们表达发布治理语义，不是通用 report helper。

`release_gate.py` 保留：

- `resolve_release_gate_policy`
- `_build_checks`
- `_build_summary`
- `_required_audit_checks_status`
- `_request_history_summary_status`
- `_recommendations`
- `_score_label`
- `_fmt_any`

这些函数决定 gate 是否 pass/warn/fail，属于发布准入规则。

`release_gate_comparison.py` 保留：

- `_row_from_gate`
- `_build_profile_deltas`
- `_delta_status`
- `_delta_explanation`
- `_comparison_recommendations`
- `_csv_value`

这些函数决定不同 profile 的差异如何解释，属于 profile comparison 规则。

`request_history_summary.py` 保留：

- `_count`
- `_checkpoint_counts`
- `_summary_status`
- `_recommendations`
- `_csv_value`
- `_checkpoint_label`

这些函数决定 request history 是否 clean/review，以及 CSV rate 如何展示，属于请求历史稳定性统计规则。

如果把这些函数迁到 `report_utils`，公共层会变成“发布治理业务层”，这和 v83 以来的公共层边界相冲突。

## 数据结构和字段语义

### release gate

主要输出仍然包括：

- `policy`
  - policy profile、audit score、ready runs、generation quality 和 request-history summary 要求。

- `summary`
  - gate status、decision、release status、audit status、ready runs、missing artifacts、pass/warn/fail count。

- `checks`
  - 每条准入检查的 id、title、status、detail。

- `recommendations`
  - 根据 gate 状态和失败检查生成的行动建议。

### release gate profile comparison

主要输出仍然包括：

- `policy_profiles`
  - 参与比较的 profile 列表。

- `baseline_profile`
  - 作为 baseline 的 profile。

- `rows`
  - 每个 bundle/profile 的 gate 结果。

- `deltas`
  - 相对 baseline profile 的 decision/check/policy 差异。

- `recommendations`
  - 关于 stricter profile、legacy profile、blocked profile 的建议。

### request history summary

主要输出仍然包括：

- `summary`
  - status、total/invalid count、ok/timeout/bad_request/error count、rate、stream/pair/artifact count、unique checkpoint count。

- `status_counts`
  - 按请求状态统计。

- `endpoint_counts`
  - 按 endpoint 统计。

- `checkpoint_counts`
  - 按 checkpoint 统计。

- `recent_requests`
  - 最近请求记录。

- `recommendations`
  - 根据 error、timeout、bad request、invalid record 生成的建议。

v108 不改变这些字段，只改变公共工具来源。

## 运行流程

v108 后三条链路仍然保持原流程：

```text
release_bundle.json
 -> build_release_gate()
 -> gate_report.json/md/html
```

```text
release_bundle.json + policy profiles
 -> build_release_gate_profile_comparison()
 -> profile comparison json/csv/delta csv/md/html
```

```text
inference_requests.jsonl
 -> build_request_history_summary()
 -> request history summary json/csv/md/html
```

公共层只负责：

- JSON 写出。
- UTC 时间戳。
- HTML 转义。
- dict/list normalization。
- 部分 CSV 标量格式化。

## 测试覆盖

本版跑以下聚焦测试：

- `tests.test_release_gate`
- `tests.test_release_gate_comparison`
- `tests.test_request_history_summary`
- `tests.test_report_utils`

它们合计覆盖：

- gate pass/warn/fail。
- strict/review/legacy policy。
- request-history audit check required/optional。
- profile matrix 和 delta explanation。
- request history status/count/rate/checkpoint 统计。
- JSON/CSV/Markdown/HTML 输出存在。
- HTML escape 防注入。

同时跑全量 `python -m unittest discover -s tests`，确保批量迁移没有影响其他治理链路。

## 证据闭环

v108 的证据放在 `c/108`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-release-gate-batch-smoke.png` 证明 release gate pass/fail 和 profile comparison delta 仍然正常。
- `03-request-history-summary-smoke.png` 证明 request history summary pass/review、输出文件和 recommendations 仍然正常。
- `04-release-governance-batch-structure-check.png` 证明三模块通用 helper 已迁移，业务 helper 保留。
- `05-playwright-release-gate-comparison-html.png` 证明 release gate comparison HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、阶段讲解索引和 v108 讲解互相对齐。

## 一句话总结

v108 把 release gate、gate profile comparison 和 request history summary 合并接入公共报告基础设施，让项目从“逐模块验证 report_utils”推进到“批量收束同类重复 helper”，同时保留发布治理各模块自己的 policy、delta、summary 和展示语义。
