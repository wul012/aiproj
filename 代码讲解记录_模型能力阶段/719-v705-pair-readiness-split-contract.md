# v705 pair-readiness split contract

## 本版目标和边界

v705 的目标是把 v704 的 split plan 变成具体 contract。它不训练模型，而是先把训练行、评估 probe 和 heldout pair probe 的边界固化下来。

本版解决的是训练前输入治理问题：避免下一次训练把评估探针直接混入训练样本，然后误把复读看成能力提升。

## 前置链路

v704 输出：

```text
decision=pair_readiness_split_plan_ready
proposed_next_artifact=pair_readiness_split_contract
training_split_count=3
evaluation_split_count=3
```

v705 只在这个 plan ready 的条件下生成 contract。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_split_contract.py`
  - contract builder。
  - 定义 training rows、evaluation probes、heldout pair probe 和检查逻辑。

- `src/minigpt/model_capability_required_term_pair_readiness_split_contract_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 同时展示训练行和评估 probe。

- `scripts/run_model_capability_required_term_pair_readiness_split_contract.py`
  - CLI。
  - 输入 v704 plan JSON 或目录。

- `tests/test_model_capability_required_term_pair_readiness_split_contract.py`
  - 覆盖 contract ready、plan fail 阻断、heldout pair probe 不进入训练、输出格式。

## Contract 字段

核心字段：

```text
training_rows
evaluation_probes
heldout_pair_probe
promotion_requirement
leakage_policy
```

本版固定：

```text
heldout_pair_probe=fixed=|loss=
```

这个 probe 只能出现在 evaluation probes 里，不能成为 training row。

## Check 设计

v705 检查：

```text
plan_passed
plan_decision
next_artifact_matches
training_rows_present
evaluation_probes_present
no_exact_eval_row_overlap
heldout_pair_probe_absent
```

`no_exact_eval_row_overlap` 允许训练行包含 `fixed=fixed` 这类 completion row，但不允许把 `fixed=`、`loss=` 或 pair probe 原样放入训练行。

## 运行证据

输出：

```text
status=pass
decision=pair_readiness_split_contract_ready
training_row_count=12
evaluation_probe_count=3
heldout_pair_probe=fixed=|loss=
model_quality_claim=contract_only
```

证据目录：

```text
e/705/解释/model-capability-required-term-pair-readiness-split-contract/
e/705/图片/v705-pair-readiness-split-contract.png
```

## 一句话总结

v705 把 pair-readiness 的训练/评估边界从计划变成可检查 contract，防止后续训练把 heldout probe 泄漏进训练样本。
