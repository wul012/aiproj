# v813 route promotion bounded real replay repair seed revision 代码讲解

## 本版目标和边界

v813 的目标是把 v812 的 repair strategy revision 转成下一轮训练可用的 revised seed。v811 已经证明 v810 repair checkpoint 退步，v812 已经给出策略：不能 promote 退步 checkpoint，下一轮必须保护 baseline 已通过 case。v813 就把这条策略落到 JSONL 和 corpus。

本版不训练模型，也不证明模型能力提升。它只准备训练输入，并且把 baseline preservation 写成明确样本。

## 前置链路

本版承接：

- v809：原始 repair seed，只有 6 条样本，主要补失败 case。
- v812：strategy revision，指出下一轮必须 carry forward 原始 repair signal，并给 regression case 加 baseline preservation。

v813 的输出会成为 v814 repair training revision 的 prepared corpus。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_seed_revision.py`
  - 核心 builder。
  - 消费 strategy revision 和原始 repair seed。
  - 生成 revised `seed_examples`、`repair_seed_revision`、`summary`。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_seed_revision_artifacts.py`
  - 输出 JSON/CSV/JSONL/corpus/text/Markdown/HTML。
  - JSONL 和 corpus 是下一版训练直接消费的关键产物。

- `scripts/build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision.py`
  - CLI 入口。
  - 支持从 v812 strategy revision 输出目录和 v809 repair seed 输出目录读取输入。

- `tests/test_model_capability_route_promotion_bounded_real_replay_repair_seed_revision.py`
  - 覆盖 baseline preservation、输入失败、输出和 CLI。

## 样本类型

v813 的 revised seed 包含四类样本：

1. `carry_forward_original_repair_seed`
   - 从 v809 原始 seed 复制过来。
   - 作用是保留已有 repair signal，避免下一轮完全换目标。

2. `baseline_preservation`
   - 只给 regression case 增加。
   - regression case 指 baseline 曾经通过，但 repair checkpoint 失败。
   - 作用是保护 baseline 已经学到的 fixed/loss route。

3. `missing_term_retention`
   - 给所有失败 repair replay case 增加。
   - 作用是把 missed terms 显式写回训练文本。

4. `contrastive_self_check`
   - 给所有失败 case 增加。
   - 作用是强化“必须同时包含 fixed 和 loss”这个判定边界。

## 核心流程

`build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision()` 的流程是：

1. 读取 strategy summary，确认 strategy revision ready。
2. 读取原始 repair seed examples。
3. 从 strategy revision 读取 case actions。
4. `_carry_forward_example()` 保留原始 seed。
5. `_case_action_examples()` 按 case action 生成新增样本。
6. `_checks()` 确认 original examples 被保留、regression case 有 preservation examples、所有样本都有 text。
7. 写出 JSONL 和 corpus。

真实运行结果：

```text
original_example_count=6
added_example_count=12
example_count=18
baseline_preservation_example_count=2
next_step=train_bounded_real_replay_repair_seed_revision
```

## 关键检查

v813 的检查不只看文件存在：

- `strategy_revision_passed`
- `strategy_revision_ready`
- `repair_seed_passed`
- `repair_seed_ready`
- `case_actions_present`
- `original_examples_carried`
- `preservation_examples_for_regressions`
- `seed_examples_have_text`

其中 `preservation_examples_for_regressions` 是本版最关键的保护：只要存在 regression case，就必须有对应的 baseline preservation example。

## 产物角色

- JSON：完整结构化证据，供后续工具读取。
- CSV：快速查看样本类型和 guardrail。
- JSONL：逐条训练样本，适合后续数据管线消费。
- Corpus：直接给 `scripts/train.py --prepared-data` 使用。
- HTML/截图：人工可视化审查。

这些产物本身不证明模型变强。真正的能力判断仍要等下一版训练后 replay comparison。

## 测试覆盖

测试覆盖：

- ready strategy + seed 可以生成 seed revision。
- 原始 seed 被 carry forward。
- regression case 有 baseline preservation examples。
- strategy 不 ready 时失败。
- CLI 能从目录读取并写出 JSONL/corpus。

这些测试保护的是“修订语料不能丢原始信号，也不能漏掉 regression 保底样本”。

## 一句话总结

v813 把 v811/v812 发现的退步约束转成了下一轮训练语料，让后续 repair training 不再只是补失败项，而是同时保护 baseline 已有能力。
