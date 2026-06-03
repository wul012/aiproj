# v825：decoder-anchor training run

## 本版目标和边界

v825 的目标是把 v824 的 decoder-anchor seed revision 训练成一个真实 checkpoint。它延续 v818 的训练证据模式：训练可以真实发生，checkpoint 可以被后续 replay 消费，但本版不把 loss 下降解释为模型能力提升。

边界很明确：不做 bounded replay、不做 baseline comparison、不打开 promotion。v825 只把“训练数据已经准备好”推进到“训练产物已经存在”。

## 前置链路

v824 生成了 48 条训练样本：

- 28 条从 prompt-aligned seed carry forward。
- 20 条新增 decoder-anchor-informed 样本。
- 其中 15 条 bridge completion 样本。
- 其中 5 条 unanchored direct-answer 样本。

v825 用这份 corpus 训练 tiny GPT。下一版 v826 才会拿 checkpoint 跑 bounded replay。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run.py`

核心报告 builder。它读取 v824 seed summary 和训练目录，检查 checkpoint、tokenizer、metrics、train config、manifest、sample、prepared corpus 是否存在，并把 metrics 的 first/last loss 汇总成训练证据。

关键字段包括：

- `artifacts`：训练目录里的文件清单。
- `metrics`：metrics.jsonl 的 first/last 记录和 loss delta。
- `decoder_anchor_training`：本版训练摘要。
- `summary`：供文本、HTML、README 消费的关键数值。
- `interpretation`：明确标记为 `training_artifact_only`。

`src/minigpt/model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_artifacts.py`

产物写入层。它把 report 写成 JSON、CSV、text、Markdown 和 HTML。CSV 记录 artifact 是否存在和大小；HTML 用于截图归档。

`scripts/build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run.py`

CLI 入口。它支持传入 v824 seed 目录或 JSON 文件，以及训练 run 目录。`--force` 会清理旧报告文件，但如果 `run/` 是 `out-dir` 内的子目录，会保留 run 目录，避免像早期训练证据那样误删刚训练出的 checkpoint。

`tests/test_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run.py`

单测覆盖 ready 路径、缺少 bridge 样本时阻断、CLI/locator/artifact 输出连通，以及 `--force` 保留嵌套 run 目录。

## 真实训练命令

```powershell
python -B scripts\train.py `
  --prepared-data e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision\model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_corpus.txt `
  --out-dir e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run\run `
  --max-iters 35 `
  --eval-interval 10 `
  --eval-iters 2 `
  --batch-size 4 `
  --block-size 32 `
  --n-layer 2 `
  --n-head 2 `
  --n-embd 32 `
  --dropout 0.0 `
  --seed 993 `
  --device cpu `
  --sample-prompt "自检：本题需要同时出现 fixed 与 loss。最终答案：" `
  --sample-tokens 24 `
  --sample-temperature 0.2 `
  --sample-top-k 10
```

随后用 evidence builder 汇总：

```powershell
python -B scripts\build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run.py `
  --decoder-anchor-seed e\824\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision `
  --run-dir e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run\run `
  --out-dir e\825\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run `
  --require-training-ready `
  --force
```

## 运行结果

训练输出：

- `device=cpu`
- `tokenizer=char`
- `tokens=3431`
- `vocab_size=94`
- `parameters=29,504`
- `final_step=35`
- `final_train_loss=4.2080`
- `final_val_loss=4.2626`

证据报告输出：

- `status=pass`
- `failed_count=0`
- `decoder_anchor_training_ready=True`
- `decoder_anchor_example_count=48`
- `bridge_example_count=15`
- `unanchored_direct_example_count=5`
- `next_step=run_decoder_anchor_checkpoint_bounded_replay`

## 测试覆盖

focused test 有 4 个断言面：

- 完整 fake run 会生成 ready training evidence。
- bridge 样本数为 0 时会失败，避免把非 decoder-anchor corpus 误当成 v825 输入。
- CLI 和 artifact 输出都能连通。
- `--force` 不会删除嵌套 `run/` 目录里的 checkpoint。

全量测试也会在提交前运行，保证新增训练证据模块没有破坏既有路线。

## 运行证据

- 训练目录：`e/825/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run/run`
- 证据报告：`e/825/解释/model-capability-route-promotion-bounded-real-replay-decoder-anchor-training-run/`
- 截图：`e/825/图片/v825-bounded-real-replay-decoder-anchor-training-run-html.png`

## 一句话总结

v825 把 decoder-anchor seed revision 推进成真实 checkpoint，但能力判断仍然被正确地推迟到 v826 的 bounded replay。
