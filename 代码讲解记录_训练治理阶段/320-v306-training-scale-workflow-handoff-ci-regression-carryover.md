# v306 training scale workflow handoff CI regression carryover

## 本版目标和边界

v306 的目标是把 v305 已经识别出来的 `batch_maturity_ci_regression_count` 和 CI-regressed batch 名称继续向下游传递到 consolidated workflow 和 execution handoff。

本版不新增新的评估报告类型，不改变模型训练逻辑，也不扩大 checkpoint 或数据集规模。它解决的是证据链断点：standalone decision 已经知道 batch 中存在 CI 回归，但 workflow / handoff 以前只暴露 `clean_batch_review_status` 这类粗粒度状态。

## 前置路线

这版接在 v304-v305 之后：

- v304 把 batch CI 回归从 training portfolio batch 带入 gated training-scale run 和 run comparison。
- v305 把同一信号带入 training-scale run decision，并让 `--require-clean-batch-review` 可以因为 CI 回归而阻断候选。
- v306 继续把 decision summary 中的 CI 回归字段传给 workflow summary、workflow artifacts、handoff guard、handoff summary 和 CLI 输出。

因此 v306 是一次下游承接，不是新建孤立层。

## 关键文件

- `src/minigpt/training_scale_workflow.py`
  - `_workflow_summary()` 新增 selected batch review、selected CI regression、aggregate CI regression、CI-regressed names 和 blocker reasons。
  - `_workflow_recommendations()` 在 workflow 层看到 CI-regressed batch 时给出专门复查建议。

- `src/minigpt/training_scale_workflow_artifacts.py`
  - workflow CSV/Markdown/HTML 输出新增 `selected_batch_maturity_ci_regression_count`、`batch_maturity_ci_regression_count` 和 `batch_maturity_ci_regression_names`。
  - 这些字段用于给一键 workflow 的读者直接看见 CI 风险来源。

- `src/minigpt/training_scale_handoff.py`
  - `_clean_batch_review_guard()` 从 decision summary 或 workflow summary 读取 CI 回归数量和名称。
  - `_handoff_allowed()` 在 strict clean-batch 模式下不只看状态字符串，也直接检查 CI 回归数量。
  - `_summary()` 把 selected/aggregate CI 回归字段写入 handoff summary。

- `src/minigpt/training_scale_handoff_artifacts.py`
  - handoff CSV/Markdown/HTML 输出新增 selected 和 aggregate CI regression 字段。
  - 这让执行交接报告不再只写 `review`，而能写清楚是否是 CI-regressed batch。

- `scripts/run_training_scale_workflow.py`
  - CLI stdout 新增 `batch_maturity_ci_regression_count` 和 `selected_batch_maturity_ci_regression_count`。

- `scripts/execute_training_scale_handoff.py`
  - CLI stdout 新增同样的 CI regression 计数字段，方便 CI 或外部脚本读取。

## 核心数据结构

workflow summary 现在新增这些字段：

```text
selected_batch_review_status
selected_batch_comparison_review_action_count
selected_batch_comparison_blocker_action_count
selected_batch_maturity_coverage_regression_count
selected_batch_maturity_ci_regression_count
batch_comparison_review_action_count
batch_comparison_blocker_action_count
batch_maturity_coverage_regression_count
batch_maturity_coverage_regression_names
batch_maturity_ci_regression_count
batch_maturity_ci_regression_names
batch_comparison_blocker_reasons
```

handoff summary 重点承接：

```text
selected_batch_maturity_ci_regression_count
batch_maturity_ci_regression_count
batch_maturity_ci_regression_names
```

这里 selected 字段描述当前选中的执行候选，aggregate 字段描述比较批次整体是否存在 CI-regressed batch。

## 运行流程

```text
training portfolio comparison
-> training portfolio batch
-> training scale run
-> training scale run comparison
-> training scale run decision
-> training scale workflow
-> training scale handoff
```

v306 只修改最后两步的证据承接。

当 decision summary 中有 `batch_maturity_ci_regression_count > 0` 时：

1. workflow summary 记录计数和名称。
2. workflow CSV/Markdown/HTML/CLI 显示计数。
3. handoff guard 从 decision 或 workflow summary 读取计数。
4. handoff summary 和 artifacts 显示计数。
5. strict clean-batch handoff 即使看到旧状态字段为 `clean`，也会因为 CI 回归数量大于 0 而阻断。

## 输入输出

输入：

- `training_scale_run_decision.json`
- `training_scale_workflow.json`

输出：

- `training_scale_workflow.json`
- `training_scale_workflow.csv`
- `training_scale_workflow.md`
- `training_scale_workflow.html`
- `training_scale_handoff.json`
- `training_scale_handoff.csv`
- `training_scale_handoff.md`
- `training_scale_handoff.html`
- CLI stdout 中的 key/value 诊断字段

这些输出是下游自动化、人工复查和版本证据共同消费的证据，不是训练产物本身。

## 测试覆盖

新增和扩展的测试集中在：

- `tests/test_training_scale_workflow.py`
  - 覆盖 workflow 从 decision summary 承接 selected/aggregate CI regression 字段。
  - 覆盖 CSV/Markdown/HTML 是否渲染这些字段。

- `tests/test_training_scale_handoff.py`
  - 覆盖 handoff summary、CSV、Markdown、HTML、CLI stdout 是否承接 CI 回归字段。
  - 覆盖 strict clean-batch review 在 `clean` 状态字符串之外，仍会检查 CI 回归数量。

验证命令包括 focused tests、Python syntax compile、source encoding hygiene 和 full unittest discovery。

## 运行证据

运行截图与解释归档在：

```text
d/306/图片
d/306/解释/说明.md
```

这些证据包含 focused tests、artifact smoke、source encoding、full unittest、文档索引检查和 git/tag 状态检查。

## 一句话总结

v306 把 CI-regressed batch 证据从“decision 能识别”推进到“workflow 和 handoff 都能看见并阻断”，让训练规模自动化入口更不容易漏掉上游 CI 风险。
