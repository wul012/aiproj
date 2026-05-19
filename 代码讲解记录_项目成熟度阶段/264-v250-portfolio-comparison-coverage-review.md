# v250 portfolio comparison coverage review 代码讲解

## 本版目标

v250 的目标是让 training portfolio comparison 消费 maturity narrative 里的 coverage regression 证据。

前几版已经完成这条上游链路：

```text
release readiness comparison -> registry -> maturity summary -> maturity narrative
```

v249 用端到端测试保护了这条链路。v250 不再新增一个报告层，而是把这个信号接到 portfolio comparison 的实际决策点：当多个训练 portfolio 比较时，即使某个 candidate 的分数最高，只要它的 maturity narrative 显示 release-readiness test coverage 回退，就不能被当作 clean baseline 直接推广。

## 不做什么

本版不改变 coverage regression 的判定规则。

本版不改 release readiness、registry、maturity summary 或 maturity narrative 的输出 schema。

本版不改训练、评估或模型生成逻辑。

本版只扩展 training portfolio comparison 对已有 maturity narrative 字段的读取、汇总、输出和 review action。

## 关键文件

### `src/minigpt/training_portfolio_comparison.py`

这是 training portfolio 比较的主逻辑。

本版新增常量：

```text
COVERAGE_REGRESSED_TREND = "coverage-regressed"
```

它把 maturity narrative 的 release-readiness trend 和 portfolio comparison 的 review 逻辑连起来。

`_portfolio_summary()` 现在从 `maturity_narrative.json` 的 `summary` 中读取这些字段：

```text
maturity_release_readiness_trend
maturity_release_readiness_test_coverage_regression_count
maturity_release_readiness_test_coverage_status_changed_count
maturity_release_readiness_max_test_coverage_percent_delta
maturity_release_readiness_max_test_coverage_gap_delta
```

这些字段不是 portfolio 自己重新计算的，而是复用 maturity narrative 已经确认过的 coverage governance 证据。

`_portfolio_delta()` 新增两类 delta：

```text
maturity_release_readiness_trend_changed
maturity_release_readiness_test_coverage_regression_delta
```

这样比较报告不只知道分数和 loss 变化，也知道 release-readiness coverage 风险是否相对 baseline 变差。

`_comparison_summary()` 新增：

```text
maturity_coverage_regression_count
maturity_coverage_regression_names
best_score_maturity_release_readiness_trend
best_score_maturity_release_readiness_test_coverage_regression_count
```

这几个字段让人读报告时能马上看到：

```text
哪些 portfolio 有 coverage regression
最高分 portfolio 是否也带 coverage regression
```

`_review_actions()` 是本版最关键的决策点。

新增判断：

```text
if _has_maturity_coverage_regression(portfolio):
    severity = "blocker" if portfolio is best-score else "review"
```

如果 coverage-regressed portfolio 同时是最高分 portfolio，生成：

```text
reason=best_score_coverage_regressed
severity=blocker
```

如果它不是最高分 portfolio，则生成：

```text
reason=portfolio_coverage_regressed
severity=review
```

这保持了 portfolio comparison 的语义：最高分 candidate 的风险会影响基线推广，非领先 candidate 的风险则主要影响归档和未来使用。

### `src/minigpt/training_portfolio_comparison_artifacts.py`

这是 comparison 输出层。

本版把新增字段写入 CSV：

```text
maturity_release_readiness_trend
maturity_release_readiness_test_coverage_regression_count
maturity_release_readiness_test_coverage_status_changed_count
maturity_release_readiness_max_test_coverage_percent_delta
maturity_release_readiness_max_test_coverage_gap_delta
maturity_release_readiness_trend_changed
maturity_release_readiness_test_coverage_regression_delta
```

Markdown summary 新增：

```text
Maturity coverage regressions
Maturity coverage portfolios
Best score release readiness trend
```

HTML stats 也新增 coverage regression 统计和 portfolio 名称。

