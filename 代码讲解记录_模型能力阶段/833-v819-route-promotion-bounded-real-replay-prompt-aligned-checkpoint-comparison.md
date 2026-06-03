# v819 route promotion bounded real replay prompt-aligned checkpoint comparison

## 本版目标和边界

v819 的目标是把 v818 的 prompt-aligned checkpoint 放回真实 bounded replay，并和 v806 baseline replay 做同套 benchmark 对比。它解决的问题是：v817/v818 做了提示对齐语料和真实训练，但这些工作是否真的转化成模型输出能力。

本版不继续训练，也不修改 benchmark suite。它只做 replay 和 comparison。这样能避免在没有能力证据时继续堆训练版本。

## 前置路线

- v806 是当前 baseline bounded real replay，`passed_case_count=2/5`。
- v815 已证明上一轮 repair checkpoint replay 为 `0/5`，相比 baseline 回归。
- v817 加入 exact benchmark prompt answers。
- v818 从 prompt-aligned corpus 训练出真实 checkpoint。
- v819 验证这个 checkpoint 是否比 v806 baseline 更好。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison.py`
  - v819 的核心比较器。
  - 比较 baseline replay 与 prompt-aligned replay。
  - 字段使用 `prompt_aligned_*`，避免沿用旧 `repair_*` 名称造成语义混乱。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison_artifacts.py`
  - JSON、CSV、TXT、Markdown、HTML 输出层。
  - HTML 展示 baseline passed、prompt-aligned passed、delta、promotion ready 和逐 case 对比。

- `scripts/compare_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint.py`
  - CLI 入口。
  - 支持 `--baseline-replay`、`--prompt-aligned-replay`、`--training-evidence`、`--require-comparison-pass`、`--require-improvement`。

- `tests/test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison.py`
  - 覆盖回归比较、training evidence ready 检查、CLI 输出与 improvement gate。

- `e/819/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-checkpoint-replay/`
  - v819 的真实 replay 与 comparison 证据目录。

## 为什么不直接复用 repair comparison

项目里已经有 `model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison`。但它的字段和文案都以 `repair_*` 为核心，training evidence ready 也检查 `bounded_real_replay_repair_training_ready`。

v818 的产物是 prompt-aligned training run，ready 字段是 `prompt_aligned_training_ready`。如果强行复用旧 comparison，会把 prompt-aligned checkpoint 写成 repair checkpoint，后续 README、HTML、诊断模块都会被旧语义污染。因此 v819 新增专用 comparison，逻辑保持一致，语义换成 prompt-aligned。

## 核心数据结构

主报告包含：

- `baseline_summary`
  - 来自 v806 baseline replay。
  - 本轮关键值是 `passed_case_count=2`、`pass_rate=0.4`。

- `prompt_aligned_summary`
  - 来自 v819 prompt-aligned replay。
  - 本轮关键值是 `passed_case_count=0`、`pass_rate=0.0`。

- `case_rows`
  - 每个 case 记录 baseline pass、prompt-aligned pass、delta、hit terms、missed terms 和 continuation。
  - 这是诊断下一版失败原因的主要输入。

- `comparison`
  - 聚合通过数量、pass rate delta、是否 improved、是否 regressed、是否 promotion ready。

- `summary`
  - 给 README/HTML 使用的压缩结论。
  - 本轮为 `prompt_aligned_checkpoint_regressed=True`、`pass_rate_delta=-0.4`。

- `interpretation`
  - 明确 `model_quality_claim=not_improved`。
  - 原因是 prompt-aligned checkpoint 通过 case 数低于 baseline。

## 核心函数

`build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison()` 是主入口：

1. 读取 baseline replay summary。
2. 读取 prompt-aligned replay summary。
3. 可选读取 v818 training evidence，并检查 `prompt_aligned_training_ready`。
4. 调用 `_case_rows()` 合并逐 case 结果。
5. 调用 `_checks()` 确认 replay 执行都通过、case count 一致、case rows 存在。
6. 调用 `_comparison()` 计算 delta 和 promotion 状态。
7. 输出 `decision`、`summary` 和 `interpretation`。

`_comparison()` 的核心规则很保守：

- `delta > 0` 才算 improved。
- `delta < 0` 直接标记 regressed。
- `promotion_ready` 必须同时满足 comparison pass、delta > 0、prompt-aligned replay 自身 `model_route_quality_ready=True`。

因此 v819 不会因为 v818 训练 loss 下降而放行，只看 replay pass count。

## 真实运行链路

第一步，运行 v818 checkpoint replay：

```powershell
python -B scripts\run_model_capability_route_promotion_bounded_real_replay.py --benchmark-suite e\803\解释\...\model_capability_route_promotion_bounded_benchmark_suite.json --suite-review e\804\解释\...\model_capability_route_promotion_bounded_benchmark_suite_review.json --dry-run e\805\解释\...\model_capability_route_promotion_bounded_benchmark_dry_run.json --checkpoint e\818\解释\...\run\checkpoint.pt --tokenizer e\818\解释\...\run\tokenizer.json --device cpu --out-dir e\819\解释\...\prompt-aligned-replay --require-execution-pass --force
```

输出为：

- `passed_case_count=0`
- `failed_case_count=5`
- `pass_rate=0.0`
- `model_route_quality_ready=False`

第二步，运行 baseline comparison：

```powershell
python -B scripts\compare_model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint.py --baseline-replay e\806\解释\...\model_capability_route_promotion_bounded_real_replay.json --prompt-aligned-replay e\819\解释\...\prompt-aligned-replay\model_capability_route_promotion_bounded_real_replay.json --training-evidence e\818\解释\...\model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run.json --out-dir e\819\解释\...\comparison --require-comparison-pass --force
```

输出为：

- `decision=model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_regressed`
- `baseline_passed_case_count=2`
- `prompt_aligned_passed_case_count=0`
- `passed_case_delta=-2`
- `pass_rate_delta=-0.4`
- `promotion_ready=False`

## 测试覆盖

本版新增 3 个 focused tests：

- baseline 2/3、prompt-aligned 0/3 时，comparison 仍然 pass，但 improvement gate 返回失败。
- training evidence 提供但 `prompt_aligned_training_ready=False` 时，comparison fail。
- CLI 能定位 replay/report 目录，生成 JSON/CSV/TXT/MD/HTML，并在 `--require-improvement` 下正确返回 `SystemExit(1)`。

这组测试保护的是 v819 的关键边界：失败的模型结果不是脚本失败；只有输入合同破坏才是 comparison fail。

## 运行证据

证据目录：

- `e/819/解释/说明.md`
- `e/819/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-checkpoint-replay/prompt-aligned-replay/`
- `e/819/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-checkpoint-replay/comparison/`
- `e/819/图片/v819-bounded-real-replay-prompt-aligned-checkpoint-comparison-html.png`

Playwright MCP 已打开 comparison HTML 并完成截图，页面能看到 baseline 2、prompt-aligned 0、delta -2 和 promotion blocked。

## 一句话总结

v819 证明 v818 的 prompt-aligned checkpoint 仍未恢复 bounded replay 能力，下一步应诊断生成失败形态，而不是继续盲目训练。
