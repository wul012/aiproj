# v180 training scale workflow artifact split 代码讲解

## 本版目标

v180 的目标是把 `training_scale_workflow.py` 中的 JSON、CSV、Markdown 和 HTML artifact 输出层拆到专用模块。v179 已经把 maturity narrative 的 summary 与 section/evidence 构造拆开；本版继续沿用“最大模块优先、契约保持、低风险收束”的路线，处理当前 module pressure 里靠前的 training-scale workflow 体量问题。

本版明确不做这些事：不改变 `run_training_scale_workflow()` 的输入参数，不改变 workflow JSON schema，不改变 `plan/`、`runs/<profile>/`、`comparison/`、`decision/` 嵌套产物目录，不改变 `scripts/run_training_scale_workflow.py` 用法，不改变 workflow summary/recommendations 的判断语义，也不改变旧代码从 `minigpt.training_scale_workflow` 导入 writer/renderer 的方式。

## 前置路线

training scale workflow 是 v75 引入的训练规模收束层。它把 v70-v74 的 scale plan、gate、gated run、run comparison 和 run decision 串成一个统一工作流：先基于数据源生成 plan，再按多个 gate profile 运行 dry-run/execute 任务，然后比较 profile 输出，最后生成可审阅的 execute handoff command。

后续 v92 曾把该模块迁移到共享 `report_utils`，但当时并没有把 workflow artifact writer 从业务编排里拆出来。随着 v165、v173、v174、v175 等版本陆续把 plan、decision、gate、promoted comparison 的 artifact writer 拆出，workflow 自身反而成了少数仍把编排和输出混在一起的 training-scale 模块。v180 的拆分补齐这条链路。

## 关键文件

- `src/minigpt/training_scale_workflow_artifacts.py`：新增 artifact 模块，负责 workflow JSON、CSV、Markdown、HTML 的渲染和写出。
- `src/minigpt/training_scale_workflow.py`：保留 `run_training_scale_workflow()`、profile 解析、profile run 摘要、plan summary、workflow summary 和 recommendations 计算。
- `tests/test_training_scale_workflow.py`：新增 facade identity 测试，确认旧入口导出的 HTML renderer 和 output writer 就是新 artifact 模块里的函数。
- `README.md`、`c/180/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`、`c/README.md`：记录 v180 的能力边界、运行证据和讲解索引。

## Artifact 模块

`training_scale_workflow_artifacts.py` 承接四类输出：

- `write_training_scale_workflow_json()`：写出完整 workflow report JSON。
- `write_training_scale_workflow_csv()`：把每个 profile run 的 status、allowed、gate、batch、readiness score 和最终 decision 摘要写成表格。
- `render_training_scale_workflow_markdown()` 和 `write_training_scale_workflow_markdown()`：输出面向交接阅读的 workflow Markdown。
- `render_training_scale_workflow_html()` 和 `write_training_scale_workflow_html()`：输出带 stats、profile run table、execute command、artifact links 和 recommendations 的 HTML。

`write_training_scale_workflow_outputs()` 仍是统一出口，会一次性写出 `training_scale_workflow.json`、`training_scale_workflow.csv`、`training_scale_workflow.md` 和 `training_scale_workflow.html`。这些文件是 workflow 的最终证据，可被后续 handoff、promotion 或 README 证据链引用。

## 主入口

`training_scale_workflow.py` 现在聚焦五件事：

1. 解析 profile 列表和 baseline profile。
2. 调用 `build_training_scale_plan()` 生成 plan，并写出 plan artifact。
3. 对每个 profile 调用 `run_training_scale_plan()`，记录 run JSON 路径和 profile summary。
4. 调用 comparison 和 decision 模块，生成跨 profile 比较与候选执行决策。
5. 组装 workflow report，并调用 artifact 模块写出最终证据。

主模块仍然从 `training_scale_workflow_artifacts.py` 导入并 re-export 旧的 writer/renderer 名称，因此旧测试、脚本和用户代码不需要修改导入路径。

## 数据结构和字段语义

workflow report 的关键字段保持不变：

- `plan_summary`：来自 plan 的 dataset name、version prefix、scale tier、char count、warning count、variant count 和 baseline。
- `runs`：每个 profile 的运行摘要，包含 gate status、batch status、blocked reason、readiness score 和对应 artifact 路径。
- `comparison_summary`：跨 profile 比较摘要，由 training scale run comparison 模块生成。
- `decision_summary`：候选 profile 的执行决策摘要。
- `summary`：workflow 层的聚合状态，包括 `allowed_count`、`blocked_count`、`decision_status`、`selected_profile` 和 `recommended_action`。
- `recommendations`：根据 decision status、blocked profile 数量和 execute command 是否存在生成的交接建议。

v180 不改变这些字段，只把它们如何被渲染成 JSON/CSV/Markdown/HTML 的代码移动到了 artifact 模块。

## 测试覆盖

`tests.test_training_scale_workflow` 覆盖以下链路：

- 完整 workflow 会生成 plan、两个 profile run、comparison、decision 和最终 HTML。
- strict decision 在 gate 未完全通过时会阻断候选 profile。
- duplicate profile 和 missing baseline 会抛出 `ValueError`。
- Markdown/HTML renderer 会输出可读内容，并正确 escape HTML title。
- 新增 facade identity 测试确认旧入口导出的 `render_training_scale_workflow_html()` 和 `write_training_scale_workflow_outputs()` 与 artifact 模块同源。

这组测试既覆盖 workflow 的业务链路，也保护了 v180 最关键的兼容性边界。

## 运行证据

v180 的运行截图归档在 `c/180`：

- `01-training-scale-workflow-tests.png`：training scale workflow 定向测试通过。
- `02-training-scale-workflow-artifact-smoke.png`：旧 facade 和新 artifact 模块函数 identity 以及模块行数检查。
- `03-maintenance-smoke.png`：module pressure 为 `pass`，没有 warn/critical 模块。
- `04-source-encoding-smoke.png`：源码编码、BOM、语法和 Python 3.11 兼容检查通过。
- `05-full-unittest.png`：全量 404 个测试通过。
- `06-docs-check.png`：README、`c/180`、讲解索引、source/test 关键词对齐。

临时 `tmp_v180_*` 日志和 `runs/*v180*` 输出会在提交前按 AGENTS 清理门禁删除，`c/180` 是保留的正式证据。

## 边界说明

`training_scale_workflow_artifacts.py` 不是新的工作流入口，也不会重新执行 plan、gate、comparison 或 decision。它只消费已经组装好的 workflow report dict，把同一份证据写成多种可读格式。业务执行仍在 `run_training_scale_workflow()` 内完成，CLI 仍使用 `scripts/run_training_scale_workflow.py`。

## 一句话总结

v180 把 training scale workflow 的 artifact 输出层从执行编排里拆出来，让训练规模工作流主模块从 485 行降到 248 行，同时保持 workflow schema、CLI、嵌套产物目录和旧 facade 导入全部不变。
