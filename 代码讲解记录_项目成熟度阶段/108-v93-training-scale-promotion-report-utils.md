# v93 training scale promotion report utility migration

## 本版目标

v93 的目标是继续轻量、定向的质量优化，把 v77 引入的 `training_scale_promotion.py` 迁移到公共 `report_utils.py` 上。

v92 已经把 consolidated workflow 接入公共报告工具。v93 继续沿训练规模治理链往后推进：workflow/handoff 之后需要一层 promotion acceptance，用来判断一次训练规模执行结果是否可以成为后续对比和基线推进的候选。

本版解决的问题是：`training_scale_promotion.py` 会读取 handoff、scale run、batch 和 per-variant portfolio artifacts，然后输出 promoted/review/blocked 验收证据。但在 v93 之前，它仍然保留私有 `utc_now`、`_dict`、`_list_of_dicts`、`_string_list`、`_md`、`_e` 和 JSON writer。这样 promotion evidence 和前置 workflow/plan/gate/run/comparison/decision evidence 在基础报告行为上仍有分叉。

v93 的结果是：training scale promotion acceptance 也开始复用公共报告基础层。

## 本版明确不做什么

v93 不改 promotion policy。

下面这些行为保持不变：

- handoff status 非 completed 时仍然 blocked。
- handoff execution returncode 非 0 时仍然 blocked。
- training scale run status 非 completed 时仍然 blocked。
- batch execution status 非 completed 时仍然 blocked。
- variant portfolio failed 时仍然 blocked。
- required artifacts 缺失时仍然 review。
- required artifacts 全部存在时才 promoted。
- `REQUIRED_VARIANT_ARTIFACTS` 列表不变。
- promotion CSV 仍然是 per-variant 多行摘要。
- CLI `--no-fail` 语义不变。

本版只迁移报告基础 helper，不调整 promoted/review/blocked 的判定规则。

## 来自哪条路线

v83 新增 `report_utils.py`。

v87-v92 已经覆盖了原始 training scale 执行链：

```text
plan -> gate -> run -> comparison -> decision -> workflow
```

v93 迁移的是执行后验收层：

```text
workflow / handoff -> promotion acceptance
```

这说明公共报告基础层不只服务执行前和执行中的 evidence，也开始服务执行后的验收 evidence。

## 关键文件

`src/minigpt/training_scale_promotion.py`

这是本版核心迁移文件。它继续负责读取 handoff、scale run、batch、variant portfolio，检查 required artifacts，产出 promotion status、blockers、review items、recommendations 和 JSON/CSV/Markdown/HTML。

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

`tests/test_training_scale_promotion.py`

这是 promotion 业务测试。它覆盖 full evidence promoted、failed handoff blocked、missing evidence review、HTML escaping 和输出可读性。

`tests/test_report_utils.py`

这是公共层测试，继续保护 JSON/CSV 写出、Markdown/HTML 转义和 list/dict 归一化。

`scripts/build_training_scale_promotion.py`

这是 promotion CLI 入口。本版不改参数，用它做 smoke 来证明迁移后 promoted 和 review 两条路径都能输出报告。

`代码讲解记录_项目成熟度阶段/108-v93-training-scale-promotion-report-utils.md`

这是本讲解文件，用来解释 v93 为什么是执行验收层的收口，而不是 promotion policy 重构。

`c/93/`

这是 v93 的运行截图和解释归档。它保存 tests、promoted smoke、review smoke、结构检查、Playwright HTML 截图和文档检查。

## 迁移前的重复点

迁移前，`training_scale_promotion.py` 自己维护了：

```text
utc_now
_list_of_dicts
_string_list
_dict
_md
_e
```

同时 promotion JSON 写出也由本模块手写：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

这些能力和 `report_utils.py` 已有原语重复。promotion 是训练规模执行后的验收证据，它应该和前置执行链路共用同一套 JSON 写出、转义和 list/dict 防御规则。

## 迁移后的引入关系

v93 让 `training_scale_promotion.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

保留 `_dict`、`_md`、`_e` 等旧别名，是为了让渲染模板保持稳定。v93 的目标不是重写 promotion 报告，而是复用公共基础设施。

## JSON 输出

`write_training_scale_promotion_json` 改为：

```text
write_json_payload(report, path)
```

`training_scale_promotion.json` 是 promotion acceptance 的机器可读证据。它包含：

- handoff path 和 handoff summary。
- training scale run digest。
- batch digest。
- variants readiness。
- evidence rows。
- summary。
- blockers。
- review items。
- recommendations。

这个 JSON 的用途是给后续 promotion index、promoted comparison 和 promoted baseline decision 消费。v93 不改变字段结构，只统一 JSON writer。

## CSV 输出

`training_scale_promotion.csv` 是 per-variant 多行摘要。

字段包括：

```text
promotion_status
handoff_status
scale_run_status
batch_status
variant
variant_status
checkpoint_exists
run_manifest_exists
registry_exists
maturity_narrative_exists
missing_required
portfolio_json
```

因此本版没有强行改用 `report_utils.write_csv_row`。多行结构继续留在本模块，由本模块理解每个 variant 的 readiness。

## Markdown 和 HTML 渲染

Markdown 报告仍然包含：

- promotion summary。
- evidence table。
- variant readiness table。
- recommendations。
- blockers。
- review items。

HTML 报告仍然包含：

- stats cards。
- evidence table。
- variant readiness table。
- recommendations。
- blockers。
- review items。

变化在于 Markdown cell、HTML escape、list/dict normalization 改为公共工具：

```text
markdown_cell
html_escape
list_of_dicts
string_list
as_dict
```

这样 promotion 报告和前置 workflow、planner、gate、run、comparison、decision 的渲染基础行为保持一致。

## 核心数据结构

`build_training_scale_promotion` 返回的 report 仍然保持原结构。

顶层字段包括：

```text
schema_version
title
generated_at
handoff_path
project_root
out_root
handoff_summary
training_scale_run_path
training_scale_run
batch_path
batch
variants
evidence_rows
summary
blockers
review_items
recommendations
```

`variants` 每行代表一个 portfolio variant：

```text
name
description
promotion_status
status
run_name
dataset_name
dataset_version
portfolio_json
portfolio_html
run_dir
step_count
completed_steps
failed_step
required_artifact_count
available_required_artifact_count
missing_required
checkpoint_exists
run_manifest_exists
registry_exists
maturity_narrative_exists
artifact_rows
```

`summary` 是验收总判断：

```text
promotion_status
handoff_status
scale_run_status
batch_status
variant_count
ready_variant_count
checkpoint_count
registry_count
maturity_narrative_count
required_artifact_count
available_required_artifact_count
evidence_count
available_evidence_count
blocker_count
review_item_count
```

## 运行流程

promotion 的主流程保持不变：

```text
load handoff
 -> resolve project_root / out_root
 -> read training_scale_run.json
 -> read training_portfolio_batch.json
 -> inspect variant portfolio reports
 -> build evidence rows
 -> compute blockers and review_items
 -> summarize promotion status
 -> write promotion outputs
