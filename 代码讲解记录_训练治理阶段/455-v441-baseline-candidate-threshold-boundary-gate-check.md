# v441 baseline-candidate threshold boundary expected-exit gate check

## 本版目标和边界

v440 已经能把 baseline-candidate threshold boundary diagnosis 变成严格 gate：候选仍被拒绝时，`--require-diagnosis-pass` 返回退出码 `2`。这个设计合理，但对 CI 或人工复核来说还有一个小缺口：如果只看到非零退出码，容易误判成脚本异常。

v441 增加一层轻量 contract check：它重新运行严格 gate，读取生成的 boundary smoke summary，并校验实际退出码是否等于 summary 里的预期退出码。本版不改变候选接受规则，也不把 rejected candidate 包装成通过模型；它只证明“这个拒绝是预期拒绝，且退出码契约一致”。

## 前置链路

本版接在 v436-v440 之后：

- v436 证明同一份 tiny smoke summary 可以跑多阈值矩阵。
- v437 增加 threshold boundary 观察字段。
- v438 把真实 tiny comparison smoke 和 threshold matrix 串成 live boundary smoke。
- v439 允许复用已有 smoke summary，并输出 diagnosis issues/actions。
- v440 增加 `--require-diagnosis-pass`，让 diagnosis 未通过时返回 `2`。

v441 的角色是复核 v440 strict gate 的退出码契约。

## 关键文件

- `src/minigpt/baseline_candidate_threshold_boundary_gate_check.py`
  - 新增 gate-check 报告模块。
  - 负责读取 boundary smoke summary，比较 `actual_exit_code`、`expected_exit_code`、`review_diagnosis.decision`，并输出 JSON/text/Markdown/HTML。
- `scripts/check_baseline_candidate_threshold_boundary_gate.py`
  - 新增命令入口。
  - 先运行 `scripts/run_baseline_candidate_threshold_boundary_smoke.py`，再把内部命令退出码交给 gate-check 模块验证。
- `tests/test_baseline_candidate_threshold_boundary_gate_check.py`
  - 覆盖 expected exit 通过、实际退出码不一致失败、summary 缺失仍能写失败报告、CLI 将内部非零退出码包装成外层 pass、`--require-pass` 失败返回 `1`。
- `d/441/解释/`
  - 保存命令输出、wrapper 退出码、HTML snapshot、gate-check artifacts 和重新运行出的 boundary smoke 产物。
- `d/441/图片/`
  - 保存 Playwright CLI 和 Playwright MCP 的 HTML 报告截图。

## 核心数据结构

gate-check JSON 的关键字段如下：

- `status`
  - `pass` 表示契约一致；`fail` 表示 source summary、预期退出码、实际退出码或 diagnosis 决策不一致。
- `decision`
  - `expected_exit_verified` 表示严格 gate 的非零退出码符合预期。
  - `fix_threshold_boundary_gate` 表示要修复 gate 或 source summary。
- `actual_exit_code`
  - 外层 wrapper 观察到的内部 strict gate 退出码。
- `expected_exit_code`
  - 命令参数或 source summary 中声明的预期退出码。
- `summary_expected_exit_code`
  - boundary smoke summary 自己记录的 `execution.expected_exit_code`。
- `diagnosis_decision`
  - 当前真实结果仍是 `candidate_not_accepted`。
- `checks`
  - 包含 `summary_exists`、`summary_loads`、`summary_status_pass`、`summary_expected_exit_matches`、`actual_exit_matches_expected`、`diagnosis_decision_matches`。

这里特别加入 `summary_loads`：如果内部 smoke 没有写出 summary，或者 summary JSON 坏了，v441 会写出结构化失败报告，而不是让异常直接中断证据链。

## 运行流程

1. `check_baseline_candidate_threshold_boundary_gate.py` 接收已有 tiny scorecard comparison smoke summary。
2. 它调用 `run_baseline_candidate_threshold_boundary_smoke.py --require-diagnosis-pass`。
3. 内部 strict gate 根据 v440 规则返回 `2`，因为 diagnosis 仍是 `candidate_not_accepted`。
4. wrapper 读取内部生成的 `baseline_candidate_threshold_boundary_smoke.json`。
5. `build_threshold_boundary_gate_check()` 比较 summary 与实际退出码。
6. 一致时输出 `status=pass`、`decision=expected_exit_verified`，wrapper 自身返回 `0`。

这个流程让“内部严格失败”与“外部契约验证通过”同时成立，避免 CI 只看 exit code 时丢失语义。

## 输入输出

输入：

- v438 的 `tiny_scorecard_comparison_smoke_summary.json`。
- 命令参数 `--thresholds 0:1:0.5`。
- 严格 gate 参数 `--require-diagnosis-pass`。
- 预期契约 `--expected-exit-code 2`、`--expected-diagnosis-decision candidate_not_accepted`。

输出：

- `gate-check/baseline_candidate_threshold_boundary_gate_check.json`
- `gate-check/baseline_candidate_threshold_boundary_gate_check.txt`
- `gate-check/baseline_candidate_threshold_boundary_gate_check.md`
- `gate-check/baseline_candidate_threshold_boundary_gate_check.html`
- `logs/threshold_boundary_gate_stdout.txt`
- `logs/threshold_boundary_gate_stderr.txt`

这些输出是本版最终证据，可被后续 CI、README、人工复核或发布治理摘要消费。

## 测试覆盖

新增测试不是只看文件存在，而是保护实际契约：

- expected exit 为 `2` 且实际 exit 为 `2` 时，报告必须 `pass`。
- actual exit 与 expected exit 不一致时，`actual_exit_matches_expected` 必须失败。
- source summary 缺失时，仍然能写出失败 JSON，而不是直接抛未归档异常。
- CLI 在内部 runner 返回 `2` 时，只要符合预期，外层 `--require-pass` 不失败。
- CLI 在预期写成 `0` 但内部返回 `2` 时，`--require-pass` 返回 `1`。

本版验证结果：

- `py_compile` 通过。
- 聚焦测试 `19 passed`。
- 全量测试 `770 passed`。
- source encoding hygiene `status=pass`，`source_count=347`，无 BOM 和语法错误。

## 运行证据

`d/441` 保存了三类证据：

- 命令级证据：stdout、wrapper exit code、内部 strict gate stdout/stderr。
- 报告级证据：JSON/text/Markdown/HTML gate-check artifacts。
- 浏览器级证据：Playwright MCP snapshot 和两张 HTML 截图。

截图里可以看到 `status=pass`、`decision=expected_exit_verified`、`actual exit=2`、`expected exit=2`、`failed checks=0`。这证明 v441 没有改变 candidate 的拒绝结论，只是把这个拒绝结论的退出码契约验证清楚。

## 一句话总结

v441 把 strict diagnosis gate 的“预期退出码 2”变成可读、可测、可归档的 contract check，避免 rejected candidate 在治理链里被误判成运行异常。
