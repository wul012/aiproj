# v856：bounded objective unassisted repair seed revision curriculum patch training run

## 本版目标和边界

v856 的目标是把 v855 patched corpus 训练成真实 checkpoint。

边界：

- 不运行 replay。
- 不声明模型能力恢复。
- 不使用 decoder anchor。
- 不修改 v836 contract。

这版只证明 patched corpus 已进入真实训练闭环。

## 前置链路

v855 生成了：

```text
patch_example_count=18
loss_focus_example_count=18
completion_surface_example_count=2
decoder_anchor_example_count=0
patched_corpus_char_count=2996
```

v856 用其中的 `model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_corpus.txt` 训练。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.py`
  - v856 adapter。把 curriculum patch summary 映射到 v852 training-run 校验可消费的 seed revision summary。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_artifacts.py`
  - v856 专属 JSON/CSV/TXT/Markdown/HTML writer。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run.py`
  - 覆盖 ready training evidence、patch not ready、writer/CLI。
- `e/856/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-training-run/`
  - 保存真实 training run 和 report。
- `e/856/图片/v856-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-training-run-html.png`
  - Playwright MCP 截图。

## adapter 映射

v852 training-run 校验需要：

```text
bounded_objective_unassisted_repair_seed_revision_ready
example_count
direct_example_count
neutral_prompt_example_count
decoder_anchor_example_count
corpus_char_count
```

v856 从 v855 patch summary 映射：

```text
curriculum_patch_ready -> seed_revision_ready
patch_example_count -> example_count/direct_example_count
loss_focus_example_count -> neutral_prompt_example_count
patched_corpus_char_count -> corpus_char_count
decoder_anchor_example_count -> 0
```

这样复用已有训练产物校验，不复制新的检查器。

## 真实训练命令

```text
python scripts/train.py --prepared-data e/855/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-curriculum-patch/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_corpus.txt --out-dir e/856/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-training-run/run --tokenizer char --batch-size 8 --block-size 64 --max-iters 80 --eval-interval 10 --eval-iters 5 --learning-rate 0.001 --train-ratio 0.9 --n-layer 2 --n-head 2 --n-embd 64 --dropout 0.0 --seed 1856 --device cpu --sample-prompt "Complete with exactly two tokens: fixed loss\ncompletion:" --sample-tokens 12 --sample-temperature 0.8 --sample-top-k 20
```

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run_ready
final_step=80
final_train_loss=1.6474262475967407
final_val_loss=1.7552181482315063
train_loss_delta=-1.906295
repair_example_count=18
neutral_prompt_example_count=18
decoder_anchor_example_count=0
model_quality_claim=training_artifact_only
next_action=run_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison
```

## 测试覆盖

focused pytest 覆盖：

- curriculum patch ready 时 training report ready。
- patch not ready 时失败。
- CLI 和 writer 输出完整产物。

```text
3 passed
```

全量验证：

```text
py_compile: pass
full pytest: 1747 passed
source encoding: source_count=1284 clean_count=1284 bom_count=0 syntax_error_count=0
git diff --check: pass
```

## 运行证据

HTML 截图：

```text
e/856/图片/v856-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-training-run-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Ready=True
Final step=80
Val loss=1.7552181482315063
Decoder anchors=0
Claim=training_artifact_only
```

## 一句话总结

v856 把 no-anchor curriculum patch 训练成真实 checkpoint，但仍把能力判断交给下一版 replay。
