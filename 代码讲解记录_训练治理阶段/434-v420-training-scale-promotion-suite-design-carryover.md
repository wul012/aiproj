# v420 training scale promotion suite-design carryover 代码讲解

## 本版目标与边界

v420 的目标是把 v419 已经带到 execution handoff 的 suite-design regression context 继续带进 training scale promotion。promotion 是把一次训练规模 handoff 判定为可推广证据的接收层，如果这里只消费 `handoff_batch_maturity_ci_regression_count`，就可能把带有 benchmark-suite blocker 的 handoff 当成 clean-batch evidence。

本版不改训练执行命令，不改 handoff 生成，也不重新计算 suite-design readiness。它只读取 handoff summary/guard 中已有字段，持久化到 promotion summary、CSV、Markdown、HTML、CLI 和 strict clean-batch acceptance gate。

## 前置链路

本版接在 v417-v419 后面：

- v417：training portfolio comparison 产生 dedicated suite-design blocker。
- v418：batch、scale run、comparison、decision、workflow 保留 suite-design regression context。
- v419：execution handoff 继续保留这些字段，并在 strict clean-batch handoff validation 中识别它们。
- v420：promotion acceptance 继续消费这些字段，避免 promotion 层丢失 blocker 原因。

## 关键文件

### `src/minigpt/training_scale_promotion.py`

`_suite_guard()` 新增读取 selected/global suite-design 字段：

- `selected_batch_maturity_suite_design_regression_count`
- `selected_batch_maturity_suite_design_regression_names`
- `batch_maturity_suite_design_regression_count`
- `batch_maturity_suite_design_regression_names`

这些字段通过 `_handoff_value()` 从 handoff summary 或 decision summary 读取，命名上统一加 `handoff_` 前缀后进入 promotion evidence。

`_clean_batch_review_guard()` 同步读取 clean-batch guard 中的 suite-design 字段。这样即使 handoff summary 由旧路径生成，只要 guard 里有字段，strict promotion 也能识别。

`_issues()` 在 `handoff_require_clean_batch_review=True` 时新增 suite-design regression 检查：

```text
handoff_clean_batch_review_status != clean
or handoff_batch_maturity_ci_regression_count > 0
or handoff_batch_maturity_suite_design_regression_count > 0
```

这意味着 legacy 输入如果写着 `clean`，但同时携带 suite-design regression count，promotion 仍会 blocked。

`_recommendations()` 新增两类提示：

- strict clean-batch 场景：推荐先解决 handoff clean batch-review requirement，并列出 suite-design portfolios。
- 非 strict 场景：promotion 可以保持可见，但 recommendation 会明确要求先处理 suite-design regressed handoff batch evidence。

### `src/minigpt/training_scale_promotion_artifacts.py`

CSV 新增四个字段：

- `handoff_selected_batch_maturity_suite_design_regression_count`
- `handoff_selected_batch_maturity_suite_design_regression_names`
- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_batch_maturity_suite_design_regression_names`

Markdown 和 HTML 的 summary/stat cards 也展示 selected/global suite-design regression count 与 names。HTML 截图能直接看到：

```text
Selected suite-design regressions = 1
Batch suite-design regressions = 1
Suite-design names = suite-design-risk
```

### `scripts/build_training_scale_promotion.py`

CLI stdout 新增：

- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_batch_maturity_suite_design_regression_names`
- `handoff_selected_batch_maturity_suite_design_regression_count`
- `handoff_selected_batch_maturity_suite_design_regression_names`

这样 CI 日志或 shell-only 审查无需打开 JSON，也能判断 promotion 是否因为 suite-design blocker 被阻断。

## 核心数据流

本版字段流向是：

```text
training_scale_handoff.summary
  -> training_scale_promotion.suite_guard / clean_batch_review_guard
  -> training_scale_promotion.summary
  -> JSON / CSV / Markdown / HTML / CLI evidence
  -> strict clean-batch promotion gate
```

字段仍保留 selected 和 global batch 两个维度：

- selected 维度说明被选中 handoff 对应 run 是否有 suite-design regression。
- global batch 维度说明整个 batch review 是否存在 suite-design regression。

promotion 使用 global batch count 作为 strict clean-batch blocker，因为它代表本次 handoff 所属 comparison evidence 是否真的干净。

## 测试覆盖

`tests/test_training_scale_promotion.py` 新增两组测试：

- suite-design context carryover：断言 summary、CSV、Markdown、HTML、CLI stdout 都出现 selected/global suite-design regression count/names，并且 recommendation 说明 suite-design risk。
- strict clean-batch blocking：当 `require_clean_batch_review=True` 且 suite-design regression count 大于 0，即使 `clean_batch_review_status=clean`，promotion 也会 blocked，CLI 返回非零。

原有 promoted、failed handoff、missing evidence、suite guard、batch review、CI regression 和 artifact facade 测试继续通过。

本轮定向验证：

- `python -m pytest tests\test_training_scale_promotion.py -q`：`14 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`712 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v420`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/420` 归档了本版截图和说明：

- `d/420/图片/01-training-scale-promotion-suite-design.png`
- `d/420/解释/v420-training-scale-promotion-suite-design-evidence.html`
- `d/420/解释/v420-training-scale-promotion-suite-design-evidence.json`
- `d/420/解释/v420-training-scale-promotion-suite-design-snapshot.md`
- `d/420/解释/说明.md`

截图证明 promotion status 是 `blocked`，handoff clean-batch status 仍是 `clean`，但 selected/global suite-design regression count 都是 `1`，因此 strict promotion 被 blocker 阻断。

一句话总结：v420 把 suite-design blocker 保留到 training scale promotion 接收层，让 promotion acceptance 不再漏掉 benchmark-suite regression 风险。
