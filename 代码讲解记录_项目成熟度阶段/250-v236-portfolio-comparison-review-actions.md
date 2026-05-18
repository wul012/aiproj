# v236 portfolio comparison review actions 代码讲解

## 本版目标

v236 的目标是把 training portfolio comparison 里的问题从“推荐语和若干 summary 计数”推进为结构化 `review_actions`。

v232-v235 已经让 maturity review 进入 best-score 选择、输出、推荐语和 review portfolio 名单。v236 继续向前一步：当 portfolio 存在执行失败、artifact 缺口、质量退化、dataset warning 或 maturity review 时，报告会生成可消费的 action row。

## 不做什么

本版不改变模型训练、评分公式、best-score 选择或 portfolio 排序。

本版不替代原有 `recommendations`，而是在其旁边增加机器可读、也能被人读输出展示的 action 表。

## `src/minigpt/training_portfolio_comparison.py`

### `REVIEW_STATUSES`

新增公共状态集合：

```text
{"review", "warn", "fail", "incomplete"}
```

它让 maturity、dataset readiness 和 dataset quality 的 review 判断使用同一套状态边界。

### `build_training_portfolio_comparison()`

比较报告现在新增：

```text
review_actions
```

同时 summary 新增：

```text
review_action_count
blocker_action_count
```

这样 JSON 顶层有完整 action rows，summary 也能快速给 dashboard 或 HTML stats 消费。

### `_review_actions()`

这个函数读取：

- portfolio summary
- baseline deltas
- best score portfolio name

并按类别生成 action：

```text
execution
artifact
quality
dataset
maturity
```

每个 action 结构是：

```text
id
portfolio
category
severity
reason
action
evidence
```

其中 `severity` 目前分为：

```text
review
blocker
```

best-score portfolio 如果 maturity status 是 review/warn/fail/incomplete，会生成 blocker action。非领先 portfolio 的 maturity review 仍生成 review action，避免把非领先风险误判成 clean baseline 阻断。

### `_review_action()`

这是 action row 的小工厂，负责统一字段和 id 格式。

id 使用：

```text
<category>-<sequence>
```

例如：

```text
maturity-1
artifact-2
```

## `src/minigpt/training_portfolio_comparison_artifacts.py`

Markdown Summary 新增：

```text
Review actions
Blocker actions
```

Markdown 还新增 `## Review Actions` 表，字段包括：

```text
ID | Portfolio | Severity | Category | Reason | Action
```

HTML stats 增加 action/blocker 数量，页面主体新增 `Review Actions` 表。

如果没有 action，Markdown/HTML 都明确显示没有 review actions，而不是留空表。

## 测试覆盖

`tests/test_training_portfolio_comparison.py` 覆盖两条关键链路：

- 非领先 review portfolio 会生成 artifact、quality、dataset、maturity 四类 review action。
- best-score review portfolio 会生成 `best_score_maturity_review` blocker action。

`tests/test_training_portfolio_comparison_artifacts.py` 覆盖 artifact renderer：

- summary 能显示 action/blocker 数量。
- Markdown/HTML 都渲染 `Review Actions`。
- action reason 能在输出中被看到。

## 输入输出

输入仍然是 training portfolio 及其链接的 scorecard、dataset card、manifest、maturity narrative 等 artifact。

输出新增：

```text
report.review_actions
report.summary.review_action_count
report.summary.blocker_action_count
```

这些字段是后续自动化审核、dashboard 汇总或 release handoff 的候选输入。

## 运行证据

本版运行证据归档在 `c/236`：

- `图片/01-training-portfolio-review-action-tests.png`
- `图片/02-portfolio-review-action-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v236 的价值不是扩大模型能力，而是把 portfolio comparison 的 review 信息从自然语言推荐语升级成结构化审查动作。

这让后续版本可以继续消费 `review_actions`，例如做 action summary、release readiness handoff 或自动化阻断策略。

## 一句话总结

v236 把 training portfolio comparison 从“说明哪里要看”推进到“列出具体 review action”，让训练组合比较更接近可执行的审查清单。
