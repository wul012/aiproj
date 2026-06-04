# v847：bounded objective unassisted repair training run

## 本版目标和边界

v847 的目标是把 v846 生成的无锚点 repair seed corpus 送进真实 tiny training，拿到一个可复核的 checkpoint。

边界：

- 不把 loss 下降解释成模型能力提升。
- 不运行 replay comparison。
- 不使用 decoder anchor。
- 不替代后续 holdout/replay 验证。

这版只回答一个问题：v846 的无锚点 seed 是否已经形成真实训练产物，并且这些产物是否齐全、可审计。

## 前置链路

输入来自 v846：

```text
e/846/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed/
```

v847 校验 seed summary 中的关键字段：

```text
bounded_objective_unassisted_repair_seed_ready=True
proposed_next_artifact=model_capability_route_promotion_bounded_objective_unassisted_repair_training_run
neutral_prompt_example_count=12
decoder_anchor_example_count=0
direct_example_count=24
corpus_char_count=1778
```

这些字段保证本版训练来自 unassisted repair route，而不是又滑回 decoder-anchor 辅助路线。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_training_run.py`
  - 负责读取 seed report 和训练 run 目录，检查 checkpoint、tokenizer、metrics、manifest、sample 和 prepared corpus 是否齐全。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_artifacts.py`
  - 负责输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run.py`
  - CLI 入口，支持 `--unassisted-repair-seed`、`--run-dir`、`--require-training-ready` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run.py`
  - 覆盖正常训练证据、缺 checkpoint、seed 含 decoder anchor、artifact writer 和 CLI。
- `e/847/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-training-run/`
  - 保存真实训练 run 和 v847 report。
- `e/847/图片/v847-bounded-objective-unassisted-repair-training-run-html.png`
  - Playwright MCP 截图，确认 HTML 可读。

## 核心数据结构

v847 report 主要包含：

```text
status
decision
source_unassisted_repair_seed
run_dir
unassisted_repair_seed_summary
artifacts
metrics
train_config
manifest
check_rows
unassisted_repair_training
summary
interpretation
```

`artifacts` 是训练产物清单，每项记录：

```text
key
path
exists
size
```

`metrics` 从 `metrics.jsonl` 解析 first/last record，并计算：

```text
train_loss_delta
val_loss_delta
record_count
```

`summary` 把下游最需要的字段压平：

```text
bounded_objective_unassisted_repair_training_ready
final_step
final_train_loss
final_val_loss
repair_example_count
neutral_prompt_example_count
decoder_anchor_example_count
proposed_next_artifact
next_step
```

## 运行流程

1. `scripts/train.py` 读取 v846 corpus，训练 40 step tiny checkpoint。
2. 训练目录生成 `checkpoint.pt`、`tokenizer.json`、`metrics.jsonl`、`train_config.json`、`run_manifest.json`、`sample.txt`、`prepared_corpus.txt`。
3. v847 builder 读取 seed report 和 run dir。
4. `_checks()` 校验 seed guard 和训练产物。
5. `_training()` 汇总最终 step/loss、artifact count 和下一步 replay route。
6. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
7. Playwright MCP 打开 HTML 并截图归档。

## 真实训练命令

```text
python scripts/train.py --prepared-data e/846/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_corpus.txt --out-dir e/847/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-training-run/run --tokenizer char --batch-size 8 --block-size 64 --max-iters 40 --eval-interval 10 --eval-iters 5 --learning-rate 0.001 --train-ratio 0.9 --n-layer 2 --n-head 2 --n-embd 64 --dropout 0.0 --seed 1847 --device cpu --sample-prompt "Return the bounded objective answer.\nanswer:" --sample-tokens 12 --sample-temperature 0.8 --sample-top-k 20
```

真实训练输出：

```text
step=1  train_loss=3.4697 val_loss=3.4674
step=10 train_loss=2.9827 val_loss=2.9507
step=20 train_loss=2.6334 val_loss=2.6046
step=30 train_loss=2.3860 val_loss=2.3689
step=40 train_loss=2.1253 val_loss=2.2304
```

这些数字说明 tiny run 可以学习 corpus 分布，但不等价于 benchmark 或 replay 能力提升。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_ready
bounded_objective_unassisted_repair_training_ready=True
final_step=40
final_train_loss=2.125275135040283
final_val_loss=2.230360507965088
train_loss_delta=-1.344413
repair_example_count=24
neutral_prompt_example_count=12
decoder_anchor_example_count=0
model_quality_claim=training_artifact_only
next_action=run_bounded_objective_unassisted_repair_replay_comparison
```

## 测试覆盖

focused pytest 覆盖：

- 正常 fake run 能生成 ready evidence。
- 缺 `checkpoint.pt` 时失败。
- seed summary 中 `decoder_anchor_example_count > 0` 时失败。
- artifact writer 和 CLI 能输出完整 sidecar。

focused pytest：

```text
4 passed
```

全量回归：

```text
1718 passed
```

source encoding hygiene：

```text
status=pass
source_count=1248
syntax_error_count=0
```

## 运行证据

真实 report：

```text
e/847/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-training-run/model_capability_route_promotion_bounded_objective_unassisted_repair_training_run.json
```

HTML 截图：

```text
e/847/图片/v847-bounded-objective-unassisted-repair-training-run-html.png
```

## 一句话总结

v847 把无锚点 repair seed 训练成真实 checkpoint，并把能力判断继续挡在 replay comparison 之后，避免把训练产物误说成模型能力。
