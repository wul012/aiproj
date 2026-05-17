# v211 promoted seed handoff suite guard evidence 代码讲解

## 本版目标

v211 的目标是把 v210 已经进入 promoted training-scale seed 的 handoff suite guard evidence，继续带到 promoted seed handoff。

v210 让 next-cycle seed 能记录 selected baseline 的 `selected_handoff_suite_consistency`、`selected_handoff_suite_mismatch_count` 和 `selected_handoff_selected_suite_path`。但 promoted seed handoff 才是下一轮 `plan_training_scale.py` 命令被审阅或执行的入口，如果这里不继续展示上游 guard，审阅者仍要回翻 seed JSON 才能确认 clean-comparison 边界。

本版补上这一步，让 seed handoff 同时保留：

1. `seed_suite_path` 和执行后生成的 `plan_suite_path`，用于检查下一轮 plan 是否延续同一套 suite。
2. seed 继承来的 `handoff_suite_guard`，用于解释这条命令来自哪个上游 suite boundary。
3. planned/execute 结果、artifact rows 和 next batch command，继续承担原来的执行交接职责。

## 不做什么

本版不重新计算 suite consistency，不改变 `_handoff_allowed()`，不改变 seed handoff blocker，不改变 planned-mode 审阅逻辑，也不改变 `--execute` 的命令运行方式。

`selected_handoff_*` 只作为审阅字段进入 summary、CSV、Markdown、HTML 和 CLI stdout。命令是否能执行，仍由 seed 状态、source 存在性、command 是否可用、review flag 和子进程返回码决定。

## 前置路线

v202-v210 已经形成：

```text
training-scale comparison
  -> decision
  -> workflow
  -> controlled handoff
  -> promotion
  -> promotion index
  -> promoted comparison
  -> promoted decision
  -> promoted seed
```

v211 再推进一层：

```text
promoted seed -> promoted seed handoff
```

这一步的价值不是提升模型质量，而是让下一轮训练规模规划的“执行入口”也能解释自己继承的 suite 边界。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

`_summary()` 现在从 `baseline_seed["handoff_suite_guard"]` 读取 guard：

```python
handoff_guard = _dict(baseline.get("handoff_suite_guard"))
```

并加入这些 summary 字段：

```text
selected_handoff_require_suite_consistency
selected_handoff_suite_consistency
selected_handoff_suite_mismatch_count
selected_handoff_selected_suite_path
handoff_suite_consistent_count
handoff_suite_mismatch_total
comparison_ready_handoff_suite_mismatch_total
```

这些字段回答“这次 seed handoff 继承的 seed，来自一条怎样的上游 handoff suite boundary”。它们与 `seed_suite_path`、`plan_suite_path` 并列，但不参与执行判断。

## `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增 selected handoff 与 handoff mismatch 字段，便于脚本或后续治理模块读取。

Markdown summary 新增：

```text
Selected handoff suite
Selected handoff mismatches
Selected handoff suite path
Handoff suite mismatches
```

HTML stats 同步展示 selected handoff suite 和 mismatch 总数，方便人工复核 seed handoff 时不用跳回 seed 报告。

## `scripts/execute_promoted_training_scale_seed.py`

CLI stdout 新增：

```text
selected_handoff_suite_consistency
selected_handoff_suite_mismatch_count
handoff_suite_mismatch_total
```

这样 planned smoke、CI 或人工终端检查可以直接确认 seed handoff 是否消费到了 seed 的 handoff guard。

## `src/minigpt/report_utils.py`

本版还融合了一项轻量质量优化：新增公共 `first_present(*values)`。

它统一表示“返回第一个不是 None 的值”，并被这些已有链路复用：

- `training_scale_handoff.py`
- `training_scale_promotion.py`
- `training_scale_promotion_index_helpers.py`
- `release_readiness.py`
- `promoted_training_scale_seed.py`

这类 helper 原本在多个文件重复定义，最容易导致字段兜底顺序慢慢漂移。收束到 `report_utils` 后，v206+ 的 required/guard 字段兜底语义更稳定。

同时，`comparison.py`、`benchmark_scorecard_comparison.py`、`training_portfolio_comparison.py`、`request_history.py`、`maturity.py` 和 `maturity_narrative.py` 改为复用 `report_utils.utc_now`。其中部分模块保留 `_utc_now()` 薄包装，只是为了减少外部行为变化。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 新增 `test_carries_seed_handoff_suite_guard_into_handoff_outputs_and_script`。

这个测试构造带 `baseline_seed["handoff_suite_guard"]` 的 seed，再构建 planned seed handoff，覆盖：

1. summary 输出 selected handoff suite status、mismatch count、selected suite path 和 mismatch total。
2. CSV/Markdown/HTML 输出包含这些字段。
3. CLI stdout 打印 selected handoff suite 和 handoff mismatch 总数。
4. planned handoff 不执行命令，但仍写出 seed handoff JSON。

`tests/test_report_utils.py` 新增公共 `first_present` 测试，保护 0、空字符串和全 None 的行为。

## 运行证据

本版运行证据归档在 `c/211`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-suite-guard-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些证据分别证明：聚焦测试通过、CLI seed handoff 能跑通、四类 artifact 都带 selected handoff 字段、source encoding 仍干净、全量 unittest 通过、README 和归档说明已经对齐。

## 证据链角色

v211 处在 promoted seed 和下一轮 training-scale plan/batch 之间。它让下一轮训练规划的审阅/执行入口既能看到命令结果，也能解释这条命令继承的 clean-comparison 边界。

## 一句话总结

v211 把 promoted seed 的 handoff suite guard 接到 seed handoff，让下一轮训练规模规划的审阅/执行入口继续保留 clean-comparison 边界，并顺手收束了低风险公共 helper。
