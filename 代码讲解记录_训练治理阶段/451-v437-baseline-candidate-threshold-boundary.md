# v437 baseline-candidate threshold boundary 代码讲解

## 本版目标与边界

v437 的目标是在 v436 threshold matrix 上补出更清楚的阈值边界解释。v436 已经能用同一份 tiny smoke summary 跑多个 `min_overall_score_delta`，证明接受路径和拒绝路径都能被复核；v437 进一步回答“边界在哪里”：最严格还接受的 threshold 是多少，第一个拒绝的 threshold 是多少，accept 到 reject 是否单调。

本版不新增训练，不扩大模型，不把 tiny smoke 解释成模型质量提升。它只增强 baseline-candidate 阈值治理的可读性和测试覆盖。

## 前置链路

本版承接 v432-v436：

- v432 生成 baseline-candidate eval loop。
- v433 生成 next-baseline handoff。
- v434 校验 handoff 与源 loop 的契约一致性。
- v435 把 handoff check 嵌回 handoff 主产物。
- v436 用 threshold matrix 同时覆盖 accept/reject 两条路径。
- v437 在 matrix 中新增 threshold boundary summary。

因此 v437 是 v436 的可解释性增强，不是新治理链。

## 关键文件

### `src/minigpt/baseline_candidate_threshold_matrix.py`

本版主要修改集中在这个模块。

#### `parse_thresholds()`

原来只支持逗号分隔：

```text
0,1
```

现在同时支持 inclusive range：

```text
0:1:0.5
```

它会解析成：

```text
[0.0, 0.5, 1.0]
```

实现上用 `Decimal` 解析 range，避免简单浮点累加导致 `0.30000000000000004` 这类文本噪声。非法 range 会抛出 `ValueError`，例如空值、非数字、步长小于等于 0、stop 小于 start。

#### `summarize_threshold_boundary()`

这是 v437 新增的核心函数。输入是一组 threshold rows，输出：

- `status`：同时存在 accept/reject 且单调时为 `pass`，否则为 `review`。
- `decision`：通过时为 `accept_reject_boundary_observed`。
- `has_accept` / `has_reject`：是否覆盖两类结果。
- `is_monotonic_acceptance`：阈值升高后是否不会重新从 reject 变 accept。
- `transition_count`：决策切换次数。
- `strictest_accepting_threshold`：仍接受 candidate 的最大阈值。
- `first_rejecting_threshold`：开始拒绝 candidate 的最小阈值。
- `accepting_thresholds` / `rejecting_thresholds`：两类阈值列表。
- `transitions`：从哪个 threshold 的哪个 decision 切到下一个 decision。

对于本版真实运行，结果是：

```text
strictest_accepting_threshold=0.0
first_rejecting_threshold=0.5
transition_count=1
is_monotonic_acceptance=True
```

这说明 candidate 与 baseline 同分；当要求“至少不退步”时可以接受，当要求至少提升 `0.5` 时就应拒绝。

#### 渲染输出

TXT 新增：

```text
threshold_boundary_status
threshold_boundary_decision
strictest_accepting_threshold
first_rejecting_threshold
is_monotonic_acceptance
transition_count
```

Markdown 新增 boundary summary bullets。HTML 摘要卡新增 boundary status、strictest accept、first reject、monotonic，便于截图直接看出阈值边界。

### `scripts/run_baseline_candidate_threshold_matrix.py`

默认 `--thresholds` 从 `0,1` 改成：

```text
0:1:0.5
```

这让本地默认运行就能观察到三点边界：`0` 接受，`0.5` 和 `1` 拒绝。命令仍兼容逗号分隔阈值。

### `tests/test_baseline_candidate_threshold_matrix.py`

本版测试覆盖：

- `0, 0.5, 1.0` 下产生 `accept_count=1`、`reject_count=2`。
- boundary summary 为 `accept_reject_boundary_observed`。
- `strictest_accepting_threshold=0.0`。
- `first_rejecting_threshold=0.5`。
- 单调性为 `True`，transition count 为 `1`。
- `parse_thresholds("0:1:0.5")` 正确展开。
- `parse_thresholds("0:1:0")` 正确拒绝。
- 人工构造非单调 rows 时 summary 返回 `review` 和 `non_monotonic_threshold_outcomes`。

这组测试保护的是边界摘要本身，而不是只保护文件是否写出。

## 输入输出格式

真实运行命令：

```text
python -B scripts\run_baseline_candidate_threshold_matrix.py d\432\解释\baseline-candidate-eval-loop\tiny-scorecard-comparison-smoke --out-dir d\437\解释\baseline-candidate-threshold-boundary --thresholds 0:1:0.5 --require-both-outcomes --force
```

主输出目录：

```text
d/437/解释/baseline-candidate-threshold-boundary
```

三个阈值子目录：

```text
threshold-0
threshold-0p5
threshold-1
```

每个子目录都有：

```text
loop/
handoff/
handoff-check/
```

这意味着 boundary summary 不是孤立计算，而是基于每个 threshold 完整跑出的 eval loop、handoff 和 handoff check。

## 运行证据

运行证据归档在 `d/437`：

- `d/437/解释/baseline-candidate-threshold-boundary/`：主矩阵和三档 threshold 子产物。
- `d/437/解释/baseline_candidate_threshold_boundary_stdout.txt`：命令输出。
- `d/437/解释/baseline_candidate_threshold_boundary_exit.txt`：退出码，结果为 `0`。
- `d/437/图片/01-baseline-candidate-threshold-boundary.png`：Playwright MCP HTML 截图。
- `d/437/解释/baseline_candidate_threshold_boundary_snapshot.md`：同一页面结构化快照。

截图证明页面展示 `thresholds=3`、`accept_count=1`、`reject_count=2`、`boundary status=pass`、`strictest accept=0.0`、`first reject=0.5`。

## 测试覆盖

本版验证包括：

```text
python -m py_compile src\minigpt\baseline_candidate_threshold_matrix.py scripts\run_baseline_candidate_threshold_matrix.py tests\test_baseline_candidate_threshold_matrix.py
python -m pytest tests\test_baseline_candidate_threshold_matrix.py tests\test_baseline_candidate_eval_loop.py tests\test_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff_check.py -q -o cache_dir=runs\pytest-cache-v437-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v437
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- py_compile：通过。
- 聚焦单测：`27 passed`。
- 全量单测：`756 passed`。
- source encoding：`status=pass`，`clean_count=341`，`syntax_error_count=0`。
- `git diff --check`：通过，仅有 Git 对 CRLF 的 warning。

说明：仓库旧 `.pytest_cache` 存在 ACL 权限异常，本轮继续显式使用 `-o cache_dir=runs\pytest-cache-v437`，验证后按清理门禁删除临时缓存。

## 证据边界

v437 证明阈值边界解释和单调性检查，不证明模型质量。候选是否真正值得替代 baseline，仍要依赖更强 benchmark 和真实训练运行。这里的 tiny smoke 只证明 baseline-candidate 工程链路在阈值附近可解释、可复核。

## 一句话总结

v437 把 baseline-candidate threshold matrix 从“有 accept/reject 两类结果”推进到“能解释 accept/reject 边界在哪里，以及这个边界是否单调可信”。
