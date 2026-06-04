# v853：bounded objective unassisted repair seed revision replay comparison

## 本版目标和边界

v853 的目标是把 v852 真实 checkpoint 放回 v836 bounded objective contract replay 中，判断 revised no-anchor corpus 是否让模型从 v848 的 zero-hit 状态向前移动。

边界：

- 不继续训练。
- 不使用 decoder anchor。
- 不把 partial hit 宣称为 contract recovery。
- 不允许 promotion。

这版只回答一个问题：v852 checkpoint 是否比 v847 checkpoint 更接近 `fixed loss` contract。

## 前置链路

链路来自：

```text
v836 objective contract
 -> v850 curriculum revision
 -> v851 seed revision
 -> v852 real training run
 -> v853 replay comparison
```

v852 已经证明 revised corpus 能训练成 checkpoint，但它的质量声明仍是：

```text
model_quality_claim=training_artifact_only
```

因此 v853 必须用 replay 给出能力证据。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison.py`
  - v853 adapter。复用 v848 no-anchor replay builder，并把 v852 training evidence 映射成可消费的 replay 输入。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison_artifacts.py`
  - v853 专属 JSON/CSV/TXT/Markdown/HTML writer。
- `scripts/run_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison.py`
  - CLI 入口，支持 `--require-comparison-ready` 和 `--require-objective-pass`。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison.py`
  - 覆盖 zero-hit、contract recovered、training not ready、writer/CLI。
- `e/853/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-replay-comparison/`
  - 保存真实 replay 产物。
- `e/853/图片/v853-bounded-objective-unassisted-repair-seed-revision-replay-comparison-html.png`
  - Playwright MCP 截图。

## adapter 映射

v848 replay builder 期望训练证据里有：

```text
bounded_objective_unassisted_repair_training_ready
```

v852 输出的是：

```text
bounded_objective_unassisted_repair_seed_revision_training_ready
```

因此 v853 adapter 只做契约保持映射：

```text
seed_revision_training_ready -> unassisted_repair_training_ready
```

随后再把输出改回 seed-revision 语义：

```text
bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready
route=bounded_objective_unassisted_repair_seed_revision
training_source=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run
```

这个设计避免复制 replay engine，也避免新建巨型文件。

## 真实 replay 命令

```text
python scripts/run_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison.py --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract/model_capability_route_promotion_bounded_objective_contract.json --training-run e/852/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-training-run/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run.json --checkpoint e/852/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-training-run/run/checkpoint.pt --tokenizer e/852/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-training-run/run/tokenizer.json --device cpu --out-dir e/853/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-replay-comparison --require-comparison-ready --force
```

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_partial_required_term_hit
objective_contract_recovered=False
canonical_case_pass=False
case_count=3
passed_case_count=0
any_hit_case_count=2
zero_hit_case_count=1
pass_rate=0.0
promotion_ready=False
model_quality_claim=partial_required_term_signal
next_action=diagnose_bounded_objective_unassisted_repair_seed_revision_partial_hit_before_more_training
```

## replay 行为解释

三个 contract case 的结果：

```text
canonical_direct_completion -> continuation=" fixed t"  hit fixed, missed loss
minimal_direct_completion   -> continuation=" fixed t"  hit fixed, missed loss
completion_label_surface    -> continuation=" ler: lo"  missed fixed/loss
```

这比 v848 的 `zero_hit_case_count=3` 更好，因为已有两个 case 命中 `fixed`。

但所有 case 仍然失败，因为 contract 要求 `fixed` 和 `loss` 都出现；因此：

```text
passed_case_count=0
objective_contract_recovered=False
promotion_ready=False
```

## 测试覆盖

focused pytest 覆盖：

- zero-hit replay 可以 ready，但不 recovery。
- fake all-pass replay 会进入 holdout-required 决策。
- seed revision training not ready 会失败并暴露 `training_ready` issue。
- artifact writer 和 CLI 能输出 JSON/CSV/TXT/Markdown/HTML。

```text
4 passed
```

全量验证：

```text
py_compile: pass
full pytest: 1738 passed
source encoding: source_count=1272 clean_count=1272 bom_count=0 syntax_error_count=0
git diff --check: pass
```

## 运行证据

HTML 截图：

```text
e/853/图片/v853-bounded-objective-unassisted-repair-seed-revision-replay-comparison-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Decision=...partial_required_term_hit
Cases=3
Passed=0
Any hits=2
Zero hits=1
Claim=partial_required_term_signal
```

## 一句话总结

v853 把 revised no-anchor branch 从 zero-hit 推进到 partial required-term signal，但仍明确挡在 contract recovery 和 promotion 之前。
