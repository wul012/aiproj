# v510 required-term pair continuation-span objective 代码讲解

## 本版目标与边界

v510 承接 v509 的阶段判断：不要继续只调 decoding profile，而是验证一个最小 continuation-span 训练目标是否能改善 `fixed/loss` 的完整词补全。

本版不做大模型训练、不扩大外部数据、不宣称生产级模型能力。它只做一件事：围绕 `fixed/loss` 构造小语料，真实训练 checkpoint，再比较 v508 的 prefix-completion 边界。

## 前置链路

v509 的 rollup 给出下一实验计划：

```text
continuation_span_objective_fixed_loss
```

它的依据来自 v503-v508：

- 内部 forced-choice 已经有配对信号。
- 自由生成没有稳定表达。
- first-token repair 只能局部改善。
- prefix-completion 显示 `fixed` 比 `loss` 更弱，需要更长前缀。

v510 只验证这条计划，不另开治理链。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_continuation_span_objective.py`
  - 主流程：读取 v509、定位 v508、抽取 fixed/loss examples、构造语料、训练、生成、prefix 对比。
- `src/minigpt/model_capability_required_term_pair_continuation_span_objective_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_continuation_span_objective.py`
  - CLI 入口，支持训练参数、输出目录、强制覆盖和 require-pass。
- `tests/test_model_capability_required_term_pair_continuation_span_objective.py`
  - 覆盖成功路径、缺源报告失败、example 选择和 corpus 构造。

## 核心数据结构

`examples` 来自 v508 的 prefix-completion probes：

- `term`
- `prompt_term`
- `scaffold_prompt`
- `source_variant_id`
- `source_pair_id`
- `source_profile_id`
- `source_checkpoint_path`
- `source_tokenizer_path`

`compare_rows` 是本版最重要的对比结构：

- `term`
- `source_minimum_hit_prefix_token_count`
- `candidate_minimum_hit_prefix_token_count`
- `minimum_hit_prefix_delta`
- `source_one_token_prefix_hit`
- `candidate_one_token_prefix_hit`
- `candidate_full_prefix_hit`

它让 v510 的结论直接落在 v508 的弱点上，而不是另起一套难以比较的指标。

## 核心函数流程

`build_model_capability_required_term_pair_continuation_span_objective()` 是主入口：

1. 从 v509 `stage_rows` 定位 v508 prefix-completion JSON。
2. `select_continuation_span_examples()` 抽取 `fixed/loss` 两个目标。
3. `build_continuation_span_corpus()` 构造 prompt 停在目标词前的 tiny 语料。
4. `_train_micro_checkpoint()` 调用现有训练脚本，产出 checkpoint/tokenizer/metrics/config。
5. `_generation_row()` 对 `fixed:` 和 `loss:` 做自由生成 probe。
6. `_candidate_prefix_rows()` 对新 checkpoint 做 forced-prefix sweep。
7. `compare_span_prefix_summaries()` 比较 v508 source 与 v510 candidate 的最小命中前缀。

## 真实结果解释

真实运行结果：

- `training_status=pass`
- `checkpoint_exists=True`
- `generation_hit_count=0`
- `candidate_pair_full_generation_hit=False`
- `candidate_one_token_prefix_hit_count=2`
- `prefix_minimum_improved_count=1`

关键变化：

- `fixed`: source min prefix `4` -> candidate min prefix `1`
- `loss`: source min prefix `1` -> candidate min prefix `1`

这说明 continuation-span objective 对 v508 暴露的 span completion 弱点有帮助，但还没有让自由生成直接 full-hit。

## 输出证据

v510 输出位置：

```text
e/510/解释/model-capability-required-term-pair-continuation-span-objective/
```

截图和说明归档在：

```text
e/510/图片
e/510/解释/说明.md
```

## 测试覆盖

测试覆盖：

- 成功路径下，fake training + fake generation + fake prefix sweep 会产生 full generation 和 prefix gain。
- 缺失 v508 prefix source 时，报告失败并返回 require-pass exit code `1`。
- example 选择保持 `fixed/loss` 顺序，corpus 真实包含 `fixed:fixed`、`loss:loss` 和 pair bridge 行。

测试重点不是模拟真实模型质量，而是保护 v510 的契约：输入来自 v509/v508，输出必须能比较 source/candidate prefix boundary。

## 一句话总结

v510 把 required-term pair 从诊断推进到真实训练实验：continuation-span objective 改善了 `fixed` 的 prefix-completion 边界，但还没有完成自由生成恢复。
