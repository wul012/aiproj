# v205 workflow handoff suite guard evidence 代码讲解

## 本版目标

v205 的目标不是再引入新的训练规模判断逻辑，而是把 v204 已经进入 consolidated workflow 的 strict suite-consistency guard，继续带到 controlled handoff 报告层。

v204 解决的是“workflow 一键入口不能绕过 strict guard”的问题，但 handoff 层原本只展示 `decision_status`、`command`、`execution` 和 artifact 计数，没有把 `require_suite_consistency`、`suite_consistency`、`suite_mismatch_count`、`selected_suite_path` 这些关键信息一起带出来。这样虽然 workflow 内部已经严格，但交接给人工审阅时，suite 边界证据会变弱。

本版把同一套 suite guard 证据写进 handoff JSON/CSV/Markdown/HTML，让 reviewed execute command 也保持和 workflow 决策一致的可见边界。

## 不做什么

本版不改变 `training_scale_run_decision.py` 的 strict 规则，不改变 suite consistency 的计算，不改变 training-scale workflow 的计划、gate、run、comparison 流程，也不训练新模型。

它只做一件事：把 workflow/decision 已经算好的 suite guard，传递到 handoff evidence 层。

## 输入和边界

`build_training_scale_handoff()` 读取两个输入：

1. workflow JSON
2. workflow 中指向的 nested decision JSON

handoff 不重新计算比较结果，也不重跑 decision。它只从 workflow summary 和 nested decision summary 读取现成证据，再把这些证据整理成 review-ready handoff report。

这条边界很重要：

- comparison 负责算 `suite_consistency`
- decision 负责按 strict guard 阻断或放行
- handoff 负责把执行命令、执行结果和 suite boundary 一起交给审阅者

## `src/minigpt/training_scale_handoff.py`

### `build_training_scale_handoff()`

主入口现在在构造 report 时多了一个 `suite_guard`：

```python
suite_guard = _suite_guard(workflow, decision)
```

这个对象放在 report 顶层，便于后续消费者一眼读到 handoff 的 suite 边界，而不用再手工去翻 workflow 和 decision 两层 JSON。

report 顶层现在包含：

```json
"suite_guard": {
  "decision_require_suite_consistency": true,
  "require_suite_consistency": true,
  "suite_consistency": "consistent",
  "suite_mismatch_count": 0,
  "selected_suite_path": "builtin:standard-zh",
  "workflow_suite_path": "builtin:standard-zh",
  "workflow_suite_name": "standard-zh"
}
```

这里要注意两类字段：

- `decision_require_suite_consistency` 和 `require_suite_consistency` 表示 strict guard 是否真的被要求
- `suite_consistency`、`suite_mismatch_count`、`selected_suite_path` 表示这次 handoff 继承的 suite 证据是什么

`workflow_suite_path` 和 `workflow_suite_name` 是辅助读值，帮助审阅者确认 handoff 的 suite 证据来自哪条 workflow 路线。

### `_summary()`

`_summary()` 现在把 suite guard 也提升进 summary：

```python
"decision_require_suite_consistency"
"require_suite_consistency"
"suite_consistency"
"suite_mismatch_count"
"selected_suite_path"
```

这样 CSV、Markdown、HTML 都能直接用 summary，而不是分别去拆 report 顶层和 nested workflow summary。

### `_recommendations()`

如果 handoff 是 strict 模式，但 `suite_consistency` 不是 `consistent`，推荐语会直接提醒：

```text
Fix benchmark suite consistency before executing this handoff as clean model-quality evidence.
```

这是一个审阅提示，不是新的阻断逻辑。真正的阻断仍然在 decision 层。

## `scripts/execute_training_scale_handoff.py`

CLI 本体没有再加新参数，它继续做两件事：

1. 调用 `build_training_scale_handoff()`
2. 写出 `training_scale_handoff.json/csv/md/html`

这层的价值是把 controlled handoff 变成一个可重放的审阅命令。v205 让这个命令输出的证据更完整，不再丢掉 strict suite boundary。

## 输出文件的角色

- JSON：最终机器可读证据，包含顶层 `suite_guard`
- CSV：便于快速筛查 suite guard 是否存在
- Markdown：适合人工快速复核和代码讲解引用
- HTML：适合在本地打开看审阅版证据

它们都不是新判断源，而是同一份 handoff 事实的不同展示面。

## 测试覆盖

`tests/test_training_scale_handoff.py` 新增了一个核心测试：

```python
test_carries_suite_guard_from_workflow_and_decision
```

它验证了：

- workflow summary 里的 strict guard 能进入 handoff summary
- handoff 顶层 `suite_guard` 能保留 strict 证据
- CSV、Markdown、HTML 都能显示 `Require suite consistency`
- `selected_suite_path` 也能穿过 workflow/decision/handoff 三层

除此之外，原来的 planned / execute / failed / HTML escape 测试继续保护旧行为没有被破坏。

## 运行结果与证据

本版对应的运行证据放在 `c/205`：

- `图片/01-handoff-suite-guard-tests.png`
- `图片/02-handoff-suite-guard-planned-smoke.png`
- `图片/03-handoff-suite-guard-execute-smoke.png`
- `图片/04-handoff-artifact-suite-guard-smoke.png`
- `图片/05-source-encoding-smoke.png`
- `图片/06-full-unittest.png`
- `图片/07-docs-check.png`

这组证据组合的意义是：

1. 代码层测试证明字段透传逻辑正确
2. planned handoff 证明非执行审阅时也能看到 strict suite boundary
3. executed handoff 证明执行后的证据仍然保留 suite boundary
4. artifact smoke 证明 JSON/CSV/Markdown/HTML 四种输出都带着同一层 suite evidence
5. source encoding 和全量 unittest 证明这不是局部热修，而是仓库级可维护状态

## 证据边界

v205 仍然不证明模型更强了。

它证明的是：训练规模链路从 workflow 到 handoff 的审阅面，已经能连续携带同一条 suite-consistency 证据链。这样人工或后续工具在审阅 `--execute` 命令时，不会误把“流程完整”当成“模型质量已被 clean comparison 证明”。

## 一句话总结

v205 把 strict suite-consistency 证据从 workflow 决策继续送到 controlled handoff 报告，让 reviewed execute 命令也保留同一条 suite boundary。