```

promotion 的核心不在模型训练，而在证据验收：它确认一次执行是否真的生成了足够的 checkpoint、manifest、eval、generation quality、scorecard、dataset card、registry、maturity summary 和 maturity narrative。

v93 没有改变这个验收流程，只迁移输出基础工具。

## promoted / review / blocked 语义

`blocked` 表示执行链路本身失败或不完整：

- handoff failed。
- command returncode 非 0。
- scale run 没完成。
- batch 没完成。
- variant portfolio failed。
- 没有 variant portfolio。

`review` 表示执行链路完成，但证据还不足以成为成熟 baseline：

- required artifact 缺失。
- evidence rows 中存在缺失项。

`promoted` 表示执行和关键证据都完整：

- handoff completed。
- scale run completed。
- batch completed。
- variant portfolio completed。
- required artifacts 都存在。

v93 不改变这些状态，只统一报告基础设施。

## 为什么这条建议合理

v93 仍然符合“收口型优化，不做架构级重构”的判断。

原因是：

- promotion 是 workflow/handoff 之后的自然验收层，边界清楚。
- v92 已经让 workflow 接入公共工具，v93 让后续验收层也对齐。
- promotion tests 覆盖 promoted、blocked、review 三条路径。
- 改动只删除重复 helper，不改变 promotion policy。
- CSV 多行结构保留本地实现，避免为了抽象破坏报告形状。

所以 v93 是一次低风险质量收口，而不是功能堆叠。

## 测试覆盖

`tests/test_training_scale_promotion.py` 覆盖四类行为。

第一类是 full evidence promoted：

- completed handoff。
- completed scale run。
- completed batch。
- variant portfolio 完整。
- required artifacts 全部存在。
- promotion status 是 `promoted`。
- blockers 和 review items 都为空。

第二类是 failed handoff blocked：

- handoff status 为 failed。
- execution returncode 为 1。
- promotion status 是 `blocked`。
- blockers 中包含 handoff status。
- recommendations 中包含 Stop promotion。

第三类是 missing evidence review：

- handoff、scale run、batch 都完成。
- registry 和 maturity narrative 缺失。
- promotion status 是 `review`。
- ready variant count 为 0。
- missing_required 中记录缺失 artifact。

第四类是输出和 HTML 转义：

- JSON 和 HTML 文件写出。
- JSON summary 可读。
- Markdown 包含 Variant Readiness。
- HTML 把 `<Promotion>` 转义成 `&lt;Promotion&gt;`。

这些测试保护的是 promotion policy 和输出契约，而不只是导入公共 helper。

`tests/test_report_utils.py` 继续保护公共工具本身。v93 focused tests 同时跑 promotion tests 和 report utils tests，证明消费者和公共层都正常。

## 运行截图和证据

v93 的运行证据归档到：

```text
c/93/图片
c/93/解释/说明.md
```

截图覆盖：

- focused tests、compileall、full regression。
- promoted smoke。
- review smoke。
- source/docs/archive structure check。
- Playwright/Chrome 打开 promotion HTML。
- README、代码讲解索引、c README 文档一致性检查。

这些截图证明 v93 的迁移保留了 promotion 的完整验收路径和 review 边界。

## 后续开发原则

v93 之后，训练规模执行链路已经从执行前规划、准入、运行、比较、决策、总入口，推进到执行后验收层。

后续如果继续收口，可以考虑：

- `training_scale_promotion_index.py`
- `promoted_training_scale_comparison.py`
- `promoted_training_scale_decision.py` 已迁移过，但可检查上游链接是否还有重复。

原则仍然是：

- 每版只迁移一个边界清楚的消费者。
- 不改业务判断。
- 不重排输出 schema。
- 多行 CSV 保留本地 writer。
- 保持 focused tests、full regression、smoke、Playwright 和文档索引闭环。

## 一句话总结

v93 把 training scale promotion acceptance 接入 `report_utils`，让训练规模执行后的 promoted/review/blocked 验收证据开始和前置执行链路共享同一套报告基础设施。
