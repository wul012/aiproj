# v439 baseline-candidate threshold boundary reuse diagnosis 代码讲解

## 本版目标与边界

v439 的目标是把 v438 的 live threshold boundary smoke 做成更适合反复复核的工具：当已经有一份真实 tiny smoke summary 时，可以用 `--smoke-summary` 直接复用它，重新生成 threshold matrix 和 boundary summary，不必每次都重跑 tiny 训练。

本版同时新增 `review_diagnosis`，把 v438 的“全阈值拒绝候选”解释成机器可读的原因和动作。它不扩大模型训练，不改变 baseline/candidate 选择，也不把 tiny smoke 当作模型质量证明。

## 前置链路

v439 承接 v438：

- v438 先跑真实 tiny scorecard comparison，再从 live summary 推导 threshold matrix。
- v438 的真实结果是 smoke 和 matrix 都通过，但 3 个阈值全部拒绝 candidate。
- v439 复用这份 v438 summary，证明同一份真实 evidence 可以被快速复核，并把拒绝原因整理为诊断字段。

因此 v439 是 v438 的复核入口和解释增强，不是新治理链。

## 关键文件

### `scripts/run_baseline_candidate_threshold_boundary_smoke.py`

本版给 CLI 增加：

```text
--smoke-summary <tiny_scorecard_comparison_smoke_summary.json>
```

运行时有两种 source mode：

- `rerun_smoke`：默认模式，和 v438 一样重新跑 tiny smoke。
- `reuse_summary`：新模式，直接使用已有 summary，不重跑训练。

为了避免误删输入，`prepare_output_dir()` 新增 `protected_path`。如果用户把 `--smoke-summary` 放在输出目录内部，又传了 `--force`，脚本会拒绝删除输出目录，防止把源 summary 一并删掉。

`reuse_smoke_summary()` 会构造一个通过状态的 command result：

```text
name=existing_tiny_scorecard_comparison_smoke_summary
returncode=0
source_summary=<path>
```

后续 matrix 构建仍然走同一条 `build_baseline_candidate_threshold_matrix()` 链路，所以复用模式不会绕过 loop、handoff 和 handoff-check。

### `src/minigpt/baseline_candidate_threshold_boundary_smoke.py`

本版新增两个核心点。

第一，summary 新增 `source_mode`：

```json
"source_mode": "reuse_summary"
```

它也会写入 `smoke.source_mode`，方便后续只看 smoke 子对象的消费者判断本次是否真的重跑训练。

第二，新增 `build_threshold_boundary_smoke_diagnosis()`。它读取三层状态：

- smoke 是否执行通过。
- matrix 是否生成通过。
- threshold boundary 是 pass 还是 review。

然后输出：

```json
{
  "status": "review",
  "decision": "candidate_not_accepted",
  "issue_count": 1,
  "action_count": 2,
  "issues": [
    {"code": "no_accepting_threshold", "severity": "review", "message": "..."}
  ],
  "actions": [
    {"code": "increase_candidate_signal", "message": "..."},
    {"code": "keep_current_baseline", "message": "..."}
  ]
}
```

诊断规则把不同问题分开：

- smoke 失败：`smoke_execution_failed`，属于 blocker。
- matrix 失败：`threshold_matrix_not_ready`，属于 blocker。
- handoff-check 失败：`handoff_check_failures`，属于 blocker。
- 所有阈值都拒绝：`no_accepting_threshold`，属于 review。
- 所有阈值都接受：`no_rejecting_threshold`，提示继续提高阈值查找边界。
- 阈值结果非单调：`non_monotonic_threshold_outcomes`，提示检查源 evidence 或行结果。

这样 v439 不会把“候选没通过”误判为脚本失败，也不会把“脚本通过”误判为候选可晋升。

### `tests/test_baseline_candidate_threshold_boundary_smoke.py`

本版新增/加强的断言包括：

- 默认构建 summary 时 `source_mode=rerun_smoke`。
- boundary pass 时诊断为 `threshold_boundary_ready`。
- `no_accepting_threshold` 时诊断为 `candidate_not_accepted`。
- handoff-check 失败时诊断为 blocker，并要求 `fix_live_threshold_boundary`。
- CLI 传入 `--smoke-summary` 时不会调用 `run_live_smoke()`，而是输出 `source_mode=reuse_summary`。

测试保护的是行为语义，不只是文件是否写出。

## 输入输出格式

本版真实运行命令：

```text
python -B scripts\run_baseline_candidate_threshold_boundary_smoke.py --smoke-summary d\438\解释\baseline-candidate-threshold-boundary-smoke\tiny-scorecard-comparison-smoke\tiny_scorecard_comparison_smoke_summary.json --out-dir d\439\解释\baseline-candidate-threshold-boundary-reuse-diagnosis --thresholds 0:1:0.5 --force
```

关键输出：

```text
source_mode=reuse_summary
accept_count=0
reject_count=3
review_diagnosis_decision=candidate_not_accepted
review_issue_count=1
review_action_count=2
```

这说明 v439 成功复用了 v438 的真实 summary，并保留候选未被接受的判断。

## 运行证据

运行证据归档在 `d/439`：

- `d/439/解释/baseline-candidate-threshold-boundary-reuse-diagnosis/`：复用模式生成的 matrix 和 summary。
- `d/439/解释/baseline_candidate_threshold_boundary_reuse_diagnosis_stdout.txt`：命令输出。
- `d/439/解释/baseline_candidate_threshold_boundary_reuse_diagnosis_exit.txt`：退出码，结果为 `0`。
- `d/439/图片/01-baseline-candidate-threshold-boundary-reuse-diagnosis.png`：Playwright MCP 截图。
- `d/439/解释/baseline_candidate_threshold_boundary_reuse_diagnosis_snapshot.md`：页面结构快照。

截图显示 `Source mode=reuse_summary`、`Diagnosis=candidate_not_accepted`、`Issue count=1`、`Action count=2`，证明复用入口和诊断字段都进入了可视化证据。

## 测试覆盖

本版验证命令：

```text
python -m py_compile src\minigpt\baseline_candidate_threshold_boundary_smoke.py scripts\run_baseline_candidate_threshold_boundary_smoke.py tests\test_baseline_candidate_threshold_boundary_smoke.py
python -m pytest tests\test_baseline_candidate_threshold_boundary_smoke.py tests\test_baseline_candidate_threshold_matrix.py -q -o cache_dir=runs\pytest-cache-v439-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v439
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- py_compile：通过。
- 聚焦测试：`11 passed`。
- 全量测试：`762 passed`。
- source encoding：`status=pass`，`source_count=344`。
- `git diff --check`：通过，仅出现 Git 对 Markdown/Python 文件的 CRLF 提示。

聚焦测试覆盖复用入口和诊断分支；全量测试确认 v439 没破坏 v432-v438 的 baseline-candidate 链路。

## 证据边界

v439 证明的是复核效率和诊断可读性，不证明 candidate 模型质量提升。当前诊断建议仍然是强化候选或保持 current baseline，而不是晋升 candidate。

## 一句话总结

v439 把 baseline-candidate threshold boundary smoke 从一次性 live evidence 推进到可复用、可诊断、可继续被后续 gate 消费的复核证据。
