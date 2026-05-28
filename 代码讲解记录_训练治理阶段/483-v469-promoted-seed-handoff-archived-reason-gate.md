# v469：promoted seed handoff archived reason gate

## 本版目标与边界

v469 解决的是通用 CI reason-count 在最终 promoted seed handoff 层的证据闭环。

v467 证明 archived-path reason 可以进入 promoted comparison。v468 证明它可以继续进入 decision 和 next-cycle seed。v469 则把它推到最终交接层：

```text
promoted seed
  -> seed handoff summary
  -> clean batch-review requirement
  -> automation gate / automation summary
  -> handoff reports and receipt
```

本版不新增 production 字段，不改变 gate 规则，也不扩大模型训练能力。它只补测试和证据，证明已有字段能承载新 reason。

## 关键测试变更

### `tests/test_promoted_training_scale_seed_handoff.py`

新增测试常量：

```python
ARCHIVED_PATH_REASON = CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON
HANDOFF_CI_REASON_COUNTS = {
    ARCHIVED_PATH_REASON: 1,
    "workflow-order-regressed": 1,
}
SELECTED_CI_REASON_COUNTS = {
    ARCHIVED_PATH_REASON: 1,
}
```

这些常量让测试表达“同一条 archived-path reason 进入 handoff 和 selected clean-batch gate”。

### fixture 只做可选扩展

`write_seed_tree()` 新增两个可选参数：

```python
handoff_ci_reason_counts: dict[str, int] | None = None
selected_ci_reason_counts: dict[str, int] | None = None
```

当调用方不传参数时，旧的默认行为仍然保留：

- handoff regression 使用 `workflow-order-regressed`。
- selected regression 使用 `missing-ci-step`。

这避免了为了 v469 证据而影响其它测试样例。

## 覆盖的两个场景

### handoff summary / report

原有 handoff clean-batch context 测试现在注入：

```python
handoff_ci_reason_counts=HANDOFF_CI_REASON_COUNTS
```

断言覆盖：

- `summary["handoff_batch_maturity_ci_regression_reason_counts"]`
- CSV
- Markdown
- HTML
- CLI stdout

输出里能看到：

```text
archived_path_portability_check_not_ready:1, workflow-order-regressed:1
```

### clean-batch automation gate

`--require-clean-batch-review` 场景现在注入：

```python
selected_ci_reason_counts=SELECTED_CI_REASON_COUNTS
```

断言覆盖：

- `summary["selected_handoff_batch_maturity_ci_regression_reason_counts"]`
- `clean_batch_review_requirement["selected_ci_regression_reason_counts"]`
- CLI 输出的 `clean_batch_review_required_selected_ci_regression_reason_counts`
- `automation_summary.decision == "stop"`
- `automation_summary.blocking_source == "automation_gate"`

这证明 selected handoff 的 archived-path reason 会真正进入自动化 gate，而不是只在外围报告里展示。

## 运行证据

证据目录：`d/469`

主要文件：

- `d/469/解释/source/promoted-seed/promoted_training_scale_seed.json`
- `d/469/解释/promoted-seed-handoff/promoted_training_scale_seed_handoff.json`
- `d/469/解释/promoted-seed-handoff/promoted_training_scale_seed_handoff.md`
- `d/469/解释/promoted-seed-handoff/promoted_training_scale_seed_handoff.html`
- `d/469/解释/promoted-seed-handoff/promoted_training_scale_seed_handoff_automation_receipt.json`
- `d/469/解释/promoted-seed-handoff/promoted_training_scale_seed_handoff_automation_receipt.txt`
- `d/469/解释/promoted-seed-handoff-cli.txt`
- `d/469/解释/playwright-handoff-snapshot.md`
- `d/469/图片/promoted-seed-handoff-archived-reason-gate.png`

CLI evidence 明确记录 `exit_code=1`，因为本版故意开启 `--require-clean-batch-review`，并让 selected handoff 携带 archived-path CI regression。这个失败是预期行为，证明 gate 能停止不干净的 selected handoff。

## 链路角色

v469 是一次“证据闭环”版本。

它不再扩散 archived-path 专用字段，而是让最终 handoff 层消费已有的 `*_ci_regression_reason_counts`。这样后续新的 CI reason 只要进入 reason-count map，就能被 handoff 报告、clean-batch requirement 和 automation gate 统一保留。

## 一句话总结

v469 把 archived-path reason-count 送进最终 handoff 和 clean-batch automation gate，完成从 comparison 到交接出口的通用 reason 贯通。
