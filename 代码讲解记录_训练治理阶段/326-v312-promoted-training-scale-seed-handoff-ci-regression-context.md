# v312 promoted seed handoff CI regression context

## 本版目标和边界

v312 解决的是 promoted training scale 链路最后一段的证据丢失问题：v311 已经把 promoted decision 中的 handoff batch CI regression 计数、名称和 comparison exclusion reasons 写进 promoted seed，但 promoted seed handoff 只展示了旧的 clean batch-review 状态和 batch blocker 字段。这样在真正执行下一轮 plan command 前，最后一份 handoff 报告看不到“哪些被拒绝输入因为 CI 回归被排除”，也不能在 strict clean-batch gate 中识别 selected handoff 的 CI 回归。

本版只做证据透传和门禁语义补强，不改变模型训练、promoted baseline 选择策略、next plan command 生成方式，也不改 receipt/assurance 现有校验流程。

## 前置能力

前置链路来自 v309-v311：

- v309 promoted comparison 重新检查 promotion index 中的 stale compare-ready rows，并写入 per-row `comparison_exclusion_reasons`。
- v310 promoted decision 把 promoted comparison 的 CI 回归和 exclusion reasons 带到 baseline selection。
- v311 promoted seed 把 selected、aggregate、comparison-ready CI 回归上下文带到 next-cycle seed。

v312 的位置是 seed -> seed handoff，目标是在下一轮 plan command 执行前保留同一套上下文。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_review.py`
  - `build_seed_handoff_clean_batch_review_summary()` 现在从 seed 的 `handoff_clean_batch_review` 中读取 selected、aggregate、comparison-ready 三类 CI 回归字段。
  - `build_seed_handoff_clean_batch_review_requirement()` 现在把 `selected_handoff_batch_maturity_ci_regression_count > 0` 视为不干净，即使 `selected_handoff_clean_batch_review_status` 仍然是 `clean`。
  - recommendation 逻辑新增两种提示：selected handoff 自身带 CI regression 时要求先解决；被拒绝的 promoted decision 输入带 CI regression 时要求继续排除。

- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`
  - JSON summary 原样保留新增字段。
  - CSV 增加 selected/aggregate/comparison-ready CI regression counters、names 和 exclusion reasons。
  - Markdown/HTML 增加 CI regression 统计卡片和条目。
  - automation receipt 增加 `selected_handoff_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_count`、`comparison_exclusion_reasons`，给轻量自动化消费者一个不打开完整 JSON 也能看到的摘要。

- `scripts/execute_promoted_training_scale_seed.py`
  - CLI stdout 打印 selected、aggregate、comparison-ready CI regression counters、names、exclusion reasons。
  - strict clean-batch 模式额外打印 `clean_batch_review_required_selected_ci_regression_count`，便于 CI 日志定位为什么 gate stop。

- `tests/test_promoted_training_scale_seed_handoff.py`
  - 扩展 `write_seed_tree()` fixture，让测试可以构造“历史 rejected CI regression”和“selected 自身 CI regression”。
  - 新增 handoff 输出/receipt/CLI 透传测试。
  - 新增 strict clean-batch gate 拦截 selected CI regression 的回归测试。

- `tests/test_promoted_training_scale_seed_handoff_review.py`
  - 新增 summary helper 测试，确认 list 字段被转成字符串列表，计数字段不丢。

## 输入输出语义

输入来自 promoted seed JSON 的 `baseline_seed.handoff_clean_batch_review`：

- `selected_handoff_batch_maturity_ci_regression_count`
- `selected_handoff_batch_maturity_ci_regression_names`
- `selected_handoff_selected_batch_maturity_ci_regression_count`
- `selected_comparison_exclusion_reasons`
- `handoff_batch_maturity_ci_regression_count`
- `handoff_selected_batch_maturity_ci_regression_total`
- `handoff_batch_maturity_ci_regression_names`
- `comparison_exclusion_reasons`
- `comparison_ready_handoff_batch_maturity_ci_regression_count`
- `comparison_ready_handoff_selected_batch_maturity_ci_regression_total`
- `comparison_ready_handoff_batch_maturity_ci_regression_names`

输出落在 handoff summary、CSV、Markdown、HTML、automation receipt 和 CLI stdout。它们都是交接证据，不直接启动训练；真正是否执行下一轮 plan command 仍由 `--execute` 决定。

## 门禁变化

旧逻辑只看：

```text
selected_handoff_require_clean_batch_review == false
或 selected_handoff_clean_batch_review_status == clean
```

v312 改为：

```text
未要求 clean batch-review
或 status == clean 且 selected_handoff_batch_maturity_ci_regression_count == 0
```

这让 stale upstream status 无法绕过 gate：只要 selected handoff 自身仍有 batch CI regression，`--require-clean-batch-review` 就会写出 `clean_batch_review_requirement.status=fail`，`automation_gate.decision=stop`，最终 `automation_summary.decision=stop`。

## 测试覆盖

本版核心测试覆盖三层：

- review helper：`test_builds_clean_batch_review_summary_with_ci_regression_context` 验证 summary helper 不丢 CI regression counters、names、exclusion reasons。
- artifact/CLI/receipt：`test_carries_seed_clean_batch_ci_regression_context_into_handoff_outputs_and_script` 验证 JSON、CSV、Markdown、HTML、automation receipt 和 CLI stdout 都能看到 aggregate CI regression context。
- strict gate：`test_script_rejects_selected_clean_batch_ci_regression_when_required` 验证 selected status 仍为 `clean` 但 selected CI regression count 为 1 时，严格 clean-batch gate 仍然 stop。

另外继续跑 seed handoff 相关单测、语法编译、source encoding hygiene、全量 unittest discover 和 `git diff --check`，保证这次是契约增强，不是只改展示。

## 运行证据

运行截图和解释归档在 `d/312`：

- `d/312/图片/01-focused-tests.png`
- `d/312/图片/02-chain-tests.png`
- `d/312/图片/03-py-compile.png`
- `d/312/图片/04-source-encoding.png`
- `d/312/图片/05-full-unittest.png`
- `d/312/图片/06-static-scan.png`
- `d/312/解释/说明.md`

这些证据分别证明 focused handoff tests、promoted seed -> seed handoff chain tests、语法编译、编码卫生、全量测试和静态字段扫描都覆盖了本版新增字段。

## 一句话总结

v312 把 promoted seed 中的 CI 回归排除证据推进到最终 seed handoff，让下一轮训练计划执行前的最后交接报告也能看见并拦截不干净的 selected handoff。
