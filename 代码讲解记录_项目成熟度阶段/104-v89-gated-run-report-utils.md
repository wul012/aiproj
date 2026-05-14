# v89 gated training scale run report utility migration

## 本版目标

v89 的目标是继续 `report_utils` 收口路线，把 v72 引入的 `training_scale_run.py` 迁移到公共报告工具上。

这个模块的职责是把一份 `training_scale_plan.json` 先交给 training scale gate，再根据 gate 结果决定是否把 variants 交给 training portfolio batch runner。它会输出：

- `training_scale_run.json`
- `training_scale_run.csv`
- `training_scale_run.md`
- `training_scale_run.html`
- gate 输出路径
- variants 路径
- batch 输出路径
- status、allowed、blocked reason 和 recommendations

v89 要解决的问题是：v88 已经让 run comparison 接入公共报告工具，v87 已经让 run decision 接入公共报告工具，但它们的直接上游 run report 仍然保留私有 JSON/CSV/Markdown/HTML helper。

本版把 gated run 层也迁入公共工具，让 run -> comparison -> decision 三层训练规模证据共享同一套报告基础设施。

## 本版明确不做什么

v89 不改变 gate-to-batch 的业务语义。

下面这些行为保持不变：

- `gate failed` 是否阻断 batch handoff
- `warn` gate 在 `allow_warn=False` 时是否阻断
- `allow_fail=True` 是否允许 fail gate 继续进入 batch runner
- batch dry-run 是否生成 `training_portfolio_batch.json`
- `planned_with_warnings`、`blocked`、`completed`、`failed` 等 status 的判断
- variants JSON 的写出位置
- gate 输出和 batch 输出的路径结构

本版只迁移报告基础设施，不改变执行策略。

## 来自哪条路线

v83 新增 `report_utils.py`，先迁移 promoted seed handoff。

v84 到 v86 把 promoted seed、baseline decision 和 controlled handoff 接入公共工具。

v87 回收 v74 `training_scale_run_decision.py`。

v88 回收 v73 `training_scale_run_comparison.py`。

v89 回收 v72 `training_scale_run.py`。

这样，原始 training scale 链路中这三层已经连续接入公共层：

```text
v72 gated run
 -> v73 run comparison
 -> v74 run decision
```

这条链路现在不再复制同一批 JSON/CSV/Markdown/HTML helper。

## 关键文件

`src/minigpt/training_scale_run.py`

这是本版核心迁移文件。它继续负责读取 plan、运行 gate、决定 batch handoff、写 variants、运行 batch runner、汇总 run report。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用它已有的 JSON/CSV 写出、Markdown/HTML 转义、list/dict 归一化和 UTC 时间工具。

`tests/test_training_scale_run.py`

这是 gated run 的业务测试，覆盖 warn gate 放行、warn gate 阻断、standard gate fail 阻断、allow-fail 强制放行、HTML 转义和输出文件可读性。

`tests/test_report_utils.py`

这是公共层测试，保护 JSON/CSV 写出、命令展示、Markdown/HTML 转义、artifact row 和 list/dict 归一化。

`scripts/run_training_scale_plan.py`

这是 CLI 入口。本版不改 CLI 参数，用户运行方式不变。

`代码讲解记录_项目成熟度阶段/104-v89-gated-run-report-utils.md`

这是本文件，解释 v89 的迁移目标、边界、字段语义和验证证据。

`c/89/`

这是 v89 的运行截图和解释归档目录。

## 迁移前的重复点

迁移前，`training_scale_run.py` 自己维护了：

```text
utc_now
_list_of_strings
_list_of_dicts
_string_list
_dict
_md
_e
```

同时 JSON 和 CSV 写出也在模块内直接处理：

```text
Path(...).write_text(json.dumps(...))
csv.DictWriter(...)
```

这些能力已经在 `report_utils.py` 中存在，继续保留会让 v72、v73、v74 这三层证据的报告基础行为分叉。

## 迁移后的引入关系

v89 让 `training_scale_run.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
list_of_strs as _list_of_strings
markdown_cell as _md
string_list as _string_list
utc_now
write_csv_row
write_json_payload
```

保留 `_dict`、`_md`、`_e` 这些别名，是为了让现有 Markdown/HTML 模板保持稳定，避免把 helper 迁移变成大规模模板重写。

## JSON 输出

`write_training_scale_run_json` 改为调用：

```text
write_json_payload(report, path)
```

这个 JSON 是 v72 的核心机器可读证据。v73 comparison、v74 decision、后续 workflow、handoff、promotion 都可以间接消费它。

公共 JSON writer 统一保证：

- 自动创建父目录
- UTF-8
- `ensure_ascii=False`
- `indent=2`

## CSV 输出

`training_scale_run.csv` 是单行摘要，因此适合直接使用：

```text
write_csv_row(row, out_path, fieldnames)
```

