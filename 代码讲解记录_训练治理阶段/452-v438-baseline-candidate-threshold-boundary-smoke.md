# v438 baseline-candidate threshold boundary smoke 代码讲解

## 本版目标与边界

v438 的目标是给 v437 threshold boundary summary 增加一个 live 入口：不再只拿已有 smoke summary 做阈值矩阵，而是先真实跑一次 tiny scorecard comparison smoke，再从这次新产物推导 threshold matrix 和 live boundary summary。

本版不扩大训练规模，不提高模型质量承诺，也不新建额外治理链。它的边界是“验证 baseline-candidate 阈值边界报告能否由刚生成的真实 evidence 复核出来”。因此，本版真实结果是 `status=pass` 但 `decision=live_threshold_boundary_review`：链路通过，候选仍未达到任何接受阈值。

## 前置链路

v438 承接 v432-v437：

- v432 生成 baseline-candidate eval loop。
- v433 生成 next-baseline handoff。
- v434 校验 handoff 与源 loop 的 contract 一致性。
- v435 把 handoff check 嵌回 handoff 主产物。
- v436 对多个 threshold 重跑 loop/handoff/check，形成 threshold matrix。
- v437 在 matrix 上增加 strictest accept、first reject、transition 和 monotonic boundary summary。

v438 只把这条链路前面的输入从“已有 summary”换成“新跑 live smoke summary”，所以它是 v437 的运行入口增强，而不是新治理面。

## 关键文件

### `src/minigpt/baseline_candidate_threshold_boundary_smoke.py`

这是本版新增的纯报告模块，负责把 live smoke、threshold matrix、boundary summary 合并为最终证据。

核心函数是 `build_baseline_candidate_threshold_boundary_smoke_summary()`。输入包括：

- `smoke_summary_path`：真实 tiny smoke 生成的 summary JSON。
- `smoke_result`：脚本执行结果，包括 `status`、`returncode` 和日志路径。
- `matrix_report`：由 `baseline_candidate_threshold_matrix` 生成的矩阵报告。
- `matrix_outputs`：matrix JSON/text/Markdown/HTML 输出路径。

输出字段分为四组：

- `smoke`：记录 live smoke 是否跑通、return code、summary 路径和日志路径。
- `matrix`：记录 threshold matrix 是否跑通、阈值数量、accept/reject 数和 handoff-check 失败数。
- `threshold_boundary`：直接复用 v437 boundary summary，包括 `status`、`decision`、`strictest_accepting_threshold`、`first_rejecting_threshold` 和单调性。
- `boundary`：明确写出 `model_quality_claim=not_claimed`，避免把 tiny smoke 误读成模型质量提升证据。

状态判定是本版的重点：只要 live smoke 和 matrix 都 `pass`，总 `status` 就是 `pass`；如果 boundary 本身是 `review`，总 `decision` 会是 `live_threshold_boundary_review`。这样可以区分“链路坏了”和“候选不够好”。

渲染函数包括：

- `render_baseline_candidate_threshold_boundary_smoke_text()`：给 CLI/stdout 使用。
- `render_baseline_candidate_threshold_boundary_smoke_markdown()`：给归档和人工 review 使用。
- `render_baseline_candidate_threshold_boundary_smoke_html()`：给截图使用。
- `write_baseline_candidate_threshold_boundary_smoke_outputs()`：统一写 JSON/text/Markdown/HTML。

HTML 里 `_compact_decision()` 会把 `live_threshold_boundary_review` 简化为 `review`，`_display_value(None)` 会显示为 `none`，这样截图不会被长字段撑开，也能直接看到候选没有可接受阈值。

### `scripts/run_baseline_candidate_threshold_boundary_smoke.py`

这是本版新增 CLI。它的运行流程是：

1. `prepare_output_dir()` 创建或清理输出目录。
2. `run_live_smoke()` 调用 v432-v433 以来复用的 tiny scorecard comparison smoke 命令，生成新的 `tiny_scorecard_comparison_smoke_summary.json`。
3. `build_baseline_candidate_threshold_matrix()` 读取这份 live summary，并按 `--thresholds 0:1:0.5` 生成 threshold matrix。
4. `write_baseline_candidate_threshold_matrix_outputs()` 写出 matrix 证据。
5. `build_baseline_candidate_threshold_boundary_smoke_summary()` 汇总 live smoke、matrix 和 boundary。
6. `write_baseline_candidate_threshold_boundary_smoke_outputs()` 写出 live-boundary-summary 证据。
7. `resolve_exit_code()` 根据总状态和 `--require-boundary-pass` 决定退出码。

