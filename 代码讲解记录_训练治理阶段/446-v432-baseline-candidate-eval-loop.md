# v432 baseline-candidate eval loop 代码讲解

## 本版目标与边界

v432 的目标是把已有 tiny scorecard comparison smoke 收束成一个直接可用的 baseline-candidate eval loop。前面几次本地改动分别做了 control checks、acceptance criteria、最小分差门槛、strict gate 退出码、summary 复用和执行元数据；本版把这些合并成一个完整版本。

本版不新增独立治理链，也不扩大模型规模。它复用现有 tiny scorecard comparison smoke，只在其外层增加一个更清楚的实验入口和晋升判定层。模型质量仍然只按 tiny smoke 边界表述，不把 plumbing evidence 说成生产级模型能力。

## 前置链路

本版承接 v315-v320 和 v334-v343 之后的 tiny benchmark/scorecard/decision/history 能力：

- tiny standard benchmark smoke 能跑出 CPU 小模型、eval suite、generation quality 和 scorecard。
- tiny scorecard comparison smoke 能固定 baseline/candidate，比较两个 scorecard，并生成 promotion decision。
- benchmark history 能记录 comparison/decision pair 的 readiness。
- v432 在这些产物之上增加一层本地 loop，将下游 comparison summary 转成结构化接收/拒绝候选的证据。

## 关键文件

### `src/minigpt/baseline_candidate_eval_loop.py`

这是 v432 的核心模块。它不负责训练，也不直接跑 smoke；它负责读取已经完成的 tiny scorecard comparison smoke summary，并输出一份更适合实验晋升审阅的 loop report。

主入口是：

```text
build_baseline_candidate_eval_loop_report(
    smoke_summary_path,
    min_overall_score_delta=0.0,
)
```

这个函数把下游 summary 拆成几个稳定部分：

- `experiment`
  - 记录 baseline/candidate 名称、suite、token cap、控制变量、max iters、seed、`min_overall_score_delta`。
- `baseline_metrics` / `candidate_metrics`
  - 记录 scorecard 状态、overall score、case count、same-checkpoint baseline 标记。
- `delta_report`
  - 记录 overall score delta、case delta、case regression、generation quality flag 改善/回退等。
- `benchmark_history`
  - 记录下游 benchmark history 的 entry/ready count 和 model-quality claim 边界。
- `control_checks`
  - 校验本轮比较是否可比，例如 smoke status、控制变量、分数存在、case count 相同、comparison ready、candidate 不低于 baseline。
- `acceptance_criteria`
  - 校验是否能真正接受候选：smoke pass、下游 decision 为 promote、selected run 为 `tiny-candidate`、control checks 全 pass，并且 overall score delta 达到设定阈值。
- `promotion_decision`
  - 将下游 promotion decision 和本层 acceptance criteria 合并成 `accepted` 布尔值与 rejected reasons。
- `execution`
  - 由 CLI 注入，记录 source mode、gate mode、fail-on-reject 和 expected exit code。

这里最重要的是边界：下游可以认为 candidate 是 `promote`，但 v432 本层仍可以因为 `min_overall_score_delta` 不满足而拒绝。也就是说，promotion decision 不再等于最终接受候选，最终接受由本层 acceptance criteria 决定。

模块还提供四种渲染输出：

```text
baseline_candidate_eval_loop.json
baseline_candidate_eval_loop.txt
baseline_candidate_eval_loop.md
baseline_candidate_eval_loop.html
```

JSON 是机器可消费证据；TXT 适合 CI/shell；Markdown 适合 review；HTML 用于运行截图和人工阅读。

### `scripts/run_baseline_candidate_eval_loop.py`

这是 v432 的命令入口。它有两种 source mode：

```text
rerun_smoke
reuse_summary
```

默认不传 `--smoke-summary` 时，脚本会调用：

```text
scripts/run_tiny_scorecard_comparison_smoke.py
```

并在输出目录下产生 baseline/candidate 的真实 tiny smoke、scorecard comparison、scorecard decision、benchmark history 和 summary-check sidecar。

传入 `--smoke-summary` 时，脚本复用已有 summary，不重新训练和评估。这对调试阈值很重要，例如同一份 summary 可以快速用不同的 `--min-overall-score-delta` 重新判定。

本版新增的关键参数是：

```text
--min-overall-score-delta
--fail-on-reject
--smoke-summary
```

`--min-overall-score-delta` 让候选必须达到明确分差，不只是“不比 baseline 差”。`--fail-on-reject` 把脚本切到 strict gate 模式：如果 loop 跑通但最终 `decision != accept_candidate`，脚本返回退出码 `2`。默认不加该参数时，拒绝候选仍算实验顺利完成，退出码为 `0`。

