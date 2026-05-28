# v468：promoted training scale decision / seed archived reason carryover

## 本版目标与边界

v468 继续沿着 v467 的方向做收口：不为 `archived_path_portability_check_not_ready` 新增 promoted training scale 专用字段，而是验证它可以作为普通 CI regression reason 继续穿过 decision 和 seed 两层。

本版目标：

```text
release / registry reason constant
  -> promoted training scale decision rejected rows / summary
  -> promoted training scale seed clean-batch review summary
  -> CLI / Markdown / HTML / JSON evidence
```

本版不改变模型训练、不新增 release gate、不改 promotion selection 规则。它只是让通用 reason-count 的下游消费更明确。

## 前置能力

- v463：archived path portability CI gate。
- v465：release readiness comparison 能产生 `archived_path_portability_check_not_ready`。
- v466：maturity / portfolio 能消费 archived-path regression。
- v467：promoted comparison 和 seed handoff review 已经证明通用 `*_ci_regression_reason_counts` 可以承载 archived-path reason。

v468 的角色是补齐 promoted decision 和 next-cycle seed 这两个中间层。

## 关键代码变更

### `src/minigpt/report_utils.py`

新增常量：

```python
CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON = "archived_path_portability_check_not_ready"
```

这个常量和既有的 `CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON` 放在一起。这样后续测试、release comparison、registry delta mapping 不需要重复手写 archived-path reason 字符串。

### `src/minigpt/release_readiness_comparison.py`

`_ci_workflow_regression_reasons()` 在检测到：

```python
ci_workflow_archived_path_portability_check_ready_regressed
```

时，追加 `CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON`。

`_ci_workflow_reason_label()` 也使用同一个常量作为 label map 的 key。这样 reason 名称只有一个定义源，降低打字错误风险。

### `src/minigpt/registry_release_readiness.py`

`CI_READY_REGRESSION_REASON_FIELDS` 把：

```python
ci_workflow_archived_path_portability_check_ready_regressed
```

映射到同一个常量。registry 汇总 release-readiness delta 时，仍然把 archived-path regression 写入统一的 `ci_regression_reason_counts`。

## decision 层验证

`tests/test_promoted_training_scale_decision.py` 的 CI regression promoted review 场景被扩展为：

```python
BATCH_CI_REASON_COUNTS = {
    "archived_path_portability_check_not_ready": 1,
    "missing-ci-step": 1,
    "workflow-order-regressed": 1,
}
```

关键断言：

- rejected `dirty-ci` 保留 archived-path reason。
- summary 的 `handoff_batch_maturity_ci_regression_reason_counts` 保留 archived-path reason。
- CSV、Markdown、HTML、CLI stdout 和 recommendations 都能看到同一个 reason-count。
- `comparison_ready_handoff_batch_maturity_ci_regression_reason_counts` 为空，证明 dirty input 没进入 clean comparison。

这证明 decision 层既保留审计上下文，又不把 rejected CI regression 当作 selected baseline 的质量证据。

## seed 层验证

`tests/test_promoted_training_scale_seed.py` 的 `include_ci_regression_context` 场景同步扩展 archived-path reason。

关键断言：

- `baseline_seed.handoff_clean_batch_review` 保留 archived-path reason。
- `summary.handoff_batch_maturity_ci_regression_reason_counts` 保留同一组 reason-counts。
- seed CLI 输出同一组 JSON reason-counts。
- selected baseline 的 selected-handoff reason-counts 仍为空，表示 selected baseline 是 clean 的。

这说明 next-cycle seed 可以携带“历史 rejected CI regression 上下文”，而不把它误判为当前 selected baseline 的污染。

## 运行证据

证据目录：`d/468`

主要文件：

- `d/468/解释/promoted-training-scale-decision/promoted_training_scale_decision.json`
- `d/468/解释/promoted-training-scale-decision-cli.txt`
- `d/468/解释/promoted-training-scale-seed/promoted_training_scale_seed.json`
- `d/468/解释/promoted-training-scale-seed-cli.txt`
- `d/468/解释/playwright-seed-snapshot.md`
- `d/468/图片/promoted-training-scale-seed-archived-reason.png`

decision evidence 表示 rejected `dirty-ci` 带 archived-path reason。seed evidence 表示这个 reason 作为 clean-batch review context 继续被保留，但 selected baseline 仍然是 clean。

## 链路角色

v468 的价值是减少未来治理信号的字段膨胀。

后续如果再出现新的 CI regression reason，只要它进入 `*_ci_regression_reason_counts`，decision 和 seed 层就能先保留、渲染、输出和审计它，而不是马上复制一套专用字段。

## 一句话总结

v468 把 archived-path regression 从 comparison 继续送到 decision / seed 层，证明通用 CI reason-count 能承接新治理原因而不制造新的大字段链。
