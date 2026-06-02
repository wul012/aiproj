# v727 objective-structure contract

## 本版目标和边界

v727 的目标是把 v726 objective-structure plan 转成真实 contract。

本版不训练模型，也不生成 corpus。它负责定义训练行、评估探针和泄漏检查，并把新 contract decision 接入现有 materializer，让下一版能直接物化。

## 前置链路

```text
v725 five-route comparison
 -> capacity probe no improvement
v726 objective-structure plan
 -> proposed_next_artifact=pair_readiness_objective_structure_contract
v727 objective-structure contract
 -> 18 training rows + 3 heldout probes
```

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_structure_contract.py`
  - 定义 row families、contract、checks、summary 和 interpretation。
- `src/minigpt/model_capability_required_term_pair_readiness_objective_structure_contract_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_readiness_objective_structure_contract.py`
  - 生成 contract 的 CLI。
- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 增加 `pair_readiness_objective_structure_contract_ready`。
  - 增加 objective-structure contract JSON filename。
- `tests/test_model_capability_required_term_pair_readiness_objective_structure_contract.py`
  - 覆盖 contract ready、失败输入、heldout isolation、materializer locator 和 artifact render。

## Contract 结构

v727 的 `contract.training_rows` 来自 5 个 row family：

```text
task_id_direct_fixed      4 rows
task_id_direct_loss       4 rows
paired_block_forward      3 rows
paired_block_reverse      3 rows
boundary_contrast         4 rows
```

这种结构和之前的单边 patch 不同：

- direct family 用 task id 明确 fixed/loss 分支。
- paired block 在同一训练样本语义中同时出现 fixed 和 loss。
- forward/reverse 同时存在，避免固定顺序成为唯一模式。
- boundary contrast 保留反污染语义。

## Heldout 边界

evaluation probes 保持：

```text
fixed=        -> fixed
loss=         -> loss
fixed=|loss=  -> fixed+loss
```

检查项包括：

```text
no_exact_eval_row_overlap
heldout_pair_absent
direct_family_balance
paired_forward_present
paired_reverse_present
```

这意味着 contract 可以描述 `fixed` 和 `loss`，但不能把 exact eval prompt 当作训练行。

## Materializer 接入

v727 同步修改 corpus materializer：

```text
PAIR_READINESS_READY_CONTRACT_DECISIONS
PAIR_READINESS_CONTRACT_JSON_FILENAMES
```

测试会把 contract JSON 写入临时目录，再调用 `locate_pair_readiness_corpus_materialization_source()`，确认目录输入能定位到新 filename。

## 证据

运行证据：

- `e/727/解释/model-capability-required-term-pair-readiness-objective-structure-contract/`
- `e/727/图片/v727-objective-structure-contract.png`

截图证明 contract ready、18 rows、5 families、6 paired rows 和全部检查通过。

## 一句话总结

v727 让 objective-structure 不再停留在计划层，而是成为下一版可直接物化和训练的 checked contract。
