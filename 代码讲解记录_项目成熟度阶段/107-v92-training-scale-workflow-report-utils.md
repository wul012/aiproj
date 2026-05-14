# v92 training scale workflow report utility migration

## 本版目标

v92 的目标是继续轻量、定向的质量优化，把 v75 引入的 `training_scale_workflow.py` 迁移到公共 `report_utils.py` 上。

v91 已经让 `plan -> gate -> run -> comparison -> decision` 五层训练规模证据共享报告基础设施。v92 继续向外层推进，把负责串联这五层的 consolidated workflow 也接入同一套公共工具。

本版解决的问题是：`training_scale_workflow.py` 是训练规模治理链的总入口，它会调用 planner、gated run、comparison 和 decision，并输出自己的 workflow JSON/CSV/Markdown/HTML。但在 v92 之前，它仍然保留私有 `utc_now`、`_dict`、`_list_of_dicts`、`_string_list`、`_md`、`_e` 和 JSON writer。这会让总入口 evidence 和它内部消费的五层 evidence 在基础报告行为上不一致。

v92 的结果是：

```text
plan -> gate -> run -> comparison -> decision -> workflow
```

这六层训练规模证据开始共享同一套报告基础设施。

## 本版明确不做什么

v92 不改 workflow 业务策略。

下面这些行为保持不变：

- 默认 profiles 仍然是 `review` 和 `standard`。
- `baseline_profile` 必须属于 profiles。
- duplicate profiles 仍然抛出 `ValueError`。
- workflow 仍然先生成 plan，再按 profile 运行 gated run。
- comparison 仍然以指定 baseline 比较多个 profile。
- decision 仍然由 `build_training_scale_run_decision` 产生。
- `decision_require_gate_pass`、`decision_require_batch_started`、`allow_warn`、`allow_fail` 的语义不变。
- workflow CSV 仍然是 per-profile 多行摘要。
- HTML 的 profile runs、execute command、artifact links 不重写结构。

本版只迁移报告基础 helper，不合并 workflow 和下游模块，也不改变执行候选选择策略。

## 来自哪条路线

v83 新增 `report_utils.py`。

v87-v91 已经把原始 training scale 链路的五层接入公共工具：

```text
v70 training scale plan
 -> v71 training scale gate
 -> v72 gated training scale run
 -> v73 training scale run comparison
 -> v74 training scale run decision
```

v92 迁移的是 v75：

```text
v75 consolidated training scale workflow
```

这说明公共报告基础层不只适用于单个 evidence report，也能服务一个串联多个 evidence report 的总入口。

## 关键文件

`src/minigpt/training_scale_workflow.py`

这是本版核心迁移文件。它继续负责把 planning、profile gated runs、comparison 和 decision 串成一个 workflow，并写出 `training_scale_workflow.json`、CSV、Markdown 和 HTML。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用它已有的：

```text
as_dict
html_escape
list_of_dicts
markdown_cell
string_list
utc_now
write_json_payload
```

`tests/test_training_scale_workflow.py`

这是 workflow 业务测试。它保护 review/standard profile 链路、strict decision blocked 链路、duplicate/missing baseline 错误、HTML escaping 和输出可读性。

`tests/test_report_utils.py`

这是公共层测试，继续保护 JSON/CSV 写出、command display、Markdown/HTML 转义和 list/dict 归一化。

`scripts/run_training_scale_workflow.py`

这是 workflow CLI 入口。本版不改参数，只用它做 smoke 证明迁移后 workflow 仍能生成 plan、runs、comparison、decision 和 workflow 总览产物。

`代码讲解记录_项目成熟度阶段/107-v92-training-scale-workflow-report-utils.md`

这是本讲解文件，用来解释 v92 为什么属于收口型优化，以及它和 v91 的关系。

`c/92/`

这是 v92 的运行截图和解释归档。它保存 tests、workflow smoke、strict smoke、结构检查、Playwright HTML 截图和文档检查。

## 迁移前的重复点

迁移前，`training_scale_workflow.py` 自己维护了：

```text
utc_now
_list_of_dicts
_string_list
_dict
_md
_e
```

同时 workflow JSON 写出也由本模块手写：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

这些工具和 `report_utils.py` 已有能力重复。workflow 是上层总入口，保留私有 helper 会让它和 plan/gate/run/comparison/decision 这些下游模块的基础行为不一致。

## 迁移后的引入关系

