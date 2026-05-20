# v316 tiny standard pair baseline smoke

## 本版目标和边界

v315 已经把 MiniGPT 拉回到一条真实模型能力证据链：

```text
tiny corpus -> train.py -> checkpoint.pt -> eval_suite.py -> generation quality -> benchmark scorecard
```

v316 继续补这条链里的一个空位：在 scorecard 之前加入 `pair_batch.py`，用同一个 tiny checkpoint 做左右两侧生成对比，让 benchmark evidence completeness 覆盖 eval suite、generation quality 和 pair batch 三组证据。

本版不证明 tiny 模型能力变强，也不把同 checkpoint pair 误写成候选模型胜过基线。它只证明：同一 checkpoint、同一 suite、同一 seed 的 pair batch 可以在 CPU smoke 中真实跑通，并且 scorecard 会把它标记为 `same_checkpoint_baseline`。这是一条可复现性基线，不是跨 checkpoint 改进证据。

## 前置能力

本版复用这些已有能力：

- `scripts/run_tiny_standard_benchmark_smoke.py`
  - v315 新增的一键 CPU smoke 入口。
- `scripts/pair_batch.py`
  - 固定 prompt suite 的左右 checkpoint 生成对比入口。
- `src/minigpt/pair_batch.py`
  - pair case/report 的 JSON、CSV、Markdown、HTML 输出层。
- `src/minigpt/benchmark_scorecard.py`
  - 已经会读取 `run/pair_batch/pair_generation_batch.json`，并识别 same-checkpoint pair baseline。

因此 v316 没有改 `pair_batch.py` 或 scorecard 核心评分逻辑，只把现有契约接进 tiny smoke。

## 关键文件

- `scripts/run_tiny_standard_benchmark_smoke.py`
  - 子命令链从 4 步扩为 5 步：

```text
train -> eval_suite -> generation_quality -> pair_batch -> benchmark_scorecard
```

  - `pair_batch` 左右两侧都使用 `run/checkpoint.pt`，但使用不同展示 id：`tiny-baseline` 和 `tiny-repeat`。
  - summary 新增 pair artifact、pair summary、scorecard pair 字段。

- `tests/test_tiny_standard_benchmark_smoke.py`
  - 真实脚本测试现在断言 `pair_generation_batch.json` 和 `.html` 都生成。
  - 断言 `pair_batch.case_count == 10`、`generated_difference_count == 0`、`same_checkpoint_baseline == True`。
  - 断言 benchmark scorecard summary 同步看到 `pair_same_checkpoint_baseline=True`。

- `README.md`
  - 当前版本升级到 v316。
  - 明确 same-checkpoint pair baseline 是 reproducibility evidence，不是 improvement evidence。

- `d/316`
  - 保存 v316 的运行截图和解释。

## 核心数据结构

tiny smoke summary 新增：

```json
{
  "pair_batch": {
    "available": true,
    "case_count": 10,
    "generated_equal_count": 10,
    "generated_difference_count": 0,
    "same_checkpoint_baseline": true,
    "comparison_mode": "same_checkpoint_baseline"
  },
  "benchmark_scorecard": {
    "pair_batch_cases": 10,
    "pair_generated_differences": 0,
    "pair_same_checkpoint_baseline": true,
    "pair_comparison_mode": "same_checkpoint_baseline"
  }
}
```

其中：

- `pair_batch` 来自 `run/pair_batch/pair_generation_batch.json`。
- `benchmark_scorecard` 的 pair 字段来自 scorecard summary，证明 scorecard 不是只生成了独立 pair artifact，而是真的消费了 pair evidence。
- `same_checkpoint_baseline=True` 说明左右 checkpoint 路径相同；scorecard 会把 pair 组件最高分限制为 reproducibility baseline 语义。

## 输入输出

典型运行命令：

```text
python -B scripts/run_tiny_standard_benchmark_smoke.py --out-dir runs/v316-tiny-standard-benchmark-smoke --suite-name standard-zh --case-token-cap 6 --max-iters 1 --eval-iters 1 --batch-size 2 --block-size 8 --n-embd 8 --force
```

输出结构新增 pair batch：

```text
out-dir/
  standard-zh-capped-suite.json
  tiny_corpus.txt
  run/
    checkpoint.pt
    eval_suite/eval_suite.json
    generation-quality/generation_quality.json
    pair_batch/pair_generation_batch.json
    pair_batch/pair_generation_batch.html
    benchmark-scorecard/benchmark_scorecard.json
  tiny_standard_benchmark_smoke_summary.json
  tiny_standard_benchmark_smoke_summary.txt
```

`pair_generation_batch.json` 是后续 scorecard 消费的机器可读证据；`pair_generation_batch.html` 是人工审查用的只读报告。

## 测试覆盖

- `tests.test_tiny_standard_benchmark_smoke`
  - 覆盖 capped suite、summary render、真实脚本链路。
- focused benchmark tests
  - 覆盖 tiny smoke、eval suite、generation quality、benchmark scorecard、pair batch 五组模块。
- full unittest
  - 确认全项目测试没有被新命令链破坏。
- source encoding 和 `py_compile`
  - 确认新增/修改 Python 文件没有 BOM、语法或编码问题。

关键断言保护的是：pair batch 不是 README 里的说明文字，而是真实写入 artifact、被 summary 读取、再被 scorecard summary 消费。

## 运行证据

v316 的截图和说明归档在：

```text
d/316/图片
d/316/解释/说明.md
```

这些证据包含 tiny smoke summary、pair batch summary、scorecard pair fields、focused tests、全量 unittest、source encoding、diff check 和静态扫描。

## 一句话总结

v316 让 tiny standard benchmark smoke 从“能跑真实 checkpoint 的 eval/quality/scorecard”推进到“scorecard 前也有同 checkpoint pair baseline 证据”，把 benchmark completeness 补齐，同时保留模型能力边界。
