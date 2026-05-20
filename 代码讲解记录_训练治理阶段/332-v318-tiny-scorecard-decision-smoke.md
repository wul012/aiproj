# v318 tiny scorecard decision smoke

## 本版目标和边界

v317 已经把两个真实 tiny benchmark run 接进 scorecard comparison：

```text
baseline tiny smoke -> candidate tiny smoke -> benchmark scorecard comparison
```

v318 继续把 comparison 后面的 decision 层接入同一个 smoke：

```text
baseline tiny smoke -> candidate tiny smoke -> scorecard comparison -> scorecard decision
```

这版仍然不宣称 tiny 模型质量。`scorecard_decision` 可能是 `blocked`、`review` 或 `promote`，三者都可以是有效 smoke 结果。v318 证明的是 decision artifact 能消费真实 comparison，并把“是否可推进”的状态写入证据链；它不证明 1 iteration tiny candidate 真的应该进入模型基线。

## 前置能力

本版复用：

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - v317 新增的双 tiny smoke + scorecard comparison 编排脚本。
- `scripts/build_benchmark_scorecard_decision.py`
  - 从 comparison 产物生成 decision JSON/CSV/Markdown/HTML。
- `src/minigpt/benchmark_scorecard_decision.py`
  - 根据 rubric score、overall delta、generation-quality flags、case regression 和 eval readiness 判断候选状态。

v318 没有改 decision 算法，只把它纳入真实 tiny smoke 链路。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增 `scorecard_decision` 子命令。
  - 新增 `scorecard-decision/` 产物检查。
  - Summary 新增 `scorecard_decision` 摘要。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 断言 decision JSON/HTML 存在。
  - 断言 stdout 包含 `command_scorecard_decision=pass`。
  - 断言 decision status 属于 `promote/review/blocked` 的合法域。

- `README.md`
  - 当前版本升级到 v318。
  - 说明 blocked decision 也是有效 smoke evidence。

- `d/318`
  - 保存运行截图和解释。

## 核心流程

子命令顺序：

```text
baseline_smoke
candidate_smoke
scorecard_comparison
scorecard_decision
```

decision 命令实际调用：

```text
python -B scripts/build_benchmark_scorecard_decision.py scorecard-comparison --out-dir scorecard-decision --min-rubric-score 80
```

输入是 comparison 输出目录，脚本会解析：

```text
scorecard-comparison/benchmark_scorecard_comparison.json
```

输出到：

```text
scorecard-decision/
  benchmark_scorecard_decision.json
  benchmark_scorecard_decision.csv
  benchmark_scorecard_decision.md
  benchmark_scorecard_decision.html
```

## Summary 字段

新增 decision 摘要：

```json
"scorecard_decision": {
  "decision_status": "blocked",
  "recommended_action": "keep_baseline_or_fix_candidate",
  "selected_name": null,
  "candidate_evaluation_count": 2,
  "blocked_candidate_count": 1,
  "recommendation_count": 2
}
```

字段语义：

- `decision_status`
  - decision 模块对 candidate 的最终状态。
- `recommended_action`
  - 后续动作建议，例如保留 baseline 或修复 candidate。
- `candidate_evaluation_count`
  - baseline 与 candidate 都会进入 evaluation 表。
- `blocked_candidate_count`
  - 非 baseline candidate 中被 blocker 拦住的数量。

如果 tiny candidate 没有比 baseline 更好，`blocked` 是合理结果，不是 smoke 失败。

## 输入输出

典型命令：

```text
python -B scripts/run_tiny_scorecard_comparison_smoke.py --out-dir runs/v318-tiny-scorecard-decision-smoke --suite-name standard-zh --case-token-cap 5 --max-iters 1 --eval-iters 1 --batch-size 2 --block-size 8 --n-embd 8 --force
```

顶层输出：

```text
tiny_scorecard_comparison_smoke_summary.json
tiny_scorecard_comparison_smoke_summary.txt
```

它们现在同时引用 baseline smoke、candidate smoke、comparison 和 decision 四类证据。

## 测试覆盖

- `tests.test_tiny_scorecard_comparison_smoke`
  - 覆盖 summary render、真实双 tiny smoke、comparison 和 decision。
- focused tests
  - 同时跑 tiny comparison smoke、standard smoke、scorecard comparison 和 scorecard decision。
- full unittest
  - 确认全仓 588 个测试通过。
- source encoding、py_compile、diff check
  - 确认新增/修改文件无语法、编码和空白问题。

这些测试保护的是“真实 comparison 可以进入 decision 层”，而不是固定某次 tiny candidate 必须被推广。

## 运行证据

归档位置：

```text
d/318/图片
d/318/解释/说明.md
```

截图包括 decision smoke summary、decision JSON 字段、decision artifact 列表、focused tests、全量 unittest、source encoding、diff check 和静态扫描。

## 一句话总结

v318 把 tiny benchmark smoke 从“两个 scorecard 能比较”推进到“comparison 能继续生成 decision 证据”，并明确 blocked/review/promote 都是决策证据，不是 tiny 模型能力证明。
