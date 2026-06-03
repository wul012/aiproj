# v826：decoder-anchor checkpoint comparison

## 本版目标和边界

v826 的目标是验证 v825 训练出的 decoder-anchor checkpoint 是否真的改善 bounded replay。它不看训练 loss 做结论，而是重新跑同一套 v803 bounded benchmark suite，并与两个历史参照对比：

- v806 baseline replay：2/5。
- v819 prompt-aligned replay：0/5。
- v826 decoder-anchor replay：0/5。

本版不做新训练、不改 benchmark、不调阈值。它只回答一个问题：v825 checkpoint 是否比 baseline 或 prompt-aligned checkpoint 更好。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.py`

三方 comparison 的核心 builder。它读取 baseline replay、prompt-aligned replay、decoder-anchor replay，以及可选的 v825 training evidence。它生成：

- `case_rows`：每个 case 的 baseline/prompt/decoder 三方 pass 状态。
- `comparison`：三方 passed count、pass rate、delta、promotion_ready。
- `summary`：README 和 HTML 使用的关键字段。
- `interpretation`：说明本版是否能声称 bounded replay improved。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_artifacts.py`

产物层。它输出 JSON、CSV、text、Markdown 和 HTML。CSV 适合看 case-level delta，HTML 用于截图归档。

`scripts/compare_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint.py`

CLI 入口。它接收三个 replay 输入和一个可选 training evidence。这里额外修复了一个真实问题：当 decoder replay 放在 comparison 输出目录下面时，`--force` 不能删除 `decoder-anchor-replay/` 子目录。新逻辑会保留嵌套输入目录，只清除旧 comparison 文件。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison.py`

单测覆盖五个点：

- decoder-anchor 相比 baseline 回退且相比 prompt 没恢复时，promotion 阻断。
- decoder-anchor 比 prompt 恢复但没超过 baseline 时，只能算 partial recovery。
- training evidence 提供但未 ready 时，comparison 失败。
- CLI、locator、artifact 输出连通。
- `--force` 保留嵌套 `decoder-anchor-replay/`，避免误删上游证据。

## 真实 replay 命令

```powershell
python -B scripts\run_model_capability_route_promotion_bounded_real_replay.py `
  --benchmark-suite e\803\解释\model-capability-route-promotion-bounded-benchmark-suite `
  --suite-review e\804\解释\model-capability-route-promotion-bounded-benchmark-suite-review `
  --dry-run e\805\解释\model-capability-route-promotion-bounded-benchmark-dry-run `
  --checkpoint e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run\run\checkpoint.pt `
  --tokenizer e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run\run\tokenizer.json `
  --device cpu `
  --out-dir e\826\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison\decoder-anchor-replay `
  --require-execution-pass `
  --force
```

真实 replay 结果是：

- `status=pass`
- `passed_case_count=0`
- `failed_case_count=5`
- `pass_rate=0.0`
- `model_route_quality_ready=False`

这说明执行链路没问题，但模型没有命中 required terms。

## comparison 命令

```powershell
python -B scripts\compare_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint.py `
  --baseline-replay e\806\解释\model-capability-route-promotion-bounded-real-replay `
  --prompt-aligned-replay e\819\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-checkpoint-replay\prompt-aligned-replay `
  --decoder-anchor-replay e\826\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison\decoder-anchor-replay `
  --training-evidence e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run `
  --out-dir e\826\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison `
  --require-comparison-pass `
  --force
```

comparison 结果：

- baseline：`2/5`
- prompt-aligned：`0/5`
- decoder-anchor：`0/5`
- decoder vs baseline pass rate delta：`-0.4`
- decoder vs prompt pass rate delta：`0.0`
- decision：`model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_regressed_from_baseline`
- next step：`diagnose_decoder_anchor_checkpoint_replay_failure_before_more_training`

## 解释

v825 的训练 loss 确实下降，但 v826 证明它没有转化为 bounded replay 命中。decoder-anchor 训练既没有恢复 baseline 的 2/5，也没有超过 prompt-aligned 的 0/5。

这意味着下一步不应该继续盲目训练，而应该诊断生成输出为什么仍然没有 required terms：是采样参数、prompt suffix、训练 token 分布、还是 checkpoint 在短训练下只学到了局部碎片。

## 运行证据

- decoder replay：`e/826/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison/decoder-anchor-replay/`
- comparison 报告：`e/826/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison/`
- 截图：`e/826/图片/v826-bounded-real-replay-decoder-anchor-checkpoint-comparison-html.png`

## 一句话总结

v826 用真实 replay 证明 v825 checkpoint 尚未带来 bounded capability 改善，并把路线从“继续训练”转向“先诊断 replay failure”。
