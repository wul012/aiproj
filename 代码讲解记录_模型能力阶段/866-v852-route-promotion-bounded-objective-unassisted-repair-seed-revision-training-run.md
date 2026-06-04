# v852：bounded objective unassisted repair seed revision training run

## 本版目标和边界

v852 的目标是把 v851 revised corpus 训练成真实 checkpoint。

边界：

- 不运行 replay。
- 不宣称模型能力恢复。
- 不使用 decoder anchor。
- 不改变 v836 contract。

这版只证明 revised corpus 已进入训练产物闭环。

## 前置链路

输入来自 v851：

```text
e/851/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision/
```

关键约束：

```text
bounded_objective_unassisted_repair_seed_revision_ready=True
neutral_prompt_example_count=18
decoder_anchor_example_count=0
```

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run.py`
  - v852 adapter。复用 v847 training-run builder，把 seed revision summary 映射成通用 unassisted seed summary。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run_artifacts.py`
  - 复用 v847 artifact renderer，并写入 v852 专属文件名。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run.py`
  - 覆盖正常训练 evidence、seed revision not ready、writer/CLI。
- `e/852/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-training-run/`
  - 保存真实训练 run 和 report。
- `e/852/图片/v852-bounded-objective-unassisted-repair-seed-revision-training-run-html.png`
  - Playwright MCP 截图。

## 为什么用 adapter

v847 已经有稳定的训练产物校验：

```text
seed summary -> run dir -> artifacts -> metrics -> summary
```

v852 只改变 seed 来源，因此 adapter 做字段映射：

```text
bounded_objective_unassisted_repair_seed_revision_ready
 -> bounded_objective_unassisted_repair_seed_ready
```

并把 next artifact 改写为：

```text
model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison
```

## 真实训练命令

```text
python scripts/train.py --prepared-data e/851/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_corpus.txt --out-dir e/852/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-training-run/run --tokenizer char --batch-size 8 --block-size 64 --max-iters 50 --eval-interval 10 --eval-iters 5 --learning-rate 0.001 --train-ratio 0.9 --n-layer 2 --n-head 2 --n-embd 64 --dropout 0.0 --seed 1852 --device cpu --sample-prompt "Complete the objective response.\nanswer:" --sample-tokens 12 --sample-temperature 0.8 --sample-top-k 20
```

训练输出：

```text
step=1  train_loss=3.4839 val_loss=3.4959
step=10 train_loss=3.0825 val_loss=3.1440
step=20 train_loss=2.7545 val_loss=2.8202
step=30 train_loss=2.5045 val_loss=2.6007
step=40 train_loss=2.2780 val_loss=2.4489
step=50 train_loss=2.1271 val_loss=2.2989
```

这些数字只说明 revised corpus 被学习，不能直接说明 replay 能力恢复。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run_ready
final_step=50
final_train_loss=2.1270718574523926
final_val_loss=2.2989022731781006
train_loss_delta=-1.356824
neutral_prompt_example_count=18
decoder_anchor_example_count=0
model_quality_claim=training_artifact_only
next_action=run_bounded_objective_unassisted_repair_seed_revision_replay_comparison
```

## 测试覆盖

focused pytest 覆盖：

- 正常 fake run 生成 ready evidence。
- seed revision not ready 时失败。
- artifact writer 和 CLI 输出完整。

focused pytest：

```text
3 passed
```

全量验证：

```text
py_compile: pass
full pytest: 1734 passed
source encoding: source_count=1268 clean_count=1268 bom_count=0 syntax_error_count=0
git diff --check: pass
```

## 运行证据

HTML 截图：

```text
e/852/图片/v852-bounded-objective-unassisted-repair-seed-revision-training-run-html.png
```

## 一句话总结

v852 把 revised corpus 训练成真实 checkpoint，并把能力判断继续留给下一版 replay comparison。
