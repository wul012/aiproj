# v829：decoder-anchor rebalanced seed revision

## 本版目标和边界

v829 的目标是把 v828 的 distribution audit 落到训练数据上：v828 已经确认 v824 corpus 中 direct-answer 只有 `10.42%`，carry-forward 达到 `58.33%`，并且 v827 显示 5 个 bounded replay case 全部 zero-hit。

这版不训练模型，不比较 checkpoint，也不做模型能力声明。它只生成一份可训练的 rebalanced seed revision，为后续真实训练提供更合理的样本分布。

## 前置链路

- v824：生成原始 decoder-anchor seed revision，包含 28 条 carry-forward、5 条 direct-answer、15 条 bridge。
- v825：用 v824 corpus 训练真实 checkpoint。
- v826：replay 后仍然 `0/5`。
- v827：诊断失败为 zero-hit 和 fragment-like。
- v828：审计分布，确认 direct 太少、carry 太多，下一步应构造 rebalanced seed。

v829 接住 v828 的 `build_decoder_anchor_rebalanced_seed_revision`。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.py`

核心 builder。它读取 v824 seed revision 和 v828 distribution audit，执行重采样和补 direct 权重样本。

关键输出：

- `seed_examples`：训练器可消费的最终样本列表。
- `bucket_rows`：重配后的 carry/direct/bridge/other 分布。
- `rebalance_rows`：每个 case 保留多少 carry、丢弃多少 carry、新增多少 direct、保留多少 bridge。
- `decoder_anchor_rebalanced_seed_revision`：核心修订摘要。
- `summary`：README、text、HTML 和后续训练脚本可读取的结果字段。
- `interpretation`：保持 `training_data_revision_only`。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_artifacts.py`

产物层。它输出 JSON、CSV、JSONL、corpus、text、Markdown 和 HTML。JSONL/corpus 是 v830 训练输入；HTML 是人工复核和截图证据。

`scripts/build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.py`

CLI 入口。关键参数：

- `--decoder-anchor-seed`
- `--distribution-audit`
- `--carry-forward-per-case`
- `--direct-rebalance-copies-per-case`
- `--out-dir`
- `--require-seed-ready`
- `--force`

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.py`

测试覆盖重配比例、audit 未要求 rebalance 的失败路径、locator、CLI 和 artifact 输出。

## 核心重配逻辑

每个 case 单独处理：

1. 找出 carry-forward、direct-answer 和 decoder-bridge 样本。
2. carry-forward 最多保留 2 条，减少旧样本主导。
3. direct-answer 原样保留。
4. decoder-bridge 全部保留，避免丢掉 v824 的 decoder-anchor 信号。
5. 每个 case 新增 2 条 `rebalanced_unanchored_direct_answer`，用于提高 direct-answer 权重。

重配后的真实分布：

- carry-forward：10 条，`0.25`
- direct-answer：15 条，`0.375`
- decoder-bridge：15 条，`0.375`

这同时越过 v828 的三个关键门槛：

- direct-answer share >= `0.2`
- carry-forward share <= `0.5`
- decoder-bridge share >= `0.25`

## 真实运行命令

```powershell
python -B scripts\build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.py `
  --decoder-anchor-seed e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision `
  --distribution-audit e\828\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-distribution-audit `
  --out-dir e\829\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision `
  --require-seed-ready `
  --force
```

## 真实结果

- `status=pass`
- `decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_ready`
- `example_count=40`
- `carry_forward_share=0.25`
- `direct_answer_share=0.375`
- `decoder_bridge_share=0.375`
- `dropped_carry_forward_count=18`
- `added_direct_answer_count=10`
- `next_step=train_decoder_anchor_rebalanced_seed_revision`

## 测试覆盖

focused tests：

- 构造两个 case 的 fake seed，确认重配后 direct/carry/bridge 比例符合阈值。
- audit 没有要求 rebalance 时，报告 fail，避免误用这个脚本做普通 seed 变换。
- 验证 locator、CLI、JSON/CSV/JSONL/corpus/text/Markdown/HTML 输出全部连通。

## 运行证据

- rebalanced seed revision：`e/829/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision/`
- 截图：`e/829/图片/v829-bounded-real-replay-decoder-anchor-rebalanced-seed-revision-html.png`

## 一句话总结

v829 把 v828 的“分布需要重配”变成一份真实可训练 corpus，为 v830 判断 rebalanced training 是否改善 bounded replay 打下数据基础。
