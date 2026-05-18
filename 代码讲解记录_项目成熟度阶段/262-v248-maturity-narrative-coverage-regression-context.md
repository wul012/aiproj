# v248 maturity narrative coverage regression context 代码讲解

## 本版目标

v248 的目标是让 maturity narrative 消费 v247 的 coverage regression context。

v247 已经让 maturity summary 能识别 registry-level coverage regression，并把 overall status 降为 `warn`。v248 继续把这些字段带到 narrative 层，让人读报告能解释：

```text
为什么 portfolio_status 是 review
release readiness trend 为什么是 coverage-regressed
coverage regression 的数量是多少
coverage gap 最大变化是多少
```

## 不做什么

本版不重新计算 coverage。

本版不改变 maturity summary 的 `coverage-regressed` 判断。

本版不改变 benchmark、dataset、request-history 的评分规则。

本版不把 coverage regression 解释为模型能力退步；它仍然是测试治理证据退步。

## 前置链路

本版承接 v239-v247：

```text
v239 coverage baseline
v240 coverage fail-under gate
v241 project audit coverage context
v242 release bundle coverage context
v243 release gate coverage audit policy
v244 release readiness coverage dashboard
v245 release readiness coverage comparison
v246 registry coverage regression tracking
v247 maturity coverage regression context
v248 maturity narrative coverage regression context
```

v248 的位置是“把机器总结翻译成人读叙事”，所以改动集中在 narrative summary、section claim、artifact 输出和 CLI。

## 关键文件

### `src/minigpt/maturity_narrative_summary.py`

summary 新增字段：

```text
release_readiness_test_coverage_regression_count
release_readiness_test_coverage_status_changed_count
release_readiness_max_test_coverage_percent_delta
release_readiness_max_test_coverage_gap_delta
```

`_release_summary()` 从 maturity summary 和 release readiness context 两个位置读取这些字段，保持兼容：

```text
release_context.test_coverage_regression_count
maturity_summary.release_readiness_test_coverage_regression_count
```

`_portfolio_status()` 新增 review 条件：

```text
release.trend_status == "coverage-regressed"
test_coverage_regression_count > 0
```

这让 narrative 不会因为 benchmark/data/request 都是 pass 就忽略 coverage 退步。

### `src/minigpt/maturity_narrative_sections.py`

Release Quality Trend claim 增加 coverage 信息：

```text
test coverage regressions=<count>
max coverage gap delta=<value>
```

这个字段的角色是解释，而不是替代原来的 trend。reviewer 能同时看到：

```text
trend=coverage-regressed
readiness regressions=0
improvements=1
coverage regressions=1
gap delta=3
```

这能避免把 coverage 退步误读为普通 release status regression。

### `src/minigpt/maturity_narrative_artifacts.py`

Markdown Portfolio Summary 新增：

```text
Release coverage regressions
Release coverage gap delta
```

HTML stats 新增：

```text
Coverage regressions
Coverage gap delta
```

HTML pill 样式把 `coverage-regressed` 纳入红色风险状态，和 `regressed` 同级展示。

### `scripts/build_maturity_narrative.py`

CLI 输出新增：

```text
release_readiness_test_coverage_regression_count
release_readiness_max_test_coverage_gap_delta
```

这让截图和 CI log 里能直接看到 coverage regression 的 narrative 结果。

### `tests/test_maturity_narrative.py`

`make_project()` fixture 增加：

```text
coverage_regression_count
```

新增测试：

```text
test_build_maturity_narrative_marks_review_for_coverage_regression
```

断言包括：

```text
portfolio_status == "review"
release_readiness_trend_status == "coverage-regressed"
release_readiness_test_coverage_regression_count == 1
release_readiness_max_test_coverage_gap_delta == 3
release_section.status == "coverage-regressed"
release_section.claim contains "test coverage regressions=1"
```

输出测试同步确认 Markdown 和 HTML 都包含 coverage regression 字段。

## 输入输出

输入仍然是 maturity narrative 的既有 artifacts：

```text
maturity_summary.json
registry.json
request_history_summary.json
benchmark_scorecard.json
benchmark_scorecard_decision.json
dataset_card.json
```

其中 maturity summary 需要含有：

```text
release_readiness_test_coverage_regression_count
release_readiness_max_test_coverage_gap_delta
```

输出仍然是：

```text
maturity_narrative.json
maturity_narrative.md
maturity_narrative.html
CLI summary lines
```

## 运行证据

本版运行证据归档在 `c/248`：

- `图片/01-maturity-narrative-coverage-tests.png`
- `图片/02-maturity-narrative-coverage-smoke.png`
- `图片/03-maturity-narrative-output-check.png`
- `图片/04-full-unittest.png`

smoke 样本中：

```text
maturity_status=warn
release_readiness_trend_status=coverage-regressed
release_readiness_test_coverage_regression_count=1
release_readiness_max_test_coverage_gap_delta=3
request_history_status=pass
benchmark_scorecards=1
benchmark_scorecard_decisions=1
dataset_cards=1
warnings=[]
```

narrative 输出：

```text
portfolio_status=review
release_section_status=coverage-regressed
test coverage regressions=1
max coverage gap delta=3
```

## 证据链角色

v248 把 coverage regression 从 maturity summary 的机器字段推进到 maturity narrative 的人读解释。

这让项目展示时能更清楚地说：

```text
不是模型能力一定退步
不是数据卡或 benchmark 失败
而是测试覆盖率治理证据相对 baseline 退步
所以 portfolio 暂时保持 review
```

## 一句话总结

v248 让 maturity narrative 具备 coverage regression 解释能力，把覆盖率退步转成 release-quality portfolio review 的清晰原因。
