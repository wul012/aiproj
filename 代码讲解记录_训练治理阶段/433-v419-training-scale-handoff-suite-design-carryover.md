# v419 training scale handoff suite-design carryover 代码讲解

## 本版目标与边界

v419 的目标是把 v418 已经带到 decision/workflow 的 suite-design regression context 继续带进 training scale execution handoff。执行交接是训练真正启动前的最后一层验证，如果这里只显示 `blocker_action_count` 或 CI regression 字段，就会丢掉 benchmark-suite blocker 的具体原因。

本版不改训练执行命令，不改 workflow/decision 生成，也不重新判断 suite-design regression。它只读取既有字段，持久化到 handoff summary、CSV、Markdown、HTML、CLI 和 strict clean-batch guard。

## 前置链路

本版接在 v418 后面：

- v417：training portfolio comparison 产生 dedicated suite-design blocker。
- v418：batch、scale run、comparison、decision、workflow 保留 suite-design regression context。
- v419：execution handoff 继续保留这些字段，并在 strict clean-batch validation 中识别它们。

## 关键文件

### `src/minigpt/training_scale_handoff.py`

`_clean_batch_review_guard()` 新增读取 selected/global suite-design 字段：

- `selected_batch_maturity_suite_design_regression_count`
- `selected_batch_maturity_suite_design_regression_names`
- `batch_maturity_suite_design_regression_count`
- `batch_maturity_suite_design_regression_names`

读取顺序和既有 CI regression 字段一致：优先 decision summary，再 fallback 到 workflow summary。

`_summary()` 把这些字段写入 handoff summary，成为 handoff JSON 的机器可读证据。

`_handoff_allowed()` 在 `decision_require_clean_batch_review=True` 时增加 suite-design regression 检查。如果 legacy 输入误报 `clean_batch_review_status=clean`，但 suite-design regression count 大于 0，handoff 仍会被 blocked。

`_recommendations()` 在非 strict 场景下也会提示：

```text
Resolve suite-design regressed batch evidence before executing this handoff as clean benchmark evidence.
```

这保持默认 handoff 可以计划执行，但不会把它称为干净 benchmark evidence。

### `src/minigpt/training_scale_handoff_artifacts.py`

CSV 增加四个字段：

- `selected_batch_maturity_suite_design_regression_count`
- `selected_batch_maturity_suite_design_regression_names`
- `batch_maturity_suite_design_regression_count`
- `batch_maturity_suite_design_regression_names`

Markdown 和 HTML 的 summary/stat cards 也展示 selected/global suite-design regression count 与 names。

### `scripts/execute_training_scale_handoff.py`

CLI stdout 新增：

- `batch_maturity_suite_design_regression_count`
- `batch_maturity_suite_design_regression_names`
- `selected_batch_maturity_suite_design_regression_count`
- `selected_batch_maturity_suite_design_regression_names`

这样本地命令、CI 日志或后续脚本无需打开 JSON，也能知道 handoff 是否带着 suite-design blocker。

## 核心数据流

本版字段流向是：

```text
training_scale_run_decision.summary
  -> training_scale_workflow.summary
  -> training_scale_handoff.clean_batch_review_guard
  -> training_scale_handoff.summary
  -> JSON/CSV/Markdown/HTML/CLI evidence
```

字段命名沿用 v418：

- selected 维度：`selected_batch_maturity_suite_design_regression_*`
- global batch 维度：`batch_maturity_suite_design_regression_*`

这样 handoff 可以同时说明“被选中执行的 run 是否有风险”和“整个 batch 比较是否有风险”。

## 测试覆盖

`tests/test_training_scale_handoff.py` 新增两组测试：

- suite-design context carryover：断言 summary、CSV、Markdown、HTML、CLI stdout 都出现 suite-design regression count/names。
- strict clean-batch blocking：当 `require_clean_batch_review=True` 且 suite-design regression count 大于 0，即使 `clean_batch_review_status=clean`，handoff 也会 blocked。

原有 CI regression、suite guard、selected blocker、artifact writer identity 测试继续通过。

本轮定向验证：

- `python -m pytest tests\test_training_scale_handoff.py -q`：`14 passed`
- 语法编译：通过

## 运行证据

`d/419` 归档了本版截图和说明：

- `d/419/图片/01-training-scale-handoff-suite-design.png`
- `d/419/解释/v419-training-scale-handoff-suite-design-evidence.html`
- `d/419/解释/v419-training-scale-handoff-suite-design-snapshot.md`
- `d/419/解释/说明.md`

截图证明 handoff status 是 `planned`，但 selected/global suite-design regression count 都是 `1`，recommendation 明确要求先处理 suite-design regressed batch evidence。

一句话总结：v419 把 suite-design blocker 保留到执行交接层，让训练真正启动前仍能看清 benchmark-suite 风险来源。
