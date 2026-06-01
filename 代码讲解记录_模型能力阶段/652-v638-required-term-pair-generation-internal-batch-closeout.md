# v638 required-term pair generation/internal batch closeout

## 本版目标和边界

v638 是 v629-v638 十版批次 closeout。它把本轮的 corpus、真实训练、forced-choice、comparison、route decision 收成一个可复核报告。

本版不新增训练结果，也不宣称模型通用能力提升；它只总结 targeted required-term pair 路线的证据。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_generation_internal_batch_closeout.py
src/minigpt/model_capability_required_term_pair_generation_internal_batch_closeout_artifacts.py
scripts/run_model_capability_required_term_pair_generation_internal_batch_closeout.py
tests/test_model_capability_required_term_pair_generation_internal_batch_closeout.py
e/638/解释/model-capability-required-term-pair-generation-internal-batch-closeout/
```

## 输入输出

输入：

```text
v636 generation/internal alignment comparison
v637 generation/internal alignment route decision
```

输出：

```text
model_capability_required_term_pair_generation_internal_batch_closeout.json
model_capability_required_term_pair_generation_internal_batch_closeout.csv
model_capability_required_term_pair_generation_internal_batch_closeout.txt
model_capability_required_term_pair_generation_internal_batch_closeout.md
model_capability_required_term_pair_generation_internal_batch_closeout.html
```

## 核心结论

```text
decision=close_batch_and_design_joint_cycle_internal_repair
batch_version_count=10
aligned_pair_full_count=0
selected_generation_route=loss-internal-joint-cycle
internal_anchor_route=loss-internal-first-token
model_quality_claim=targeted_generation_signal_only
```

这说明本轮最大进展是 v630 的 generation pair-full。它是真实训练正结果，但 forced-choice 仍未 full match，因此不能升级成稳定能力声明。

## Closeout Items

`joint_cycle_generation_pair_full`：确认 v630 joint-cycle 是本轮唯一 generation pair-full。

`internal_alignment_not_ready`：确认没有路线同时满足 generation/internal pair-full。

`balanced_anchor_rejected`：确认 balanced-anchor 在生成和内部评分中都是 fixed-only。

`next_route_selected`：确认下一步路线是 joint-cycle internal repair。

## 测试覆盖

新增测试覆盖：

- 正常 closeout 会选择 `close_batch_and_design_joint_cycle_internal_repair`。
- route decision 缺失 selected route 时失败。
- 五种输出格式都能渲染。

## 一句话总结

v638 把十版推进收束为清晰结论：生成 pair-full 已经出现，稳定能力还没出现，下一轮要做 internal repair 和跨 seed 重复。
