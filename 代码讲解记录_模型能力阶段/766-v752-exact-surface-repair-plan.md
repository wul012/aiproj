# v752 exact-surface repair plan 代码讲解

## 本版目标和边界

v752 的目标是把 v751 诊断结果转成下一步 contract patch 的计划。v751 说明 exact-heldout-pair 未通过，但 arrow-heldout-pair 通过；v752 因此规划一个最小 exact-surface repair。

本版不新增训练 row，不训练模型，也不修改 checkpoint。它只生成 plan artifact，并把后续 patch 的约束写清楚。

## 前置路线

- v749：训练脚本内观察到 pair-full。
- v750：独立 replay 只得到 partial，exact required surface 未通过。
- v751：诊断为 prompt-surface sensitivity。
- v752：把这个诊断变成 exact-surface repair plan。

这条路线保持了节制：先诊断，再计划，再 patch，再训练，避免看到一点正向信号就 promotion。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_plan.py`
  - 计划核心。
  - 输入 v751 sensitivity diagnostic。
  - 通过 checks 确认 diagnostic pass、decision 正确、promotion blocked、exact surface missed、optional surface signal present。
  - 输出 plan、summary、interpretation。

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_plan_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - HTML 展示 plan readiness、next artifact、row budget、checks 和 patch strategy。

- `scripts/run_model_capability_required_term_pair_readiness_exact_surface_repair_plan.py`
  - CLI 入口。
  - 输入 v751 输出目录或 JSON。

- `tests/test_model_capability_required_term_pair_readiness_exact_surface_repair_plan.py`
  - 覆盖 plan ready、promotion not blocked failure、optional signal missing failure、locator、artifact 输出。

## 输入输出结构

输入是 v751 diagnostic：

```text
decision=pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found
promotion_blocked=True
required_missed_surface_ids=['exact-heldout-pair']
optional_pair_full_surface_ids=['arrow-heldout-pair']
```

输出是 v752 plan：

```text
decision=pair_readiness_exact_surface_repair_plan_ready
proposed_next_artifact=pair_readiness_exact_surface_repair_contract_patch
repair_row_budget=4
model_quality_claim=plan_only
```

## patch strategy 解释

v752 的 plan 要求下一版：

- 保留 `fixed=fixed` 和 `loss=loss` exact direct rows。
- 保留 v747 的四条 fixed-preserving transfer rows。
- 最多新增 4 条 near-exact surface bridge rows。
- 新 rows 可以描述 pipe/equals 结构，但不能直接使用 exact heldout prompt `fixed=|loss=`。
- patch 后必须重新 materialize、train、independent replay，再谈 promotion guard。

这里的核心边界是：修 exact surface，但不把 exam answer 写进训练集。

## checks 保护了什么

- `diagnostic_passed`
  - v751 必须执行成功。

- `diagnostic_decision`
  - 只接受 prompt-surface sensitivity found。

- `promotion_blocked`
  - 如果 promotion 没有被 blocked，就不需要 repair plan。

- `exact_surface_missed`
  - 必须确认 missed required surface 是 exact-heldout-pair。

- `optional_surface_signal_present`
  - 至少有一个 optional surface pair-full，说明不是完全无信号。

这些 checks 让 v752 不会在输入证据不足时继续推进 patch。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_exact_surface_repair_plan.py -q -o cache_dir=runs\pytest-cache-v752-focused
```

结果为 5 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_exact_surface_repair_plan.py e\751\解释\model-capability-required-term-pair-readiness-fixed-preserving-transfer-prompt-surface-sensitivity-diagnostic --out-dir e\752\解释\model-capability-required-term-pair-readiness-exact-surface-repair-plan --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_exact_surface_repair_plan_ready`
- `Next artifact pair_readiness_exact_surface_repair_contract_patch`
- `Row budget 4`
- patch strategy 包含不训练 `fixed=|loss=` 的约束。

截图位于：

```text
e/752/图片/v752-exact-surface-repair-plan.png
```

## 证据链角色

v752 是 v751 diagnosis 到 v753 contract patch 的桥。它让下一版 patch 有明确的预算、输入、边界和成功条件。

一句话总结：v752 把 exact surface 问题从诊断推进到可执行计划，同时保住 heldout 不泄漏的底线。