字段仍由本模块定义：

```text
status
allowed
gate_status
gate_profile
execute
variant_count
batch_status
blocked_reason
```

字段语义不属于公共层；公共层只负责稳定写出 CSV。

## Markdown 和 HTML 渲染

Markdown 报告仍然包含：

- status
- allowed
- gate/profile
- execute
- batch status
- plan path
- variants path
- gate table
- batch table
- recommendations

HTML 报告仍然包含：

- header
- stats cards
- gate summary
- batch summary
- recommendations

变化在于 Markdown cell 和 HTML escape 改为公共工具：

```text
markdown_cell
html_escape
```

测试里会用 `<demo>` 作为 dataset name，确认 HTML 中出现 `&lt;demo&gt;`，而不是未经转义的 `<demo>`。

## 核心运行流程

`run_training_scale_plan` 的流程保持不变：

1. 读取 `training_scale_plan.json`
2. 构建 training scale gate
3. 写出 gate artifacts
4. 根据 `allow_warn` 和 `allow_fail` 判断是否 allowed
5. 写出 `training_scale_variants.json`
6. 如果 allowed，构建 training portfolio batch plan
7. 如果 allowed，运行 batch runner
8. 写出 batch outputs
9. 汇总 run status
10. 写出 run JSON/CSV/Markdown/HTML

v89 只替换第 10 步的报告基础设施，以及前面 summary/render 时用到的 list/dict/转义 helper。

## 关键状态语义

`planned_with_warnings`

表示 gate 是 `warn`，但 `allow_warn=True`，因此允许进入 batch dry-run。它不是失败，而是提醒后续不要把这类证据直接当成模型能力提升证明。

`blocked`

表示 gate 结果没有被当前策略允许。例如 gate failed 且没有 `allow_fail`，或者 gate warned 且 `allow_warn=False`。此时 batch 不启动。

`planned`

表示 gate 放行，batch runner 生成了计划层产物。

`completed`

表示 batch execution 完成。当前 smoke 多用 dry-run，所以一般不会走到真实 completed。

`failed`

表示 batch execution 层报告失败。

## gate 和 batch 摘要

`gate` 摘要包含：

- overall status
- pass count
- warn count
- fail count
- profile

`batch_summary` 摘要包含：

- status
- variant count
- completed variant count
- failed variant
- comparison status

这些字段是后续 v73 comparison 计算 readiness score 的来源，因此 v89 必须保持字段名和结构稳定。

## 测试覆盖

`tests/test_training_scale_run.py` 覆盖六类行为。

第一类是 review gate 放行 warn plan：

- `allowed=True`
- status 是 `planned_with_warnings`
- gate overall status 是 `warn`
- batch summary status 是 `planned`
- batch artifact 和 run JSON 都存在

第二类是 warn plan 被阻断：

- 设置 `allow_warn=False`
- `allowed=False`
- status 是 `blocked`
- blocked reason 是 `gate warned and allow_warn is false`
- batch artifact 不存在

第三类是 standard gate fail 阻断：

- tiny corpus 在 standard profile 下失败
- status 是 `blocked`
- blocked reason 是 `gate failed`
- batch summary 是 `skipped`

第四类是 allow-fail 强制放行：

- standard gate 失败
- 设置 `allow_fail=True`
- batch summary 仍然进入 `planned`

第五类是 HTML 转义：

- dataset name 使用 `<demo>`
- HTML 中必须出现 `&lt;demo&gt;`
- 原始 `<demo>` 不能直接出现

第六类是机器可读输出：

- `training_scale_run.json` 可以被 JSON 读取
- schema version 为 1
- 包含 gate_outputs 和 batch_outputs
- CSV 文件存在

这些断言保护的是 gate-to-batch 边界，而不只是写文件成功。

`tests/test_report_utils.py` 继续保护公共工具本身。v89 focused tests 同时跑 gated run tests 和 report utils tests，证明消费者和公共层都正常。

## 运行截图和证据

v89 的运行证据归档到：

```text
c/89/图片
c/89/解释/说明.md
```

截图会覆盖：

- focused tests、compileall、full regression
- allowed smoke
- blocked smoke
- source/docs/archive structure check
- Playwright/Chrome HTML 渲染
- README 与讲解索引检查

这些截图是本版提交随附的证据链。

## 后续开发原则

v89 之后，原始 training scale 链路还剩 plan、gate、workflow、promotion、promotion index 等模块可以继续小步迁移。

继续推进时要保持这个原则：

- 只迁移输出基础设施。
- 不混入 gate 阈值、batch 执行策略、promotion 条件等业务调整。
- 保留原字段顺序和路径结构。
- 每版用 focused tests、smoke、Playwright 和文档索引闭环。

## 一句话总结

v89 把 gated training scale run 接入 `report_utils`，让 run、comparison、decision 三层训练规模证据开始共享同一套报告基础设施。
