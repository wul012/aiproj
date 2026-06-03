# v832：decoder-anchor rebalanced failure diagnostic

## 本版目标和边界

v832 的目标是解释 v831 的失败：v829 已经修复训练数据分布，v830 已经完成训练，但 v831 replay 仍然是 `0/5`。这版要判断失败是否仍可归因于数据分布，还是已经转向生成/解码层问题。

这版不训练新 checkpoint，不改 benchmark，不追加 seed。它只做失败诊断。

## 前置链路

- v828：发现 direct-answer 太少、carry-forward 太多。
- v829：构造 rebalanced seed，direct-answer 占比提升到 `0.375`，carry-forward 降到 `0.25`。
- v830：用 rebalanced corpus 训练 checkpoint。
- v831：rebalanced checkpoint replay 仍然 `0/5`。

v832 接住 v831 的 `diagnose_rebalanced_checkpoint_replay_failure_before_more_training`。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.py`

核心 builder。它读取 rebalanced replay、四方 comparison、rebalanced seed、training run 和 corpus，生成 case diagnostics、root causes 和 summary。

关键字段：

- `case_diagnostics`：每个 bounded replay case 的 prompt/corpus 覆盖、zero-hit、fragment-like、missed terms、诊断和建议动作。
- `root_causes`：聚合根因，例如分布已修但 replay zero-hit、fragmented generation、loss 没转化为 replay recovery。
- `diagnostic`：统计 failed/zero-hit/fragment-like/root-cause count。
- `summary`：README 和 CLI 消费的扁平字段。
- `interpretation`：明确 `model_quality_claim=not_improved`。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic_artifacts.py`

产物层。输出 JSON、CSV、text、Markdown 和 HTML。CSV 保存 case 级诊断，HTML 用于运行截图。

`scripts/diagnose_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure.py`

CLI 入口。显式接收 replay、comparison、seed、training 和 corpus，避免隐式路径造成误诊断。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.py`

测试覆盖 ready 诊断、comparison 不 ready 的失败路径、locator、CLI 和 artifact 输出。

## 核心诊断逻辑

每个 replay case 会检查：

- prompt 是否在 seed/corpus 中出现。
- expected terms 在 seed/corpus 中出现次数。
- 是否 zero-hit。
- 是否 fragment-like generation。
- 诊断类型和下一步建议。

与 v827 的区别在于，v832 额外检查 rebalanced seed 的分布是否已经修复。如果 direct/carry 已满足阈值但 replay 仍 0/5，就生成根因：

`rebalanced_distribution_repaired_but_replay_zero_hit`

这说明问题不应继续简单归因于 v828 的分布失衡。

## 真实运行命令

```powershell
python -B scripts\diagnose_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure.py `
  --rebalanced-replay e\831\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison\rebalanced-replay `
  --comparison e\831\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison `
  --rebalanced-seed e\829\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision `
  --training-run e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run `
  --corpus e\829\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision\model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_corpus.txt `
  --out-dir e\832\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-failure-diagnostic `
  --require-diagnostic-ready `
  --force
```

## 真实结果

- `status=pass`
- `failed_case_count=5`
- `zero_hit_case_count=5`
- `fragment_like_case_count=5`
- `root_cause_count=4`
- `next_step=run_rebalanced_decoder_profile_sweep_before_more_training`

## 测试覆盖

focused tests：

- 构造分布已修但 replay zero-hit 的样例，确认会生成 rebalanced distribution root cause。
- comparison 为 fail 时，diagnostic fail。
- CLI、locator、JSON/CSV/text/Markdown/HTML 输出全部连通。

## 运行证据

- 诊断报告：`e/832/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-failure-diagnostic/`
- 截图：`e/832/图片/v832-bounded-real-replay-decoder-anchor-rebalanced-failure-diagnostic-html.png`

## 一句话总结

v832 证明 rebalanced route 的失败已经不只是训练数据分布问题，下一步要做解码 profile sweep 来判断是否存在可恢复的生成面。
