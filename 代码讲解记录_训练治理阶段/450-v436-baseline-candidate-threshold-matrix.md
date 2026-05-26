# v436 baseline-candidate threshold matrix 代码讲解

## 本版目标与边界

v436 的目标是给 v432-v435 的 baseline-candidate 链路补一个轻量阈值矩阵：同一份 tiny scorecard comparison smoke summary，使用不同 `min_overall_score_delta` 重新推导 eval loop、handoff 和 handoff check，确认接受路径和拒绝路径都能被真实产物覆盖。

本版不新增训练、不扩大模型、不声称候选模型变好。它验证的是治理链路边界：当阈值为 `0` 时，同分 candidate 可以作为 no-regression baseline 被接受；当阈值为 `1` 时，同一 candidate 会因为没有达到最小分差而被拒绝。两条路径都必须保留 handoff contract check `pass`。

## 前置链路

本版承接 v432-v435：

- v432 把 tiny scorecard comparison smoke summary 转为 baseline-candidate eval loop。
- v433 把 eval loop 转为 next-baseline handoff。
- v434 从 handoff 的 `source_loop_report` 重建 expected handoff 并校验关键字段。
- v435 把 handoff check summary 嵌回 handoff 主产物。
- v436 用阈值矩阵同时跑出 accept/reject 两种 handoff 行为。

这不是新治理链，而是对已有 baseline-candidate 链路的边界覆盖。

## 关键文件

### `src/minigpt/baseline_candidate_threshold_matrix.py`

这是本版核心模块，负责从一个 smoke summary 生成矩阵报告。

核心入口：

```text
build_baseline_candidate_threshold_matrix(smoke_summary_path, out_dir, thresholds, generated_at)
```

它先调用 `resolve_baseline_candidate_eval_loop_smoke_summary()` 定位 v432 smoke summary，再对每个 threshold 调用 `_build_threshold_row()`。每一行都会生成三层证据：

```text
threshold-<value>/loop
threshold-<value>/handoff
threshold-<value>/handoff-check
```

矩阵主报告的关键字段：

- `status`：所有行存在且 handoff check 没有失败时为 `pass`。
- `decision`：通过时为 `threshold_matrix_ready`。
- `source_smoke_summary`：输入 smoke summary 路径。
- `threshold_count`：阈值数量。
- `accept_count`：`loop_decision=accept_candidate` 的行数。
- `reject_count`：`loop_decision=reject_candidate` 的行数。
- `handoff_check_failure_count`：handoff check 非 pass 的行数。
- `rows`：每个 threshold 的 loop/handoff/check 摘要。
- `boundary.model_quality_claim`：固定为 `not_claimed`。

`_build_threshold_row()` 是这版最重要的链路函数。它做四件事：

1. 调用 `build_baseline_candidate_eval_loop_report()`，用当前 threshold 重建 loop。
2. 根据 loop decision 设置 strict gate 的 `expected_exit_code`：接受为 `0`，拒绝为 `2`。
3. 调用 `build_baseline_candidate_handoff()` 和 `build_baseline_candidate_handoff_check()` 生成 handoff 与 check。
4. 调用 `embed_baseline_candidate_handoff_check()`，把 check summary 嵌回 handoff，再写回 handoff 输出。

这样每个 threshold row 都不是只看一个 summary 字段，而是完整复用 v432-v435 的真实构建路径。

### `scripts/run_baseline_candidate_threshold_matrix.py`

这是命令行入口，参数包括：

- `smoke_summary`：v432 smoke summary JSON 或目录。
- `--out-dir`：矩阵输出目录。
- `--thresholds`：逗号分隔阈值，默认 `0,1`。
- `--require-both-outcomes`：要求至少有一个 accept 和一个 reject，否则返回 `2`。
- `--force`：替换已有输出目录。

`resolve_exit_code()` 的语义很清楚：

- 矩阵自身失败返回 `1`。
- 要求双 outcome 但缺 accept/reject 任一类时返回 `2`。
- 结构通过且 outcome 满足要求时返回 `0`。

