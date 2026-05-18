# v237 portfolio comparison blocker action CLI gate 代码讲解

## 本版目标

v237 的目标是让 v236 的结构化 `review_actions` 能进入命令行自动化门禁。

v236 已经能在 training portfolio comparison JSON、Markdown 和 HTML 中生成 review action 清单。v237 不再继续扩展 action 类型，而是让 `scripts/compare_training_portfolios.py` 在显式开启时根据 blocker action 返回非零退出码。

## 不做什么

本版不改变 `build_training_portfolio_comparison()` 的默认语义。

本版不让所有 review action 都阻断命令。

本版也不改变 batch planning 自动生成的旧比较命令，默认 CLI 仍保持退出 0。

## `scripts/compare_training_portfolios.py`

### 新增参数

新增：

```text
--fail-on-blocker-action
```

含义是：报告正常写出之后，如果 summary 中：

```text
blocker_action_count > 0
```

脚本返回 `SystemExit(1)`。

### 输出变化

脚本现在额外打印：

```text
review_action_count=<n>
blocker_action_count=<n>
```

并打印 decision：

```text
decision=blocked_by_review_actions
decision=continue_with_portfolio_comparison
```

这样 CI 或上游脚本可以只看 stdout 和退出码，就知道是继续比较还是被 blocker action 阻断。

### 为什么是 opt-in

training portfolio batch 早已有比较命令，历史上这个命令主要用于生成报告。

如果默认改成遇到 blocker 就退出 1，会让旧批处理链路突然变成失败。因此 v237 选择显式开关，让自动化可以主动开启严格门禁，同时保留旧命令兼容。

## `tests/test_training_portfolio_comparison.py`

新增 CLI 级测试：

```text
test_cli_can_fail_on_blocker_review_actions
```

测试构造两个 portfolio：

- baseline 是 ready。
- candidate 是 best-score 且 maturity status 是 review。

这个场景会产生：

```text
best_score_maturity_review
severity=blocker
```

测试分两次执行脚本：

1. 默认命令不带 `--fail-on-blocker-action`，返回 0。
2. 带 `--fail-on-blocker-action`，返回 1。

同时断言 stdout 包含：

```text
blocker_action_count=1
decision=continue_with_portfolio_comparison
decision=blocked_by_review_actions
```

并确认 JSON/Markdown/HTML 输出目录仍被写出。

## 输入输出

输入仍是多个 `training_portfolio.json` 或 portfolio 目录。

输出仍是：

```text
training_portfolio_comparison.json
training_portfolio_comparison.csv
training_portfolio_comparison.md
training_portfolio_comparison.html
```

新增的是 CLI 行为：

- 默认：写出报告，退出 0。
- 开启 gate 且有 blocker action：写出报告，退出 1。

## 运行证据

本版运行证据归档在 `c/237`：

- `图片/01-training-portfolio-cli-gate-tests.png`
- `图片/02-cli-gate-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v237 把 review action 从“可读报告字段”推进到“可选自动化阻断条件”。

这使 training portfolio comparison 可以继续服务人工复核，也可以被 CI 或后续 workflow 用作严格门禁。

## 一句话总结

v237 为 portfolio comparison 增加 blocker action CLI gate，让训练组合比较开始具备可选的自动化失败语义。
