# v753 exact-surface repair contract patch 代码讲解

## 本版目标和边界

v753 的目标是把 v752 exact-surface repair plan 落成可检查、可物化的 contract patch。

v752 只是计划：最多 4 条 near-exact bridge rows、保留 fixed-preserving route、不训练 exact heldout prompt。v753 把这些要求写入代码检查，并生成新的 `contract.training_rows`。

本版不训练模型，不宣称能力提升。它的结束条件是：contract patch 通过 plan、base contract、row budget、fixed-preserving row preservation、heldout isolation 和 eval overlap 检查，并能被 materializer 识别。

## 前置路线

- v751 诊断出 prompt-surface sensitivity。
- v752 生成 exact-surface repair plan。
- v753 接在 v752 后面，将 plan 变成实际 contract patch。

这条路线保持了证据顺序：诊断 -> 计划 -> contract patch -> materialization -> training -> replay。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.py`
  - 核心 contract patch builder。
  - 定义 `EXACT_SURFACE_REPAIR_ROWS`，共 4 条。
  - `build_exact_surface_repair_contract_patch()` 读取 v752 plan 和 v747 base contract，生成 patched contract。
  - `_checks()` 保护 plan decision、base contract decision、row budget、direct rows、fixed-preserving rows、heldout isolation 和 eval overlap。

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示 base rows、patched rows、repair rows、added rows 和 checks。

- `scripts/run_model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.py`
  - CLI 入口。
  - `--repair-plan` 指向 v752。
  - `--base-contract` 指向 v747。

- `tests/test_model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.py`
  - 覆盖 patch ready、wrong base failure、materialization compatibility、artifact 输出。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 新增 ready decision：`pair_readiness_exact_surface_repair_contract_patch_ready`。
  - 新增 contract JSON filename：`model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.json`。
  - 这让 v754 可以直接把 v753 输出目录作为 materialization 输入。

## 核心 rows

v753 新增的 4 条 rows 是：

```text
exact_surface_bridge pipe equals tokens map fixed and loss => fixed loss
exact_surface_bridge fixed equals pipe loss equals expects fixed loss
exact_surface_bridge compact pipe structure keeps fixed before loss
exact_surface_bridge no space pipe joins fixed token and loss token
```

这些 rows 的目标是描述 pipe/equals 结构，让模型更接近 exact surface，但不直接训练 `fixed=|loss=`。

## 核心检查

v753 的 checks 包括：

- `repair_plan_passed`
  - v752 plan 必须通过。

- `repair_plan_decision`
  - plan decision 必须是 `pair_readiness_exact_surface_repair_plan_ready`。

- `next_artifact_matches`
  - plan 必须请求 `pair_readiness_exact_surface_repair_contract_patch`。

- `base_contract_decision`
  - base 必须是 v747 fixed-preserving transfer contract patch。

- `repair_row_budget_respected`
  - 新增 rows 必须小于等于 plan 的 4 行预算。

- `fixed_preserving_rows_preserved`
  - v747 的 fixed-preserving transfer rows 必须仍在训练 rows 中。

- `exact_direct_rows_preserved`
  - `fixed=fixed` 和 `loss=loss` 必须仍在训练 rows 中。

- `heldout_pair_absent`
  - `fixed=|loss=` 不能进入任何训练 rows。

- `heldout_pair_absent_from_patch`
  - patch rows 不能包含 exact heldout prompt。

- `no_exact_eval_row_overlap`
  - eval prompt 不能和 training rows 完全重叠。

这些检查让 v753 是一个受控 contract patch，而不是无约束地把 heldout prompt 周边内容塞进训练集。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.py tests\test_model_capability_required_term_pair_readiness_corpus_materialization.py -q -o cache_dir=runs\pytest-cache-v753-focused
```

结果为 9 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.py --repair-plan e\752\解释\model-capability-required-term-pair-readiness-exact-surface-repair-plan --base-contract e\747\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-contract-patch --out-dir e\753\解释\model-capability-required-term-pair-readiness-exact-surface-repair-contract-patch --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_exact_surface_repair_contract_patch_ready`
- `Base rows 20`
- `Patched rows 24`
- `Repair rows 4`
- `heldout_pair_absent pass False`
- `no_exact_eval_row_overlap pass []`

截图位于：

```text
e/753/图片/v753-exact-surface-repair-contract-patch.png
```

## 证据链角色

v753 是 v752 计划到 v754 materialization 的桥。它让 exact-surface repair 不停留在文档，而是成为 materializer 能消费的 checked contract。

一句话总结：v753 将 exact-surface repair route 推进到可物化 contract patch，下一版应生成训练 corpus。
