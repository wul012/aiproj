# v731 direct-prompt bridge contract patch

## 本版目标和边界

v731 的目标是根据 v730 diagnostic 给 v727 objective-structure contract 打补丁。

本版不训练模型、不生成 corpus。它只新增 bridge rows，让 raw `fixed=` 和 `loss=` surface 出现在训练语料语义中，同时继续禁止 heldout pair probe `fixed=|loss=` 泄漏。

## 前置链路

```text
v729 objective-structure training
 -> fixed/loss direct probes both miss
v730 surface mismatch diagnostic
 -> raw_surface_reference_count=0
v731 direct-prompt bridge patch
 -> add raw fixed= and loss= bridge rows
```

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.py`
  - 定义 bridge rows。
  - 合并 base contract 和 patch rows。
  - 检查 diagnostic、base contract、fixed/loss 平衡和 heldout 泄漏。
- `src/minigpt/model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.py`
  - CLI 入口，要求 `--diagnostic` 和 `--base-contract`。
- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 接入 `pair_readiness_direct_prompt_bridge_contract_patch_ready`。
  - 接入 bridge patch JSON filename。
- `tests/test_model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.py`
  - 覆盖 ready、错误 diagnostic、materializer locator 和五格式输出。

## Patch 内容

v731 增加 8 条 bridge rows：

```text
4 rows for fixed=
4 rows for loss=
```

示例：

```text
bridge=direct_prompt | prompt=fixed= | answer=fixed
fixed= -> fixed token
bridge=direct_prompt | prompt=loss= | answer=loss
loss= -> loss token
```

它们不是 exact `fixed=` 或 `loss=` 单行，因此没有把 direct prompt 作为独立训练行；但它们足够暴露 raw prompt surface，修复 v730 诊断出的 raw refs=0 问题。

## 泄漏边界

核心检查：

```text
no_exact_eval_row_overlap
heldout_pair_absent
fixed_bridge_balance
loss_bridge_balance
diagnostic_recommends_bridge
```

最重要的是：

```text
heldout_pair_absent pass False
```

这表示 `fixed=|loss=` 没有进入训练 rows。

## Materializer 接入

v731 将新 decision 和 JSON filename 加入 materializer：

```text
pair_readiness_direct_prompt_bridge_contract_patch_ready
model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.json
```

因此下一版可以直接调用 corpus materialization。

## 证据

运行证据：

- `e/731/解释/model-capability-required-term-pair-readiness-direct-prompt-bridge-contract-patch/`
- `e/731/图片/v731-direct-prompt-bridge-contract-patch.png`

截图显示 patch ready、base rows 18、patched rows 26、bridge rows 8。

## 一句话总结

v731 把 v730 的 surface mismatch 诊断转成可物化 contract patch，为下一轮训练提供 raw direct prompt bridge。
