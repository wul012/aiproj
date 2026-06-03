# v830：decoder-anchor rebalanced training run

## 本版目标和边界

v830 的目标是用 v829 rebalanced corpus 训练一个真实 tiny checkpoint，并把训练产物包装成可复核证据。

这版不做 bounded replay，不比较 v806/v819/v826，也不声称模型能力提升。它只证明 rebalanced seed 已经转化为真实 checkpoint，供 v831 replay 使用。

## 前置链路

- v828：确认 v824 corpus direct-answer 太少、carry-forward 太多。
- v829：把 48 条原 seed 重配为 40 条训练样本，其中 carry-forward 10 条、direct-answer 15 条、decoder-bridge 15 条。

v830 接住 v829 的 `train_decoder_anchor_rebalanced_seed_revision`。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.py`

核心 builder。它读取 rebalanced seed report 和真实训练 run 目录，检查训练产物是否完整。

关键检查：

- rebalanced seed `status=pass`。
- `decoder_anchor_rebalanced_seed_revision_ready=True`。
- direct-answer share 仍大于等于 `0.2`。
- carry-forward share 仍小于等于 `0.5`。
- bridge examples 仍存在。
- checkpoint、tokenizer、metrics、run manifest、prepared corpus 都存在。
- metrics 至少有首尾记录。
- train config 中 `max_iters` 为正。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_artifacts.py`

产物层。输出 JSON、CSV、text、Markdown 和 HTML。CSV 保存 artifact 表，HTML 用于截图，JSON 供后续 replay/comparison 读取 checkpoint 路径和训练摘要。

`scripts/build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.py`

CLI 入口。它读取 `--rebalanced-seed` 和 `--run-dir`，再写出训练证据。`--force` 会保留嵌套的 `run/` 目录，避免清理报告目录时误删 checkpoint。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.py`

测试覆盖 ready run、direct share 未修复时失败、CLI/artifact 输出连通，以及 `--force` 保留 nested run。

## 真实训练命令

```powershell
python -B scripts\train.py `
  --prepared-data e\829\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision\model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_corpus.txt `
  --out-dir e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run `
  --max-iters 35 `
  --eval-interval 10 `
  --eval-iters 2 `
  --batch-size 4 `
  --block-size 32 `
  --n-layer 2 `
  --n-head 2 `
  --n-embd 32 `
  --dropout 0.0 `
  --seed 1093 `
  --device cpu `
  --sample-prompt "自检：本题需要同时出现 fixed 与 loss。最终答案：" `
  --sample-tokens 24 `
  --sample-temperature 0.2 `
  --sample-top-k 10
```

## 真实结果

- `status=pass`
- `decision=model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_ready`
- `failed_count=0`
- `final_step=35`
- `final_train_loss=4.193515300750732`
- `final_val_loss=4.194498062133789`
- `rebalanced_example_count=40`
- `direct_answer_count=15`
- `decoder_bridge_count=15`
- `next_step=run_decoder_anchor_rebalanced_checkpoint_bounded_replay`

## 测试覆盖

focused tests：

- 构造 fake run 目录，确认 checkpoint、tokenizer、metrics、manifest 和 prepared corpus 都被识别。
- direct share 被改回低于阈值时，训练报告 fail。
- CLI、JSON/CSV/text/Markdown/HTML 输出全部连通。
- `--force` 不删除嵌套 `run/`。

## 运行证据

- 训练 run 与报告：`e/830/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run/`
- 截图：`e/830/图片/v830-bounded-real-replay-decoder-anchor-rebalanced-training-run-html.png`

## 一句话总结

v830 把 v829 的 rebalanced seed 转化成真实 checkpoint，但模型能力仍然等待 v831 bounded replay 验证。
