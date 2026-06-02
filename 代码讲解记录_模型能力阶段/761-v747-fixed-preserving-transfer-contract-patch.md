# v747 fixed-preserving transfer contract patch 代码讲解

## 本版目标和边界

v747 的目标是把 v746 的 fixed-preserving transfer plan 落成可物化 contract patch。

v746 只是计划：保留 direct-completion exact rows、transfer row budget 限制到 4、禁止 exact heldout pair prompt。v747 则把这些约束写成代码检查，并生成实际 `contract.training_rows`。

本版不训练模型，不判断能力提升。它的结束条件是：contract patch 通过计划、base contract、row budget、heldout isolation、eval overlap 等检查，并能被 materializer 识别。

## 前置路线

v745 关闭 full surrogate transfer patch route，因为 v744 从 v738 的 direct pair-full 回退到 loss-only。

v746 生成 fixed-preserving transfer plan，要求下一版不再添加 8 条 broad transfer rows，而是只加 4 条更克制的 fixed-preserving bridge rows。

v747 接在 v746 后面，验证这个计划是否能成为下一轮训练输入。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.py`
  - 核心 contract patch builder。
  - 定义 `FIXED_PRESERVING_TRANSFER_ROWS`，共 4 条。
  - `build_fixed_preserving_transfer_contract_patch()` 读取 transfer plan 和 base contract，生成 patched contract。
  - `_checks()` 保护 plan decision、base contract decision、row budget、direct rows 保留、heldout isolation 和 eval overlap。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示 base rows、patched rows、transfer rows、added rows 和 checks。

- `scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.py`
  - CLI 入口。
  - `--transfer-plan` 指向 v746。
  - `--base-contract` 指向 v736。

- `tests/test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.py`
  - 覆盖 row budget、wrong artifact failure、materialization compatibility、artifact 输出。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 新增 ready decision：`pair_readiness_fixed_preserving_transfer_contract_patch_ready`。
  - 新增 contract JSON filename：`model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.json`。
  - 这让 v748 可以直接把 v747 输出目录作为 materialization 输入。

## 核心 rows

v747 新增的 4 条 rows 是：

```text
fixed_preserving_transfer guard fixed before loss => fixed loss
fixed_preserving_transfer compact fixed/loss keeps fixed => fixed loss
fixed_preserving_transfer reverse loss then fixed keeps fixed => loss fixed
fixed_preserving_transfer boundary fixed retained with loss
```

这些 rows 的设计目标是给模型一点 fixed/loss 共现桥接，但避免 v742 那种 8 行 broad surrogate rows 对 direct surface 造成更强干扰。

## 核心检查

v747 的 checks 包括：

- `transfer_plan_passed`
  - v746 plan 必须通过。

- `transfer_plan_decision`
  - plan decision 必须是 `pair_readiness_fixed_preserving_transfer_plan_ready`。

- `next_artifact_matches`
  - plan 必须请求 `pair_readiness_fixed_preserving_transfer_contract_patch`。

- `base_contract_decision`
  - base 必须是 v736 的 direct-completion surface contract。

- `transfer_row_budget_respected`
  - 4 条新增 rows 必须小于等于 plan budget。

- `broad_pair_transfer_rows_not_reused`
  - 新 rows 不能复用 v742 的 `pair_transfer ...` broad route。

- `exact_direct_rows_preserved`
  - `fixed=fixed` 和 `loss=loss` 必须仍在训练 rows 中。

- `heldout_pair_absent`
  - `fixed=|loss=` 不能进入训练 rows。

- `no_exact_eval_row_overlap`
  - exact eval prompts 不能作为训练 rows。

这些检查让 v747 不是“又加四行”，而是一次带边界的 contract patch。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.py tests\test_model_capability_required_term_pair_readiness_corpus_materialization.py -q -o cache_dir=runs\pytest-cache-v747-focused
```

结果为 9 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.py --transfer-plan e\746\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-plan --base-contract e\736\解释\model-capability-required-term-pair-readiness-direct-completion-surface-contract --out-dir e\747\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-contract-patch --require-pass --force
```

核心输出：

```text
decision=pair_readiness_fixed_preserving_transfer_contract_patch_ready
base_training_row_count=16
patched_training_row_count=20
fixed_preserving_transfer_row_count=4
```

Playwright 快照确认 HTML 中可见 base rows、patched rows、transfer rows 和新增 rows。

## 证据链角色

v747 是 v746 计划到 v748 materialization 的桥。它把“更轻、更 fixed-preserving”的想法变成可检查 contract，并把 materializer 注册补齐。

一句话总结：v747 将 fixed-preserving transfer route 从计划推进到可物化 contract patch，下一版应生成训练 corpus。
