# v317 tiny scorecard comparison smoke

## 本版目标和边界

v315-v316 已经让项目能在 CPU 上跑一条真实 tiny benchmark 链：

```text
tiny corpus -> train.py -> checkpoint.pt -> eval_suite.py -> generation quality -> pair batch -> benchmark scorecard
```

v317 的目标是把“单次 scorecard 产物”推进到“两个真实 tiny run 的 scorecard comparison”。新脚本会连续跑 baseline 和 candidate 两个 tiny standard benchmark smoke，然后调用现有 `compare_benchmark_scorecards.py` 生成跨 run 比较报告。

边界同样重要：两个 tiny run 都是极小数据、1 iteration、CPU smoke。它们的分数差异只证明 scorecard comparison 链路能跑通，不证明模型能力变好或变差。因此 summary 固定记录：

```text
model_quality_claim=not_claimed
```

## 前置能力

本版复用这些已有能力：

- `scripts/run_tiny_standard_benchmark_smoke.py`
  - v316 后已经包含 train、eval suite、generation quality、same-checkpoint pair batch 和 scorecard。
- `scripts/compare_benchmark_scorecards.py`
  - 读取两个 scorecard JSON 或 run directory，输出 comparison JSON/CSV/Markdown/HTML 和 case-delta CSV。
- `src/minigpt/benchmark_scorecard_comparison.py`
  - 负责 baseline 选择、run delta、case delta、task/difficulty delta、recommendations。

v317 没有修改 scorecard comparison 核心算法，只新增一个 orchestration smoke，让“真实 tiny run -> scorecard -> comparison”的链路可一键验证。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增主脚本。
  - 依次执行 `baseline_smoke`、`candidate_smoke`、`scorecard_comparison` 三个子命令。
  - 汇总 baseline/candidate scorecard、pair baseline 状态、comparison summary 和 command 状态。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 覆盖 summary rendering。
  - 真实执行两次 tiny smoke，再比较两个 scorecard，断言 comparison JSON/HTML 和 case delta 产物存在。

- `README.md`
  - 当前版本升级到 v317。
  - 说明这是 comparison plumbing evidence，不是 tiny 模型能力结论。

- `d/317`
  - 保存本版截图与解释。

## 核心流程

脚本执行顺序：

```text
baseline_smoke:
  run_tiny_standard_benchmark_smoke.py --seed 1337

candidate_smoke:
  run_tiny_standard_benchmark_smoke.py --seed 2026

scorecard_comparison:
  compare_benchmark_scorecards.py baseline/run candidate/run
```

`compare_benchmark_scorecards.py` 接收 run directory，因为它已有路径解析能力：

```text
run/benchmark-scorecard/benchmark_scorecard.json
```

## Summary 字段

顶层 summary 关注三类信息：

1. 两个 tiny smoke 是否完整：

```json
"baseline_smoke": {
  "status": "pass",
  "scorecard_overall_status": "pass",
  "pair_same_checkpoint_baseline": true
}
```

2. comparison 是否真实消费两个 scorecard：

```json
"scorecard_comparison": {
  "scorecard_count": 2,
  "baseline_name": "tiny-baseline",
  "case_delta_count": 20,
  "non_comparison_ready_count": 0
}
```

3. 模型能力边界：

```json
"interpretation": {
  "comparison_is_smoke_only": true,
  "model_quality_claim": "not_claimed"
}
```

`case_delta_count=20` 来自 2 个 scorecard x 10 个 standard-zh case。baseline 自身也会生成一组 baseline delta 行，这是 comparison 模块的既有结构。

## 输入输出

典型命令：

```text
python -B scripts/run_tiny_scorecard_comparison_smoke.py --out-dir runs/v317-tiny-scorecard-comparison-smoke --suite-name standard-zh --case-token-cap 5 --max-iters 1 --eval-iters 1 --batch-size 2 --block-size 8 --n-embd 8 --force
```

输出结构：

```text
out-dir/
  baseline/
    tiny_standard_benchmark_smoke_summary.json
    run/benchmark-scorecard/benchmark_scorecard.json
  candidate/
    tiny_standard_benchmark_smoke_summary.json
    run/benchmark-scorecard/benchmark_scorecard.json
  scorecard-comparison/
    benchmark_scorecard_comparison.json
    benchmark_scorecard_comparison.csv
    benchmark_scorecard_case_deltas.csv
    benchmark_scorecard_comparison.md
    benchmark_scorecard_comparison.html
  tiny_scorecard_comparison_smoke_summary.json
  tiny_scorecard_comparison_smoke_summary.txt
```

comparison JSON/CSV 是后续机器消费证据；Markdown/HTML 是人工审查证据；顶层 summary 用于 CI 或截图快速判断。

## 测试覆盖

- `test_render_summary_keeps_comparison_and_boundary_fields`
  - 确认 text summary 输出 comparison count、case delta 和 `model_quality_claim=not_claimed`。
- `test_tiny_scorecard_comparison_smoke_runs_real_chain`
  - 真实跑两次 tiny benchmark smoke 和一次 scorecard comparison。
  - 断言 baseline/candidate scorecard 存在、comparison JSON 存在、HTML 存在、case delta count 为 20。
- focused tests
  - 覆盖 v316 tiny smoke、v317 comparison smoke 和 benchmark comparison 模块。
- full unittest
  - 确认全项目测试通过。

这些测试保护的是“跨运行 scorecard comparison 链路真实可跑”，而不是固定某个 tiny run 必然胜出。

## 运行证据

v317 运行截图和解释归档在：

```text
d/317/图片
d/317/解释/说明.md
```

其中包括 comparison smoke summary、comparison JSON fields、comparison artifact 列表、focused tests、全量 unittest、source encoding、diff check 和静态扫描。

## 一句话总结

v317 让 MiniGPT 的 tiny benchmark smoke 从“单 run scorecard 完整”推进到“两次真实 tiny run 可以进入 scorecard comparison”，但继续把结论限定为比较链路证据，而不是模型质量证明。
