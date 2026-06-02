# v710 pair-readiness loss-retention contract patch

## 本版目标和边界

v710 的目标是把 v709 的 loss-retention repair plan 落实成 contract patch。

本版不训练模型，只 patch contract，并更新 materializer，使它接受 `pair_readiness_loss_retention_contract_patch_ready` 作为可 materialize 的输入。

## 前置链路

v709 输出：

```text
decision=pair_readiness_loss_retention_repair_plan_ready
proposed_next_artifact=pair_readiness_loss_retention_contract_patch
```

v705 提供 base contract。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_loss_retention_contract_patch.py`
  - patch builder。
  - 读取 repair plan 和 base contract。
  - 新增 loss-retention rows。
  - 检查 heldout pair probe 不泄漏。

- `src/minigpt/model_capability_required_term_pair_readiness_loss_retention_contract_patch_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_readiness_loss_retention_contract_patch.py`
  - CLI。
  - 输入 v709 plan，另传 `--base-contract`。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 小改 materializer，让它接受原始 split contract 或 loss-retention patched contract。

- `tests/test_model_capability_required_term_pair_readiness_loss_retention_contract_patch.py`
  - 覆盖 patch ready、可 materialize、错误 plan 阻断、输出格式。

## Patch 设计

新增 rows：

```text
loss=l
loss=lo
loss=los
loss=loss
loss branch keeps l before fixed
loss branch resists fixed completion
loss prompt should not become fixed
loss direct retention beats fixed pollution
```

它没有删除 fixed rows，也没有加入 heldout pair probe。

## 运行证据

输出：

```text
decision=pair_readiness_loss_retention_contract_patch_ready
base_training_row_count=12
patched_training_row_count=20
added_training_row_count=8
```

证据目录：

```text
e/710/解释/model-capability-required-term-pair-readiness-loss-retention-contract-patch/
e/710/图片/v710-pair-readiness-loss-retention-contract-patch.png
```

## 一句话总结

v710 把 loss-retention repair plan 变成可检查 contract patch，并保持后续 corpus materialization 链路兼容。
