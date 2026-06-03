# v831：decoder-anchor rebalanced checkpoint comparison

## 本版目标和边界

v831 的目标是复核 v830 rebalanced checkpoint 是否真的改善 bounded replay。v829 重新平衡了 seed，v830 训练出 checkpoint，但能力是否改善只能通过同一套 bounded benchmark replay 判断。

这版不训练新模型，不修改 benchmark，也不再调整 seed。它只做 replay 和四方 comparison。

## 前置链路

- v806：baseline bounded real replay，`2/5`。
- v819：prompt-aligned checkpoint replay，`0/5`。
- v826：decoder-anchor checkpoint replay，`0/5`。
- v830：rebalanced checkpoint training run。

v831 把 v830 checkpoint 放入同一套 v803 bounded benchmark suite，避免只看训练 loss 或 corpus 分布就判断模型变好。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.py`

核心 builder。它读取四份 replay report 和可选的 v830 training evidence，生成 route rows、pass-rate delta 和 promotion 判断。

关键字段：

- `route_rows`：baseline、prompt_aligned、decoder_anchor、rebalanced 四条路线的 passed count、case count、pass rate。
- `checkpoint_comparison`：四方比较摘要，例如 rebalanced vs baseline delta、rebalanced vs decoder-anchor delta。
- `summary`：面向 README/CLI 的扁平字段。
- `interpretation`：本版明确给出 `model_quality_claim=not_improved`。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_artifacts.py`

产物层。输出 JSON、CSV、text、Markdown 和 HTML。CSV 是 route table，HTML 用于截图归档。

`scripts/compare_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint.py`

CLI 入口。它读取四份 replay 和可选 rebalanced training evidence。`--force` 会保留 comparison 目录里的 nested replay 子目录。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.py`

测试覆盖 still-regressed、partial-recovery、locator、CLI 和 artifact 输出。

## 真实 replay 命令

```powershell
python -B scripts\run_model_capability_route_promotion_bounded_real_replay.py `
  --benchmark-suite e\803\解释\model-capability-route-promotion-bounded-benchmark-suite `
  --suite-review e\804\解释\model-capability-route-promotion-bounded-benchmark-suite-review `
  --dry-run e\805\解释\model-capability-route-promotion-bounded-benchmark-dry-run `
  --checkpoint e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run\checkpoint.pt `
  --tokenizer e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run\tokenizer.json `
  --device cpu `
  --out-dir e\831\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison\rebalanced-replay `
  --require-execution-pass `
  --force
```

## 真实 comparison 命令

```powershell
python -B scripts\compare_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint.py `
  --baseline-replay e\806\解释\model-capability-route-promotion-bounded-real-replay `
  --prompt-aligned-replay e\819\解释\model-capability-route-promotion-bounded-real-replay-prompt-aligned-checkpoint-replay\prompt-aligned-replay `
  --decoder-anchor-replay e\826\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-checkpoint-comparison\decoder-anchor-replay `
  --rebalanced-replay e\831\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison\rebalanced-replay `
  --rebalanced-training e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run `
  --out-dir e\831\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison `
  --require-comparison-pass `
  --force
```

## 真实结果

- rebalanced replay：`passed_case_count=0/5`
- baseline：`2/5`
- prompt-aligned：`0/5`
- decoder-anchor：`0/5`
- rebalanced：`0/5`
- `rebalanced_vs_baseline_pass_rate_delta=-0.4`
- `rebalanced_vs_decoder_anchor_pass_rate_delta=0.0`
- `promotion_ready=False`
- `model_quality_claim=not_improved`
- `next_step=diagnose_rebalanced_checkpoint_replay_failure_before_more_training`

## 测试覆盖

focused tests：

- rebalanced 与 decoder-anchor 持平且低于 baseline 时，decision 为 still-regressed。
- rebalanced 高于 decoder-anchor 但仍低于 baseline 时，decision 为 partial recovery。
- CLI、locator、JSON/CSV/text/Markdown/HTML 输出全部连通。

## 运行证据

- replay 与 comparison：`e/831/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison/`
- 截图：`e/831/图片/v831-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison-html.png`

## 一句话总结

v831 证明 rebalanced seed/training 没有带来 bounded replay 改善，下一步应诊断 rebalanced checkpoint 的失败形态，而不是继续盲目加训练。
