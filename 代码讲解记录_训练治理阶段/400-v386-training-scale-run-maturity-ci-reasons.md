# v386 training scale run maturity CI reasons 代码讲解

## 本版目标和边界

v386 的目标是把 v385 training portfolio batch 已经保留的 maturity CI regression reason counts，继续带到 gated training scale run 的 `batch_summary`。

v385 解决的是 batch 层可以看到 CI 回归原因。但 gated scale run 是下一层汇总入口，它原先只保存 batch 的 CI 回归数量和名字。这样 `training_scale_run.json`、CSV、Markdown、HTML 和 CLI stdout 只能说明“这个 scale run 有 CI-regressed batch portfolios”，不能说明原因构成。v386 补齐这个 scale-run 级别的证据视图。

本版不改变 gate 策略，不改变 batch 是否执行，不改变 scale-run readiness 评分，也不改变 run comparison/decision/handoff。它只把 batch review summary 里的原因计数保留到 gated scale run 报告里。

## 前置能力

本版承接 v385：

```text
training_portfolio_batch.comparison_review_summary.maturity_ci_regression_reason_counts
        |
        v
training_scale_run.batch_summary.maturity_ci_regression_reason_counts
        |
        v
training_scale_run CSV / Markdown / HTML / CLI stdout
```

这条链路的意义是：batch 层已经知道 CI 回归原因，scale-run 层负责把它作为训练规模门禁结果的一部分保存下来，方便后续 review、归档或人工判断。

## 关键文件

### `src/minigpt/training_scale_run.py`

`_batch_summary()` 新增：

```text
maturity_ci_regression_reason_counts
```

字段来自 batch report 的 `comparison_review_summary`。代码用 `_int_mapping()` 做归一化，只保留非空 key 和正整数 count。跳过 batch 时，该字段为空映射 `{}`，和其他 skipped summary 字段一致。

`write_training_scale_run_csv()` 新增列：

```text
maturity_ci_regression_reason_counts
```

CSV 使用项目已有的 `write_csv_row()` 和 `csv_cell()` 逻辑，字典会以 JSON 字符串形式写入，方便 CI 日志或后续工具读取。

Markdown 和 HTML 增加：

```text
CI regression reasons
```

它放在 Batch 区域中，紧跟 CI regressions 名单，表示这些原因仍属于 batch summary，而不是 gate 自己做出的判断。

### `tests/test_training_scale_run.py`

`test_batch_summary_carries_ci_regression_review_context()` 扩展了 fixture：

```json
{
  "maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2,
    "ci_order_violations_increased": 1
  }
}
```

测试断言：

- `_batch_summary()` 保留 reason counts；
- Markdown 展示 `CI regression reasons`；
- HTML 展示 `CI regression reasons`；
- 文本里包含 `ci_failed_checks_increased:2`。

这证明字段从 batch review summary 进入 scale-run report，而不是只出现在某个孤立 renderer。

### `scripts/run_training_scale_plan.py`

脚本已经打印：

```text
batch_summary=<json>
```

因为 v386 把 reason counts 放进 `batch_summary`，所以 CLI stdout 自动带出该字段，不需要新增 CLI 参数或额外打印行。

## 数据结构说明

输入来自 batch review summary：

```json
{
  "maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2,
    "ci_order_violations_increased": 1
  }
}
```

scale-run 输出中的 `batch_summary` 保持同名字段：

```json
{
  "batch_summary": {
    "maturity_ci_regression_count": 1,
    "maturity_ci_regression_names": ["ci-risk"],
    "maturity_ci_regression_reason_counts": {
      "ci_failed_checks_increased": 2,
      "ci_order_violations_increased": 1
    }
  }
}
```

字段不改名，是为了表达它仍然来自 batch 的 maturity CI review，而不是 scale-run gate 自己分类出来的原因。

## 运行流程

```text
run_training_scale_plan()
        |
        v
run_training_portfolio_batch_plan()
        |
        v
_batch_summary()
  - copy maturity CI count / names / reason counts
        |
        v
write_training_scale_run_outputs()
  - JSON / CSV / Markdown / HTML
        |
        v
scripts/run_training_scale_plan.py stdout batch_summary
```

这条流程让 gated scale run 不仅知道 batch 里有 CI review 风险，还能直接说明原因构成。

## 测试覆盖

本版定向测试运行：

```text
python -m pytest tests/test_training_scale_run.py -q
```

测试覆盖了 gate 允许、gate 阻断、standard suite handoff、renderers 和 batch reason-count carryover。reason-count 断言集中在已有 CI regression review context 测试里，避免新增重复 fixture。

## 证据归档

本版运行截图和说明放在：

```text
d/386/图片
d/386/解释/说明.md
```

`d/386/解释/v386-training-scale-run-maturity-ci-reasons-evidence.html` 是本版静态证据页，用于 Playwright 截图和文档验证；它不是最终机器消费源。

## 一句话总结

v386 把 maturity CI regression reason counts 从 batch 层推进到 gated scale run，使训练规模门禁报告也能直接看到 CI 回归原因。
