# v403 Tiny Scorecard Comparison Smoke Summary/Output Split

## 版本目标

v403 的目标是把 `scripts/run_tiny_scorecard_comparison_smoke.py` 从一个 766 行的单文件烟雾脚本，拆成「CLI 入口壳 + summary 计算模块 + output 渲染模块」三层。

它解决的是维护性问题：

- 入口文件过长，命令流、摘要汇总和文本渲染都挤在一起。
- `build_summary`、`decision_summary`、`render_summary`、`write_summary_outputs` 混在同一个脚本里，不利于继续维护。
- 现有测试依赖脚本模块导出名，拆分时必须保持兼容。

本版不做的事：

- 不改 benchmark 结果，不改 compare/decision 链路语义。
- 不新增新的治理链。
- 不把 tiny smoke 的“比较证据”升级成模型质量结论。

## 来源路线

v403 承接 v401-v402 的 tiny benchmark smoke / benchmark history / suite design 证据链。

- v401 把 benchmark history 摘要写进 CI wrapper plan。
- v402 把 eval suite design coverage 写进 tiny standard benchmark smoke。
- v403 在此基础上收口脚本结构，把 comparison smoke 的汇总和输出分层。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 现在只保留参数解析、运行编排、命令执行和出口判断。
  - 继续向外导出旧函数名，避免测试和调用方断链。

- `src/minigpt/tiny_scorecard_comparison_smoke_summary.py`
  - 负责 `build_summary`、benchmark history 汇聚、comparison/decision 摘要、remediation gate 判断和 threshold profile 计算。

- `src/minigpt/tiny_scorecard_comparison_smoke_outputs.py`
  - 负责 summary 文本渲染、JSON/TXT 输出、可选 summary-check sidecar 写入。

- `README.md`
  - 更新当前版本说明和 benchmark 模块说明。

- `d/403/解释/说明.md`
  - 运行证据说明页。

## 核心结构

summary 模块保留这些输入输出：

- 输入：baseline/candidate/comparison/decision/history 目录和 `run_config`。
- 输出：一个统一的 smoke `summary` 字典，里面继续携带 `baseline_smoke`、`candidate_smoke`、`scorecard_comparison`、`scorecard_decision`、`benchmark_history`、`remediation_gate`。

output 模块只做展示和落盘：

- `render_summary(summary)` 把 summary 字典写成键值文本。
- `write_summary_outputs(...)` 写 JSON/TXT。
- `write_summary_and_optional_check(...)` 在需要时写 inline check sidecar。

## 验证

这版验证了两类东西：

1. 结构兼容
   - `tests/test_tiny_scorecard_comparison_smoke.py` 继续通过，说明脚本导出名和 summary 语义没有断。
   - `tests/test_ci_tiny_scorecard_smoke.py` 继续通过，说明 CI wrapper 仍能消费同一条 smoke 链。

2. 语法与边界
   - `python -m py_compile` 通过。
   - `git diff --check` 通过。

## 一句话总结

v403 把一条能跑的 tiny comparison smoke 变成了更容易继续维护的三层结构，而不是继续在一个大脚本里堆逻辑。
