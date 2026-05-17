# v206 promotion suite guard evidence 代码讲解

## 本版目标

v206 的目标是把 v205 已经进入 controlled handoff 的 suite guard，继续带到 training-scale promotion acceptance 层。

v205 让 `training_scale_handoff.json` 能记录：

- 是否要求 suite consistency
- 实际 suite consistency
- mismatch 数量
- selected suite path

但 promotion 层原本只关心 handoff 是否完成、scale run 是否完成、batch 是否完成、variant evidence 是否齐全。这样 promotion JSON/CSV/Markdown/HTML 虽然能说明一个运行是否可作为 promoted baseline，却没有保留“这个 promoted baseline 是否来自 clean suite comparison”的审阅边界。

本版补上这条证据延伸。

## 不做什么

本版不改变 promotion 的 `promoted` / `review` / `blocked` 判定，不重新计算 suite consistency，也不把 suite guard 变成新的 promotion blocker。

suite consistency 的计算仍然属于 comparison 层，strict guard 的阻断仍然属于 decision 层，handoff 负责承接 execute command，promotion 这里只负责保留并展示 handoff 已经携带的 suite evidence。

## `src/minigpt/training_scale_promotion.py`

### `build_training_scale_promotion()`

promotion builder 现在会从 handoff 读出：

```python
suite_guard = _suite_guard(handoff)
```

然后把它写入 report 顶层：

```json
"suite_guard": {
  "handoff_require_suite_consistency": true,
  "handoff_suite_consistency": "consistent",
  "handoff_suite_mismatch_count": 0,
  "handoff_selected_suite_path": "builtin:standard-zh"
}
```

命名里保留 `handoff_` 前缀，是为了明确这不是 promotion 自己重新计算出来的结论，而是 promotion 从 handoff evidence 继承过来的边界。

### `_suite_guard()`

`_suite_guard()` 有两个读取来源：

1. `handoff["suite_guard"]`
2. `handoff["summary"]`

这样可以兼容 v205 新 handoff，也能读取只把字段放进 summary 的报告。读取优先级是：

- 优先顶层 `suite_guard`
- 其次 handoff summary

`decision_require_suite_consistency` 和 `require_suite_consistency` 两个字段都支持，是为了兼容 workflow、decision、handoff 各层略有差异的命名。

### `_summary()`

promotion summary 新增：

```json
{
  "handoff_require_suite_consistency": true,
  "handoff_suite_consistency": "consistent",
  "handoff_suite_mismatch_count": 0,
  "handoff_selected_suite_path": "builtin:standard-zh"
}
```

这些字段进入 summary 后，artifact writer 就能统一读取，而不用每个展示面再去拆 handoff。

## `src/minigpt/training_scale_promotion_artifacts.py`

CSV 新增四列：

```text
handoff_require_suite_consistency
handoff_suite_consistency
handoff_suite_mismatch_count
handoff_selected_suite_path
```

Markdown 新增三条摘要：

```text
Handoff require suite consistency
Handoff suite consistency
Handoff suite mismatch count
Handoff selected suite path
```

HTML stats 新增：

```text
Handoff strict suite
Handoff suite
Suite mismatch
Selected suite
```

这些输出都是只读证据面。它们不参与 promotion 决策，只帮助审阅者知道 promoted baseline 是否继承了 clean-comparison 边界。

## 测试覆盖

`tests/test_training_scale_promotion.py` 新增：

```python
test_carries_handoff_suite_guard_into_promotion_evidence
```

这个测试做了两件关键保护：

1. 构造带 `suite_guard` 的 completed handoff，确认 promotion report 能读到 suite guard。
2. 断言 `promotion_status` 仍是 `promoted`，证明本版只是证据传播，不改变 status 语义。

同时测试还检查 CSV、Markdown、HTML 都出现了 suite guard 字段，避免某个审阅面缺证据。

## 运行证据

本版运行证据归档在 `c/206`：

- `图片/01-promotion-suite-guard-tests.png`
- `图片/02-promotion-suite-guard-smoke.png`
- `图片/03-promotion-artifact-suite-guard-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

其中 promotion smoke 构造了一个完整 handoff -> scale run -> batch -> variant evidence 树，promotion 结果保持 `promoted`，同时 summary 显示 `handoff_suite_consistency=consistent`。

## 证据链角色

v206 让 training-scale 链路的 suite boundary 更连续：

```text
comparison -> decision -> workflow -> handoff -> promotion
```

promotion 层不再只说明“这个 handoff 可 promotion”，也能说明“这个 promotion 继承的 handoff 是否带 clean suite evidence”。

## 一句话总结

v206 把 handoff suite guard 继续带到 promotion acceptance 报告，让 promoted baseline 的证据里保留 clean-comparison 边界。
