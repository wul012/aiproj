# v267 training scale run comparison artifact writer split

## 本版目标和边界

v267 的目标是给 training-scale run comparison 做一次 contract-preserving 收口。`training_scale_run_comparison.py` 原来同时负责 run 加载、baseline 选择、readiness delta、suite consistency、batch-review aggregation、recommendations，以及 JSON/CSV/Markdown/HTML 输出。本版只把 artifact writer 和 HTML/Markdown helper 移到独立模块。

本版不改变：

- `build_training_scale_run_comparison()` 的 report schema；
- baseline 选择规则；
- readiness score 和 delta 计算；
- suite consistency 判断；
- batch comparison review/blocker 计数；
- `training_scale_run_comparison.json/csv/md/html` 文件名和内容契约；
- CLI `scripts/compare_training_scale_runs.py` 的使用方式。

## 前置链路

v253 开始让 gated scale runs 和 scale-run comparison 聚合 batch comparison review/blocker counts，v254-v261 再把 selected-run review context 继续传给 decision、handoff、promotion、promoted comparison、promoted decision、promoted seed 和 seed handoff。v266 先拆 handoff artifact writer，本版顺着同一条训练规模链路，把 run comparison 的输出层也拆出，避免比较模块继续承担报告渲染细节。

## 关键文件

### `src/minigpt/training_scale_run_comparison_artifacts.py`

新增 artifact 模块，负责：

- `write_training_scale_run_comparison_json()`
- `write_training_scale_run_comparison_csv()`
- `render_training_scale_run_comparison_markdown()`
- `write_training_scale_run_comparison_markdown()`
- `render_training_scale_run_comparison_html()`
- `write_training_scale_run_comparison_html()`
- `write_training_scale_run_comparison_outputs()`

它同时承接 `_runs_table()`、`_list_section()`、`_style()`、`_card()` 这些只服务 HTML/Markdown 输出的 helper。这个模块不计算 readiness，不判断 suite consistency，也不选择 baseline，只消费已经生成的 report。

### `src/minigpt/training_scale_run_comparison.py`

主文件继续负责比较语义：

- `load_training_scale_run()` 读取单个 `training_scale_run.json`；
- `build_training_scale_run_comparison()` 组装 comparison report；
- `_run_summary()` 从 run、gate、plan、batch 中提取比较字段；
- `_select_baseline()` 支持按默认、索引或名称选 baseline；
- `_run_delta()` 生成 allowed/readiness/suite/gate/batch relation；
- `_comparison_summary()` 汇总 allowed/blocked、suite paths、batch review/blocker、coverage regression；
- `_recommendations()` 生成对 blocked、mixed-suite、review/blocker 的行动建议。

为了兼容旧入口，主文件从 artifact 模块 re-export writer/render 函数。旧脚本和测试继续从 `minigpt.training_scale_run_comparison` 导入 `write_training_scale_run_comparison_outputs()`。

### `tests/test_training_scale_run_comparison.py`

新增 `test_artifact_module_matches_legacy_exports()`，同时走旧 facade 和新 artifact 模块：

- Markdown render 完全一致；
- HTML render 完全一致；
- CSV 输出完全一致；
- 新模块仍写出 `training_scale_run_comparison.html`。

这个测试保护的是输出契约和导入兼容，不只是“文件存在”。

## 输入输出

输入仍然是一个或多个 `training_scale_run.json` 文件，或包含该文件的目录。Comparison report 仍然包含：

- `run_count`
- `baseline`
- `runs`
- `baseline_deltas`
- `summary`
- `best_by_readiness`
- `recommendations`

输出仍然是：

- `training_scale_run_comparison.json`
- `training_scale_run_comparison.csv`
- `training_scale_run_comparison.md`
- `training_scale_run_comparison.html`

本版没有新增字段，只移动 writer/render 实现位置。

## 测试覆盖

- 聚焦测试覆盖 allowed/blocked run comparison、mixed-suite 判断、目录输入、best-by-readiness、HTML escape、重复名称/空输入错误，以及新旧 artifact 输出一致性。
- workflow 和 run-decision 相关测试一起运行，确认下游仍能从旧入口消费 comparison 输出函数。
- contract smoke 检查 legacy/artifact 输出等价、文件名不变、主文件降到 311 行、artifact 文件 249 行。
- 全量 unittest 和 source encoding 检查保护跨模块回归。

## 证据归档

运行截图和解释归档在 `c/267`：

- `c/267/图片/01-focused-tests.png`
- `c/267/图片/02-contract-smoke.png`
- `c/267/图片/03-full-unittest.png`
- `c/267/图片/04-source-encoding.png`
- `c/267/图片/05-docs-check.png`
- `c/267/解释/说明.md`

## 一句话总结

v267 把 training-scale run comparison 的 artifact writer 从比较 builder 中拆出，让主文件从 542 行降到 311 行，同时保留旧导入入口和四类输出契约。
