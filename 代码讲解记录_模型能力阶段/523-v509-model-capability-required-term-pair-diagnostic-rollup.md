# v509 required-term pair diagnostic rollup 代码讲解

## 本版目标与边界

v509 的目标不是再加一个零散报告，而是把 v503-v508 的六个 required-term pair 诊断合并成一个可复核的阶段结论。

本版明确不做三件事：

- 不训练模型。
- 不修改 checkpoint 或 tokenizer。
- 不把 forced-choice、forced-first-token、forced-prefix 证据宣称为自由生成能力。

它解决的问题是：经过 v503-v508 后，下一步到底该继续调 decoding，还是应该改变训练目标。

## 前置链路

v509 依赖六个前置证据：

- v503：forced-choice diagnostic 证明 `symmetric-anchor` 变体内部可同时偏向 `fixed/loss`。
- v504：generation-gap audit 证明内部信号没有稳定表达到自由生成。
- v505：decoding-gap probe 证明小 decoding profiles 只有 partial expression，没有 full profile recovery。
- v506：decoding-path trace 证明 expected first token 排名不低，但采样第一步没有稳定命中。
- v507：first-token repair 证明强制第一 token 只能局部改善。
- v508：prefix-completion sweep 证明 `fixed` 需要更长 forced prefix，问题已经进入 span completion。

v509 的角色是把这些离散证据收成一个下一步实验选择。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_diagnostic_rollup.py`
  - 收集源报告、构造 stage rows、汇总 summary、生成下一实验计划。
- `src/minigpt/model_capability_required_term_pair_diagnostic_rollup_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML，让 rollup 既可被脚本消费，也能人工检查。
- `scripts/run_model_capability_required_term_pair_diagnostic_rollup.py`
  - CLI 入口，支持从 `e/` 目录自动查找 v503-v508 诊断报告。
- `tests/test_model_capability_required_term_pair_diagnostic_rollup.py`
  - 覆盖 rollup pass、缺失输入 fail、artifact 输出和 next plan 字段。

## 核心数据结构

`stage_rows` 每行对应一个源诊断：

- `stage`
- `label`
- `status`
- `decision`
- `source_path`
- `summary`

这个结构保证 v509 不是孤立结论，而是能反查到每个阶段的源 JSON。

`summary` 抽取跨阶段关键指标：

- `forced_choice_full_match_variant_count`
- `forced_generation_gap_variant_count`
- `decoding_profile_full_hit_count`
- `path_first_sample_match_count`
- `first_token_repair_improved_prompt_count`
- `prefix_one_token_hit_probe_count`
- `span_completion_gap_probe_count`

`next_experiment_plan` 是本版加厚的重点：

- `plan_id`
- `recommended`
- `reason`
- `target_terms`
- `source_metrics`
- `steps`
- `minimum_success_criteria`
- `excluded_options`

它把“下一步做什么”写成可检查契约，而不是只写一句建议。

## 核心函数流程

`collect_required_term_pair_diagnostic_reports()` 从输入目录按文件名查找六个源报告。如果某个报告缺失，返回空 dict 和空 path，由后续结构检查处理。

`build_model_capability_required_term_pair_diagnostic_rollup()` 做四步：

1. `_input_issues()` 检查源报告是否存在且 `status=pass`。
2. `_stage_rows()` 保留每个源报告的 status、decision、summary 和 source path。
3. `_summary()` 抽取跨阶段关键指标。
4. `_next_experiment_plan()` 根据 rollup decision 输出下一步实验计划。

`_rollup_decision()` 的判断顺序偏保守：

- 如果已有 full profile recovery，说明 decoding 已恢复。
- 如果 prefix completion 仍有 span gap，则推荐 continuation-span objective。
- 如果只看到局部改善，则继续 generation-side probe。
- 如果只看到内部信号，则记录 internal signal not expressed。

本轮真实结果落在第二类：`rollup_continue_with_span_objective`。

## 输出证据

v509 输出位置：

```text
e/509/解释/model-capability-required-term-pair-diagnostic-rollup/
```

截图和说明归档在：

```text
e/509/图片
e/509/解释/说明.md
```

HTML 报告新增三类信息：

- 顶部 summary 说明阶段整体状态。
- Next Experiment Plan 说明下一步实验、成功标准和排除路线。
- Stages 表展示每个源报告的路径和关键指标。

## 测试覆盖

测试覆盖两条关键路径：

- 六个输入报告齐全时，rollup 输出 `required_term_pair_next_span_objective`，并生成多格式 artifact。
- 缺失 `prefix_completion` 报告时，`status=fail`，`--require-pass` 对应 exit code 为 `1`。

断言不仅检查 pass/fail，还检查：

- `next_experiment_plan.plan_id`
- `minimum_success_criteria`
- Markdown/HTML 是否写出 next plan
- CSV 是否包含 `source_path` 和 `key_metric`

## 一句话总结

v509 把 required-term pair 的连续诊断从“看到很多现象”推进到“选定下一类实验”：最小 continuation-span objective。