脚本还把执行模式写入报告：

```text
execution_source_mode
execution_gate_mode
execution_fail_on_reject
execution_expected_exit_code
```

这样后续只看报告也能知道它是探索运行还是严格 gate。

### `tests/test_baseline_candidate_eval_loop.py`

测试覆盖 v432 的主要契约：

- 下游 promote 且本层条件满足时，report 为 `accept_candidate`。
- 下游 blocked 时，report 为 `reject_candidate`，并保留 blocker/recommendation 和硬门槛失败原因。
- 下游 promote 但 control check 失败时，本层仍拒绝候选。
- 下游 promote 但 `min_overall_score_delta` 未达标时，本层仍拒绝候选。
- JSON/text/Markdown/HTML 四类输出都会写出。
- smoke command 使用固定 baseline/candidate 输入。
- exploratory 模式拒绝候选时退出码为 `0`。
- strict gate 模式拒绝候选时退出码为 `2`。
- `--smoke-summary` 能复用既有 summary。
- `prepare_output_dir` 会保护位于输出目录内的 summary，避免 `--force` 误删输入。
- `annotate_execution_summary` 会把 source/gate/exit code 写入 report。

这些测试的重点不是覆盖 PyTorch 训练本身，而是保护 baseline-candidate loop 的报告契约、决策语义和 CLI 行为。

## 输入输出格式

v432 的真实运行命令归档在 `d/432`：

```text
python -B scripts\run_baseline_candidate_eval_loop.py --out-dir d\432\解释\baseline-candidate-eval-loop --decision-min-rubric-score 0 --min-overall-score-delta 1 --fail-on-reject --force
```

本次输出的关键字段是：

```text
status=pass
decision=reject_candidate
execution_source_mode=rerun_smoke
execution_gate_mode=strict
execution_fail_on_reject=True
execution_expected_exit_code=2
controlled_variable=max_iters
min_overall_score_delta=1.0
baseline_score=81.17
candidate_score=81.17
overall_score_delta=0.0
control_status=pass
acceptance_status=fail
promotion_status=promote
promotion_accepted=False
promotion_rejected_reasons=min_overall_score_delta expected >= 1.0, got 0.0
```

这说明下游 promotion decision 认为 `tiny-candidate` 可 promote，但 v432 本层因为要求至少提升 `1.0` 分而拒绝候选。strict gate 因此返回 `2`，这正是预期行为。

## 运行证据

运行证据归档在 `d/432`：

- `d/432/解释/baseline-candidate-eval-loop/`：完整 baseline-candidate eval loop 输出。
- `d/432/图片/01-baseline-candidate-eval-loop.png`：Playwright MCP 渲染 HTML 报告截图。
- `d/432/解释/baseline_candidate_eval_loop_snapshot.md`：Playwright MCP 页面快照。
- `d/432/解释/baseline_candidate_eval_loop_strict_stdout.txt`：strict gate 命令输出。
- `d/432/解释/baseline_candidate_eval_loop_strict_exit.txt`：strict gate 退出码。

截图证明 HTML 报告能直观看到 `reject_candidate`、`strict`、`Exit=2`、`Control=pass`、`Acceptance=fail` 和 rejected reason。JSON/TXT/Markdown 证明同样的信息能被机器、CI 和人工 review 消费。

## 测试覆盖

本版验证包括：

```text
python -m py_compile src\minigpt\baseline_candidate_eval_loop.py scripts\run_baseline_candidate_eval_loop.py tests\test_baseline_candidate_eval_loop.py
python -m pytest tests\test_baseline_candidate_eval_loop.py tests\test_tiny_scorecard_comparison_smoke.py -q
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- 单测：`20 passed`
- source encoding：`status=pass`，`clean_count=332`
- strict gate：按设计返回 `exit_code=2`
- `git diff --check`：仅 CRLF 提示

## 证据边界

v432 证明的是 baseline-candidate 实验闭环和晋升 gate 行为，而不是模型效果提升。当前 tiny smoke 的 baseline/candidate 分数相同，`overall_score_delta=0.0`；在 `--min-overall-score-delta 1` 的严格要求下拒绝候选，是正确的保守行为。

这也是 v432 的工程价值：候选可以被下游 promotion decision 标记为 `promote`，但最终进入下一轮 baseline 之前，还必须通过本层明确的接收条件。

## 一句话总结

v432 把 tiny scorecard comparison 从一组比较产物收束成可复用 baseline-candidate eval loop，并给它补上明确的 acceptance criteria、strict gate 退出码和运行证据边界。
