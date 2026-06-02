# v754 exact-surface repair corpus materialization 代码讲解

## 本版目标和边界

v754 的目标是把 v753 exact-surface repair contract patch 变成真实训练输入。

v753 已经证明 contract patch 可检查、可物化；v754 负责把其中 24 条 training rows 按固定 repeat 展开成 corpus，并保留 heldout eval fixture。

本版不训练模型，不生成 checkpoint，不判断 exact surface 是否修复。它只证明训练输入已经准备好，且 heldout prompt 没有泄漏。

## 前置路线

- v751 诊断出 exact surface miss 与 arrow surface pass 的敏感性。
- v752 生成 exact-surface repair plan。
- v753 生成 checked contract patch。
- v754 将 patch 物化为训练 corpus。

这条路线仍然遵守“先数据证据，后模型解释”的顺序。

## 关键复用文件

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - v754 复用通用 materializer。
  - v753 已注册 `pair_readiness_exact_surface_repair_contract_patch_ready`，所以 materializer 可以识别新 contract。

- `scripts/run_model_capability_required_term_pair_readiness_corpus_materialization.py`
  - CLI 入口。
  - 输入 v753 输出目录。
  - `--repeat 320` 保持与 v748/v743 一致，便于后续训练对比。

- `e/754/解释/model-capability-required-term-pair-readiness-exact-surface-repair-corpus-materialization/`
  - 保存 materialization report。
  - 保存 `pair_readiness_training_corpus.txt`。
  - 保存 `pair_readiness_heldout_eval_fixture.json`。

## 输入输出结构

输入是 v753 contract patch：

```text
decision=pair_readiness_exact_surface_repair_contract_patch_ready
contract.training_rows=24
contract.evaluation_probes=3
```

输出是 v754 materialization report：

```text
decision=pair_readiness_corpus_materialized
training_line_count=7680
evaluation_probe_count=3
model_quality_claim=data_artifact_only
```

`training_line_count=7680` 的来源是：

```text
24 training rows * repeat 320 = 7680 lines
```

## 核心检查

v754 的 checks 包括：

- `contract_passed`
  - source contract 必须是 pass。

- `contract_decision`
  - source contract decision 必须属于 ready decisions。

- `repeat_positive`
  - repeat 必须大于 0。

- `training_rows_present`
  - contract 必须有 training rows。

- `heldout_not_in_training_rows`
  - exact heldout prompt 不能是 training row。

- `heldout_not_in_corpus`
  - exact heldout prompt 不能出现在物化后的 corpus 行中。

这些检查保护的是训练输入边界。下一版训练后，才能判断 v753 rows 是否真正改善 exact surface。

## 运行证据

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_corpus_materialization.py e\753\解释\model-capability-required-term-pair-readiness-exact-surface-repair-contract-patch --out-dir e\754\解释\model-capability-required-term-pair-readiness-exact-surface-repair-corpus-materialization --repeat 320 --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Status pass`
- `Decision pair_readiness_corpus_materialized`
- `Train lines 7680`
- `Eval probes 3`
- `contract_decision pair_readiness_exact_surface_repair_contract_patch_ready`

截图位于：

```text
e/754/图片/v754-exact-surface-repair-corpus-materialization.png
```

## 证据链角色

v754 是 v753 contract patch 与 v755 training run 之间的数据闸口。它把 exact-surface repair 从合同层推进到训练输入层。

一句话总结：v754 将 exact-surface repair route 推进到可训练 corpus，下一版应训练并观察 exact pair surface 是否改善。
