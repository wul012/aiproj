# v231 eval readiness chain integration test 代码讲解

## 本版目标

v231 的目标是补测试纪律，而不是继续新增报告。

前几版已经把 eval readiness 从 eval suite 推到 scorecard、comparison、decision 和 maturity narrative。v231 要保护这条链路：如果后续某一层改动把 readiness 丢了，测试会直接失败。

## 不做什么

本版不改变生产代码行为。

本版不增加新的 JSON/HTML 报告层。

本版不扩大模型能力声明，只补一个跨模块测试。

## `tests/test_eval_readiness_chain.py`

### 测试边界

这个测试覆盖的链路是：

```text
benchmark_scorecard_comparison
-> benchmark_scorecard_decision
-> maturity_narrative
```

它不直接调用 eval suite builder，因为这里要保护的是 v227-v230 已经形成的 scorecard-level readiness 消费链。

### `make_scorecard()`

`make_scorecard()` 写入最小但完整的 scorecard JSON fixture：

```text
summary.eval_suite_coverage_status
summary.eval_suite_comparison_status
summary.rubric_avg_score
summary.overall_score
rubric_scores
case_scores
drilldowns
```

其中 baseline 使用：

```text
eval_suite_comparison_status = pass
```

candidate 使用：

```text
eval_suite_comparison_status = warn
```

同时 candidate 的分数更高，确保它本来会被选中；这样测试能证明 review 状态来自 eval readiness，而不是来自分数回退。

### comparison 阶段

测试调用真实函数：

```text
build_benchmark_scorecard_comparison()
write_benchmark_scorecard_comparison_outputs()
```

断言 comparison summary 里出现：

```text
non_comparison_ready_runs = ["candidate"]
```

这证明 scorecard summary 的 readiness 被 comparison 消费。

### decision 阶段

测试继续调用：

```text
build_benchmark_scorecard_decision()
write_benchmark_scorecard_decision_outputs()
```

断言：

```text
decision_status = review
non_comparison_ready_candidates = ["candidate"]
```

这证明 promotion decision 没有把高分但 non-comparison-ready 的 candidate 当作 clean promote。

### maturity narrative 阶段

`write_maturity_inputs()` 写入 maturity narrative 需要的最小输入：

```text
maturity_summary.json
registry.json
request_history_summary.json
dataset_card.json
benchmark_scorecard.json
benchmark_scorecard_decision.json
```

然后调用：

```text
build_maturity_narrative()
```

断言：

- `portfolio_status == review`
- selected run 是 `candidate`
- selected eval comparison status 是 `warn`
- non-ready candidates 保留 `candidate`
- Benchmark Promotion Decision section 是 `warn`
- recommendations 包含 `review-only`

## 为什么这版有价值

单元测试已经分别覆盖了 comparison、decision 和 maturity narrative。

但单测容易出现一个盲区：每层都对自己的 fixture 通过，真实产物字段却可能对不上。

v231 的新增测试用上一层真实输出作为下一层输入，能捕捉字段名漂移、summary 丢字段、artifact 写出路径变化这类链路问题。

## 运行证据

本版运行证据归档在 `c/231`：

- `图片/01-eval-readiness-chain-tests.png`
- `图片/02-eval-readiness-chain-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v231 是一次测试加固版。

它不扩展治理链，而是让已经形成的 eval readiness 链路更难被未来改动破坏。

## 一句话总结

v231 用一条跨模块 integration test 把 eval readiness 的 review 边界固定住，让 scorecard comparison、promotion decision 和 maturity narrative 之间的证据传递更可信。
