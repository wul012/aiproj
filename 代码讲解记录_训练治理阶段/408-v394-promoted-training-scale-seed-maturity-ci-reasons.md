# v394 promoted training scale seed maturity CI reasons 代码讲解

## 本版目标和边界

v394 的目标是把 v393 promoted baseline decision 已经保留的 selected/global/comparison-ready handoff maturity CI regression reason counts，继续带到 promoted training scale next-cycle seed。

promoted seed 是 baseline decision 和下一轮 `plan_training_scale.py` 命令之间的交接层。这个层负责确认 selected baseline、下一轮语料来源、suite 继承和 next plan command。v394 让这个交接层也能解释被排除的 dirty CI decision inputs，避免 next seed 只知道 count，却看不到原因分布。

本版不改变 seed readiness 判定，不改变 next plan command 生成规则，不执行训练，不改变 promoted seed handoff。它只把 reason counts 带到 seed 的 clean-batch review、summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 前置能力

本版承接 v384-v393：

```text
portfolio comparison maturity CI reasons
        |
        v
batch review reason counts
        |
        v
workflow + handoff
        |
        v
promotion
        |
        v
promotion index
        |
        v
promoted comparison
        |
        v
promoted decision
        |
        v
promoted next-cycle seed
```

v393 已经让 promoted decision 在 baseline 选择前保留 reason-count evidence。v394 的作用是让下一轮 seed 在发出 plan command 前也携带这份解释。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_review.py`

`build_seed_handoff_clean_batch_review()` 新增从 decision summary 或 selected baseline 中读取：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts
selected_handoff_selected_batch_maturity_ci_regression_reason_counts
```

同时从 decision summary 读取：

```text
handoff_batch_maturity_ci_regression_reason_counts
handoff_selected_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts
```

`build_seed_handoff_clean_batch_review_summary()` 再把这些字段提升到 seed summary，供 artifact、CLI 和后续 handoff 消费。

`append_seed_handoff_clean_batch_recommendation()` 在 rejected decision inputs 带 CI regression 时输出 observed reasons，让人读建议时不必打开 JSON。

### `src/minigpt/promoted_training_scale_seed_artifacts.py`

CSV、Markdown、HTML 新增 selected/full/comparison-ready reason-count 字段。

Markdown summary 新增：

```text
Selected handoff batch CI regression reasons
Selected handoff selected batch CI regression reasons
Handoff batch CI regression reasons
Handoff selected batch CI regression reasons
Comparison-ready handoff batch CI regression reasons
Comparison-ready selected batch CI regression reasons
```

HTML stat cards 和 Baseline Seed section 同步展示这些字段。它们用于人工审查；机器消费仍以 `promoted_training_scale_seed.json` 为准。

### `scripts/build_promoted_training_scale_seed.py`

stdout 新增 JSON 格式 reason-count 输出：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts=<json>
handoff_batch_maturity_ci_regression_reason_counts=<json>
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts=<json>
```

这让 CI 日志和 shell reader 可以直接看到 next-cycle seed 是否携带 rejected-input CI reason context。

### `tests/test_promoted_training_scale_seed.py`

测试 fixture 在 decision summary 中加入：

```json
{
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  },
  "handoff_selected_batch_maturity_ci_regression_reason_counts": {
    "workflow-order-regressed": 1
  },
  "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": {}
}
```

断言覆盖 nested `handoff_clean_batch_review`、top-level summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 数据结构说明

seed summary 示例：

```json
{
  "selected_handoff_batch_maturity_ci_regression_reason_counts": {},
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  },
  "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": {}
}
```

这表示 selected baseline 干净，dirty CI inputs 被留在 seed 证据里作为解释，但不会污染 next plan command 的 baseline。

## 运行流程

```text
build_promoted_training_scale_seed()
        |
        v
load promoted_training_scale_decision.json
        |
        v
build_seed_handoff_clean_batch_review()
  - carry selected/full/comparison-ready reason counts
        |
        v
build_seed_handoff_clean_batch_review_summary()
  - expose reason counts in seed summary
        |
        v
_plan_command()
  - command generation remains unchanged
        |
        v
write JSON / CSV / Markdown / HTML
        |
        v
scripts/build_promoted_training_scale_seed.py
  - print reason-count JSON before handoff
```

promoted seed 仍是交接证据，不执行训练，也不写新的 training scale plan，除非后续 handoff 显式执行命令。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_promoted_training_scale_seed.py -q
```

覆盖点：

- ready/review/blocked seed 状态保持不变；
- next plan command 生成逻辑保持不变；
- nested clean-batch review 保留 reason counts；
- top-level summary 保留 selected/full/comparison-ready reason counts；
- CSV、Markdown、HTML、CLI stdout 展示 reason counts；
- recommendations 包含 observed reason detail。

## 维护边界

`promoted_training_scale_seed_artifacts.py` 已接近 500 行。本版只做字段贯通，没有继续拆分。若后续继续把 reason counts 推到 seed handoff 或 automation receipt，建议先把 seed artifact 的 Markdown/HTML section 拆到独立模块，避免形成难维护的大文件。

## 证据归档

本版运行截图和说明放在：

```text
d/394/图片
d/394/解释/说明.md
```

`d/394/解释/v394-promoted-training-scale-seed-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v394 把 maturity CI regression reason counts 从 promoted decision 推进到 promoted next-cycle seed，让下一轮 plan command 发出前也能解释被排除 decision input 的 CI 回归原因。
