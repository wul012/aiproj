# v320 tiny budget comparison smoke

## 本版目标和边界

v319 已经让 tiny scorecard decision 的阻断原因进入顶层 smoke summary。v320 继续推进“真实评估”方向：让同一个 tiny scorecard comparison smoke 可以给 baseline 和 candidate 设置不同训练步数。

本版解决的问题是：之前 comparison smoke 只能比较两个不同 seed 的 tiny run，训练预算始终相同；如果想做“candidate 多训练一步是否改变 scorecard/decision”的最小实验，只能绕开 smoke 脚本手工跑。v320 新增预算覆盖参数，让这条链路可以直接表达：

```text
baseline max-iters=1
candidate max-iters=2
```

边界同样明确：这不是模型能力宣称。tiny CPU run 的数据量、步数和模型规模都很小，预算差异只证明比较链路能记录实验配置并把不同预算传到真实训练命令。

## 前置能力

本版复用：

- v315 的 tiny standard benchmark smoke。
- v316 的 same-checkpoint pair baseline。
- v317 的 scorecard comparison。
- v318 的 scorecard decision。
- v319 的 decision diagnostics summary。

v320 没有新增评估算法，也没有改 scorecard/decision 的判定规则；它只增强 tiny comparison smoke 的实验配置能力。

## 关键文件

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 新增 `--baseline-max-iters`。
  - 新增 `--candidate-max-iters`。
  - 新增 `build_run_config()`，集中计算 baseline/candidate 训练预算、差值和预算模式。
  - `tiny_smoke_command()` 接收每个 run 自己的 `max_iters`，确保 baseline 与 candidate 命令可以不同。
  - 顶层 summary 新增 `run_config`，文本输出新增 `config_*` 字段。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - render 测试断言 config 字段进入 line-oriented summary。
  - 真实 smoke 测试跑 baseline 1 iter 与 candidate 2 iter。
  - 断言 candidate command text 中包含 `--max-iters 2`，证明参数不是只写进 summary。

- `README.md`
  - 当前版本升级到 v320。
  - 记录 budget comparison smoke 的能力边界和 tag。

- `d/320`
  - 保存本版运行截图和解释。

## 核心数据结构

新增 `run_config`：

```json
{
  "suite_name": "standard-zh",
  "case_token_cap": 5,
  "baseline_max_iters": 1,
  "candidate_max_iters": 2,
  "max_iters_delta": 1,
  "budget_mode": "candidate_more_iters",
  "eval_iters": 1,
  "batch_size": 2,
  "block_size": 8,
  "n_layer": 1,
  "n_head": 1,
  "n_embd": 8,
  "baseline_seed": 1337,
  "candidate_seed": 2026
}
```

字段语义：

- `baseline_max_iters`
  - baseline tiny training run 的训练步数。
- `candidate_max_iters`
  - candidate tiny training run 的训练步数。
- `max_iters_delta`
  - candidate 减 baseline 的训练步数差。
- `budget_mode`
  - `matched_iters`、`candidate_more_iters` 或 `candidate_fewer_iters`。

文本 summary 同步输出：

```text
config_baseline_max_iters=1
config_candidate_max_iters=2
config_max_iters_delta=1
config_budget_mode=candidate_more_iters
```

## 运行流程

v320 的四段链路不变：

```text
baseline_smoke
candidate_smoke
scorecard_comparison
scorecard_decision
```

变化发生在前两段命令构造：

```text
baseline_smoke  -> run_tiny_standard_benchmark_smoke.py --max-iters 1
candidate_smoke -> run_tiny_standard_benchmark_smoke.py --max-iters 2
```

然后 comparison 和 decision 继续消费两个 run 的 scorecard 产物：

```text
baseline/run/benchmark-scorecard/benchmark_scorecard.json
candidate/run/benchmark-scorecard/benchmark_scorecard.json
  -> scorecard-comparison
  -> scorecard-decision
  -> tiny_scorecard_comparison_smoke_summary.json
```

## 输入输出

典型命令：

```text
python -B scripts/run_tiny_scorecard_comparison_smoke.py --out-dir runs/v320-tiny-budget-comparison-smoke --suite-name standard-zh --case-token-cap 5 --max-iters 1 --baseline-max-iters 1 --candidate-max-iters 2 --eval-iters 1 --batch-size 2 --block-size 8 --n-embd 8 --force
```

顶层输出：

```text
runs/v320-tiny-budget-comparison-smoke/tiny_scorecard_comparison_smoke_summary.json
runs/v320-tiny-budget-comparison-smoke/tiny_scorecard_comparison_smoke_summary.txt
```

`commands` 中会保留实际命令文本，candidate command 应包含：

```text
--max-iters 2
```

这让“预算差异确实进入训练命令”成为可审计证据。

## 测试覆盖

- `tests.test_tiny_scorecard_comparison_smoke`
  - 新增 `build_run_config` 默认预算测试，保护未传 override 时仍然是 matched budget。
  - 真实 smoke 测试覆盖 baseline 1 iter / candidate 2 iter。
  - 断言 summary JSON、summary text 和 candidate command text 三处都能看到预算差异。
- focused tests
  - 继续覆盖 tiny standard benchmark smoke、scorecard comparison 和 scorecard decision。
- full unittest
  - 确认全仓测试通过。
- source encoding、py_compile、diff check 和静态扫描
  - 保护新增 CLI 参数、summary 字段、文档索引和证据说明。

这些测试保护的是实验配置链路，不保证 candidate 多训练一步一定变好。

## 运行证据

归档位置：

```text
d/320/图片
d/320/解释/说明.md
```

截图覆盖：

- 单测与 focused tests。
- 真实 budget comparison smoke summary。
- `run_config` JSON 字段。
- baseline/candidate command text 中的不同 `--max-iters`。
- source encoding、full unittest、py_compile、diff check 和静态扫描。

## 一句话总结

v320 让 tiny scorecard comparison smoke 从“不同 seed 比较”推进到“可记录并执行不同训练预算的最小真实比较”，为后续更系统的 benchmark budget 实验打底。
