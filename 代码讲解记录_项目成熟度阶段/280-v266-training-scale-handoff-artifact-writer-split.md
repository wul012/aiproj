# v266 training scale handoff artifact writer split

## 本版目标和边界

v266 的目标是给 training-scale handoff 做一次收口型拆分。`training_scale_handoff.py` 已经承担 workflow 读取、decision command 校验、可选执行、suite guard 传递、batch-review context 汇总、artifact 探测和 JSON/CSV/Markdown/HTML 输出。本版只把输出层移到独立 artifact 模块，让 handoff 主文件回到“验证与执行编排”的职责。

本版不改变：

- `build_training_scale_handoff()` 的返回结构；
- `handoff_allowed`、`blocked_reason`、`execution.status`、`summary` 字段；
- suite consistency guard 传递方式；
- selected batch review/blocker 计数；
- `training_scale_handoff.json/csv/md/html` 文件名和内容契约；
- `scripts/execute_training_scale_handoff.py` 的调用方式。

## 前置链路

v255 先把 selected-run batch review context 接入 handoff，v205-v218 又让 handoff 持续承载 suite guard、clean evidence gate 和 persisted gate artifacts。后续 v256-v261 把这些 handoff 证据向 promotion、index、promoted comparison、promoted decision、promoted seed 和 seed handoff 继续传递。v266 不再新增业务字段，而是把 handoff 的输出层拆出，降低后续继续维护执行边界时的文件压力。

## 关键文件

### `src/minigpt/training_scale_handoff_artifacts.py`

新增 artifact 模块，负责 handoff 报告的落盘和渲染：

- `write_training_scale_handoff_json()`
- `write_training_scale_handoff_csv()`
- `render_training_scale_handoff_markdown()`
- `write_training_scale_handoff_markdown()`
- `render_training_scale_handoff_html()`
- `write_training_scale_handoff_html()`
- `write_training_scale_handoff_outputs()`

它也承接 `_command_section()`、`_execution_section()`、`_artifact_section()`、`_list_section()`、`_style()`、`_card()` 这些只服务 HTML/Markdown 输出的 helper。这个文件不决定是否能执行 command，也不改 summary 语义，只负责把已经生成的 report 变成四种 artifact。

### `src/minigpt/training_scale_handoff.py`

主文件继续负责真实 handoff 语义：

- `load_training_scale_workflow()` 读取 workflow JSON；
- `build_training_scale_handoff()` 组装 handoff report；
- `_handoff_allowed()` 判断 decision command 是否允许执行；
- `_execution_result()` 在 `--execute` 场景运行命令并记录 return code、耗时、stdout/stderr tail；
- `_artifact_rows()` 探测训练输出目录中的 run、batch、variant 和 checkpoint artifact；
- `_suite_guard()` 保留 upstream strict-suite boundary；
- `_summary()` 和 `_recommendations()` 输出人机都能消费的 review 结论。

为了兼容旧入口，`training_scale_handoff.py` 从 artifact 模块 re-export writer/render 函数。因此旧测试、脚本和外部调用仍然可以从 `minigpt.training_scale_handoff` 导入 `write_training_scale_handoff_outputs()`。

### `tests/test_training_scale_handoff.py`

新增 `test_artifact_module_matches_legacy_exports()`，它同时调用旧入口和新 artifact 模块：

- 比较 Markdown render 结果完全一致；
- 比较 HTML render 结果完全一致；
- 比较 CSV 输出完全一致；
- 确认新 artifact 模块仍写出 `training_scale_handoff.html`。

这个测试保护的是“拆文件但不改契约”，不是只证明函数能被导入。

## 输入输出

输入仍然是 `training_scale_workflow.json` 或包含该文件的目录。核心 report 仍然包含：

- `workflow_path`
- `decision_status`
- `handoff_allowed`
- `blocked_reason`
- `command` / `command_text`
- `execution`
- `suite_guard`
- `artifact_rows`
- `summary`
- `recommendations`

输出仍然是：

- `training_scale_handoff.json`
- `training_scale_handoff.csv`
- `training_scale_handoff.md`
- `training_scale_handoff.html`

本版没有新增字段，只移动 writer/render 实现位置。

## 测试覆盖

- 聚焦 handoff 测试运行 8 个用例，覆盖 planned、blocked、execute completed、execute failed、HTML escape、suite guard propagation、selected batch blocker propagation，以及新旧 artifact 导出一致性。
- contract smoke 会检查新旧输出函数的 Markdown/HTML/CSV 等价，且确认主文件从 540 行降到 297 行、artifact 文件为 261 行。
- 全量 unittest 保护其他治理链路不受拆分影响。
- source encoding 检查确认新增文件没有 BOM、不可打印字符或语法错误。

## 证据归档

运行截图和解释归档在 `c/266`：

- `c/266/图片/01-focused-tests.png`
- `c/266/图片/02-contract-smoke.png`
- `c/266/图片/03-full-unittest.png`
- `c/266/图片/04-source-encoding.png`
- `c/266/图片/05-docs-check.png`
- `c/266/解释/说明.md`

## 一句话总结

v266 把 training-scale handoff 的 artifact writer 从验证/执行 builder 中拆出，让主文件从 540 行降到 297 行，同时保留旧导入入口和四类输出契约。
