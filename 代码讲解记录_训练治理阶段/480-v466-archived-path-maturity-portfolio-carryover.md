# v466：archived path 回归进入 maturity / portfolio 消费层

## 本版目标与边界

v466 解决的是 v465 之后的下游消费问题。v465 已经能在 release readiness comparison 里发现 archived path portability readiness 从 ready 变成 not-ready，并输出 `archived_path_portability_check_not_ready`。但如果这个信号只留在 comparison 层，后续 maturity summary、maturity narrative 和 training portfolio comparison 仍然需要读原始 JSON 才能判断风险。

本版目标是把这个信号接入现有链路：

```text
release readiness comparison
  -> registry release readiness delta summary
  -> maturity summary
  -> maturity narrative
  -> training portfolio comparison / review action
```

本版不新增治理链，不改变 v465 的回归判定，也不扩大模型训练能力。它只是让既有的 archived path CI 回归原因被后续模块稳定消费。

## 前置能力

- v463：新增 archived path portability CI gate。
- v464：把 archived path readiness 从 CI workflow hygiene 传到 audit、bundle、readiness。
- v465：release readiness comparison 能识别 archived path readiness 回归，并生成 `archived_path_portability_check_not_ready` reason。

v466 的角色是把 v465 的 reason 继续向成熟度和 portfolio 侧传递。

## 关键代码变更

### `src/minigpt/registry_release_readiness.py`

registry delta summary 新增：

```python
ci_workflow_archived_path_portability_check_ready_regression_count
```

它统计 comparison delta 中 `ci_workflow_archived_path_portability_check_ready_regressed=True` 的数量。这个字段和 boundary gate、boundary plan、drift smoke 的回归计数保持同一种结构。

### `src/minigpt/maturity.py`

maturity summary 从 registry 的 release readiness context 中读取：

```python
release_readiness_ci_archived_path_portability_check_ready_regression_count
```

当 registry 不存在或字段缺失时，缺省上下文仍返回 `None`，避免旧产物被强制要求包含新字段。

### `src/minigpt/maturity_artifacts.py`

Markdown、HTML 和概览统计中增加 archived path regression 展示。这样用户不需要打开 JSON，也能在 maturity summary 页面看到这类 CI 回归。

### `src/minigpt/maturity_narrative_summary.py`

narrative summary 从 maturity summary 或 release context 中 coalesce archived path regression 计数，并把它写回 release context：

```python
ci_workflow_archived_path_portability_check_ready_regression_count
```

这保证 narrative 即使从不同输入组合构建，也能拿到同一个信号。

### `src/minigpt/maturity_narrative_sections.py`

release quality section 的 claim 增加：

```text
CI archived path regressions=<count>
```

这让自然语言叙述和机器字段保持同步。

### `src/minigpt/training_portfolio_comparison.py`

portfolio row 新增：

```python
maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count
```

summary 也新增 best-score 对应字段：

```python
best_score_maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count
```

这样当 best-score candidate 有 archived path CI 回归时，比较摘要能直接指出风险。

### `src/minigpt/training_portfolio_comparison_review.py`

`has_maturity_ci_regression()` 把 archived path regression count 纳入 ready-regression 计数。review action 的 evidence 也加入：

```python
ci_archived_path_portability_check_ready_regression_count
```

因此分数更高的 candidate 如果携带 archived path CI 回归，仍会触发 blocker 或 review action。

### CLI 输出

- `scripts/build_maturity_summary.py`
- `scripts/build_maturity_narrative.py`
- `scripts/register_runs.py`
- `scripts/compare_training_portfolios.py`

这些脚本都补充了 archived path regression 相关输出，方便 CI 日志和本地验证直接检索。

## 运行证据

证据目录：`d/466`

主要产物：

- `d/466/解释/registry-archived-path/registry.json`
- `d/466/解释/maturity-summary-archived-path/maturity_summary.json`
- `d/466/解释/maturity-narrative-archived-path/maturity_narrative.json`
- `d/466/解释/training-portfolio-comparison-archived-path/training_portfolio_comparison.json`
- `d/466/图片/training-portfolio-comparison-archived-path.png`

其中 portfolio comparison 证明了一个关键场景：candidate 的 score 和 loss 更好，但它继承了 archived path CI regression，因此 review layer 仍会产生 blocker action。

## 测试覆盖

新增和更新的测试覆盖了四个层面：

- registry summary 能统计 archived path readiness regression。
- maturity summary 能把该字段放入 summary 和 release context。
- maturity narrative 能把该字段写入 summary、section claim 和 recommendation。
- training portfolio comparison 能把该字段写入 portfolio row、summary、CSV/Markdown/HTML、review action evidence，并让 `has_maturity_ci_regression()` 返回 true。

这些测试保护的是“同一个 CI 回归原因被下游一致消费”，而不是单纯检查字符串存在。

## 一句话总结

v466 把 archived path portability 的 CI 回归从 release readiness comparison 的局部发现，推进为 maturity 和 portfolio 评审都会消费的阻断信号。
