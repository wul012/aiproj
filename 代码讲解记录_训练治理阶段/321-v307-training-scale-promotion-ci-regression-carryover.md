# v307 training scale promotion CI regression carryover

## 本版目标和边界

v307 的目标是把 v306 handoff 已经暴露的 batch CI regression 证据继续带入 training scale promotion。

本版不新增 promotion index、不改 promoted seed 链路，也不改变训练执行逻辑。它只修补 promotion acceptance 的证据断点：promotion 以前能看到 handoff 的 clean-batch 状态和 coverage regression，但看不到 `batch_maturity_ci_regression_count`。

## 前置路线

本版接在 v304-v306 之后：

- v304 把 batch CI 回归带入 training-scale run 和 run comparison。
- v305 把它带入 standalone decision，并让 strict clean-batch decision 可以阻断。
- v306 把它带入 workflow 和 execution handoff，并让 strict handoff 可以阻断。
- v307 把 handoff CI 回归继续带入 promotion acceptance。

## 关键文件

- `src/minigpt/training_scale_promotion.py`
  - `_suite_guard()` 读取 selected 和 aggregate handoff CI regression 字段。
  - `_clean_batch_review_guard()` 读取 handoff guard 或 summary 中的 CI regression 数量和名称。
  - `_issues()` 在 clean-required promotion 下，如果 CI regression 数量大于 0，也加入 blocker。
  - `_summary()` 输出 selected/aggregate handoff CI regression 证据。
  - `_recommendations()` 对 CI-regressed handoff batch 给出专门建议。

- `src/minigpt/training_scale_promotion_artifacts.py`
  - CSV/Markdown/HTML 输出 `handoff_selected_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_count` 和 `handoff_batch_maturity_ci_regression_names`。

- `scripts/build_training_scale_promotion.py`
  - CLI stdout 新增 handoff CI regression 计数，方便 CI 或外部脚本读取。

- `tests/test_training_scale_promotion.py`
  - fixture 增加 `batch_ci_regression_count` 和 `batch_ci_regression_names`。
  - 新增 promotion carryover、artifact rendering、CLI output、strict clean-required blocker 测试。

## 核心字段

promotion summary 现在新增：

```text
handoff_selected_batch_maturity_ci_regression_count
handoff_batch_maturity_ci_regression_count
handoff_batch_maturity_ci_regression_names
```

selected 字段描述当前 handoff 选中的候选，aggregate 字段描述整个 handoff batch 是否含 CI-regressed portfolio。

## 运行流程

```text
training scale decision
-> consolidated workflow
-> execution handoff
-> promotion acceptance
```

v307 只修改最后一步。

如果 handoff 中存在 `batch_maturity_ci_regression_count > 0`：

1. promotion summary 会记录数量和名称。
2. promotion CSV/Markdown/HTML 会渲染这些字段。
3. CLI 会打印机器可读 key/value 字段。
4. 如果 handoff 要求 clean batch-review，promotion 会阻断，即使旧 status 字段仍写着 `clean`。

## 测试覆盖

新增测试覆盖：

- 普通 promoted handoff 默认 CI regression count 为 0。
- promotion 能承接 handoff CI regression count/name 并渲染到 CSV/Markdown/HTML。
- `scripts/build_training_scale_promotion.py` 能打印 handoff CI regression count。
- clean-required handoff 即使状态为 `clean`，只要 CI regression count 大于 0，promotion 仍然 blocked。

验证命令覆盖 focused promotion/handoff 测试、source encoding、Python compile 和 full unittest discovery。

## 运行证据

运行截图与解释归档在：

```text
d/307/图片
d/307/解释/说明.md
```

这些证据证明 v307 没有新建孤立报告，而是把 v306 的 handoff CI regression 风险继续接到 promotion acceptance。

## 一句话总结

v307 让 promotion acceptance 不再只相信 clean-batch 状态字符串，而能直接消费并阻断 CI-regressed handoff batch 证据。
