# v746 fixed-preserving transfer plan 代码讲解

## 本版目标和边界

v746 的目标是把 v745 的路线关闭结论转成下一版可执行的 fixed-preserving transfer plan。

v745 已证明 full surrogate pair-transfer patch 让 direct hits 从 2 退到 1，并且 `fixed` 被挤掉。v746 不再扩大那条路线，而是计划一个更小、更保守的补丁：保留 direct-completion exact rows，把 transfer rows 限制到 4 条以内，并显式保护 fixed 分支。

本版不训练模型，不生成 contract patch，也不修改 materializer。它只是 plan layer。

## 前置路线

v744 训练显示 pair-transfer patch 变成 loss-only。

v745 把 v738、v740、v744 对齐后，得到 `pair_readiness_pair_prompt_transfer_regressed_stop_route`。

v746 只接受这种 regressed stop route 作为输入。如果输入不是这条结论，plan 会 fail。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.py`
  - 核心计划构建逻辑。
  - `locate_fixed_preserving_transfer_plan_source()` 支持输入 v745 输出目录。
  - `_checks()` 校验 v745 是否确实是回归路线关闭。
  - `_plan()` 写出下一版 contract patch 的目标、row budget、保留行、禁止行和成功 guard。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 报告展示 plan ready、next artifact、row budget、patch strategy。

- `scripts/run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.py`
  - CLI 入口。
  - 输入可以是 v745 diagnostic JSON，也可以是输出目录。
  - `--require-pass` 用于让计划前置条件不满足时失败。

- `tests/test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.py`
  - 覆盖 plan ready、route 未关闭时 fail、无 fixed regression 时 fail、五种 artifact 输出。

## 核心检查

v746 的 `check_rows` 包含：

- `diagnostic_passed`
  - v745 诊断必须 `status=pass`。

- `diagnostic_decision`
  - v745 decision 必须是 `pair_readiness_pair_prompt_transfer_regressed_stop_route`。

- `transfer_route_closed`
  - full surrogate transfer route 必须已经关闭。

- `fixed_regressed`
  - 本计划只针对 fixed 被挤掉的回归。

- `direct_hit_regressed`
  - transfer hit delta 必须小于 0。

- `pair_probe_still_not_ready`
  - direct-completion pair prompt replay 仍不能 ready。

这些检查确保 v746 不是泛化的“再试一次”，而是只在证据明确时规划 fixed-preserving patch。

## Plan 字段

`plan.proposed_next_artifact` 为：

```text
pair_readiness_fixed_preserving_transfer_contract_patch
```

`plan.transfer_row_budget` 为：

```text
4
```

这个数字故意低于 v742 的 8 条 transfer rows，避免继续扩大导致 fixed drift 的训练压力。

`plan.direct_completion_rows_to_preserve` 包含：

```text
fixed=fixed
loss=loss
```

这保证下一版 contract patch 必须保留 v738 成功的 direct surface。

`plan.heldout_pair_prompt_must_remain_absent` 为：

```text
fixed=|loss=
```

这继续保护 pair prompt heldout 隔离。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.py -q -o cache_dir=runs\pytest-cache-v746-focused
```

结果为 4 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan.py e\745\解释\model-capability-required-term-pair-readiness-pair-prompt-transfer-regression-diagnostic --out-dir e\746\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-plan --require-pass --force
```

核心输出：

```text
decision=pair_readiness_fixed_preserving_transfer_plan_ready
transfer_row_budget=4
model_quality_claim=plan_only
```

Playwright 快照确认 HTML 中可见 `Next artifact`、`Row budget=4` 和 patch strategy。

## 证据链角色

v746 是从“路线关闭”到“下一步设计”的桥。它没有把负结果包装成能力提升，而是把 v745 的 stop-route 判断转成更窄、更易检查的下一步 contract。

一句话总结：v746 把 full surrogate transfer patch 的失败收敛成 fixed-preserving 小补丁计划，下一版应验证 contract 本身是否遵守这个计划。
