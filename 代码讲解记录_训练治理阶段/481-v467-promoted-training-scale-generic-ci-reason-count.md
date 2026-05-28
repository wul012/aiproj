# v467：promoted training scale generic CI reason-count

## 本版目标与边界

v467 解决的是 archived path CI regression reason 在 promoted training scale 链路中的表达方式问题。

v463-v466 已经完成了 archived path portability 从 CI gate 到 release readiness、maturity、portfolio 的传递。如果继续把 `archived_path_portability_check_not_ready` 做成 promoted training scale 的一整套专用字段，项目会继续增长大量“某个原因一个字段”的重复链路。v467 选择反过来收束：让这个新原因留在已有的通用字段里。

本版目标：

```text
CI regression reason map
  -> promoted training scale comparison rows / summary
  -> Markdown / HTML / CSV / CLI
  -> seed handoff review summary / requirement
```

本版不新增治理链，不改变模型训练逻辑，也不把 archived path 变成 promoted training scale 的专用字段。

## 前置能力

- v463：新增 archived path portability CI gate。
- v465：release readiness comparison 能输出 `archived_path_portability_check_not_ready`。
- v466：maturity 和 portfolio 能消费 archived path regression count。
- v304-v312：训练规模链路已经建立 `*_ci_regression_reason_counts` 这类通用 reason-count 字段。

v467 的角色是证明 promoted training scale 可以继续复用这条通用通道。

## 关键代码变更

### `src/minigpt/report_utils.py`

新增：

```python
def ci_regression_reason_count(reason: str, *values: Any) -> int:
    reason_name = str(reason).strip()
    if not reason_name:
        return 0
    for value in values:
        count = positive_int_mapping(value).get(reason_name)
        if count is not None:
            return count
    return 0
```

它只做一件事：从一个或多个 reason-count map 中读取指定 reason 的正整数计数。

原来的 `ci_boundary_plan_check_ready_regression_count()` 仍然保留数值字段优先的兼容语义：

```python
for value in values:
    count = _int_count_or_none(value)
    if count is not None:
        return max(0, count)
return ci_regression_reason_count(CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON, *values)
```

这保证旧调用方传专用 count 时行为不变；当旧字段缺失但 reason map 里存在 `boundary_gate_plan_check_not_ready` 时，也能得到正确计数。

## promoted training scale comparison 链路

### 输入

本版用 `d/467/解释/source-index/promotion-index/training_scale_promotion_index.json` 构造了三个 promoted 输入：

- `alpha`：clean-required 且可比较。
- `beta`：clean-required，但带有 CI regression reason。
- `gamma`：可比较。

`beta` 的 reason map 包含：

```json
{
  "archived_path_portability_check_not_ready": 1,
  "missing-ci-step": 1,
  "workflow-order-regressed": 1
}
```

### 输出

`scripts/compare_promoted_training_scale_runs.py` 生成：

- `promoted_training_scale_comparison.json`
- `promoted_training_scale_comparison.csv`
- `promoted_training_scale_comparison.md`
- `promoted_training_scale_comparison.html`

关键结果：

```text
comparison_status=compared
promoted_count=3
comparison_ready_count=2
handoff_batch_maturity_ci_regression_count=3
handoff_batch_maturity_ci_regression_reason_counts={"archived_path_portability_check_not_ready": 1, ...}
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts={}
```

这说明 `beta` 的 archived-path reason 被保留下来，但没有进入 clean comparison。reason 是审计证据，不是放行条件。

## seed handoff review 链路

`tests/test_promoted_training_scale_seed_handoff_review.py` 把 archived-path reason 放进：

- `selected_handoff_batch_maturity_ci_regression_reason_counts`
- `selected_handoff_selected_batch_maturity_ci_regression_reason_counts`
- `handoff_batch_maturity_ci_regression_reason_counts`
- `handoff_selected_batch_maturity_ci_regression_reason_counts`

断言覆盖两层：

- summary 会保留 archived-path reason。
- clean-batch requirement 会把 archived-path reason 放进 `selected_ci_regression_reason_counts`。

同时 boundary plan-check count 仍能从旧字段或 reason map 中得到，不破坏已有逻辑。

## 测试覆盖

### `tests/test_report_utils.py`

新增 `test_ci_regression_reason_count_reads_generic_reason_maps()`：

- 验证 archived-path reason 能从通用 map 中取到。
- 验证未知 reason 和空 reason 返回 0。
- 验证 boundary plan helper 继续兼容显式 count 优先。

### `tests/test_promoted_training_scale_comparison.py`

扩展 clean-batch comparison 场景：

- `beta` 带 archived-path reason。
- row、summary、CSV、Markdown、HTML、recommendations 和 CLI stdout 都必须保留该 reason。
- `comparison_ready_handoff_batch_maturity_ci_regression_reason_counts` 必须为空，证明被污染的 promoted 输入没有进入 clean comparison。

### `tests/test_promoted_training_scale_seed_handoff_review.py`

扩展 seed handoff review 场景：

- summary 层保留 archived-path reason。
- requirement 层保留 `selected_ci_regression_reason_counts`。
- boundary plan-check 仍优先生成专门的 detail / recommendation。

## 运行证据

证据目录：`d/467`

主要文件：

- `d/467/解释/source-index/promotion-index/training_scale_promotion_index.json`
- `d/467/解释/promoted-training-scale-comparison/promoted_training_scale_comparison.json`
- `d/467/解释/promoted-training-scale-comparison/promoted_training_scale_comparison.md`
- `d/467/解释/promoted-training-scale-comparison/promoted_training_scale_comparison.html`
- `d/467/解释/promoted-training-scale-comparison-cli.txt`
- `d/467/解释/playwright-snapshot.md`
- `d/467/图片/promoted-training-scale-archived-reason.png`

截图来自 Playwright MCP，打开的是本地 HTTP 服务下的 HTML 报告。截图确认页面可见，snapshot 确认标题、source index path、Promoted Inputs、Comparison 和 Recommendations 都在页面结构中。

## 链路角色

v467 的价值不是增加模型能力，而是减少治理字段膨胀。

如果后面再出现新的 CI regression reason，例如新的 GitHub Actions gate、artifact digest gate、dataset provenance gate，只要它们能写入 `*_ci_regression_reason_counts`，promoted training scale comparison 和 seed handoff review 就能先保留和展示它们，而不必立刻新增一整套专用字段。

## 一句话总结

v467 把 archived path portability regression 固定在通用 CI reason-count 通道里，让训练治理链路更容易扩展，也更不容易被字段膨胀拖垮。
