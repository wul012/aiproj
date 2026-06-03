# v816 route promotion bounded real replay failure alignment diagnostic 代码讲解

## 本版目标和边界

v816 的目标是诊断为什么 v814 revised checkpoint 在 v815 仍然 `0/5`。前几版已经证明继续普通 repair seed 和短训没有带来 bounded replay 提升，所以本版不再训练，而是检查 benchmark prompt、revised corpus、replay continuation 和训练 evidence 是否对齐。

本版不宣称模型能力提升，也不构建新 seed。它只给出 root-cause diagnostic，并把下一步指向 prompt-aligned seed revision。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.py`
  - 核心诊断模块。
  - 消费 benchmark suite、checkpoint comparison、seed revision、training revision 和 corpus。
  - 生成 `case_diagnostics`、`root_causes`、`summary`。

- `src/minigpt/model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 展示 `Case Diagnostics` 和 `Root Causes`。

- `scripts/diagnose_model_capability_route_promotion_bounded_real_replay_failure_alignment.py`
  - CLI 入口。
  - 支持从历史 evidence 目录直接定位 JSON。

- `tests/test_model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic.py`
  - 覆盖 prompt/corpus gap 诊断、输出和 CLI。

## 核心诊断

`_case_diagnostic()` 对每个 benchmark case 做四类检查：

- benchmark prompt 是否原样出现在 revised corpus；
- expected terms 是否出现在 repair continuation；
- corpus 中 `fixed` 和 `loss` 的出现次数；
- 该 case 的推荐动作。

如果 prompt 不在 corpus 中，诊断为：

```text
benchmark_prompt_not_represented_in_training_corpus
```

如果 prompt 在 corpus 中、corpus 也有 required terms，但生成仍 miss，则诊断为：

```text
required_terms_present_but_generation_not_anchored
```

## Root Causes

真实 v816 输出有 3 条 root cause：

- `benchmark_prompt_training_corpus_gap`
  - evidence: `prompt_gap_count=2`
  - 含义：部分 benchmark prompt 没有原样进入 revised corpus。

- `repair_training_not_replay_aligned`
  - evidence: `pass_rate_delta=-0.4`
  - 含义：训练产物存在，但 replay 仍然比 baseline 退步。

- `loss_improvement_not_sufficient_for_exact_terms`
  - evidence: `final_val_loss=3.9442`
  - 含义：loss 下降不能替代 exact-term generation 验证。

## 运行结果

真实运行：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic_ready
case_count=5
failed_case_count=5
prompt_gap_count=2
root_cause_count=3
next_step=build_prompt_aligned_seed_revision
```

这里的 `status=pass` 仍然只是诊断合同成立，不代表模型能力恢复。

## 为什么这版重要

v813/v814 说明“加入 baseline preservation 并重新训练”还不够。v816 进一步指出：训练样本没有完全贴近 benchmark prompt，所以模型在真实 replay prompt 上仍然无法稳定生成 `fixed loss`。

下一步应该把 v803 suite 的 exact prompts 直接变成训练样本，并设置更严格的 replay-first gate。

## 一句话总结

v816 把连续 repair 失败从“训练不够”重新定位为“benchmark prompt 与训练语料、exact-term 生成目标没有充分对齐”，为下一轮 prompt-aligned seed revision 提供了证据。
