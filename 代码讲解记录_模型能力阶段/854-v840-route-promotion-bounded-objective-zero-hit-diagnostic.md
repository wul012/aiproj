# v840：bounded objective zero-hit diagnostic

## 本版目标和边界

v840 的目标是解释 v839 为什么 zero-hit。v839 已经证明 v838 checkpoint 在 3 个 objective contract cases 上全部没有命中 `fixed/loss`；v840 不继续训练，也不改语料，而是先把失败原因拆清楚。

本版的边界很重要：它不是新治理链，也不是能力提升，只是把“训练 loss 下降但 replay zero-hit”的矛盾转成可行动诊断。

## 前置链路

输入来自三处：

- v839 replay comparison：真实 replay 输出、continuation、hit/missed terms。
- v837 objective seed：direct examples 数量和 corpus。
- v838 training run：真实训练 loss、checkpoint evidence。

诊断要同时看这三者，避免只从一个指标下结论。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.py`
  - 读取 replay/seed/training/corpus，生成 case diagnostics、root causes 和 next step。
- `src/minigpt/model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/diagnose_model_capability_route_promotion_bounded_objective_replay_zero_hit.py`
  - CLI 入口，支持目录输入、corpus 文件和 `--require-diagnostic-ready`。
- `tests/test_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.py`
  - 覆盖 near-miss zero-hit、objective 已 recovered 时失败、输出和 CLI。
- `e/840/解释/model-capability-route-promotion-bounded-objective-replay-zero-hit-diagnostic/`
  - 保存真实诊断产物。
- `e/840/图片/v840-bounded-objective-zero-hit-diagnostic-html.png`
  - Playwright MCP 截图。

## 核心诊断逻辑

每条 case diagnostic 包含：

```text
case_id
zero_hit
near_miss_terms
prompt_in_corpus
term_corpus_count
hit_terms
missed_terms
continuation_preview
diagnosis
recommended_action
```

near-miss 使用轻量 Levenshtein 规则判断：如果 continuation 中的英文片段距离目标词只差 1 个编辑距离，就记录为 near miss。v839 中的 `wixed` 距离 `fixed` 是一次替换，因此被归入：

```text
near_miss_character_substitution_without_exact_term
```

## 真实结果

v840 输出：

```text
zero_hit_case_count=3
near_miss_case_count=3
prompt_in_corpus_count=3
root_cause_count=4
```

这说明：

- 不是 prompt 没进 corpus。
- 不是训练完全没学到局部形态。
- 但模型没有稳定生成 exact required terms。
- 继续盲目加训练轮次风险较高，应该先做 decoder anchor probe。

## 根因

本版 root causes 包括：

- `objective_replay_zero_required_term_hits`
- `near_miss_character_substitution`
- `direct_prompts_present_but_generation_unanchored`
- `loss_reduction_did_not_transfer_to_exact_generation`

这比一句“模型没学会”更可行动，因为它指出问题在 exact decoding/anchoring，不是简单的数据缺失。

## 测试覆盖

聚焦测试覆盖：

- `wixed w` 能被识别为 near-miss zero-hit。
- 如果 objective 已 recovered，诊断会失败，防止错误使用。
- CLI 和 artifact writer 能输出 JSON、CSV、TXT、Markdown、HTML。

本版聚焦测试结果是 `3 passed`。

## 运行证据

真实命令：

```text
python scripts/diagnose_model_capability_route_promotion_bounded_objective_replay_zero_hit.py --replay-comparison e/839/解释/model-capability-route-promotion-bounded-objective-replay-comparison --objective-seed e/837/解释/model-capability-route-promotion-bounded-objective-seed --training-run e/838/解释/model-capability-route-promotion-bounded-objective-training-run --corpus e/837/解释/model-capability-route-promotion-bounded-objective-seed/model_capability_route_promotion_bounded_objective_seed_corpus.txt --out-dir e/840/解释/model-capability-route-promotion-bounded-objective-replay-zero-hit-diagnostic --require-diagnostic-ready --force
```

HTML 截图保存到：

```text
e/840/图片/v840-bounded-objective-zero-hit-diagnostic-html.png
```

## 一句话总结

v840 把 v839 的 zero-hit 失败从“模型没过”细化为“direct prompts 已在 corpus、loss 已下降，但 exact decoding 仍发生 near-miss 字符替换”，下一步应先做 decoder anchor probe。
