# v252 portfolio batch comparison review summary 代码讲解

## 本版目标

v252 的目标是让 training portfolio batch 消费 portfolio comparison 的 review action。

v250 让 comparison 能把 coverage-regressed best-score portfolio 标成 blocker。

v251 把 comparison 的 review/recommendation 规则拆进 `training_portfolio_comparison_review.py`。

但 batch 层仍然只知道 comparison 是否写出，并没有把 review action、blocker action 或 coverage-regressed portfolio 摘要放在 batch 报告的醒目位置。v252 补上这个下游消费点。

## 不做什么

本版不改 comparison 的 review 判定规则。

本版不改 training portfolio batch 的执行顺序。

本版不让 dry-run 自动变成 execute。

本版不新增新的报告类型，只增强已有 batch JSON/Markdown/HTML。

## 关键文件

### `src/minigpt/training_portfolio_batch.py`

这是 batch 执行入口。

原流程是：

```text
run each variant portfolio
build training portfolio comparison
write comparison outputs
store comparison_summary
```

v252 在写出 comparison 后新增：

```text
comparison_review_summary = _comparison_review_summary(comparison_report)
```

`comparison_review_summary` 只保存 batch 需要的摘要字段：

```text
review_action_count
blocker_action_count
maturity_review_count
maturity_review_names
maturity_coverage_regression_count
maturity_coverage_regression_names
blocker_reasons
blocker_portfolios
```

同时 `execution` 新增：

```text
comparison_review_action_count
comparison_blocker_action_count
```

这样自动化脚本不用打开 comparison JSON，也能先从 batch 执行摘要判断有没有 blocker。

`_recommendations()` 也变得更谨慎：

```text
if blocker_action_count > 0:
    Resolve batch comparison blocker review actions before selecting the next baseline.

if review_action_count > 0:
    Review batch comparison actions before choosing the next baseline or rerunning with --execute.
```

这让 batch 不会在 comparison 有 blocker 时继续建议“选择下一基线”。

### `src/minigpt/training_portfolio_batch_artifacts.py`

这是 batch 输出层。

Markdown 开头新增：

```text
Comparison review actions
Comparison blocker actions
Coverage-regressed portfolios
```

Comparison 表格新增：

```text
Review actions
Blocker actions
Maturity reviews
Coverage regressions
Blocker reasons
```

HTML stats 和 `Comparison Hook` 面板也显示同样信息。

这保证风险既存在于机器可读 JSON，也出现在人读报告中。

### `tests/test_training_portfolio_batch.py`

本版扩展了 dry-run batch 测试。

原测试只断言：

```text
comparison JSON exists
comparison summary planned_count == 2
```

现在还断言：

```text
report["comparison_review_summary"]["review_action_count"] == comparison["summary"]["review_action_count"]
report["comparison_review_summary"]["blocker_action_count"] == 0
recommendations contains "Review batch comparison actions"
```

这证明 batch 摘要不是另算一套，而是与 comparison summary 对齐。

新增测试：

```text
test_batch_comparison_review_summary_carries_blockers
```

它构造一个最小 comparison report：

```text
review_action_count=2
blocker_action_count=1
blocker reason=best_score_coverage_regressed
coverage regression portfolio=candidate
```

断言 batch 摘要保留：

```text
blocker_reasons == ["best_score_coverage_regressed"]
blocker_portfolios == ["candidate"]
```

## 输入输出

输入仍然是 batch 执行中生成的 comparison report：

```text
training_portfolio_comparison.json
summary.review_action_count
summary.blocker_action_count
summary.maturity_coverage_regression_names
review_actions[]
```

输出进入 batch report：

```json
{
  "execution": {
    "comparison_review_action_count": 4,
    "comparison_blocker_action_count": 0
  },
  "comparison_review_summary": {
    "review_action_count": 4,
    "blocker_action_count": 0,
    "maturity_coverage_regression_names": [],
    "blocker_reasons": [],
    "blocker_portfolios": []
  }
}
```

如果 comparison 出现 best-score coverage blocker，batch 会在 `blocker_reasons` 里保留：

```text
best_score_coverage_regressed
```

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_training_portfolio_batch tests.test_training_portfolio_comparison tests.test_training_portfolio_comparison_review -q
Ran 19 tests OK
```

全量测试：

```text
python -B -m unittest discover -s tests -q
Ran 490 tests OK
```

编码检查：

```text
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-v252-final
status=pass
source_count=267
clean_count=267
```

## 运行证据

本版运行证据归档在 `c/252`：

- `图片/01-batch-review-focused-tests.png`
- `图片/02-batch-review-structure-check.png`
- `图片/03-full-unittest.png`
- `图片/04-source-encoding.png`
- `解释/说明.md`

结构检查证明：

```text
batch_has_comparison_review_summary=True
batch_execution_has_review_counts=True
artifacts_markdown_has_review_actions=True
artifacts_html_has_blocker_actions=True
test_covers_blocker_summary=True
```

## 证据链角色

v252 是 v250-v251 的下游落点。

v250 让 comparison 识别风险。

v251 让 review 规则有独立边界。

v252 让 batch 入口也能看到这些风险，避免批量 variant 矩阵只展示“comparison 已写出”，却不提示 comparison 内部已有 blocker。

## 一句话总结

v252 把 portfolio comparison 的 review/blocker 风险带回 batch 层，让批量训练矩阵在选择下一基线前先看见下游审查结果。