Portfolio 表格里的 maturity 列现在展示：

```text
portfolio status / release readiness trend / coverage regression count
```

这让本地 HTML 不需要打开 JSON 就能看到为什么最高分 portfolio 被 review action 阻断。

### `tests/test_training_portfolio_comparison.py`

测试 fixture `make_portfolio()` 新增 maturity coverage 参数：

```text
maturity_release_trend
coverage_regression_count
```

新增测试：

```text
test_best_scoring_coverage_regressed_portfolio_blocks_promotion
```

测试构造：

```text
baseline:
  score=82
  release readiness trend=stable
  coverage regression count=0

candidate:
  score=92
  release readiness trend=coverage-regressed
  coverage regression count=2
```

断言重点：

```text
best_score_name == "candidate"
best_score_maturity_release_readiness_trend == "coverage-regressed"
maturity_coverage_regression_count == 1
review_action_count == 1
blocker_action_count == 1
reason == "best_score_coverage_regressed"
```

这证明高分不会盖过 coverage regression。

### `tests/test_training_portfolio_comparison_artifacts.py`

该测试保护输出层。

它确认：

```text
CSV 包含 coverage regression 字段
Markdown 包含 Maturity coverage regressions
HTML 包含 Coverage regressions
```

这避免未来只改内存 JSON 而忘记人读和机器消费输出。

## 输入输出

输入来自 training portfolio 的 artifact 链接：

```text
training_portfolio.json
  artifacts.maturity_narrative -> maturity_narrative.json
```

`maturity_narrative.json` 中被消费的关键片段是：

```json
{
  "summary": {
    "portfolio_status": "ready",
    "release_readiness_trend_status": "coverage-regressed",
    "release_readiness_test_coverage_regression_count": 2,
    "release_readiness_test_coverage_status_changed_count": 1,
    "release_readiness_max_test_coverage_percent_delta": 8.5,
    "release_readiness_max_test_coverage_gap_delta": 3
  }
}
```

输出进入 comparison report：

```text
training_portfolio_comparison.json
training_portfolio_comparison.csv
training_portfolio_comparison.md
training_portfolio_comparison.html
```

其中 `review_actions` 会包含：

```json
{
  "category": "maturity",
  "severity": "blocker",
  "reason": "best_score_coverage_regressed",
  "evidence": {
    "maturity_release_readiness_trend": "coverage-regressed",
    "coverage_regression_count": 2
  }
}
```

## 测试覆盖

本版聚焦测试：

```text
python -B -m unittest tests.test_training_portfolio_comparison tests.test_training_portfolio_comparison_artifacts -q
Ran 10 tests OK
```

全量测试：

```text
python -B -m unittest discover -s tests -q
Ran 487 tests OK
```

编码检查：

```text
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-v250
status=pass
clean_count=265
syntax_error_count=0
compatibility_error_count=0
```

## 运行证据

本版运行证据归档在 `c/250`：

- `图片/01-training-portfolio-coverage-tests.png`
- `图片/02-training-portfolio-coverage-smoke.png`
- `图片/03-training-portfolio-output-check.png`
- `图片/04-full-unittest.png`
- `解释/说明.md`

其中 smoke 构造了一个最高分但 coverage-regressed 的 candidate，并证明输出：

```text
best_score_name=candidate
best_score_release_trend=coverage-regressed
review_action_count=1
blocker_action_count=1
first_action_reason=best_score_coverage_regressed
```

## 证据链角色

v250 是 coverage governance 系列从“证据传递”走向“决策消费”的版本。

v246-v249 解决的是 coverage regression 能不能传到 maturity narrative。

v250 解决的是 portfolio comparison 会不会用这个证据阻断有风险的最佳分数基线。

## 一句话总结

v250 让训练 portfolio 的基线选择尊重 release-readiness coverage 回退：分数最高不等于可推广，coverage-regressed 必须先进入 blocker review。
