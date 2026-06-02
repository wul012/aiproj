# v742 pair prompt transfer contract patch

## 本版目标和边界

v742 的目标是把 v741 的 repair plan 落成一个 materializer-ready contract patch。

本版不训练、不生成 corpus、不做 replay。它只修改训练输入合约：在 v736 direct-completion surface contract 上添加非 heldout 的 pair-transfer rows。

## 前置链路

```text
v740 pair-probe replay
 -> exact heldout pair not ready
v741 repair plan
 -> propose pair_readiness_pair_prompt_transfer_contract_patch
v742 contract patch
 -> add surrogate transfer rows, keep fixed=|loss= held out
```

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch.py`
  - 读取 v741 repair plan 和 v736 base contract。
  - 生成 patched contract。
  - 检查 base contract、plan、row addition 和 leakage 边界。
- `src/minigpt/model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch.py`
  - CLI 入口。
- `tests/test_model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch.py`
  - 覆盖 patch ready、错误 plan、materializer 兼容和五格式输出。
- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 接入 `pair_readiness_pair_prompt_transfer_contract_patch_ready`。
  - 接入新 JSON 文件名。

## patch rows

新增 8 行：

```text
pair_transfer pipe surrogate fixed | loss => fixed loss
pair_transfer slash surrogate fixed/loss => fixed loss
pair_transfer comma surrogate fixed, loss => fixed loss
pair_transfer words fixed plus loss => fixed loss
pair_transfer bracket [fixed][loss] => fixed loss
pair_transfer reverse loss | fixed => loss fixed
pair_transfer reverse loss/fixed => loss fixed
pair_transfer boundary answer contains fixed and loss together
```

这些 rows 的共同点：

- fixed/loss 在同一行出现。
- 覆盖不同 separator style。
- 不包含 exact heldout `fixed=|loss=`。

## 核心检查

v742 的主要检查项：

```text
repair_plan_passed
repair_plan_decision
next_artifact_matches
base_contract_passed
base_contract_decision
pair_transfer_rows_added
pair_transfer_row_count
exact_direct_rows_preserved
heldout_pair_absent
heldout_pair_absent_from_patch
no_exact_eval_row_overlap
```

其中最关键的是：

- exact direct rows 仍在。
- pair-transfer rows 加入。
- heldout pair prompt 不在 patch rows 和 training rows 里。
- 新 decision 能被 materializer 接受。

## 真实输出

```text
status=pass
decision=pair_readiness_pair_prompt_transfer_contract_patch_ready
base_training_row_count=16
patched_training_row_count=24
pair_transfer_row_count=8
```

## 证据

运行输出：

```text
e/742/解释/model-capability-required-term-pair-readiness-pair-prompt-transfer-contract-patch/
```

截图：

```text
e/742/图片/v742-pair-prompt-transfer-contract-patch.png
```

截图可见：

- `Decision=pair_readiness_pair_prompt_transfer_contract_patch_ready`
- `Base rows=16`
- `Patched rows=24`
- `Transfer rows=8`

## 一句话总结

v742 把 pair prompt transfer 修复从计划推进到可物化 contract patch，同时继续保护 exact heldout pair prompt 不泄漏。
