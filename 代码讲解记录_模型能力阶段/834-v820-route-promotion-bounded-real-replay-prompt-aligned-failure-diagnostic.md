# v820 route promotion bounded real replay prompt-aligned failure diagnostic

## 本版目标和边界

v820 的目标是诊断 v819 prompt-aligned checkpoint 为什么仍然在 bounded replay 中 0/5。它不是继续训练，也不是修改 benchmark，而是把 v817 seed、v818 training、v819 replay 和 v819 comparison 合在一起，判断失败是语料覆盖问题、训练问题，还是生成锚定问题。

本版不声明模型能力提升。它的输出是下一步实验方向：优先做 decoder anchor 或 forced prefix probe，而不是继续盲目增加训练轮次。

## 前置路线

- v817 已把 v803 的 5 个 exact benchmark prompts 加入 seed corpus。
- v818 已从该 corpus 训练出真实 checkpoint。
- v819 replay 证明该 checkpoint 仍然 `0/5`，相对 v806 baseline 的 `2/5` 继续回归。
- v820 需要解释为什么“prompt 已对齐”仍然没有生成 `fixed loss`。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.py`
  - 核心诊断器。
  - 读取 replay、comparison、seed revision、training run 和 corpus。
  - 输出逐 case diagnosis、root causes、summary 和 interpretation。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_artifacts.py`
  - 输出层。
  - 写 JSON、CSV、TXT、Markdown、HTML。
  - CSV 聚焦逐 case 诊断，HTML 展示 zero-hit、fragment-like、root causes。

- `scripts/diagnose_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure.py`
  - CLI 入口。
  - 输入包括 `--prompt-aligned-replay`、`--comparison`、`--prompt-aligned-seed`、`--training-run`、`--corpus`。

- `tests/test_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.py`
  - 覆盖 prompt 已在 corpus、generation 仍零命中的诊断路径。

- `e/820/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-failure-diagnostic/`
  - 本版真实诊断证据。

## 核心数据结构

`case_diagnostics` 是 v820 最重要的表。每个 case 包含：

- `case_id`
  - v803 bounded benchmark case id。

- `prompt_in_seed`
  - replay prompt 是否出现在 v817 seed examples 中。

- `prompt_in_corpus`
  - replay prompt 是否出现在 v817 corpus 中。

- `hit_terms` / `missed_terms`
  - replay 实际命中的 required terms 和缺失 terms。

- `zero_hit`
  - 是否完全没有命中 `fixed` 或 `loss`。

- `fragment_like_generation`
  - continuation 是否像字符碎片，而不是完整词。

- `term_seed_count` / `term_corpus_count`
  - required terms 在 seed/corpus 里的出现次数。
  - 真实 v820 结果中 `fixed` 与 `loss` 各出现 47 次。

- `diagnosis`
  - 本 case 的诊断类别。
  - 真实结果为 `character_fragmentation_without_term_anchoring`。

- `recommended_action`
  - 本 case 的下一步动作。
  - 真实结果指向 `run_decoder_anchor_or_forced_prefix_probe`。

## 核心函数

`build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic()` 是主入口：

1. 读取 v819 prompt-aligned replay。
2. 读取 v819 comparison，确认 promotion blocked。
3. 读取 v817 prompt-aligned seed revision。
4. 读取 v818 training run。
5. 读取 v817 corpus。
6. 对每个 replay row 调用 `_case_diagnostic()`。
7. 调用 `_root_causes()` 汇总根因。
8. 调用 `_checks()` 确认输入链路可用。
9. 输出 `diagnostic`、`summary` 和 `interpretation`。

`_case_diagnostic()` 的判断顺序很重要：

- 如果 prompt 不在 corpus，说明还是语料对齐问题。
- 如果 prompt 在 corpus 且 required terms 在 corpus，但 generation 零命中，说明问题转为生成锚定。
- 如果 continuation 有大量散落字符和空格，又没有完整 required terms，则标记 `fragment_like_generation=True`。

`_root_causes()` 根据全部 case 聚合出四类根因：

- `exact_prompts_present_but_generation_unanchored`
- `zero_required_term_hits`
- `character_fragmentation_dominates_generation`
- `loss_reduction_did_not_transfer_to_replay`

这些根因共同说明：v820 已经把问题从“没有见过这个 prompt”推进到“见过 prompt 但生成不了完整目标词”。

## 真实运行结果

本版真实 CLI 输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_ready
diagnostic_ready=True
case_count=5
failed_case_count=5
zero_hit_case_count=5
fragment_like_case_count=5
root_cause_count=4
next_step=run_decoder_anchor_or_forced_prefix_probe
```

最关键的证据是：

- 5 个 benchmark prompt 全部在 corpus 中。
- `fixed` 在 corpus 中出现 47 次。
- `loss` 在 corpus 中出现 47 次。
- 但 5 个 replay case 全部 zero-hit。
- continuation 形态多为字符碎片，例如 `fi i`、`fts td st`，没有组成完整 `fixed` 或 `loss`。

## 测试覆盖

本版新增 3 个 focused tests：

- prompt 已在 corpus、terms 已出现，但 generation 零命中时，诊断能产生 `exact_prompts_present_but_generation_unanchored`。
- comparison 输入失败时，diagnostic status 变为 `fail`。
- CLI 能定位 replay/comparison/seed/training 目录，并写出 JSON/CSV/TXT/MD/HTML。

这组测试保护的是诊断边界：v820 不是简单看失败 case 数，而是必须证明“语料覆盖仍失败”的状态。

## 运行证据

证据目录：

- `e/820/解释/说明.md`
- `e/820/解释/model-capability-route-promotion-bounded-real-replay-prompt-aligned-failure-diagnostic/`
- `e/820/图片/v820-bounded-real-replay-prompt-aligned-failure-diagnostic-html.png`

Playwright MCP 已打开 HTML 报告并完成截图，页面显示 failed 5/5、zero hit 5、fragments 5、root causes 4。

## 一句话总结

v820 把 prompt-aligned checkpoint 的失败原因从“训练语料没覆盖”推进到“生成没有锚住完整 required terms”，下一步应做解码锚定或 forced prefix probe。
