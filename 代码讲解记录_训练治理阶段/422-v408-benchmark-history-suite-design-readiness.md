# v408 benchmark history suite design readiness

## 本版目标和边界

v408 的目标是把 v407 已经进入 benchmark scorecard promotion decision 的 suite-design readiness 继续接入 benchmark history ledger。这样 history 层不只知道某次 comparison/decision 是否 promote、review 或 blocked，也能记录 prompt suite design 是否足够 comparison-ready。

本版不新增评测题集，不训练 checkpoint，也不改变 scorecard 的打分规则。它只做一件事：让历史账本消费已有的 `eval_suite_design_*` 和 `non_design_comparison_ready_*` 字段，避免后续 maturity、audit、release 读取 benchmark history 时丢掉这条边界。

## 前置能力

本版承接：

- v405：eval suite 报告开始输出 `design_summary`。
- v406：benchmark scorecard 与 scorecard comparison 携带 suite-design readiness。
- v407：benchmark scorecard decision 把 suite-design 不就绪转成 review/remediation 条件。

v408 位于这条链路的历史归档层，负责把单次决策里的 suite-design caveat 变成可累计、可渲染、可被后续治理消费的 ledger 字段。

## 关键文件

### `src/minigpt/benchmark_history.py`

`_entry()` 新增 history 字段：

```text
eval_suite_design_comparison_status
non_design_comparison_ready_count
design_comparison_changed_count
```

字段来源采用兼容读法：

```text
comparison.summary.non_design_comparison_ready_count
decision.summary.comparison_non_design_comparison_ready_count
decision.summary.non_design_comparison_ready_candidate_count
```

也就是说，history 优先消费 comparison summary；如果某些上游只提供 decision summary，同样可以保住 suite-design 信号。

`_promotion_readiness()` 现在要求两层都干净：

```text
eval_suite_comparison_status in {None, pass}
non_comparison_ready_count == 0
eval_suite_design_comparison_status in {None, pass}
non_design_comparison_ready_count == 0
```

如果 decision 写着 `promote`，但 suite design 不是 comparison-ready，history 会把该 entry 的 `promotion_readiness` 保持为 `review`，防止账本把它误记成 clean promotion evidence。

`_boundary()` 增加：

```text
suite-design-not-comparison-ready
mixed-suite-design-comparison-readiness
```

summary 和 readiness requirement 也新增：

```text
suite_design_non_comparison_ready_entry_count
design_comparison_changed_entry_count
suite_design_non_comparison_ready_entries
```

这些字段是历史层的边界信号，不是模型能力提升证明。

### `src/minigpt/benchmark_history_artifacts.py`

CSV 新增：

```text
eval_suite_design_comparison_status
non_design_comparison_ready_count
design_comparison_changed_count
```

Markdown 和 HTML 的 ledger 表格新增 `Eval Compare` 与 `Design Compare` 两列。这样审阅 history artifact 时，不需要再回到原始 scorecard comparison 或 decision JSON，也能看出：

- 生成结果是否来自普通 eval comparison-ready 题集。
- 题集设计本身是否适合比较。

HTML stats 和 readiness requirement 面板同步展示 suite-design not-ready 计数。

### `scripts/build_benchmark_history.py`

CLI stdout 新增：

```text
suite_design_non_comparison_ready_entry_count
design_comparison_changed_entry_count
```

这样命令行运行 history 构建时，不用打开 JSON 也能看到 suite-design readiness 是否影响了本次历史账本。

### `tests/test_benchmark_history.py`

测试 fixture 新增 `candidate_design_status`，并覆盖两个路径：

- 干净 suite design：promotion history 仍为 `ready`，boundary 仍为 `standard-benchmark-candidate-evidence`。
- 非 comparison-ready suite design：即使 decision status 写成 `promote`，history 也把 `promotion_readiness` 降为 `review`，boundary 变成 `suite-design-not-comparison-ready`，readiness requirement 记录 `suite_design_non_comparison_ready_entries`。

输出测试也断言 CSV、Markdown、HTML 都包含 `eval_suite_design_comparison_status` 或 `Design Compare`。

## 输入输出

输入仍是：

```text
benchmark_scorecard_comparison.json
benchmark_scorecard_decision.json
```

输出增加：

```text
benchmark_history.json
  entries[].eval_suite_design_comparison_status
  entries[].non_design_comparison_ready_count
  summary.suite_design_non_comparison_ready_entry_count
  readiness_requirement.failed_reasons[]

benchmark_history.csv
  eval_suite_design_comparison_status

benchmark_history.md/html
  Eval Compare
  Design Compare
```

这些产物是 benchmark history evidence。它们可以支持后续 maturity/audit/release 判断，但不能单独证明模型已经达到生产质量。

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_benchmark_history.py -q
python -m py_compile src\minigpt\benchmark_history.py src\minigpt\benchmark_history_artifacts.py tests\test_benchmark_history.py
```

本版也回归 scorecard decision 与 comparison delta 相关测试，确认 v406-v407 的上游字段仍然能被 history 正确消费。

## 运行证据

运行截图与说明归档在：

```text
d/408/图片/01-benchmark-history-suite-design-evidence.png
d/408/解释/说明.md
d/408/解释/v408-benchmark-history-suite-design-evidence.html
```

截图页展示本版新增字段、readiness 降级逻辑和定向测试结果，用来证明 suite-design readiness 已经进入 benchmark history 层。

## 一句话总结

v408 把 prompt suite design 不就绪从单次 promotion decision 推进到 benchmark history ledger，让后续治理链读取历史时不会把题集设计问题误看成干净模型提升证据。
