# v810 route promotion bounded real replay repair training run

## 本版目标和边界

v810 接在 v809 repair seed 后面。v809 已经生成 JSONL/corpus seed；v810 真实调用 `scripts/train.py`，用 repair seed corpus 训练一个小型 bounded repair checkpoint，并生成训练 evidence。

本版不做：

- 不声称模型能力已经提升。
- 不把 loss 下降当作 replay 通过。
- 不修改 v803 benchmark suite。
- 不改变 v806 的 baseline replay 结果。

## 训练输入

训练数据来自：

```text
e/809/解释/model-capability-route-promotion-bounded-real-replay-repair-seed/model_capability_route_promotion_bounded_real_replay_repair_seed_corpus.txt
```

这份 corpus 是 v809 从 3 个 failed cases 生成的 6 条 bounded seed examples。

## 训练配置

本版使用小型 CPU 配置：

```text
max_iters=20
batch_size=4
block_size=32
n_layer=2
n_head=2
n_embd=32
dropout=0.0
seed=991
device=cpu
```

训练结果：

```text
step=1  train_loss=4.1748 val_loss=4.1785
step=10 train_loss=4.0373 val_loss=4.0192
step=20 train_loss=3.9741 val_loss=3.9439
```

这些 loss 只能说明 repair corpus 上的训练在运行，不证明 benchmark replay 一定通过。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_training_run.py`

这是训练 evidence builder，提供：

- `locate_route_promotion_bounded_real_replay_repair_seed(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_real_replay_repair_training_run(...)`
- `resolve_exit_code(report, require_training_ready=...)`

它读取 repair seed report 和 run dir，检查：

- `checkpoint.pt`
- `tokenizer.json`
- `metrics.jsonl`
- `train_config.json`
- `run_manifest.json`
- `sample.txt`
- `prepared_corpus.txt`

并解析 metrics，记录：

- `final_step`
- `final_train_loss`
- `final_val_loss`
- `train_loss_delta`
- `val_loss_delta`

### `training_run`

核心字段包括：

- `ready`
- `artifact_count`
- `metric_record_count`
- `final_step`
- `final_train_loss`
- `final_val_loss`
- `max_iters`
- `seed`
- `proposed_next_artifact`
- `next_step`

真实结果的下一步是：

```text
run_repair_checkpoint_bounded_replay
```

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_training_run_artifacts.py`

输出 JSON/CSV/text/Markdown/HTML。CSV 展示 run artifacts，HTML 用于人工检查 checkpoint、metrics、manifest 是否齐全。

### `scripts/build_model_capability_route_promotion_bounded_real_replay_repair_training_run.py`

CLI 支持：

- `--repair-seed`
- `--run-dir`
- `--out-dir`
- `--require-training-ready`
- `--force`

## 真实运行证据

本版实际训练：

```powershell
python -B scripts/train.py --prepared-data <v809 corpus> --out-dir e/810/解释/model-capability-route-promotion-bounded-real-replay-repair-training-run/run --max-iters 20 --eval-interval 10 --eval-iters 2 --batch-size 4 --block-size 32 --n-layer 2 --n-head 2 --n-embd 32 --dropout 0.0 --seed 991 --device cpu
```

本版 evidence：

```powershell
python -B scripts/build_model_capability_route_promotion_bounded_real_replay_repair_training_run.py --repair-seed e/809/解释/model-capability-route-promotion-bounded-real-replay-repair-seed/model_capability_route_promotion_bounded_real_replay_repair_seed.json --run-dir e/810/解释/model-capability-route-promotion-bounded-real-replay-repair-training-run/run --out-dir e/810/解释/model-capability-route-promotion-bounded-real-replay-repair-training-run/training-evidence --require-training-ready --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_repair_training_run_ready
failed_count=0
bounded_real_replay_repair_training_ready=True
final_step=20
final_train_loss=3.9741125106811523
final_val_loss=3.9439306259155273
next_step=run_repair_checkpoint_bounded_replay
```

## 测试覆盖

测试文件是 `tests/test_model_capability_route_promotion_bounded_real_replay_repair_training_run.py`，覆盖：

- fake run 具备 checkpoint/tokenizer/metrics/manifest 时 evidence ready。
- 缺少 checkpoint 时 fail。
- CLI 和 artifact writer 输出 JSON/CSV/text/Markdown/HTML。

本版运行：

```powershell
python -m py_compile src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_training_run.py src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_training_run_artifacts.py scripts/build_model_capability_route_promotion_bounded_real_replay_repair_training_run.py tests/test_model_capability_route_promotion_bounded_real_replay_repair_training_run.py
python -m pytest tests/test_model_capability_route_promotion_bounded_real_replay_repair_seed.py tests/test_model_capability_route_promotion_bounded_real_replay_repair_training_run.py -q -o cache_dir=runs/pytest-cache-v810-focused
```

结果：

- focused tests: `6 passed`

## 截图和归档

运行证据归档在：

- `e/810/解释/说明.md`
- `e/810/解释/model-capability-route-promotion-bounded-real-replay-repair-training-run/`
- `e/810/图片/v810-bounded-real-replay-repair-training-run-html.png`

Playwright MCP 快照确认 HTML 页面展示：

- `Ready: True`
- `Final step: 20`
- `Val loss: 3.9439306259155273`
- `Next: run_repair_checkpoint_bounded_replay`

## 一句话总结

v810 把 bounded repair seed 推进到真实训练 checkpoint，但仍把模型能力判断留给下一版 replay，而不是用训练完成替代能力证据。