默认行为是 exploratory：候选被拒绝不让脚本失败，因为这正是本版要保留的事实。如果调用者传入 `--require-boundary-pass`，则 boundary 仍为 `review` 时退出 `2`，便于更严格的 CI 或晋升流程使用。

### `tests/test_baseline_candidate_threshold_boundary_smoke.py`

测试覆盖四类风险：

- summary 能记录 live smoke、matrix 和 threshold boundary 的关键字段。
- `--require-boundary-pass` 会把 review boundary 转成退出码 `2`。
- live smoke 和 matrix 都通过时，即使 boundary 是 review，总 `status` 仍为 `pass`。
- CLI 在 mock live smoke 的情况下，会从 fake summary 构建 matrix，并生成最终 live-boundary-summary。

这些断言保护的是语义边界：候选拒绝不是执行失败，执行失败也不能被 boundary review 掩盖。

## 输入输出格式

本版真实命令：

```text
python -B scripts\run_baseline_candidate_threshold_boundary_smoke.py --out-dir d\438\解释\baseline-candidate-threshold-boundary-smoke --thresholds 0:1:0.5 --force
```

主要输出：

```text
d/438/解释/baseline-candidate-threshold-boundary-smoke/tiny-scorecard-comparison-smoke
d/438/解释/baseline-candidate-threshold-boundary-smoke/threshold-boundary-matrix
d/438/解释/baseline-candidate-threshold-boundary-smoke/live-boundary-summary
```

本版真实结果：

```text
status=pass
decision=live_threshold_boundary_review
smoke_status=pass
matrix_status=pass
threshold_count=3
accept_count=0
reject_count=3
threshold_boundary_status=review
threshold_boundary_decision=no_accepting_threshold
first_rejecting_threshold=0.0
```

这说明三个阈值 `0`、`0.5`、`1` 都拒绝 candidate；它没有产生 accepting threshold，但矩阵、handoff check 和 live smoke 执行链路是干净的。

## 运行证据

运行证据归档在 `d/438`：

- `d/438/解释/baseline-candidate-threshold-boundary-smoke/`：完整 live smoke、matrix 和 summary 产物。
- `d/438/解释/baseline_candidate_threshold_boundary_smoke_stdout.txt`：命令输出。
- `d/438/解释/baseline_candidate_threshold_boundary_smoke_exit.txt`：退出码，结果为 `0`。
- `d/438/图片/01-baseline-candidate-threshold-boundary-smoke.png`：HTML 截图。
- `d/438/解释/baseline_candidate_threshold_boundary_smoke_snapshot.md`：页面结构快照。

截图中能直接看到 `Status=pass`、`Decision=review`、`Accept count=0`、`Reject count=3`、`Strictest accept=none`、`First reject=0.0`。本轮先尝试 Playwright MCP，因 MCP 在本地 `file:` 页面/新标签会话上超时，最终按仓库规则回退到 Playwright CLI 的 Chrome channel 截图。

## 测试覆盖

本版验证命令：

```text
python -m py_compile src\minigpt\baseline_candidate_threshold_boundary_smoke.py scripts\run_baseline_candidate_threshold_boundary_smoke.py tests\test_baseline_candidate_threshold_boundary_smoke.py
python -m pytest tests\test_baseline_candidate_threshold_boundary_smoke.py tests\test_baseline_candidate_threshold_matrix.py -q -o cache_dir=runs\pytest-cache-v438-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v438
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- py_compile：通过。
- 聚焦测试：`9 passed`。
- 全量测试：`760 passed`。
- source encoding：`status=pass`，`source_count=344`。
- `git diff --check`：通过，仅出现 Git 对 README/归档 Markdown 的 CRLF 提示。

## 证据边界

v438 证明 live smoke 产物可以驱动 threshold matrix 和 boundary summary，且候选拒绝结论能被保留下来。它不证明 candidate 模型变强，也不改变 baseline 选择；模型能力提升仍需要更强 benchmark、更多真实训练和持续历史对比。

## 一句话总结

v438 把 baseline-candidate threshold boundary 从“静态复算矩阵”推进到“先跑真实 tiny smoke、再复核阈值边界”的 live 证据层，同时保持候选未晋升这个结论不被粉饰。
