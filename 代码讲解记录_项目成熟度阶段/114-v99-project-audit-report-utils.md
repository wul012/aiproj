# 第九十九版代码讲解：Project Audit 接入 report_utils

## 本版目标

v99 的目标是继续做轻量、定向的质量收口：把 `project_audit.py` 里的通用报告 helper 迁移到 `report_utils`。

本版解决的问题是：project audit 是 release bundle 和 release gate 的上游证据，但它仍然保留了自己的一份 UTC 时间、JSON 写出、HTML 转义和 list/dict 归一化逻辑。v97 已经让 release bundle 接入公共工具，v99 则把它的上游审计层也接到同一套基础设施上。

本版明确不做：

- 不改变 project audit 的评分权重。
- 不改变 pass/warn/fail 判定。
- 不改变 request history summary 的审计要求。
- 不改变 Markdown/HTML 报告布局。
- 不拆分 `project_audit.py` 的大结构。
- 不修改 release bundle、release gate 或训练流程。

## 路线来源

这版延续 v83-v97 的 report-utils consolidation 路线。

前置链路是：

```text
v83 shared report utility
 -> v84-v95 training-scale/promoted-scale report migrations
 -> v96 generation quality report migration
 -> v97 release bundle report migration
 -> v98 README maturity summary cleanup
 -> v99 project audit report migration
```

v99 选择 project audit，而不是先拆 `server.py` 或 `registry.py`，原因是它更适合保守迁移：

- 重复 helper 明确。
- 测试覆盖已经存在。
- 位于发布治理链关键位置。
- 迁移后能和 release bundle 形成上下游一致性。

## 关键文件

- `src/minigpt/project_audit.py`
  - 删除本地 `utc_now`。
  - 删除本地 `_dict`。
  - 删除本地 `_list_of_dicts`。
  - 删除本地 `_e`。
  - 删除 `datetime/timezone` 和 `html` 直接导入。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`、`list_of_dicts`。

- `tests/test_project_audit.py`
  - 本版没有改测试文件。
  - 原有测试继续验证完整项目审计、request history warn、缺 model card 失败、输出产物和 HTML 转义。

- `README.md`
  - 当前版本更新为 v99。
  - 成熟度矩阵中的 release/maturity governance 和 shared report infrastructure 更新到 project audit migration。
  - 增加 v99 tag 和 `c/99` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `114-v99-project-audit-report-utils.md` 索引。
  - 把当前阶段基线更新到 v99。

- `c/99/解释/说明.md`
  - 说明本版截图、smoke、结构检查和 tag 的证据含义。

## 核心迁移点

迁移前，project audit 自己实现：

```python
utc_now()
write_project_audit_json()
_dict()
_list_of_dicts()
_e()
```

迁移后，这些语义来自：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)
```

`write_project_audit_json()` 变成：

```python
def write_project_audit_json(audit: dict[str, Any], path: str | Path) -> None:
    write_json_payload(audit, path)
```

这让 project audit 的 JSON 输出行为和其他 report-utils 迁移模块保持一致。

## 保留本地 helper 的原因

本版没有把所有 helper 都搬走。

这些函数保留在 `project_audit.py`：

- `_string_list`
- `_md`
- `_fmt`
- `_fmt_delta`
- `_fmt_any`
- `_rank_label`
- `_generation_quality_label`

原因是它们不只是通用工具，而是 project audit 的显示语义。

例如 `_string_list` 会过滤空字符串，适合 recommendations/warnings 的展示；`_rank_label` 把空 rank 显示为 `unranked`；`_generation_quality_label` 把状态和 case 数合并成审计表格里的可读字段。把这些硬迁到公共层会让 `report_utils` 变成业务语义仓库，反而降低边界清晰度。

## 数据结构和字段语义

project audit 的主要输出仍然是：

- `summary`
  - 记录 `overall_status`、`score_percent`、pass/warn/fail 数量、ready run 数量、request history 状态。

- `checks`
  - 每个审计检查包含 `id`、`title`、`status`、`detail`。
  - 这些字段决定 release bundle 和 release gate 后续如何理解项目状态。

- `request_history_context`
  - 从 request history summary 里提取状态、记录数、错误率和最近时间。

- `runs`
  - 展示 registry/model card 中每个 run 的可审计状态。

- `recommendations`
  - 根据失败或 warning 检查给出下一步行动。

v99 没有改变这些字段的结构和含义，只改变它们写出和渲染时使用的基础 helper。

## 运行流程

project audit 的运行链路仍然是：

```text
registry.json
 -> optional model_card.json
 -> optional request_history_summary.json
 -> build_project_audit()
 -> project_audit.json
 -> project_audit.md
 -> project_audit.html
```

v99 只改变输出阶段的底层工具：

- `generated_at` 使用公共 `utc_now`。
- JSON 写出使用公共 `write_json_payload`。
- HTML 转义使用公共 `html_escape`。
- dict/list 归一化使用公共 `as_dict` 和 `list_of_dicts`。

## 测试覆盖

本版使用原有 project audit 测试作为回归保护。

关键覆盖包括：

- 完整 registry + model card + request history summary 时，审计结果仍然是 `pass`。
- request history summary 为 watch 时，审计结果仍然是 `warn`。
- 缺 model card / experiment card 时，审计结果仍然是 `fail`，并保留推荐动作。
- 输出函数仍然写出 JSON、Markdown 和 HTML。
- HTML 标题和 run 文本仍然正确转义，防止报告注入。

同时跑 `tests.test_report_utils`，确保公共工具本身行为仍然稳定。

## 证据闭环

v99 的证据放在 `c/99`：

- 单测截图证明行为回归通过。
- complete smoke 证明完整证据输入仍然通过审计。
- missing model-card smoke 证明失败边界仍然保留。
- structure check 证明私有 helper 已移除，公共 helper 已接入。
- Playwright 截图证明 HTML 报告能被真实 Chrome 打开。
- docs check 证明 README、阶段索引、归档说明和讲解文件互相对齐。

## 一句话总结

v99 把 project audit 接入公共报告基础设施，让发布治理链的审计上游和 release bundle 下游共享同一套基础工具，同时保持审计策略不变。
