# v251 portfolio comparison review split 代码讲解

## 本版目标

v251 的目标是拆分 training portfolio comparison 的 review 规则。

v250 已经让 training portfolio comparison 消费 maturity narrative 的 coverage regression 证据，并在最高分 portfolio 带 coverage 回退时生成 blocker review action。这个方向是合理的，但它让 `training_portfolio_comparison.py` 继续变厚：同一个文件同时负责 artifact 读取、summary 组装、baseline delta、review action、recommendation 和 coverage predicate。

本版选择做收束型优化，把 review action 和 recommendation 迁出主比较器。

## 不做什么

本版不改变 comparison report 的 schema。

本版不改变 review action 的 reason、severity、category 或 evidence 字段。

本版不改变 CLI、输出文件名、Markdown/HTML 渲染或 CSV 字段。

本版不新增新的治理报告层。

## 关键文件

### `src/minigpt/training_portfolio_comparison_review.py`

这是本版新增的 review 规则模块。

它承接四类职责：

```text
REVIEW_STATUSES
COVERAGE_REGRESSED_TREND
build_training_portfolio_review_actions()
build_training_portfolio_recommendations()
```

同时暴露两个小 predicate：

```text
is_review_status()
has_maturity_coverage_regression()
```

`build_training_portfolio_review_actions()` 保留原有动作顺序和语义：

```text
execution -> artifact -> quality -> dataset -> maturity coverage -> maturity status
```

因此 action id 仍按生成顺序命名，例如：

```text
execution-1
artifact-2
maturity-1
```

coverage regression 逻辑也保持 v250 的行为：

```text
best-score + coverage-regressed -> severity=blocker, reason=best_score_coverage_regressed
non-leading + coverage-regressed -> severity=review, reason=portfolio_coverage_regressed
```

### `src/minigpt/training_portfolio_comparison.py`

主比较器现在导入 review 模块：

```text
build_training_portfolio_review_actions
build_training_portfolio_recommendations
has_maturity_coverage_regression
is_review_status
```

它保留这些职责：

```text
load_training_portfolio()
_portfolio_summary()
_portfolio_delta()
_comparison_summary()
_delta_explanation()
```

拆分后结构检查显示：

```text
training_portfolio_comparison.py lines=465
training_portfolio_comparison_review.py lines=240
```

这让主文件回到更可维护的范围，后续如果继续扩展 review action，不必再次挤进 artifact 读取和 delta 计算文件。

### `tests/test_training_portfolio_comparison_review.py`

这是新增的直接单测。

第一组测试保护 predicate 宽容性：

```text
is_review_status(" warn ") == True
has_maturity_coverage_regression(count="2") == True
has_maturity_coverage_regression(trend="coverage-regressed", count="not-a-number") == True
has_maturity_coverage_regression(trend="stable", count="not-a-number") == False
```

这覆盖了 v250 收尾时提到的健壮性点：坏的数字字符串不应该让 review 判断崩掉。

第二组测试直接保护 blocker action：

```text
best_score_name=candidate
maturity_release_readiness_trend=coverage-regressed
coverage_regression_count=1
```

期望输出：

```text
reason=best_score_coverage_regressed
severity=blocker
```

### 既有 comparison 测试

`tests/test_training_portfolio_comparison.py` 和 `tests/test_training_portfolio_comparison_artifacts.py` 没有被削弱。

它们继续证明：

```text
build_training_portfolio_comparison()
JSON/CSV/Markdown/HTML artifact writers
CLI blocker gate
coverage-regressed best-score blocker
```

在拆分后仍然保持行为一致。

## 输入输出

输入仍然是多个 training portfolio：

```text
training_portfolio.json
linked benchmark_scorecard.json
linked dataset_card.json
linked maturity_narrative.json
linked run_manifest.json
```

输出仍然是原来的 comparison artifacts：

```text
training_portfolio_comparison.json
training_portfolio_comparison.csv
training_portfolio_comparison.md
training_portfolio_comparison.html
```

review 模块只改变内部职责边界，不改变这些 artifacts。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_training_portfolio_comparison_review tests.test_training_portfolio_comparison tests.test_training_portfolio_comparison_artifacts -q
Ran 12 tests OK
```

全量测试：

```text
python -B -m unittest discover -s tests -q
Ran 489 tests OK
```

编码检查：

```text
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-v251-final
status=pass
source_count=267
clean_count=267
```

## 运行证据

本版运行证据归档在 `c/251`：

- `图片/01-review-split-focused-tests.png`
- `图片/02-review-split-structure-check.png`
- `图片/03-full-unittest.png`
- `图片/04-source-encoding.png`
- `解释/说明.md`

结构证据证明：

```text
main_no_private_review_actions=True
main_no_private_recommendations=True
review_module_has_blocker_reason=True
review_module_has_predicate=True
```

## 证据链角色

v251 是 v250 的质量收口。

v250 让 coverage regression 影响 portfolio baseline promotion。

v251 确保这个 review 规则有独立边界、独立测试和可继续扩展的位置。

## 一句话总结

v251 把 portfolio comparison 的 review/recommendation 规则从主比较器拆到专用模块，在不改变输出契约的前提下把主文件压回更可维护的形态。