v92 让 `training_scale_workflow.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

和前几版一样，保留 `_dict`、`_md`、`_e` 等旧别名，是为了让模板结构尽量不变。迁移目标是减少重复工具，而不是重写 Markdown/HTML。

## JSON 输出

`write_training_scale_workflow_json` 改为：

```text
write_json_payload(report, path)
```

`training_scale_workflow.json` 是 workflow 的机器可读总览证据。它包含：

- plan summary 和 plan outputs。
- 每个 profile 的 run summary。
- comparison summary 和 comparison outputs。
- decision summary 和 decision outputs。
- execute command text。
- workflow summary。
- recommendations。

这个 JSON 的上游和下游都很清楚：它汇总 v70-v74 的产物，同时给 v76 controlled handoff 提供更高层的执行决策上下文。

## CSV 输出

`training_scale_workflow.csv` 是 per-profile 多行摘要，不是单行 summary。

因此本版没有强行使用 `report_utils.write_csv_row`。它仍然保留本地 `csv.DictWriter`，每个 profile 写一行：

```text
profile
status
allowed
gate_status
batch_status
readiness_score
run_json
decision_status
selected_profile
recommended_action
```

这和 v91 的原则一致：公共工具负责重复基础行为，业务表格结构仍留在当前模块。

## Markdown 和 HTML 渲染

Markdown 报告仍然包含：

- generated time
- scale tier
- char count
- profiles
- decision status
- selected profile
- recommended action
- runs table
- execute command
- artifact links
- recommendations

HTML 报告仍然包含：

- stats cards
- profile runs table
- decision execute command
- workflow artifact links
- recommendations

变化在于 Markdown cell、HTML escape、list/dict normalization 改为公共工具：

```text
markdown_cell
html_escape
list_of_dicts
string_list
as_dict
```

这样 workflow 和下游 evidence 的转义、空值处理、list/dict 防御行为保持一致。

## 核心数据结构

`run_training_scale_workflow` 返回的 report 仍然保持原结构。

顶层字段包括：

```text
schema_version
title
generated_at
project_root
out_root
sources
profiles
baseline_profile
execute
compare
allow_warn
allow_fail
decision_min_readiness
decision_require_gate_pass
decision_require_batch_started
plan_summary
plan_outputs
runs
comparison_summary
comparison_outputs
decision_summary
decision_outputs
execute_command_text
summary
recommendations
```

`runs` 每行代表一个 profile 的 gated run：

```text
profile
status
allowed
gate_status
gate_pass_count
gate_warn_count
gate_fail_count
batch_status
comparison_status
blocked_reason
outputs
gate_outputs
batch_outputs
readiness_score
comparison_status
```

`summary` 是 workflow 的总判断：

```text
scale_tier
char_count
variant_count
profile_count
allowed_count
blocked_count
comparison_baseline
decision_status
recommended_action
selected_profile
selected_gate_status
selected_batch_status
selected_readiness_score
```

## 运行流程

workflow 的主流程保持不变：

```text
resolve profiles
 -> build_training_scale_plan
 -> write plan outputs
 -> for each profile: run_training_scale_plan
 -> build_training_scale_run_comparison
 -> write comparison outputs
 -> build_training_scale_run_decision
 -> write decision outputs
 -> build workflow summary
 -> write workflow outputs
```

这里的关键是：workflow 自己不重新实现 plan/gate/run/comparison/decision 的业务规则。它只负责把这些产物按顺序串起来，并把结果整理成一个总览 evidence。

v92 没有改变这条链路，只改变 workflow 自己写报告时使用的基础工具。

## 为什么这条建议合理

这次推进仍然符合“收口型优化，不做架构级重构”的判断。

原因是：

- workflow 是 plan/gate/run/comparison/decision 的外层总入口，迁移收益明确。
- v91 已经让五层下游证据共享公共工具，v92 让总入口也对齐。
- 测试可以覆盖正常 review/standard 链路和 strict blocked 链路。
- 改动只删除重复 helper，不改变 workflow 的 profile 和 decision 策略。
- CSV 多行结构保留本地实现，避免为了抽象而改变报告形状。

所以 v92 是一次边界清楚、风险可控的代码质量收口。

## 测试覆盖

`tests/test_training_scale_workflow.py` 覆盖四类行为。

第一类是完整 workflow：

- review/standard 两个 profile 都运行。
- decision status 为 `ready`。
- selected profile 是 `review`。
- allowed count 为 1。
- blocked count 为 1。
- plan、run、comparison、decision、workflow HTML 都写出。
- execute command 中包含 `--execute`。

第二类是 strict decision blocked：

- `decision_require_gate_pass=True` 时 warn-only candidate 被阻止。
- decision status 为 `blocked`。
- selected profile 为 `None`。
- candidate count 为 0。

第三类是 profile 输入校验：

- duplicate profiles 抛出 `ValueError`。
- baseline profile 不在 profiles 中抛出 `ValueError`。

第四类是渲染和输出：

- Markdown 包含 Runs section。
- HTML 正确转义 `<workflow>`。
- JSON 可以读取且 schema version 为 1。
- CSV 文件存在。

这些测试保护的是 workflow 的业务串联和输出契约，而不是只验证 helper 能导入。

`tests/test_report_utils.py` 继续保护公共工具本身。v92 focused tests 同时跑 workflow tests 和 report utils tests，证明消费者和公共层都正常。

## 运行截图和证据

v92 的运行证据归档到：

```text
c/92/图片
c/92/解释/说明.md
```

截图覆盖：

- focused tests、compileall、full regression。
- review/standard workflow smoke。
- strict blocked workflow smoke。
- source/docs/archive structure check。
- Playwright/Chrome 打开 workflow HTML。
- README、代码讲解索引、c README 文档一致性检查。

这些截图证明 v92 的迁移不是口头上的“代码更干净”，而是保留了 workflow 的正常路径、阻断路径和浏览器证据。

## 后续开发原则

v92 之后，原始 training scale 链路已经形成：

```text
plan -> gate -> run -> comparison -> decision -> workflow
```

后续如果继续收口，可以考虑：

- `training_scale_promotion.py`
- `training_scale_promotion_index.py`
- `promoted_training_scale_comparison.py`

但原则仍然是：

- 每版只迁移一个边界清楚的消费者。
- 不改业务判断。
- 不重排输出 schema。
- 多行 CSV 保留本地 writer。
- 保持 focused tests、full regression、smoke、Playwright 和文档索引闭环。

## 一句话总结

v92 把 consolidated training scale workflow 接入 `report_utils`，让 plan、gate、run、comparison、decision、workflow 六层训练规模证据共享同一套报告基础设施，并保持 workflow 策略不变。