这让它既能作为本地检查命令，也能作为 CI 中的边界覆盖检查。

### `tests/test_baseline_candidate_threshold_matrix.py`

测试覆盖四类风险：

- 同一 smoke summary 在 `[0.0, 1.0]` 下生成一条 accept row 和一条 reject row。
- 写出的 JSON/text/Markdown/HTML 产物存在，并且 threshold-0 的 handoff 已嵌入 `handoff_check.status=pass`。
- `parse_thresholds("")` 会拒绝空阈值。
- CLI 在 `--require-both-outcomes` 下只生成 accept 时返回 `2`。

测试 fixture 会创建 baseline/candidate checkpoint 文件和 eval-loop 所需的 smoke summary 字段，避免测试只覆盖空壳路径。

## 输入输出格式

v436 真实运行输入：

```text
d/432/解释/baseline-candidate-eval-loop/tiny-scorecard-comparison-smoke
```

真实运行命令：

```text
python -B scripts\run_baseline_candidate_threshold_matrix.py d\432\解释\baseline-candidate-eval-loop\tiny-scorecard-comparison-smoke --out-dir d\436\解释\baseline-candidate-threshold-matrix --thresholds 0,1 --require-both-outcomes --force
```

主 TXT 摘要包含：

```text
status=pass
decision=threshold_matrix_ready
threshold_count=2
accept_count=1
reject_count=1
handoff_check_failure_count=0
row=threshold=0.0,loop_decision=accept_candidate,handoff_ready=True,next_baseline_source=candidate,expected_exit_code=0,handoff_check_status=pass
row=threshold=1.0,loop_decision=reject_candidate,handoff_ready=False,next_baseline_source=current_baseline,expected_exit_code=2,handoff_check_status=pass
```

这说明同一份 candidate 在阈值边界两侧的行为是可复核的，而不是靠人工解释。

## 运行证据

运行证据归档在 `d/436`：

- `d/436/解释/baseline-candidate-threshold-matrix/`：矩阵主输出和每个 threshold 的 loop/handoff/check 子产物。
- `d/436/解释/baseline_candidate_threshold_matrix_stdout.txt`：命令输出。
- `d/436/解释/baseline_candidate_threshold_matrix_exit.txt`：退出码，结果为 `0`。
- `d/436/图片/01-baseline-candidate-threshold-matrix.png`：Playwright MCP 渲染 HTML 截图。
- `d/436/解释/baseline_candidate_threshold_matrix_snapshot.md`：同一页面的结构化快照。

截图证明主 HTML 直接显示 `status=pass`、`accept_count=1`、`reject_count=1`、`check failures=0`。

## 测试覆盖

本版验证包括：

```text
python -m py_compile src\minigpt\baseline_candidate_threshold_matrix.py scripts\run_baseline_candidate_threshold_matrix.py tests\test_baseline_candidate_threshold_matrix.py
python -m pytest tests\test_baseline_candidate_threshold_matrix.py tests\test_baseline_candidate_eval_loop.py tests\test_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff_check.py -q -o cache_dir=runs\pytest-cache-v436-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v436
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- py_compile：通过。
- 聚焦单测：`26 passed`。
- 全量测试：`755 passed`。
- source encoding：`status=pass`，`clean_count=341`，`syntax_error_count=0`。
- `git diff --check`：通过，仅有 Git 的 CRLF warning。

说明：仓库旧 `.pytest_cache` 存在 ACL 权限异常，本轮继续使用 `-o cache_dir=runs\pytest-cache-v436`，验证后按清理门禁删除临时缓存。

## 证据边界

v436 的边界非常明确：它证明 threshold gate 和 handoff contract 可以在同一真实 smoke summary 上复核两种路径，但不证明模型能力超过 baseline。tiny CPU smoke 仍是流水线证据，矩阵报告中 `boundary.model_quality_claim=not_claimed`。

## 一句话总结

v436 把 baseline-candidate 链路从“单条严格拒绝证据”推进到“同一输入可复核接受/拒绝两侧阈值行为，并保留 handoff check 一致性”的阶段。
